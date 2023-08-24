import asyncio
import datetime
from datetime import datetime, timedelta, timezone
import io
import json
import logging
import os
import configparser
import AC_server_command
import ir_data_gui

import discord
import random
import openai
import iracing_stats
from IR_api_handler import IR_Handler
from ir_service_monitor import ir_service_monitor
from discord import Embed, File, app_commands
from discord.ext import commands
from dotenv import load_dotenv
from gpt import OpenAI
import re
import pandas as pd
import interactions


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
#client = interactions.Client(intents=intents)

# Setup Some Variables

last_cleanup_time = 0
cleanup_interval = 12
global cleanup_enabled
cleanup_enabled = True
ir_service_monitor_enabled = False
user_id_to_monitor = 663521697860943936  # iRacing Stats bot
self_id_to_monitor = 1085398619278024766  # ChatSRD bot
ir_service_monitor_channels = [
    1121817152081629234,
    204786457280380928,
]  # iRacing Service Monitor
# Setup Logging
logger = logging.getLogger("chatsrd_log")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("chat_srd.log", encoding="utf-8", mode="a")
print(f"Log file created at: {handler.baseFilename}")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)
iracing_api = IR_Handler()

load_dotenv()
import json

openai = OpenAI()
config = configparser.ConfigParser()

bot_commands = [command.name for command in bot.commands]


def load_configuration():
    with open("chatsrd-configuration.json", "r") as file:
        configuration = json.load(file)
    return configuration


def save_configuration(configuration):
    with open("chatsrd-configuration.json", "w") as file:
        json.dump(configuration, file, indent=4)


def ms_to_laptime(ms):
    total_secs = ms / 10000  # this is not ms but 1/10000th of a second
    minutes = int(total_secs // 60)
    seconds = int(total_secs % 60)
    remaining_ms = int(ms % 1000)
    return f"{minutes}:{seconds:02d}.{remaining_ms:03d}"


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]

@bot.command(
    name="chief",
    help="Sets up an OpenAI chatbot and responds to user prompts with generated text.\n Usage: /chief <prompt>",)
async def chief(ctx, *message: str):
    configuration = load_configuration()
    if configuration["setup_ai"] is True:
        prompt = "".join(f"{word} " for word in message)
        openai_check_result = openai.setup_ai(prompt)
        logger.info(f"Chief command called with prompt: {prompt}")
        # if openai.setup_ai is none retry the prompt 5 times
        if openai_check_result is None:
            logger.info("An error occured, retrying prompt.")
            await asyncio.sleep(5)
            for _ in range(5):
                openai_check_result = openai.setup_ai(prompt)
                if openai_check_result is not None:
                    break
        else:
            await ctx.send(openai_check_result)
            logger.info(f"Chief command called by {ctx.author} with prompt: {prompt}")
    else:
        await ctx.send("Chat-SRD OpenAI Integration is currently disabled.")
        return


@bot.command(name="setupsheet", help="Displays a car setup cheat sheet")
async def setupsheet(ctx):
    await ctx.send(file=File(".\\images\setup-sheet.jpg"))
    logger.info(f"{ctx.author} called the setupsheet command.")


@bot.command(name="sdk", help="Watch SDK get into a wreck")
async def sdk(ctx):
    await ctx.send("https://www.twitch.tv/sdktheway")
    logger.info(f"{ctx.author} called the SDK command.")


@bot.command(
    name="commands", help="Show a list of all Chat-SRD commands\n Usage: /commands"
)
async def commands_list(ctx):
    embed = Embed(
        title="Chat-SRD Commands",
        description="Here's a list of available commands:",
        color=0x00FF00,  # Green color
    )

    # Add a field to embed. embed. add_field name value help inline False
    for command in bot.commands:
        embed.add_field(name=command.name, value=command.help, inline=False)

    await ctx.send(embed=embed)
    logger.info(f"{ctx.author} used the retrieved the command list.")


