
import discord
from discord.ext import commands, tasks
import asyncio
import logging
import re 
import os, json

import bingobot_admin
from bingo import bingodata, board, teams, discordbingo, WOM
import bingo.commands


# Settings

with open("token.txt", 'r') as fp:
    gTOKEN = fp.readline()

gPREFIX = "¬"


# Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

description = '''Discord osrs bot'''
bot = commands.Bot(intents=intents, command_prefix=gPREFIX, description='Bingo time',  case_insensitive=True)



async def isBingoTaskApproved(bot, payload):
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    # Todo: Check message author is actually bingobot or channel is the mod channel?

    # ignore reactions from bingobot
    if message.author.id == payload.user_id:
        return

    # Parse message:
    f = re.findall("\[(.*?)\:(.*?)\]", message.content)
    if not f:
        return

    team = f[0][0]
    tile = f[0][1]

    # Check user permissions
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    perms = discordbingo.userGetPermLevels(user)

    # if not bingo.commands.PermLevel.Admin in perms and not bingo.commands.PermLevel.Mod in perms:
    #     await channel.send(f'{user.name} you are not an admin!')
    #     return

    # if bingo.commands.PermLevel.Player in perms:
    #     if team == perms[bingo.commands.PermLevel.Player]:
    #         await channel.send(f'{user.name} you are in that team!')
    #         return

    teams.addApproval(guild, team, tile, user)
    await discordbingo.auditLogGuild(guild, user, f"Approved tile {tile} for team {team}")


async def isBingoTaskUnapproved(bot, payload):
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    # Todo: Check message author is actually bingobot

    # ignore reactions from bingobot
    if message.author.id == payload.user_id:
        return

    # Parse message:
    f = re.findall("\[(.*?)\:(.*?)\]", message.content)
    if not f:
        return

    team = f[0][0]
    tile = f[0][1]

    # Check user permissions
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    perms = discordbingo.userGetPermLevels(user)

    # if not bingo.commands.PermLevel.Admin in perms and not bingo.commands.PermLevel.Mod in perms:
    #     await channel.send(f'{user.name} you are not an admin!')
    #     return

    # if bingo.commands.PermLevel.Player in perms:
    #     if team == perms[bingo.commands.PermLevel.Player]:
    #         await channel.send(f'{user.name} you are in that team!')
    #         return

    teams.removeApproval(guild, team, tile, user)
    await discordbingo.auditLogGuild(guild, user, f"Removed approval on tile {tile} for team {team}")



@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    # intervalTasks.start(bot)

@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) == '✅':
        await isBingoTaskApproved(bot, payload)

@bot.event
async def on_raw_reaction_remove(payload):
    if str(payload.emoji) == '✅':
        await isBingoTaskUnapproved(bot, payload)

# @tasks.loop(seconds=3600)
# async def intervalTasks(bot):
#     guild = bot.guilds[0]
#     WOM.WOMg.updateGroup()
#     teams.updateAllXPTiles(guild)


# async def setup(ctx,bot, FileName):
#     FileName = FileName + ".json"
#     with open(FileName) as file:
#         data = json.load(file)

#     count_tasks = [task for task in data if task['type'] in ['count', 'set count']]

#     if count_tasks:
#         task_index = 0
#         task = count_tasks[task_index]
#         button_label = task['name']

#         class TaskView(discord.ui.View):
#             def __init__(self):
#                 super().__init__()
#                 self.task_index = task_index
#                 self.subsection_index = 0
#                 self.subsection_button_disabled = True  # Initially disable the "Next Subsection" button

#             @discord.ui.button(label=button_label)
#             async def next_task(self, button: discord.ui.Button, interaction: discord.Interaction):
#                 self.task_index = (self.task_index + 1) % len(count_tasks)
#                 task = count_tasks[self.task_index]
#                 button.label = task['name']
#                 self.subsection_index = 0  # Reset the subsection index when switching tasks

#                 # Enable/disable the "Next Subsection" button based on the number of subsections
#                 self.subsection_button_disabled = len(task.get('type specific', {}).get('subcounter', [])) <= 1

