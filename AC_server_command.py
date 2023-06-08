import discord
from discord.ui import Button
from discord.ext import commands
from discord import ButtonStyle, ui, Interaction, Embed
from discord.ui import Button, View, Select
from ftplib import FTP


import configparser
import ftplib
import copy
from main import logger 
config = configparser.ConfigParser()

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
        
        options = []
        config.read('.\\ac_server_config\discord_server_cfg.ini')
        for section in config.sections():
            options.append(discord.SelectOption(label=section))

        # Now we create a new ConfigSelect with the refreshed options
        new_select = ConfigSelect(options)
        
        # Then we create a new view and add the new_select to it
        new_view = ui.View()
        new_view.add_item(new_select)

        # Finally, we edit the interaction response to use our new view with the refreshed options
        await interaction.response.edit_message(embed=embed, view=new_view)
        

class CloseButton(Button):
    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.secondary, label="Close")
        self.parent_view = view
    async def callback(self, interaction):
        self.parent_view.clear_items()
        # Remove the view from the message and clear the message content
        await interaction.message.delete()

class ConfigSelectView(ui.View):
    def __init__(self, config_path):
        super().__init__()
        options = []
        config.clear()
        config.read(config_path)
        for section in config.sections():
            options.append(discord.SelectOption(label=section))
        self.add_item(ConfigSelect(options))
        self.add_item(CloseButton(self))


class MenuView(View):
    def __init__(self):
        super().__init__()
        button0 = Button(row=1, label="#SRD - AC Hotlap Server Manager", style=discord.ButtonStyle.red, disabled=True, emoji="<:srdLogo:829183292322218044>")
        button1 = Button(row=2, label="Server Configuration", style=discord.ButtonStyle.green, emoji="⚙️")
        button2 = Button(row=2, label="Entry List Configuration", style=discord.ButtonStyle.green, emoji="📊")
        button3 = Button(row=2, label="FTP/Commit Server Settings", style=discord.ButtonStyle.green, emoji="🔧")
        button4 = Button(row= 2, label="Commands", style=discord.ButtonStyle.green, emoji="🏎️")

        button0.callback = self.button0_callback
        button1.callback = self.button1_callback
        button2.callback = self.button2_callback
        button3.callback = self.button3_callback
        button4.callback = self.button4_callback

        self.add_item(button0)
        self.add_item(button1)
        self.add_item(button2)
        self.add_item(button3)
        self.add_item(button4)

        self.config_view_shown = False

    async def button0_callback(self, interaction):
    # Actions for button 2 click
        await interaction.response.send_message("")

    async def button1_callback(self, interaction):
        view = ConfigSelectView('.\\ac_server_config\\discord_server_cfg.ini')
        await interaction.response.send_message("Select a configuration category:", view=view)
        logger.info("Server Configuration was selected.")

    async def button2_callback(self, interaction):
        view = ConfigSelectView('.\\ac_server_config\\discord_entry_list.ini')
        await interaction.response.send_message("Select a configuration category:", view=view)
        logger.info("Entry List Configuration was selected.")

    async def button3_callback(self, interaction):
        # Actions for button 3 click
        upload_ftp()
        await interaction.response.send_message("New Config has been uploaded to the FTP Server.")
        logger.info("New configuration was uploaded via FTP")

    async def button4_callback(self, interaction):
        # Actions for button 3 click
        await interaction.response.send_message("Button 4 clicked!")

def merge_configs():
    # Server Config Merge
    # Read existing .ini file
    base_server_config = configparser.ConfigParser()
    base_server_config.read('.\\ac_server_config\\base_server_cfg.ini')

    # Read modified .ini file
    discord_server_config = configparser.ConfigParser()
    discord_server_config.read('.\\ac_server_config\\discord_server_cfg.ini')

    # Merge sections and key-value pairs
    for section in discord_server_config.sections():
        if section not in base_server_config:
            # If the section doesn't exist in config1, add it
            base_server_config[section] = discord_server_config[section]
        else:
            # If the section exists in both, merge the key-value pairs
            for key, value in discord_server_config[section].items():
                base_server_config[section][key] = value
        with open('.\\ac_server_config\\merged_server_cfg.ini', 'w') as merged_file:
            base_server_config.write(merged_file)
            logger.info("Server Config was merged.")
    
    # Entry List Merge
    # Read existing .ini file

    base_entry_list_config = configparser.ConfigParser()
    base_entry_list_config.read('.\\ac_server_config\\base_entry_list.ini')

    # Read modified .ini file
    discord_entry_list_config = configparser.ConfigParser()
    discord_entry_list_config.read('.\\ac_server_config\\discord_entry_list.ini')
        
# Merge sections and key-value pairs
    for section in discord_entry_list_config.sections():
        if section not in base_entry_list_config:
            # If the section doesn't exist in config1, add it
            base_entry_list_config[section] = discord_entry_list_config[section]
        else:
            # If the section exists in both, merge the key-value pairs
            for key, value in discord_entry_list_config[section].items():
                base_entry_list_config[section][key] = value
        with open('.\\ac_server_config\\merged_server_cfg.ini', 'w') as merged_file:
            base_entry_list_config.write(merged_file)
            logger.info("Server Config was merged.")

def upload_ftp():
    ftp = FTP()
    host = '54.39.130.225'
    port = 8821
    user = 'srdPublicUser'
    passwd = 'lanceTroll'
    local_filepath = '.\\ac_server_config\\merged_server_cfg.ini'

    # Connect and login
    ftp.connect(host, port)
    ftp.login(user, passwd)
    remote_filename = 'server_cfg.ini'
    remote_directory = '/54.39.130.225_9546'
    ftp.cwd(remote_directory)
    # Open the file in binary mode
    with open('.\\ac_server_config\\merged_server_cfg.ini', 'rb') as f:
        # Use FTP's STOR command to upload the file
        ftp.storbinary(f'STOR {remote_filename}', f)

    ftp.quit()