@bot.command(
    name="autoclean",
    help="Enables or disables the automated iRacing Stats Cleanup.\n Usage: /autoclean <enable/disable>",
)
async def autoclean(ctx, action: str):
    if action.lower() not in ["enable", "disable"]:
        await ctx.send(
            "Invalid action. Please use either /autoclean enable or disable."
        )
        logger.warning("Invalid action entered for /autoclean command.")
        return
    if action.lower() == "enable":
        cleanup_enabled = True
        await ctx.send("iRacing Stats Cleanup enabled.")
        logger.info(
            f"{ctx.author} enabled iRacing Stats Autoclean. Autoclean interval: {cleanup_interval} hours."
        )
    elif action.lower() == "disable":
        cleanup_enabled = False
        await ctx.send("iRacing Stats Cleanup Autoclean disabled.")
        logger.info(f"{ctx.author} disabled the iRacing Stats Autoclean.")


@bot.command(
    name="ir_service_monitor",
    help="Enables or disables the automated iRacing Service Monitor.\n Usage: /ir_service_monitor <enable/disable>",
)
@commands.has_permissions(manage_messages=True)
async def ir_service_monitor(ctx, action: str):
    if action.lower() not in ["enable", "disable"]:
        await ctx.send(
            "Invalid action. Please use either /ir_service_monitor enable or disable."
        )
        logger.warning("Invalid action entered for /ir_service_monitor command.")
        return
    if action.lower() == "enable":
        ir_service_monitor_enabled = True
        await ctx.send("iRacing Service Monitor enabled.")
        logger.info(f"{ctx.author} enabled iRacing Service Monitor.")
    elif action.lower() == "disable":
        ir_service_monitor_enabled = False
        await ctx.send("iRacing Service Monitor disabled.")
        logger.info(f"{ctx.author} disabled the iRacing Service Monitor.")


@bot.command(
    name="interval",
    help="Sets the time in hours iRacing Stats Cleanup will wait between each cleanup.\n Usage: /interval <hours>",
)
@commands.has_permissions(manage_messages=True)
async def interval(ctx, hours: int):
    global cleanup_interval
    cleanup_interval = hours
    await ctx.send(
        f"iRacing Stats Thread Cleanup interval set to {cleanup_interval} hours."
    )
    logger.info(
        f"{ctx.author} set the iRacing Stats Thread Cleanup interval to {cleanup_interval} hours."
    )


@bot.command(
    name="cleanup", help="Manually cleans up iRacing Stats threads.\n Usage: /cleanup"
)
async def cleanup_now(ctx):
    global last_cleanup_time, cleanup_interval, cleanup_enabled, user_id_to_monitor

    now = datetime.now()
    for channel_id in read_channel_ids():
        channel = bot.get_channel(channel_id)
        if channel:
            deleted_messages = []
            async for message in channel.history(limit=None):
                if (
                    message.author.id == user_id_to_monitor
                    and message.created_at.timestamp()
                    < (now - timedelta(hours=cleanup_interval)).timestamp()
                ):
                    await message.delete()
                    logger.info(
                        f"Deleted messages by {message.author} in {message.channel}:\n{message.content}"
                    )
                    deleted_messages.append(message)
                    await asyncio.sleep(1.5)

                elif (
                    message.author.id == self_id_to_monitor
                    and message.created_at.timestamp()
                    < (now - timedelta(hours=cleanup_interval)).timestamp()
                ):
                    await message.delete()
                    await asyncio.sleep(1.5)
                    logger.info(
                        f"Deleted messages by {message.author} in {message.channel}:\n{message.content}"
                    )
            await channel.send(
                f"iRacing Reports \ Chat-SRD Cleanup Completed: Deleted {len(deleted_messages)} messages."
            )
            logger.info("Auto Cleanup iRacing Stats message on schedule.")


def read_channel_ids():
    with open("chatsrd-configuration.json", "r") as file:
        data = json.load(file)
        return data["channel_ids"]


def update_channel_ids(channel_ids):
    with open("chatsrd-configuration.json", "w") as file:
        json.dump(channel_ids, file)


