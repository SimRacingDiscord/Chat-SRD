import discord
from discord.ext import commands
from discord import ButtonStyle, ui, Interaction, Embed
from discord.ui import Button, View, Select, button
import os
import json

import configparser
from typing import List
import ftplib
from ftplib import FTP
from main import logger

config = configparser.ConfigParser()

# Classes and methods for the server configuration menu


def generate_embed(bot_commands):
    embed = discord.Embed(
        title="Bot commands", description="Here are all the AC Hotlap Server Commands:"
    )
    for command in bot_commands:
        embed.add_field(
            name=command, value=f"Help text for {command} not available", inline=False
        )
    return embed


class MenuView(View):
    def __init__(self):
        """Creates a menu with buttons for server configuration, entry list configuration"""
        super().__init__()

        button0 = Button0()
        button1 = Button1()
        button2 = Button2()
        button3 = Button3()
        button4 = Button4()
        button5 = Button5()

        self.add_item(button0)
        self.add_item(button1)
        self.add_item(button2)
        self.add_item(button3)
        self.add_item(button4)
        self.add_item(button5)
        self.add_item(CloseButton(self))

        self.config_view_shown = False

    def clear_items(self):
        # Code to clear items here
        self.children.clear()

    async def button0_callback(self, interaction):
        # Actions for button 2 click
        await interaction.response.send_message("")

    async def button1_callback(self, interaction):
        view = ConfigSelectView(".\\ac_server_config\\discord_server_cfg.ini")
        await interaction.response.send_message(
            "Select a configuration category:", view=view
        )
        logger.info("Server Configuration was selected.")

    async def button2_callback(self, interaction):
        view = ConfigSelectView(".\\ac_server_config\\discord_entry_list.ini")
        await interaction.response.send_message(
            "Select a configuration category:", view=view
        )
        logger.info("Entry List Configuration was selected.")

    async def button3_callback(self, interaction):
        # Actions for button 3 click
        upload_ftp()
        await interaction.response.send_message(
            "New Config has been uploaded to the FTP Server."
        )
        logger.info("New configuration was uploaded via FTP")

    async def button4_callback(self, interaction):
        # Actions for button 3 click
        view = ButtonEmbed(embed=embed)
        await interaction.response.send_message(view=view)


class Button0(Button):
    def __init__(self):
        super().__init__(
            row=1,
            label="#SRD - AC Hotlap Server Manager",
            style=discord.ButtonStyle.red,
            disabled=False,
            emoji="<:srdLogo:829183292322218044>",
        )

    async def callback(self, interaction):
        await interaction.response.send_message("")


class Button1(Button):
    def __init__(self):
        super().__init__(
            row=2,
            label="Server Configuration",
            style=discord.ButtonStyle.green,
            emoji="⚙️",
        )

    async def callback(self, interaction):
        view = ConfigSelectView(".\\ac_server_config\\discord_server_cfg.ini")
        await interaction.response.send_message(
            "Select a configuration category:", view=view
        )
        logger.info("Server Configuration was selected.")


class Button2(Button):
    def __init__(self):
        super().__init__(
            row=2,
            label="Entry List Configuration",
            style=discord.ButtonStyle.green,
            emoji="📊",
        )

    async def callback(self, interaction):
        view = ConfigSelectView(".\\ac_server_config\\discord_entry_list.ini")
        await interaction.response.send_message(
            "Select a configuration category:", view=view
        )
        logger.info("Entry List Configuration was selected.")


class Button3(Button):
    def __init__(self):
        super().__init__(
            row=2,
            label="FTP/Commit Server Settings",
            style=discord.ButtonStyle.green,
            emoji="🔧",
        )

    async def callback(self, interaction):
        upload_ftp()
        await interaction.response.send_message(
            "New Config has been uploaded to the FTP Server."
        )
        logger.info("New configuration was uploaded via FTP")


class Button4(Button):
    def __init__(self):
        super().__init__(
            row=2, label="Commands", style=discord.ButtonStyle.blurple, emoji="🏎️"
        )

    async def callback(self, interaction):
        # get all commands from the bot starting with 'ac_' and list them
        view = EmbedView()
        await interaction.response.send_message("", view=view, embed=view.embed)
        logger.info("AC Commands were listed.")