#                 embed = self.create_embed(task)
#                 await interaction.response.edit_message(content=None, embed=embed, view=self)

#             @discord.ui.button(label="Next Subsection", disabled=True)  # Initially disable the button
#             async def next_subsection(self, button: discord.ui.Button, interaction: discord.Interaction):
#                 task = count_tasks[self.task_index]
#                 subcounter = task.get('type specific', {}).get('subcounter', [])
#                 self.subsection_index = (self.subsection_index + 1) % len(subcounter)
#                 embed = self.create_embed(task)
#                 await interaction.response.edit_message(content=None, embed=embed, view=self)

#             @discord.ui.button(label="Add Amount")
#             async def add_amount(self, button: discord.ui.Button, interaction: discord.Interaction):
#                 task = count_tasks[self.task_index]
#                 type_specific = task.get('type specific', {})
#                 subcounter = type_specific.get('subcounter', [])
#                 if subcounter:
#                     current_subsection = subcounter[self.subsection_index]
#                     amount = current_subsection.get('amount', 0)
#                     try:
#                         message = await interaction.channel.send("Enter the value to add to the amount:")
#                         response = await bot.wait_for("message", check=lambda m: m.author == interaction.user and m.channel == interaction.channel)
#                         value = int(response.content)
#                         amount += value
#                         current_subsection['amount'] = amount
#                         write_data_to_file(data, FileName)  # Write the updated data to the file
#                         embed = self.create_embed(task)
#                         await interaction.response.edit_message(content=None, embed=embed, view=self)
#                         await message.delete()
#                         await response.delete()
#                         await interaction.followup.send(f"Added {value} to the amount.")
#                     except ValueError:
#                         await interaction.followup.send("Invalid input. Please enter a valid number.")
#                 else:
#                     amount = type_specific.get('amount', 0)
#                     try:
#                         message = await interaction.channel.send("Enter the value to add to the amount:")
#                         response = await bot.wait_for("message", check=lambda m: m.author == interaction.user and m.channel == interaction.channel)
#                         value = int(response.content)
#                         amount += value
#                         type_specific['amount'] = amount
#                         write_data_to_file(data, FileName)  # Write the updated data to the file
#                         embed = self.create_embed(task)
#                         await interaction.response.edit_message(content=None, embed=embed, view=self)
#                         await message.delete()
#                         await response.delete()
#                         await interaction.followup.send(f"Added {value} to the amount.")
#                     except ValueError:
#                         await interaction.followup.send("Invalid input. Please enter a valid number.")

#             def create_embed(self, task):
#                 embed = discord.Embed(title="Count Task", description=task['name'], color=discord.Color.green())
#                 embed.add_field(name="Description", value=task['description'], inline=False)

#                 type_specific = task.get('type specific', {})
#                 if 'goal' in type_specific:
#                     embed.add_field(name="Goal", value=type_specific['goal'])
#                 if 'amount' in type_specific:
#                     embed.add_field(name="Amount", value=type_specific['amount'])

#                 subcounter = type_specific.get('subcounter', [])
#                 if len(subcounter) > 0:
#                     current_subsection = subcounter[self.subsection_index]
#                     subcounter_description = f"**Subcounter:**\n{current_subsection.get('set', '')}:\nGoal: {current_subsection.get('goal', '')}\nAmount: {current_subsection.get('amount', '')}\n\n"
#                     embed.add_field(name="\u200b", value=subcounter_description, inline=False)

#                     self.next_subsection.disabled = False
#                 else:
#                     self.next_subsection.disabled = True

#                 return embed

#         view = TaskView()
#         embed = view.create_embed(task)
#         message = await ctx.send(embed=embed, view=view)
#         await view.wait()

#     else:
#         await ctx.send("No count tasks available.")




@bot.command()
async def bingo(ctx: discord.ext.commands.Context, *args):
    """ Administer the Bingo """

    await bingobot_admin.command(ctx, args) 



logging.basicConfig(level=logging.ERROR)
bingodata.initData("./")

bot.run(gTOKEN)