@bot.command(
    name="channel",
    help="Add or remove a text channel ID where the bot is allowed to perform cleanup and cleanup activities.\n Usage: /channel <add/remove> <forum/text> <channel_id>",
)
@commands.has_permissions(manage_messages=True)
async def set_channel(ctx, action: str, channel_id: int):
    channel_ids = read_channel_ids()
    if action.lower() not in ["add", "remove"]:
        await ctx.send("Invalid action. Please use either /channel add or remove.")
        logger.warning("Invalid action entered for /channel command.")
        return
    if action.lower() == "add":
        if channel_id not in channel_ids:
            channel_ids.append(channel_id)
            print("Text channel ID {channel_id} has been added.")
            logger.info(f"Text channel ID {channel_id} has been added.")
        else:
            await ctx.send(f"Text channel ID {channel_id} is already in the list.")
            print("Text channel ID {channel_id} is already in the list.")
            logger.info(f"Text channel ID {channel_id} is already in the list.")
    if action.lower() == "remove":
        if channel_id in channel_ids:
            channel_ids.remove(channel_id)
            await ctx.send(f"Text channel ID {channel_id} has been removed.")
            print(f"Text channel ID {channel_id} has been removed.")
            logger.info(f"Text channel ID {channel_id} has been removed.")
        else:
            print(f"Text channel ID {channel_id} is not in the list.")
            await ctx.send(f"Text channel ID {channel_id} is not in the list.")

    # Update the channel IDs in the JSON file

    update_channel_ids(channel_ids)
    logger.ingo(f"{ctx.author} updated the channel IDs in the JSON file.")


@bot.command(
    name="log",
    help="Sends the log file as an attachment or clears it.\n Usage: /log <get/clear>",
)
@commands.has_permissions(manage_messages=True)
async def log(ctx, action: str = "get"):
    log_file = next(
        (
            handler.baseFilename
            for handler in logger.handlers
            if isinstance(handler, logging.FileHandler)
        ),
        None,
    )
    if log_file is None:
        await ctx.send("No log file found.")
        return

    if action.lower() == "get":
        try:
            with open("chat_srd.log", "rb") as log_file:
                log_content = log_file.read()

            if log_content:
                log_bytes = io.BytesIO(log_content)
                log_attachment = discord.File(log_bytes, filename="chat_srd.log")
                await ctx.send(file=log_attachment)
                logger.info("The log file has been sent.")
            else:
                await ctx.send("The log file is empty.")
        except FileNotFoundError:
            await ctx.send("The log file could not be found.")
            logger.info("The log file could not be found.")
    elif action.lower() == "clear":
        try:
            with open(log_file, "w") as f:
                f.truncate(0)
                logger.info("The log file has been cleared.")

            await ctx.send("The log file has been cleared.")
            logger.info("The log file has been cleared.")
        except FileNotFoundError:
            await ctx.send("The log file could not be found.")
    else:
        await ctx.send("Invalid action. Usage: /log <get/clear>")
        logger.warning("Invalid action entered for /log command.")


# Start the bot and set cleanup time


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord.")
    logger.info(f"{bot.user.name} has connected to Discord.")
    try: 
        synced = await bot.tree.sync()
        print(f"Synced {synced} commands")
    except Exception as e:
        print(e)
    global last_cleanup_time
    last_cleanup_time = datetime.now()
    logger.info("Chat SRD Autoclean has started.")
    bot.loop.create_task(cleanup_old_messages())
    AC_server_command.parse_results_json()
    # bot.loop.create_task(ir_service_monitor_task())

@commands.has_permissions(manage_messages=True)
@bot.tree.command (name='say')
@app_commands.describe(thing_to_say = "What to say")
async def say(Interaction: discord.Interaction, thing_to_say: str):
    await Interaction.response.send_message(thing_to_say, ephemeral = False)

async def ir_service_monitor_task():
    global ir_service_monitor_enabled
    while True:
        if ir_service_monitor_enabled:
            webhook_url = "https://discord.com/api/webhooks/1134726152150331442/g_DeNqVdYBLUCrhovxULDxCKECvYs3hXO8lIscDRB9tv6hoi8M0uy8OV5eAWFQf7r2wI"
            service_monitor = ir_service_monitor(webhook_url)
            channel = bot.get_channel(ir_service_monitor_channels[0])
            maintenance_message = []
            while True:
                status = await service_monitor.fetch_status()
                if status["maint_messages"] != maintenance_message:
                    maintenance_message = [status["maint_messages"]]
                    await channel.send(
                        f"iRacing Maintenance Message: {maintenance_message}"
                    )
                else:
                    print("IR Service Monitor disabled")
                await asyncio.sleep(60)


