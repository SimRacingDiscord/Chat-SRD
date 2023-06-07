import discord
from discord.ui import Button
from discord.ext import commands


@bot.command()
async def menu(ctx):
    button = Button(label="Server General Config", style=discord.ButtonStyle.green, emoji="⚙️")
    button2 = Button(label="Server Assist Config", style=discord.ButtonStyle.green, emoji="🔧")
    button3 = Button(label="Server Car / Track Config", style=discord.ButtonStyle.green, emoji="🔒")
    view = View()
    view.add_item(button)
    view.add_item(button2)
    view.add_item(button3)
    await ctx.send("Server Config Menu", view=view)

#
#ftp = ftplib.FTP('ftp.server.com', 'username', 'password')
#with open('file_to_upload.txt', 'rb') as file:
#    ftp.storbinary('STOR /path/to/remote/file.txt', file)
#ftp.quit()