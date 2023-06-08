import asyncio
import datetime
from datetime import datetime, timedelta
import io
import json
import logging
import os
import configparser
import AC_server_command

import discord
import openai
from discord import Embed, File
from discord.ext import commands
from dotenv import load_dotenv

from gpt import OpenAI

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix='>', intents=intents)

# Setup Some Variables

last_cleanup_time = 0
cleanup_interval = 12 
global cleanup_enabled
cleanup_enabled = True 
user_id_to_monitor = 663521697860943936 # iRacing Stats bot

# Setup Logging 
logger = logging.getLogger("chatsrd_log")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("chat_srd.log", encoding="utf-8", mode="a")
print(f"Log file created at: {handler.baseFilename}")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


load_dotenv()
import json
openai = OpenAI()
config = configparser.ConfigParser()


def load_configuration():
    with open('configuration.json', 'r') as file:
        configuration = json.load(file)
    return configuration

def save_configuration(configuration):
    with open('configuration.json', 'w') as file:
        json.dump(configuration, file, indent=4)

@bot.command(name='chief')
async def chief(ctx, *message: str):
    """
    Sets up an OpenAI chatbot and responds to user prompts with generated
    text.
    
    :param ctx: ctx for the channel where the command was called
    :param message: The message to send to the chatbot
    """
    configuration = load_configuration()
    if configuration['setup_ai'] is True: 
        prompt = "".join(f"{word} " for word in message)
        openai_check_result = openai.setup_ai(prompt)
        logger.info(f"Chief command called with prompt: {prompt}")
        #if openai.setup_ai is none retry the prompt 5 times
        if openai_check_result is None:
            logger.info('An error occured, retrying prompt.')
            await asyncio.sleep(5)
            for _ in range(5):
                openai_check_result = openai.setup_ai(prompt)
                if openai_check_result is not None:
                    break

        else:
            await ctx.send(openai_check_result)
            logger.info(f"Chief command called with prompt: {prompt}")
    else: 
        await ctx.send("Chat-SRD OpenAI Integration is currently disabled.")
        return
        
@bot.command(name='setupsheet', description='Displays a car setup cheat sheet')
async def setupsheet(ctx):
    await ctx.send(file=File('.\\images\setup-sheet.jpg'))
    logger.info(f"{ctx.author} called the setupsheet command.")

@bot.command(name='sdk', description='Watch SDK get into a wreck')
async def sdk(ctx):
    await ctx.send("https://www.twitch.tv/sdktheway")
    logger.info(f"{ctx.author} called the SDK command.")

@bot.command(name='commands', help='Show a list of all Chat-SRD commands\n Usage: /commands')
async def commands_list(ctx):
    """
    Shows a list of all Chat-SRD commands.
    :param ctx: ctx for the channel where the command was called
    """
    embed = Embed(
        title="Chat-SRD Commands",
        description="Here's a list of available commands:",
        color=0x00FF00  # Green color
        )

    # Add a field to embed. embed. add_field name value help inline False
    for command in bot.commands:
        embed.add_field(name=command.name, value=command.help, inline=False)

    await ctx.send(embed=embed)
    logger.info(f"{ctx.author} used the retrieved the command list.")



@bot.command(name='autoclean', help='Enables or disables the automated iRacing Stats Cleanup.')
async def autoclean(ctx, action: str):
    """
    Enables or disables the automated iRacing Stats Cleanup.
    :param ctx: ctx for the channel where the command was called
    :param action: Enable or disable the automated iRacing Stats Cleanup.
    """
    if action.lower() not in ["enable", "disable"]:
        await ctx.send("Invalid action. Please use either /autoclean enable or disable.")
        logger.warning("Invalid action entered for /autoclean command.")
        return
    if action.lower() == "enable":
        cleanup_enabled = True
        await ctx.send("iRacing Stats Cleanup enabled.")
        logger.info(f"{ctx.author} enabled iRacing Stats Autoclean. Autoclean interval: {cleanup_interval} hours.")
    elif action.lower() == "disable":
        cleanup_enabled = False
        await ctx.send("iRacing Stats Cleanup Autoclean disabled.")
        logger.info(f"{ctx.author} disabled the iRacing Stats Autoclean.")