class Button5(Button):
    def __init__(self):
        super().__init__(
            row=3, label="Session Results", style=discord.ButtonStyle.blurple, emoji="📊"
        )

    async def callback(self, interaction):
        # bring up the results selection
        view = ResultsSelectView()
        await interaction.response.send_message("", view=view, embed=view.embed)
        logger.info("AC Results were selected.")


class CloseButton(Button):
    def __init__(self, parent_view):
        """A subclass of the Button class that clears the items of ConfigSelect"""
        super().__init__(style=discord.ButtonStyle.secondary, label="Close")
        self.parent_view = parent_view

    async def callback(self, interaction):
        if hasattr(self.parent_view, "clear_items"):
            self.parent_view.clear_items()
        # Remove the view from the message and clear the message content
        await interaction.message.delete()


class EmbedView(ui.View):
    def __init__(self):
        super().__init__()
        self.embed = discord.Embed(
            title="AC Hotlap Server Commands",
            description="Bot commands to configure the AC Hotlap Server.",
        )
        self.embed.add_field(
            name="ac_set", value="Set a value in the server config.", inline=False
        )
        self.embed.add_field(
            name="ac_get", value="Get a value from the server config.", inline=False
        )
        self.embed.add_field(
            name="ac_uploadftp",
            value="Upload the current config to the server.",
            inline=False,
        )
        self.embed.add_field(
            name="ac_stats", value="Display server stats.", inline=False
        )
        self.add_item(CloseButton(self))

    def clear_items(self):
        self.children.clear()


class ConfigSelectView(ui.View):
    def __init__(self, config_path):
        """initializes a view with options from a configuration file and adds a
        select widget and a close button to it."""
        super().__init__()
        config.clear()
        config.read(config_path)
        options = [discord.SelectOption(label=section) for section in config.sections()]
        self.add_item(ConfigSelect(options, self))
        self.add_item(CloseButton(self))


class ConfigSelect(Select):
    def __init__(self, options, parent_view):
        super().__init__(
            placeholder="Select a configuration category:", options=options
        )
        self.parent_view = parent_view

    async def callback(self, interaction):
        selected_option = self.values[0]
        config_values = dict(config[selected_option])

        embed = Embed(
            title=f"Configuration: {selected_option}",
            description="Here are the settings for this section:",
        )
        for key, value in config_values.items():
            embed.add_field(name=key, value=value, inline=False)

        options = []
        config.read(".\\ac_server_config\\discord_server_cfg.ini")
        for section in config.sections():
            options.append(
                discord.SelectOption(label=section, value=section.replace(" ", "_"))
            )

        # Now we create a new ConfigSelect with the refreshed options
        new_select = ConfigSelect(options, self)  # Pass self as the parent view

        # Then we create a new view and add the new_select to it
        new_view = ui.View()
        new_view.add_item(new_select)
        new_view.add_item(CloseButton(self.parent_view))

        # Finally, we edit the interaction response to use our new view with the refreshed options
        await interaction.response.edit_message(embed=embed, view=new_view)


