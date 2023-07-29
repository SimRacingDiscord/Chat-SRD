import discord
from discord.ext import commands
from discord import ButtonStyle, ui, Interaction, Embed
from discord.ui import Button, View, Select, button
import os
import json

# Classes and methods for the server configuration menu


def generate_embed(bot_commands):
    embed = discord.Embed(title="Bot commands", description="List of iRacing Commands:")
    for command in bot_commands:
        embed.add_field(
            name=command, value=f"Help text for {command} not available", inline=False
        )
    return embed


class ir_MenuView(View):
    def __init__(self):
        """Creates a menu with buttons navigating the iRacing Data API"""
        super().__init__()

        button0 = Button0()
        button1 = Button1()
        button2 = Button2()
        button3 = Button3()
        button4 = Button4()
        button5 = Button5()
        button6 = Button6()

        self.add_item(button0)
        self.add_item(button1)
        self.add_item(button2)
        self.add_item(button3)
        self.add_item(button4)
        self.add_item(button5)
        self.add_item(button6)
        self.add_item(CloseButton(self))

        self.config_view_shown = False

    def clear_items(self):
        # Code to clear items here
        self.children.clear()

    async def button0_callback(self, interaction):
        # Actions for button 2 click
        await interaction.response.send_message("")

    async def button1_callback(self, interaction):
        await interaction.response.send_message("")
        logger.info("Server Configuration was selected.")

    async def button2_callback(self, interaction):
        await interaction.response.send_message("")
        logger.info("Entry List Configuration was selected.")

    async def button3_callback(self, interaction):
        # Actions for button 3 click
        await interaction.response.send_message("")
        logger.info("New configuration was uploaded via FTP")

    async def button4_callback(self, interaction):
        # Actions for button 3 click
        await interaction.response.send_message("")


class Button0(Button):
    def __init__(self):
        super().__init__(
            row=1,
            label="#Chat SRD - iRacing Data UI",
            style=discord.ButtonStyle.red,
            disabled=False,
            emoji="<:srdLogo:829183292322218044>",
        )

    async def callback(self, interaction):
        await interaction.response.send_message("")


class Button1(Button):
    def __init__(self):
        super().__init__(
            row=2, label="Series Info", style=discord.ButtonStyle.green, emoji="🏎️"
        )

    async def callback(self, interaction):
        await interaction.response.send_message("Select a Series:")


class Button2(Button):
    def __init__(self):
        super().__init__(
            row=2, label="Season Info", style=discord.ButtonStyle.green, emoji="🏎️"
        )

    async def callback(self, interaction):
        await interaction.response.send_message("Select a Series:")
        logger.info("Season Info was selected.")


class Button3(Button):
    def __init__(self):
        super().__init__(
            row=2,
            label="Season Race Guide",
            style=discord.ButtonStyle.green,
            emoji="🏎️",
        )

    async def callback(self, interaction):
        await interaction.response.send_message("")
        logger.info("New configuration was uploaded via FTP")


class Button4(Button):
    def __init__(self):
        super().__init__(
            row=3, label="Series Stats", style=discord.ButtonStyle.blurple, emoji="📊"
        )

    async def callback(self, interaction):
        # get all commands from the bot starting with 'ac_' and list them
        await interaction.response.send_message("")
        logger.info("AC Commands were listed.")


class Button5(Button):
    def __init__(self):
        super().__init__(
            row=3, label="Season Results", style=discord.ButtonStyle.blurple, emoji="📊"
        )

    async def callback(self, interaction):
        # bring up the results selection
        await interaction.response.send_message("")
        logger.info("AC Results were selected.")


class Button6(Button):
    def __init__(self):
        super().__init__(
            row=3,
            label="Season Standings",
            style=discord.ButtonStyle.blurple,
            emoji="📊",
        )

    async def callback(self, interaction):
        # bring up the results selection
        await interaction.response.send_message("")
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