@bot.command(name='interval', help='Sets the time in hours iRacing Stats Cleanup will wait between each cleanup.\n Usage: /interval <hours>')
@commands.has_permissions(manage_messages=True)
async def interval(ctx, hours: int):
    """
    Sets the cleanup interval for an iRacing stats thread based on the inputted
    number of hours.
    
    :param ctx: ctx for the channel where the command was called
    :param hours: This parameter is used to set the interval in hours (int) at which the
    iRacing Stats Thread will be cleaned up.
    """
    global cleanup_interval
    cleanup_interval = hours
    await ctx.send(f'iRacing Stats Thread Cleanup interval set to {cleanup_interval} hours.')
    logger.info(f'{ctx.author} set the iRacing Stats Thread Cleanup interval to {cleanup_interval} hours.')

@bot.command(name='cleanup', help='Manually cleans up iRacing Stats threads.\n Usage: /cleanup')
async def cleanup_now(ctx):
    """
    Cleans up all messages in threads made by the iRacing Stats bot.
    
    :param ctx: ctx for the channel where the command was called
    """

    global user_id_to_monitor
    deleted_messages_count = 0
    for channel_id in read_channel_ids():
        channel = bot.get_channel(channel_id)
        if channel:
            messages_to_delete = []
            async for message in channel.history(limit=None):
                if message.author.id == user_id_to_monitor:
                    messages_to_delete.append(message)
                    logger.info("Calculating messages for deletion...")
                    if len(messages_to_delete) >= 100:
                        await channel.delete_messages(messages_to_delete)
                        deleted_messages_count += len(messages_to_delete)
                        messages_to_delete = []
            if messages_to_delete:  # if there are leftover messages less than 100
                await channel.delete_messages(messages_to_delete)
                deleted_messages_count += len(messages_to_delete)
                logger.info(f"Deleted {deleted_messages_count} messages.")
            await channel.send(f'Manual Cleanup Completed: Deleted {deleted_messages_count} messages.')
            logger.info('Manual cleanup completed.')

def read_channel_ids():
    with open("configuration.json", "r") as file:
        data = json.load(file)
        return data["channel_ids"]

def update_channel_ids(channel_ids):
    with open("configuration.json", "w") as file:
        json.dump(channel_ids, file)

@bot.command(name="channel", help="Add or remove a text channel ID where the bot is allowed to perform cleanup and cleanup activities.\n Usage: /channel <add/remove> <forum/text> <channel_id>")
@commands.has_permissions(manage_messages=True)
async def set_channel(ctx, action: str, channel_id: int):
    """Chat SRD - set_channel: Add or remove a text channel ID where the bot performs autocleanup and cleanup activities.
        Args:
        action (str): add / remove.
        channel_id (int) : The channel ID to add or remove.

    Examples:
        /channel add 1221309128 - Adds a channel ID to the list of channels where the bot can perform cleanup and cleanup activities.
        /channel remove 1221309128 - Removes a channel ID from the list of channels where the bot can perform cleanup and cleanup activities.
    """
    channel_ids = read_channel_ids()
    if action.lower() not in ["add", "remove"]:
        await ctx.send("Invalid action. Please use either /channel add or remove.")
        logger.warning("Invalid action entered for /channel command.")
        return
    if action.lower() == "add":
        if channel_id not in channel_ids:
            channel_ids.append(channel_id)
            print('Text channel ID {channel_id} has been added.')
            logger.info(f"Text channel ID {channel_id} has been added.")    
        else:
            await ctx.send(f"Text channel ID {channel_id} is already in the list.")
            print('Text channel ID {channel_id} is already in the list.')
            logger.info(f"Text channel ID {channel_id} is already in the list.")
    if action.lower() == "remove":
        if channel_id in channel_ids:
            channel_ids.remove(channel_id)
            await ctx.send(f"Text channel ID {channel_id} has been removed.")
            print(f'Text channel ID {channel_id} has been removed.')
            logger.info(f"Text channel ID {channel_id} has been removed.")
        else:
            print(f'Text channel ID {channel_id} is not in the list.')
            await ctx.send(f"Text channel ID {channel_id} is not in the list.")

    # Update the channel IDs in the JSON file
    
    update_channel_ids(channel_ids)
    logger.ingo(f"{ctx.author} updated the channel IDs in the JSON file.")