class ResultsSelect(Select):
    def __init__(self, session_data):
        self.session_data = session_data
        options = [
            discord.SelectOption(label=key, value=key) for key in session_data.keys()
        ]
        super().__init__(placeholder="Select a Session", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_session = self.values[0]
        session_data = self.session_data[selected_session]
        await interaction.response.send_message(
            f"Session Data for {selected_session}: {session_data}"
        )


class ResultsSelectView(discord.ui.View):
    def __init__(self, session_data):
        super().__init__()
        self.add_item(ResultsSelect(session_data))
        self.add_item(CloseButton(self))


def parse_results_json():
    local_results_directory = "./ac_results"
    session_data = {}
    files = [
        f
        for f in os.listdir(local_results_directory)
        if os.path.isfile(os.path.join(local_results_directory, f))
    ]
    sorted_files = sorted(
        files,
        key=lambda f: os.path.getmtime(os.path.join(local_results_directory, f)),
        reverse=True,
    )
    newest_files = sorted_files[:10]

    for file in newest_files:
        with open(os.path.join(local_results_directory, file)) as json_file:
            data = json.load(json_file)
            session_data[file] = data
            # get a specific key from data
            # print(data['laps'][0]['car']['car'])

    return session_data


def merge_configs():
    # Server Config Merge
    # Read existing .ini file
    base_server_config = configparser.ConfigParser()
    base_server_config.read(".\\ac_server_config\\base_server_cfg.ini")

    # Read modified .ini file
    discord_server_config = configparser.ConfigParser()
    discord_server_config.read(".\\ac_server_config\\discord_server_cfg.ini")

    # Merge sections and key-value pairs
    for section in discord_server_config.sections():
        if section not in base_server_config:
            # If the section doesn't exist in config1, add it
            base_server_config[section] = discord_server_config[section]
        else:
            # If the section exists in both, merge the key-value pairs
            for key, value in discord_server_config[section].items():
                base_server_config[section][key] = value
        with open(".\\ac_server_config\\merged_server_cfg.ini", "w") as merged_file:
            base_server_config.write(merged_file)
            logger.info("Server Config was merged.")

    # Entry List Merge
    # Read existing .ini file

    base_entry_list_config = configparser.ConfigParser()
    base_entry_list_config.read(".\\ac_server_config\\base_entry_list.ini")

    # Read modified .ini file
    discord_entry_list_config = configparser.ConfigParser()
    discord_entry_list_config.read(".\\ac_server_config\\discord_entry_list.ini")

    # Merge sections and key-value pairs
    for section in discord_entry_list_config.sections():
        if section not in base_entry_list_config:
            # If the section doesn't exist in config1, add it
            base_entry_list_config[section] = discord_entry_list_config[section]
        else:
            # If the section exists in both, merge the key-value pairs
            for key, value in discord_entry_list_config[section].items():
                base_entry_list_config[section][key] = value
        with open(".\\ac_server_config\\merged_server_cfg.ini", "w") as merged_file:
            base_entry_list_config.write(merged_file)
            logger.info("Server Config was merged.")


def upload_ftp():
    """
    This function uploads a file to an FTP server using the FTP protocol.
    """
    ftp = FTP()
    host = os.getenv("FTP_HOST")
    port = int(os.getenv("FTP_PORT"))
    user = os.getenv("FTP_USER")
    passwd = os.getenv("FTP_PASSWORD")

    local_filepath = ".\\ac_server_config\\merged_server_cfg.ini"
    # Connect and login
    try:
        ftp.connect(host, port)
        logger.info("Connected to FTP Server.")
    except Exception as e:
        logger.error("Error: Cannot connect to FTP Server.")
        return
    try:
        ftp.login(user, passwd)
        logger.info("Logged in to FTP Server.")
    except Exception as e:
        logger.error("Error: Cannot login to FTP Server.")
        return
    remote_filename = "server_cfg.ini"
    remote_directory = "/54.39.130.225_9546"
    try:
        ftp.cwd(remote_directory)
        logger.info("Changed directory to /54.39.130.225_9546")
    except Exception as e:
        logger.error("Error: Cannot change directory to /54.39.130.225_9546")
        return
    try:
        # Open the file in binary mode
        with open(".\\ac_server_config\\merged_server_cfg.ini", "rb") as f:
            # Use FTP's STOR command to upload the file
            ftp.storbinary(f"STOR {remote_filename}", f)
            logger.info("Uploaded server_cfg.ini to FTP Server.")
    except Exception as e:
        logger.error("Error: Cannot upload server_cfg.ini to FTP Server.")
        return

    ftp.quit()
    logger.info("Disconnected from FTP Server.")


def ftp_getresults():
    ftp = FTP()
    host = os.getenv("FTP_HOST")
    port = int(os.getenv("FTP_PORT"))
    user = os.getenv("FTP_USER")
    passwd = os.getenv("FTP_PASSWORD")
    try:
        ftp.connect(host, port)
        logger.info("Connected to FTP Server.")
    except Exception as e:
        logger.error("Error: Cannot connect to FTP Server.")
        return
    try:
        ftp.login(user, passwd)
        logger.info("Logged in to FTP Server.")
    except Exception as e:
        logger.error("Error: Cannot login to FTP Server.")
        return

    remote_results_directory = "/54.39.130.225_9546/results"
    local_results_directory = "./ac_results"
    try:
        ftp.cwd(remote_results_directory)
        logger.info("Changed directory to /54.39.130.225_9546/results")
        for filename in ftp.nlst():
            # Check if the filename ends with '.json'
            if filename.endswith(".json"):
                local_filepath = os.path.join(local_results_directory, filename)
                with open(local_filepath, "wb") as local_file:
                    ftp.retrbinary(f"RETR {filename}", local_file.write)
                print(f"Downloaded: {filename}")

    except ftplib.all_errors as e:
        print("FTP error:", e)
        return