async def cleanup_old_messages():
    """purpose: Deletes messages older than the cleanup interval from the channels in the channel_ids list."""

    global last_cleanup_time, cleanup_interval, cleanup_enabled, user_id_to_monitor

    while not bot.is_closed():
        if cleanup_enabled:
            now = datetime.now()

        if now > last_cleanup_time + timedelta(hours=cleanup_interval):
            last_cleanup_time = now
            for channel_id in read_channel_ids():
                channel = bot.get_channel(channel_id)
                if channel:
                    deleted_messages = []
                    async for message in channel.history(limit=None):
                        if (
                            message.author.id in user_id_to_monitor
                            and message.created_at.timestamp()
                            < (now - timedelta(hours=cleanup_interval)).timestamp()
                        ):
                            await message.delete()
                            logger.info(
                                f"Deleted messages by {message.author} in {message.channel}:\n{message.content}"
                            )
                            deleted_messages.append(message)
                    await channel.send(
                        f"iRacing Reports \ Chat-SRD Cleanup Completed: Deleted {len(deleted_messages)} messages."
                    )
                    logger.info("Auto Cleanup iRacing Stats message on schedule.")
        await asyncio.sleep(60)  # check every minute


# Assetto Corsa Server Commands
# Commands to manage the AC server


@bot.command(
    name="ac_config", help="View the AC server configuration menu.\n Usage: /ac_config"
)
async def ac_config(ctx):
    view = AC_server_command.ConfigSelectView()
    await ctx.send("Select a configuration category:", view=view, delete_after=45)


@bot.command(
    name="ac_menu", help="View the AC server configuration menu.\n Usage: /ac_menu"
)
async def ac_menu(ctx):
    view = AC_server_command.MenuView()
    await ctx.send("Select a configuration category:", view=view, delete_after=45)


@bot.command(
    name="ac_set",
    help="Updates a key-value pair in the AC server configuration file.\n Usage: /ac_set <section> <value> \n /ac_set SERVER tc_allowed 1",
)
@commands.has_permissions(manage_messages=True)
async def ac_set(ctx, section: str, key: str, *, value: str):
    # Load the existing config file
    config.read(".\\ac_server_config\discord_server_cfg.ini")
    # If the section exists in the config
    section_lower = section.lower()
    config_changes = []
    # Check if the section exists in the config (ignoring case)
    for config_section in config.sections():
        if config_section.lower() == section_lower:
            # If the key exists in the section
            if key in config[config_section]:
                # Update the key with the new value
                config[config_section][key] = value
                # Save the updated config file
                with open(
                    ".\\ac_server_config\discord_server_cfg.ini", "w"
                ) as configfile:
                    config.write(configfile)
                config_changes.append(
                    f"Setting: {key} Section: {config_section} Value: {value}."
                )
                await ctx.send(f"Updated {key} in {config_section} with {value}.")
                print(config_changes)
                AC_server_command.merge_configs()
                logger.info(
                    f"{ctx.author} updated {key} in {config_section} with {value} and the configuration has been merged with base config."
                )
                return
            else:
                await ctx.send(f"{section} not found in the config file.")
                logger.warning(
                    f"Key not found:  {ctx.author} tried to update {key} in {config_section} with {value} but the key was not found in the config file."
                )


@bot.command(
    name="ac_uploadftp",
    help="Uploads the AC server configuration to the FTP server.\n Usage: /ac_uploadftp",
)
@commands.has_permissions(manage_messages=True)
async def ac_uploadftp(ctx):
    AC_server_command.upload_ftp()
    await ctx.send("New Config has been uploaded to the FTP Server.")
    logger.info(f"{ctx.author} uploaded the configuration to the FTP server.")