@bot.command(name="log", help="Sends the log file as an attachment or clears it.\n Usage: /log <get/clear>")
@commands.has_permissions(manage_messages=True)
async def log(ctx, action: str = "get"):
    """Chat-SRD - log: Get or Clear the log file.

    Args:
        action (str): get / clear. Defaults to "get".

    Examples:
        /log get - Gets the log file as an attachment.
        /log clear - Clears the log file.
    """
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
            with open('chat_srd.log', 'rb') as log_file:
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
            with open(log_file, 'w') as f:
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
    print(f'{bot.user.name} has connected to Discord.')
    logger.info(f'{bot.user.name} has connected to Discord.')
    global last_purge_time
    last_cleanup_time = datetime.now() - timedelta(hours=(cleanup_interval))
    logger.info('Chat SRD Autoclean has started.')


    bot.loop.create_task(cleanup_old_messages())

async def cleanup_old_messages():
    """_summary_ : Deletes messages older than the cleanup interval from the channels in the channel_ids list.
    """

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
                            if message.author.id == user_id_to_monitor and message.created_at.timestamp() < now - cleanup_interval * 3600:
                                await message.delete()
                                logger.info(f"Deleted messages by {message.author} in {message.channel}:\n{message.content}")
                                deleted_messages.append(message)
                        await channel.send(f'iRacing Reports Cleanup Completed: Deleted {len(deleted_messages)} messages.')
                        logger.info('Auto Cleanupd iRacing Stats message on schedule.')
        await asyncio.sleep(60)  # check every minute
        cleanup_old_messages.start()


@bot.command(name="ac_config")
async def ac_config(ctx):
    """
    View the AC server configuration.
    :param: ctx: ctx for the channel where the command was called
    """
    view = AC_server_command.ConfigSelectView()
    await ctx.send("Select a configuration category:", view=view, delete_after=45)


@bot.command(name="ac_menu")
async def ac_menu(ctx):
    """
    Bring up the AC server management buttons.
    :param: ctx: ctx for the channel where the command was called
    """
    view = AC_server_command.MenuView()
    await ctx.send("Select a configuration category:", view=view, delete_after=45)


@bot.command(name="ac_set")
@commands.has_permissions(manage_messages=True)
async def ac_set(ctx, section: str, key: str, *, value: str):
    """
    Updates a key-value pair in a configuration file and logs the changes.
    Modifies a copy of the base ini file before merging it back to create a new file.
    This step is necessary to limit the information available to the bot. 
    """
    # Load the existing config file
    config.read('.\\ac_server_config\discord_server_cfg.ini')
    # If the section exists in the config
    section_lower = section.lower()

    # Check if the section exists in the config (ignoring case)
    for config_section in config.sections():
        if config_section.lower() == section_lower:
            # If the key exists in the section
            if key in config[config_section]:
                # Update the key with the new value
                config[config_section][key] = value
                # Save the updated config file
                with open('.\\ac_server_config\discord_server_cfg.ini', 'w') as configfile:
                    config.write(configfile)
                await ctx.send(f"Updated {key} in {config_section} with {value}.")
                AC_server_command.merge_configs()
                logger.info(f"{ctx.author} updated {key} in {config_section} with {value} and the configuration has been merged with base config.")
                return
            else:
                await ctx.send(f"{section} not found in the config file.")
                logger.warning(f"Key not found:  {ctx.author} tried to update {key} in {config_section} with {value} but the key was not found in the config file.")
   

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)
