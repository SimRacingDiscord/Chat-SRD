import discord
from discord.ext import commands
from discord import ButtonStyle, ui, Interaction, Embed
from discord.ui import Button, View, Select, button
import logging 
import os
import json

# Classes and methods for the server configuration menu

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def generate_embed(bot_commands):
    embed = discord.Embed(title="Bot commands", description="List of iRacing Commands:")
    for command in bot_commands:
        embed.add_field(
            name=command, value=f"Help text for {command} not available", inline=False
        )
    return embed


class EmbedPaginatorView(View):
    def __init__(self, embeds):
        super().__init__(timeout=180.0)  # Adjust the timeout as needed
        self.embeds = embeds
        self.current_embed = 0

        self.update_view()

    def clear_items(self):
        """Clear all items (buttons) from the view."""
        self.children.clear()

    def create_embed(self, page_number):
        """Create a single embed for the given page number."""
        page_data = self.embeds[page_number]
        description = []
        
        for idx, season in enumerate(page_data['seasons'], start=1):
            season_info = (
                f"{idx}. Series Name: {season['series_name']}\n"
                f"   Season Name: {season['season_name']}\n"
                f"   Official: {season['official']}\n"
                f"   Season Year: {season['season_year']}\n"
                f"   Season Quarter: {season['season_quarter']}\n"
                f"   License Group: {season['license_group']}\n"
                f"   Fixed Setup: {season['fixed_setup']}\n"
                f"   Driver Changes: {season['driver_changes']}\n"
            )
            description.append(season_info)

        embed = discord.Embed(
            title='Season Events',
            description='\n'.join(description),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f'Page {page_number+1}/{len(self.embeds)}')

        return embed

    def update_view(self):
        """Update buttons and add them to the view."""
        self.clear_items()

        if self.current_embed > 0:
            self.previous_button = ui.Button(style=ButtonStyle.primary, label="Previous", custom_id="previous_btn")
            self.previous_button.callback = self.on_previous_click
            self.add_item(self.previous_button)

        if self.current_embed < len(self.embeds) - 1:
            self.next_button = ui.Button(style=ButtonStyle.primary, label="Next", custom_id="next_btn")
            self.next_button.callback = self.on_next_click
            self.add_item(self.next_button)

    async def on_previous_click(self, interaction: Interaction):
        if self.current_embed > 0:
            self.current_embed -= 1
            embed = self.create_embed(self.current_embed)
            await interaction.response.edit_message(embed=embed)
            self.update_view()

    async def on_next_click(self, interaction: Interaction):
        if self.current_embed < len(self.embeds) - 1:
            self.current_embed += 1
            embed = self.create_embed(self.current_embed)
            await interaction.response.edit_message(embed=embed)
            self.update_view()



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