@bot.command(
    name="ac_getresults",
    help="Downloads the results from the AC server.\n Usage: /ac_getresults",
)
@commands.has_permissions(manage_messages=True)
async def ac_getresults(ctx):
    AC_server_command.ftp_getresults()
    await ctx.send("Results have been downloaded from the AC server.")
    logger.info(f"{ctx.author} downloaded the results from the AC server.")


@bot.command(
    name="ac_parseresults",
    help="Parses the results from the AC server.\n Usage: /ac_parseresults",
)
@commands.has_permissions(manage_messages=True)
async def ac_parseresults(ctx):
    AC_server_command.parse_results_json()
    await ctx.send("Results have been manually parsed.")
    logger.info(f"{ctx.author} manually parsed the results from the AC server.")


@bot.command(
    name="ac_results",
    help="Displays the results from the AC server.\n Usage: /ac_results",
)
async def ac_results(ctx: commands.Context):
    session_data = AC_server_command.parse_results_json()
    view = AC_server_command.ResultsSelectView(session_data)
    await ctx.send("Select a session:", view=view)


# IRacing Commands
# Commands to pull iRacing stats


@bot.command(name="ir_menu", help="View the iRacing Data GUI.\n Usage: /ir_menu")
async def ir_menu(ctx):
    view = ir_data_gui.ir_MenuView()
    await ctx.send("", view=view, delete_after=45)


@bot.tree.command(name='ir_incidents', description='Displays a bar graph of recent incidents per driver.')
@app_commands.describe(driver_names="Enter the driver names separated by commas.")
async def ir_incidents(Interaction: discord.Interaction, driver_names: str):
    # Process the driver names
    name_list = [name.strip() for name in driver_names.split(",")]
    
    # Fetch data and create the bar graph
    data = iracing_api.get_recentincidents(*name_list)
    iracing_stats.bar_graph_recentincidents(data)
    
    # Prepare the file and embed to send
    file = discord.File("./images/incidents.png", filename="incidents.png")
    hot_pink = int("FF69B4", 16)
    embed = discord.Embed(
        title="Recent Incidents per Driver",
        description=f"Recent incident Report for {driver_names}.",
        color=hot_pink,
    )
    embed.set_image(url="attachment://incidents.png")
    
    # Send the embed and file
    await Interaction.response.send_message(embed=embed, file=file, ephemeral=False)



@bot.command()
async def ir_eventlist(ctx, season_year=None, season_quarter=None):
    data = iracing_api.get_eventlist(
        season_year, season_quarter
    )  # Assuming this returns a dict
    if not season_quarter or not season_year:
        season_year, season_quarter = iracing_api.get_current_year_season()
    if data.get("seasons"):
        embeds = []
        for i in range(0, len(data["seasons"]), 10):
            embed = discord.Embed(
                title=f"Events for {season_year} Q{season_quarter}", color=0x00FF00
            )
            events = "\n".join(
                [
                    f"{index+1}. {event['season_name']}"
                    for index, event in enumerate(data["seasons"][i : i + 10])
                ]
            )
            embed.add_field(name="Events", value=events, inline=False)
            embeds.append(embed)

        view = ir_data_gui.EmbedPaginatorView(embeds)
        view.ctx = ctx
        view.message = await ctx.send(embed=embeds[0], view=view)
    else:
        embed = discord.Embed(
            title=f"Events for {season_year} Q{season_quarter}",
            description=f"No events found for {season_year} Q{season_quarter}.",
            color=0x00FF00,
        )
        await ctx.send(embed=embed)


