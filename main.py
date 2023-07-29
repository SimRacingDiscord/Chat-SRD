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
from discord import Embed, File
from discord.ext import commands
from dotenv import load_dotenv
from gpt import OpenAI
import re
import pandas as pd


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix=">", intents=intents)

# Setup Some Variables

last_cleanup_time = 0
cleanup_interval = 12
global cleanup_enabled
cleanup_enabled = True
user_id_to_monitor = [663521697860943936, 1085398619278024766]  # iRacing Stats bot
self_id_to_monitor = 1085398619278024766  # ChatSRD bot

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


@bot.command(
    name="chief",
    help="Sets up an OpenAI chatbot and responds to user prompts with generated text.\n Usage: /chief <prompt>",
)
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
                    message.author.id in user_id_to_monitor
                    and message.created_at.timestamp()
                    < (now - timedelta(hours=cleanup_interval)).timestamp()
                ):
                    await message.delete()
                    logger.info(
                        f"Deleted messages by {message.author} in {message.channel}:\n{message.content}"
                    )
                    deleted_messages.append(message)
                    await asyncio.sleep(1)
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
    global last_cleanup_time
    last_cleanup_time = datetime.now()
    logger.info("Chat SRD Autoclean has started.")
    bot.loop.create_task(cleanup_old_messages())
    AC_server_command.parse_results_json()


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


@bot.command(
    name="ir_incidents",
    help="Displays the recent incidents for the specified drivers.\n Usage: /ir_incidents <driver1>, <driver2>, <driver3>",
)
async def ir_incidents(ctx, *, names_input):
    name_list = []
    name_list = [name.strip() for name in names_input.split(",")]
    data = iracing_api.get_recentincidents(*name_list)
    iracing_stats.bar_graph_recentincidents(data)
    file = discord.File("./images/incidents.png", filename="incidents.png")
    embed = discord.Embed(
        title="Recent Incidents per Driver", description="Recent incident Report."
    )
    embed.set_image(url="attachment://incidents.png")
    await ctx.send(file=file, embed=embed)


@bot.command(
    name="ir_stats",
    help="Displays the iRacing stats for the specified drivers.\n Usage: /ir_stats <driver1>, <driver2>, <driver3>",
)
async def ir_stats(ctx, *args):
    raw_args = " ".join(args)
    split_args = raw_args.split("start_date")  # Split arguments by 'start_date'
    # Extract drivers
    drivers = [driver.strip() for driver in split_args[0].split(",") if driver.strip()]
    # Extract dates
    start_date_str = None
    end_date_str = None
    if len(split_args) > 1:
        dates = split_args[1].split("end_date")
        start_date_str = dates[0].strip()
        if len(dates) > 1:
            end_date_str = dates[1].strip()
    try:
        # Pass the driver names and dates to the function
        chart_data = iracing_api.get_member_irating_chart(*drivers)
        iracing_stats.line_chart_irating(chart_data, start_date_str, end_date_str)
    except Exception as e:
        await ctx.send(str(e))

    data = iracing_api.get_member_irating_chart(*drivers)
    dates = []
    if start_date_str or end_date_str:
        dates.extend((start_date_str, end_date_str))
    else:
        dates.append("No Date Selected")
    # Passing the data and dates to the plotting function
    iracing_stats.line_chart_irating(data, start_date_str, end_date_str)
    hot_pink = int("FF69B4", 16)
    file = discord.File("./images/driver_irating.png", filename="driver_irating.png")
    embed = Embed(
        title="iRating History",
        description=f"IRating over time for driver(s) {drivers}.\n Date Filter: {dates}.",
        color=discord.Color(hot_pink),
    )
    embed.set_image(url="attachment://driver_irating.png")
    embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")
    await ctx.send(file=file, embed=embed)


@bot.command(
    name="ir_lastrace",
    help="Return stats for the drivers last race. \n Usage: /ir_lastrace <driver>",
)
async def ir_lastrace(ctx, *display_name):
    display_name = " ".join(display_name)
    data = iracing_api.get_member_last_race(display_name)
    subsession_id = data["subsession_id"]
    subsession_data = iracing_api.get_subsession(subsession_id)
    # add a check to see if the data is empty
    irating_change = data["newi_rating"] - data["oldi_rating"]
    if not data:
        await ctx.send("No data found for this driver.")
        return
    qualifying_time = data["qualifying_time"]
    if qualifying_time == 0:
        qualifying_time = "No Time Recorded"

    hot_pink = int("FF69B4", 16)
    embed = Embed(
        title=f"Last Race Results for {display_name}", color=discord.Color(hot_pink)
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
    await ctx.send(embed=embed)


@bot.command(
    name="ir_consistency",
    aliases=["in_consistency"],
    help="Return the lap times and trend line for their most recent race. \n Usage: /ir_consistency <driver>",
)
async def ir_consistency(ctx, *args):
    subsession_id = None
    if len(args) == 0:
        await ctx.send("Please specify a driver.")
        return

    try:
        # Check if the last argument can be converted to an int
        # If so, treat it as the subsession_id
        subsession_id = int(args[-1])
        display_name = " ".join(args[:-1])
    except ValueError:
        # If not, treat all arguments as part of the display_name
        display_name = " ".join(args)

    lap_data = iracing_api.get_laptimes(display_name, subsession_id)
    if subsession_id is None:
        race_data = iracing_api.get_member_last_race(display_name)
        car = iracing_api.get_carmodel(race_data["car_id"])
    else:
        race_data = iracing_api.get_subsession(subsession_id)
        car = "car"
    iracing_stats.line_chart_laps(lap_data)
    hot_pink = int("FF69B4", 16)
    file = discord.File("./images/line_chart_laps.png", filename="line_chart_laps.png")
    embed = Embed(
        title="Lap Consistency",
        description=f"Lap Times for driver {display_name}.\n",
        color=discord.Color(hot_pink),
    )
    embed.add_field(name="Series Name:", value=race_data["series_name"], inline=False)
    embed.add_field(name="Car Driven:", value=car, inline=False)
    embed.set_image(url="attachment://line_chart_laps.png")
    embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")
    await ctx.send(file=file, embed=embed)


@bot.command(
    name="ir_raceposition",
    help="Chart the lap position of each driver over the race session. \n Usage: /ir_raceposition <driver> <subsession_id>",
)
async def ir_raceposition(ctx, subsession_id):
    data = iracing_api.get_race_position_data(subsession_id)
    iracing_stats.line_chart_race_position(data)
    hot_pink = int("FF69B4", 16)
    file = discord.File(
        "./images/race_position_line.png", filename="race_position_line.png"
    )
    embed = Embed(
        title="Driver Position through Race",
        description=f"Driver position line plot for Race Session {subsession_id}.\n",
        color=discord.Color(hot_pink),
    )
    embed.set_image(url="attachment://race_position_line.png")
    embed.set_thumbnail(url="https://iili.io/HPr9MoQ.png")
    await ctx.send(file=file, embed=embed)


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
        name="ir_menu",
        value="Display the iRacing Stats GUI.\n *In Progress*.",
        inline=False,
    )
    embed.add_field(
        name="ir_stats",
        value="Display an iRating line graph for one or multiple drivers.\n Usage: >ir_stats <driver> \n >ir_stats <driver1>, <driver2> \n >ir_stats <driver1>, <driver2> start_date <yyyy-mm-dd> end_date <yyyy-mm-dd>",
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
