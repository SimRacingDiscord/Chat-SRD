import argparse
import asyncio
import datetime
from datetime import datetime, timedelta
import io
import json
import logging
import os
import configparser
import copy

import discord
import openai
from discord import Embed, File, ButtonStyle, ui, Interaction
from discord.ui import Button, View, Select
from discord.ext import commands
from dotenv import load_dotenv



import gpt
from gpt import OpenAI

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix='>', intents=intents)

last_cleanup_time = 0
cleanup_interval = 12 
global cleanup_enabled
cleanup_enabled = True 
user_id_to_monitor = 663521697860943936 # iRacing Stats bot

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
    configuration = load_configuration()
    if configuration['setup_ai'] is True: 
        prompt = "".join(f"{word} " for word in message)
        openai_check_result = openai.setup_ai(prompt)
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

@bot.command(name='sdk', description='Watch SDK get into a wreck')
async def sdk(ctx):
    await ctx.send("https://www.twitch.tv/sdktheway")

@bot.command(name='commands', help='Show a list of all Chat-SRD commands\n Usage: /commands')
async def commands_list(ctx):
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
    global cleanup_interval
    cleanup_interval = hours
    await ctx.send(f'iRacing Stats Thread Cleanup interval set to {cleanup_interval} hours.')
    logger.info(f'{ctx.author} set the iRacing Stats Thread Cleanup interval to {cleanup_interval} hours.')

@bot.command(name='cleanup', help='Manually cleans up iRacing Stats threads.\n Usage: /cleanup')
async def cleanup_now(ctx):
    global user_id_to_monitor
    deleted_messages_count = 0
    for channel_id in read_channel_ids():
        channel = bot.get_channel(channel_id)
        if channel:
            messages_to_delete = []
            async for message in channel.history(limit=None):
                if message.author.id == user_id_to_monitor:
                    messages_to_delete.append(message)
                    if len(messages_to_delete) >= 100:
                        await channel.delete_messages(messages_to_delete)
                        deleted_messages_count += len(messages_to_delete)
                        messages_to_delete = []
            if messages_to_delete:  # if there are leftover messages less than 100
                await channel.delete_messages(messages_to_delete)
                deleted_messages_count += len(messages_to_delete)
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

# Admin / Moderator command: Grant a specific number of Feedback Points to a user.


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord.')
    logger.info(f'{bot.user.name} has connected to Discord.')
    global last_purge_time
    last_cleanup_time = datetime.now() - timedelta(hours=(cleanup_interval))
    logger.info('Chat SRD Autoclean has started.')


    bot.loop.create_task(cleanup_old_messages())

async def cleanup_old_messages():
    global last_cleanup_time, cleanup_interval, cleanup_enabled, user_id_to_monitor

    while not bot.is_closed():
        if cleanup_enabled:
            now = datetime.now()\
            
        if now > last_cleanup_time + timedelta(hours=cleanup_interval):
                last_cleanup_time = now
                for channel_id in read_channel_ids():
                    channel = bot.get_channel(channel_id)
                    if channel:
                        deleted_messages = []
                        async for message in channel.history(limit=None):
                            if message.author.id == user_id_to_monitor and message.created_at.timestamp() < now - cleanup_interval * 3600:
                                await message.delete()
                                deleted_messages.append(message)
                        await channel.send(f'iRacing Reports Cleanup Completed: Deleted {len(deleted_messages)} messages.')
                        logger.info('Auto Cleanupd iRacing Stats message on schedule.')
        await asyncio.sleep(60)  # check every minute
        cleanup_old_messages.start()

class PageView(ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.current_page = 0

    @discord.ui.button(emoji='\u23EE', style=discord.ButtonStyle.secondary)  # rewind button
    async def go_first(self, button, interaction):
        self.current_page = 0
        await interaction.message.edit(embed=self.embeds[self.current_page])

    @discord.ui.button(emoji='\u25C0', style=discord.ButtonStyle.secondary)  # left arrow button
    async def go_previous(self, button, interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.message.edit(embed=self.embeds[self.current_page])

    @discord.ui.button(emoji='\u25B6', style=discord.ButtonStyle.secondary)  # right arrow button
    async def go_next(self, button, interaction):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.message.edit(embed=self.embeds[self.current_page])

    @discord.ui.button(emoji='\u23ED', style=discord.ButtonStyle.secondary)  # fast-forward button
    async def go_last(self, button, interaction):
        self.current_page = len(self.embeds) - 1
        await interaction.message.edit(embed=self.embeds[self.current_page])



class ConfigSelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="Select a configuration category:", options=options)

    async def callback(self, interaction):
        selected_option = self.values[0]
        
        # Fetch configuration values for the selected option
        config_values = dict(config[selected_option])

        # Create the embed
        embed = Embed(title=f"Configuration: {selected_option}", description="Here are the settings for this section:")

        # Add fields to the embed for each configuration value
        for key, value in config_values.items():
            embed.add_field(name=key, value=value, inline=False)

        await interaction.response.edit_message(embed=embed)

class ConfigSelectView(ui.View):
    def __init__(self):
        super().__init__()
        options = []
        config.read('.\\ac_server_config\discord_server_cfg.ini')
        for section in config.sections():
            options.append(discord.SelectOption(label=section))
        self.add_item(ConfigSelect(options))

@bot.command(name="ac_config")
async def ac_config(ctx):
    view = ConfigSelectView()
    await ctx.send("Select a configuration category:", view=view)


class MenuView(View):
    def __init__(self):
        super().__init__()
        button0 = Button(row=1, label="#SRD - AC Hotlap Server Manager", style=discord.ButtonStyle.red, disabled=True, emoji="<:srdLogo:829183292322218044>")
        button1 = Button(row=2, label="Server General Config", style=discord.ButtonStyle.green, emoji="⚙️")
        button2 = Button(row=2, label="FTP/Commit Server Settings", style=discord.ButtonStyle.green, emoji="🔧")
        button3 = Button(row= 2, label="Commands", style=discord.ButtonStyle.green, emoji="🏎️")

        button0.callback = self.button0_callback
        button1.callback = self.button1_callback
        button2.callback = self.button2_callback
        button3.callback = self.button3_callback

        self.add_item(button0)
        self.add_item(button1)
        self.add_item(button2)
        self.add_item(button3)

    async def button0_callback(self, interaction):
    # Actions for button 2 click
        await interaction.response.send_message("Button 2 clicked!")

    async def button1_callback(self, interaction):
        message = copy.copy(interaction.message)
        message.content = f"{bot.command_prefix}ac_config"
        new_ctx = await bot.get_context(message, cls=commands.Context)
        new_ctx.author = interaction.user
        await bot.invoke(new_ctx)


    async def button2_callback(self, interaction):
        # Actions for button 2 click
        await interaction.response.send_message("Button 2 clicked!")

    async def button3_callback(self, interaction):
        # Actions for button 3 click
        await interaction.response.send_message("Button 3 clicked!")

@bot.command(name="ac_menu")
async def ac_menu(ctx):
    view = MenuView()
    await ctx.send("Select a configuration category:", view=view)
   

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)