@bot.tree.command(name='ir_careerstats', description='Displays a driver\'s career stats.')
@app_commands.describe(
    driver_name="Enter the drivers iRacing name "
)
async def ir_careerstats(Interaction: discord.Interaction, driver_name: str):
    #display_name = " ".join(display_name)
    data = iracing_api.get_member_stats(driver_name)

    # Create an embed object
    hot_pink = int("FF69B4", 16)
    embed = Embed(
        title="Driver Career Stats",
        color=hot_pink,
        timestamp=datetime.now(timezone.utc),
        description=f"Career Stats for {driver_name}",
    )
    embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")

    # Loop through each category in the stats
    for item in data["stats"]:
        category_id = item["category_id"]
        category = item["category"]
        starts = item["starts"]
        wins = item["wins"]
        top5 = item["top5"]
        poles = item["poles"]
        avg_start_position = item["avg_start_position"]
        avg_finish_position = item["avg_finish_position"]
        laps = item["laps"]
        laps_led = item["laps_led"]
        avg_incidents = item["avg_incidents"]
        avg_points = item["avg_points"]
        win_percentage = item["win_percentage"]
        top5_percentage = item["top5_percentage"]
        laps_led_percentage = item["laps_led_percentage"]
        total_club_points = item["total_club_points"]

        # Add a field to the embed object
        embed.add_field(
            name=category,
            value=f"Starts: {starts}\nWins: {wins}\nTop 5s: {top5}\nPoles: {poles}\nAvg Start Position: {avg_start_position}\nAvg Finish Position: {avg_finish_position}\nLaps: {laps}\nLaps Led: {laps_led}\nAvg Incidents: {avg_incidents}\nAvg Points: {avg_points}\nWin Percentage: {win_percentage}\nTop 5 Percentage: {top5_percentage}\nLaps Led Percentage: {laps_led_percentage}\nTotal Club Points: {total_club_points}",
            inline=True,
        )

    await Interaction.response.send_message(embed=embed)


@bot.tree.command(name='ir_stats', description='Displays one or more driver\'s iRating history.')
@app_commands.describe(
    driver_names="Enter one or more driver's iRacing name. If entering multiple drivers use commas.",
    start_date="Enter the start date for the iRating plot. (Optional)",
    end_date="Enter the end date for the iRating plot. (Optional)"
)
async def ir_stats_slash(Interaction: discord.Interaction, driver_names: str, start_date: str = None, end_date: str = None):
    # Extract drivers
    drivers = [driver.strip() for driver in driver_names.split(",")]

    try:
        # Pass the driver names to the function
        chart_data = iracing_api.get_member_irating_chart(*drivers)
        iracing_stats.line_chart_irating(chart_data, start_date, end_date)

        hot_pink = int("FF69B4", 16)
        file = discord.File("./images/driver_irating.png", filename="driver_irating.png")
        embed = discord.Embed(
            title="iRating History",
            description=f"IRating over time for driver(s) {drivers}.\n Date Filter: {start_date or 'Start Date Not Specified'} - {end_date or 'End Date Not Specified'}",
            color=discord.Color(hot_pink),
        )
        embed.set_image(url="attachment://driver_irating.png")
        embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")

        await Interaction.response.send_message(embed=embed, file=file, ephemeral=False)

    except Exception as e:
        await Interaction.response.send_message(str(e))


@bot.tree.command(name='ir_lastrace', description="Display Stats on a drivers last race.")
@app_commands.describe(
    driver_name="Enter the driver's iRacing name.")
async def ir_lastrace_slash(Interaction: discord.Interaction , driver_name:str):
    data = iracing_api.get_member_last_race(driver_name)
    subsession_id = data["subsession_id"]
    subsession_data = iracing_api.get_subsession(subsession_id)
    # add a check to see if the data is empty
    irating_change = data["newi_rating"] - data["oldi_rating"]
    if not data:
        await Interaction.response.send_message("No data found for this driver.")
        return
    qualifying_time = data["qualifying_time"]
    if qualifying_time == 0:
        qualifying_time = "No Time Recorded"

    hot_pink = int("FF69B4", 16)
    embed = Embed(
        title=f"Last Race Results for {driver_name}", color=discord.Color(hot_pink)
    )
    embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")
    embed.add_field(name="Year", value=subsession_data["season_year"], inline=True)
    embed.add_field(name="Season", value=subsession_data["season_quarter"], inline=True)
    embed.add_field(
        name="Race Week", value=subsession_data["race_week_num"] + 1, inline=True
    )
    embed.add_field(name="Series Name", value=data["series_name"], inline=False)
    embed.add_field(name="Track Name", value=data["track"]["track_name"], inline=True)
    embed.add_field(
        name="Track Configuration",
        value=subsession_data["track"]["config_name"],
        inline=True,
    )
    embed.add_field(
        name="Weather",
        value="Ambient Temperature:"
        + " "
        + str(subsession_data["weather"]["temp_value"])
        + "f"
        + "\n"
        + "Relative Humidity:"
        + " "
        + str(subsession_data["weather"]["rel_humidity"])
        + "%",
        inline=False,
    )
    embed.add_field(
        name="Strength of Field", value=data["strength_of_field"], inline=False
    )
    embed.add_field(
        name="Session Start Time", value=data["session_start_time"], inline=False
    )
    embed.add_field(name="Qualifying Time", value=qualifying_time, inline=False)
    embed.add_field(name="Winner", value=data["winner_name"], inline=False)
    embed.add_field(name="Start Position", value=data["start_position"], inline=False)
    embed.add_field(name="Finish Position", value=data["finish_position"], inline=False)
    embed.add_field(
        name="Average Lap Time",
        value=ms_to_laptime(subsession_data["race_summary"]["average_lap"]),
        inline=False,
    )
    embed.add_field(name="Laps Led", value=data["laps_led"], inline=False)
    embed.add_field(name="Incidents", value=data["incidents"], inline=False)
    embed.add_field(name="Season Points Earned", value=data["points"], inline=False)
    irating_str = f"{irating_change:+} ({data['newi_rating']})"
    embed.add_field(name="iRating", value=irating_str, inline=False)
    # embed.set_footer(text="chat-SRD iRacing Data API Bot - #Simracing Discord")
    await Interaction.response.send_message(embed=embed)


@bot.tree.command(name='ir_consistency', description="Display a Driver's lap consistency ")
@app_commands.describe(
    driver_name="Enter the driver's iRacing name.",
    subsession_id="Enter the subsession ID if known, or leave blank. (Optional)"
)
async def ir_consistency_slash(Interaction: discord.Interaction, driver_name: str, subsession_id: int = None):

    if not driver_name:
        await Interaction.response.send_message("Please specify a driver.", ephemeral=True)
        return

    try:
        lap_data = iracing_api.get_laptimes(driver_name, subsession_id)
        if subsession_id is None:
            race_data = iracing_api.get_member_last_race(driver_name)
            car = iracing_api.get_carmodel(race_data["car_id"])
        else:
            race_data = iracing_api.get_subsession(subsession_id)
            car = "car"
        
        iracing_stats.line_chart_laps(lap_data)

        hot_pink = int("FF69B4", 16)
        file = discord.File("./images/line_chart_laps.png", filename="line_chart_laps.png")
        embed = discord.Embed(
            title="Lap Consistency",
            description=f"Lap Times for driver {driver_name}.",
            color=discord.Color(hot_pink),
        )
        embed.add_field(name="Series Name:", value=race_data["series_name"], inline=False)
        embed.add_field(name="Car Driven:", value=car, inline=False)
        embed.set_image(url="attachment://line_chart_laps.png")
        embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")

        await Interaction.response.send_message(embed=embed, file=file, ephemeral=False)

    except Exception as e:
        await Interaction.response.send_message(str(e), ephemeral=True)


@bot.tree.command(name='ir_raceposition', description='Plots a line chart of driver position over a race session.')
@app_commands.describe(
    subsession_id="Enter the subsession ID for the desired race session.",
    interpolate="Select if you want to interpolate the data. If not selected, standard data will be used."
)
async def ir_raceposition_slash(Interaction: discord.Interaction, subsession_id: int, interpolate: bool = False):
    data = iracing_api.get_race_position_data(subsession_id)
    try:
        if interpolate:
            iracing_stats.line_chart_race_position_interpolate(data)
            image_filename = "race_position_line_interpolate.png"
        else:
            iracing_stats.line_chart_race_position(data)
            image_filename = "race_position_line.png"

        hot_pink = int("FF69B4", 16)
        file = discord.File(
            f"./images/{image_filename}", filename=image_filename
        )

        if interpolate: 
            embed = discord.Embed(
            title="Driver Position through Race - Interpolated",
            description=f"Driver position interpolated line plot for Race Session {subsession_id}.\n",
            color=discord.Color(hot_pink)
        )
        else:
            embed = discord.Embed(
            title="Driver Position through Race",
            description=f"Driver position line plot for Race Session {subsession_id}.\n",
            color=discord.Color(hot_pink))

        embed.set_image(url=f"attachment://{image_filename}")
        embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")

        await Interaction.response.send_message(embed=embed, file=file, ephemeral=False)

    except Exception as e:
        await Interaction.response.send_message(str(e), ephemeral=True)

@bot.command(
    name="ir_raceposition_interpolate",
    help="Chart the lap position of each driver over the race session into interpolated curves. \n Usage: /ir_raceposition_interpolate <driver> <subsession_id>",
)
async def ir_raceposition_interpolate(ctx, subsession_id):
    data = iracing_api.get_race_position_data(subsession_id)
    iracing_stats.line_chart_race_position_interpolate(data)
    hot_pink = int("FF69B4", 16)
    file = discord.File(
        "./images/race_position_line_interpolate.png",
        filename="race_position_line_interpolate.png",
    )
    embed = Embed(
        title="Driver Position through Race",
        description=f"Driver position interpolated line plot for Race Session {subsession_id}.\n",
        color=discord.Color(hot_pink),
    )
    embed.set_image(url="attachment://race_position_line_interpolate.png")
    embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")
    await ctx.send(file=file, embed=embed)


@bot.command(name="ir_commands", help="List all available iracing stats commands")
async def ir_commands(ctx):
    hot_pink = int("FF69B4", 16)
    embed = Embed(
        title="iRacing Stats Commands",
        description="List of all available iRacing Stats commands",
        color=discord.Color(hot_pink),
    )
    embed.add_field(
        name="chief",
        value="Get setup advice from AI trained crew chief. \n Usage: >chief How can I reduce understeer if I'm understeering while steering.",
        inline=False,
    )
    embed.add_field(
        name="ir_menu",
        value="Display the iRacing Stats GUI.\n *In Progress*.",
        inline=False,
    )
    embed.add_field(
        name="ir_stats",
        value="Display an iRating line graph for one or multiple drivers. Range can be customized by including start_date and/or end_date arguments.\n Usage: >ir_stats <driver> \n >ir_stats <driver1>, <driver2> \n >ir_stats <driver1>, <driver2> start_date <yyyy-mm-dd> end_date <yyyy-mm-dd>",
        inline=False,
    )
    embed.add_field(
        name="ir_careerstats",
        value="Display Career Stats for all series.\n Usage: >ir_careerstats <driver>",
        inline=False,
    )
    embed.add_field(
        name="ir_lastrace",
        value="Display the results of a drivers last race.\n Usage: >ir_lastrace <driver>",
        inline=False,
    )
    embed.add_field(
        name="ir_consistency",
        value="Display a line graph of a drivers lap times with trend line. Without supplying a subsession ID, the last race will be used.\n Usage: >ir_consistency <driver> \n >ir_consistency <subsession_id>",
        inline=False,
    )
    embed.add_field(
        name="ir_incidents",
        value="Display a bar graph of one or many drivers incidents.\n Usage: >ir_incidents <driver> \n >ir_incidents <driver1>, <driver2>",
        inline=False,
    )
    embed.add_field(
        name="ir_raceposition",
        value="Display a line graph of driver positions during the race.\n Usage: >ir_raceposition <subsession_id>",
        inline=False,
    )
    embed.add_field(
        name="ir_raceposition_interpolate",
        value="Display an interpolated line graph of driver positions during the race.\n Usage: >ir_raceposition_interpolate <subsession_id>",
        inline=False,
    )
    embed.add_field(
        name="ir_eventlist",
        value="Displays the iRacing event list for all licenses. Returns current year/season if no arguments supplied.\n Usage: >ir_eventlist \n >ir_eventlist <year> <season>",
        inline=False,
    )
    embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")
    await ctx.send(embed=embed)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        print(f"Received button click: {interaction.data}")


@bot.event
async def on_error(event, *args, **kwargs):
    with open("err.log", "a") as f:
        if event == "on_message":
            f.write(f"Unhandled message: {args[0]}\n")
        else:
            raise


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    bot.run(token)
