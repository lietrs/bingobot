
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

gPREFIX = "$"


# Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

description = '''Discord osrs bot'''
bot = commands.Bot(intents=intents, command_prefix=gPREFIX, description='Bingo time',  case_insensitive=True)

async def isBotApprovalPost(bot, payload):
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    # Todo: Check message author is actually bingobot

    # ignore reactions from bingobot
    if message.author.id == payload.user_id:
        return (None, None)

    # Parse message:
    f = re.findall("\[(.*?)\:(.*?)\]", message.content)
    if f:
        team = f[0][0]
        tile = f[0][1]
    else:
        # Lookup by description
        spl = channel.name.split("-")
        team = "-".join(spl[0:-1])
        if spl[-1] != "approvals":
            return (None, None)

        brd = board.load(bot.get_guild(payload.guild_id))
        tile = brd.findTileByDescription(message.content)
        if not tile:
            return (None, None)

    return (team, tile)

async def isBingoTaskApproved(bot, payload):
    team, tile = await isBotApprovalPost(bot, payload)
    if not team:
        return

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
    team, tile = await isBotApprovalPost(bot, payload)
    if not team:
        return

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


@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) == '✅':
        await isBingoTaskApproved(bot, payload)

@bot.event
async def on_raw_reaction_remove(payload):
    if str(payload.emoji) == '✅':
        await isBingoTaskUnapproved(bot, payload)




async def updateAllXPTiles(server):
    brd = board.load(server)
    xpTiles = brd.getXpTiles()
    for tnm in xpTiles:
        xpTile = brd.getTileByName(tnm)
        skill = xpTile.skill
        WOM.WOMc.updateData(skill)

        for team in discordbingo.listTeams(server):
            teamName = discordbingo.getTeamDisplayName(server, team)
            tmpData = WOM.WOMc.getTeamData(skill, teamName)

            if not tmpData:
                print(f"Missing data for {team} in {skill}, ignoring")
                continue

            totalXP = tmpData.getTotalXP()

            tmData = teams.loadTeamBoard(server, team)
            newApproved = teams._setProgress(brd, tmData, tnm, totalXP)
            teams.saveTeamBoard(server, team, tmData)

            if newApproved:
                await discordbingo.sendToTeam(server, team, f"Congratulations {teamName} on completing the {skill} tile!")

            print(f"{team} has {totalXP} xp gained in {skill}")
        print("^^^^^^^^^^^^^^^^^^^^")

@tasks.loop(seconds=3600)
async def intervalTasks(guild):
    WOM.WOMg.updateGroup()
    await updateAllXPTiles(guild)
    
@bot.command()
async def startWOM(ctx: discord.ext.commands.Context):
    intervalTasks.start(ctx.guild)


@bot.command()
async def updateWOM(ctx: discord.ext.commands.Context):
    # WOM.WOMg.updateGroup()
    await updateAllXPTiles(ctx.guild)




class TaskView(discord.ui.View):
    def __init__(self, guild, teamName, count_tasks):
        super().__init__()
        self.count_tasks = count_tasks
        self.guild = guild
        self.teamName = teamName

        self.task_index = 0
        self.subsection_index = 0

        self.subsection_button_disabled = True  # Initially disable the "Next Subsection" button

    def taskKey(self):
        section_key = self.count_tasks[self.task_index]
        if isinstance(section_key, list):
            task_key = section_key[self.subsection_index]
        else:
            task_key = section_key

    def update(self):
        brd = board.load(self.guild)
        task = brd.getTileByName(self.taskKey())
        button_label = task.name

        # Enable/disable the "Next Subsection" button based on the number of subsections
        self.subsection_button_disabled = not isinstance(self.count_tasks[self.task_index], list)


    @discord.ui.button(label="Next Section")
    async def next_task(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.task_index = (self.task_index + 1) % len(self.count_tasks)
        self.subsection_index = 0  # Reset the subsection index when switching tasks

        self.update()
        embed = self.create_embed()
        await interaction.response.edit_message(content=None, embed=embed, view=self)


    @discord.ui.button(label="Next Subsection", disabled=True)  # Initially disable the button
    async def next_subsection(self, button: discord.ui.Button, interaction: discord.Interaction):

        self.subsection_index = (self.subsection_index + 1) % len(self.count_tasks[self.task_index])
        embed = self.create_embed()
        await interaction.response.edit_message(content=None, embed=embed, view=self)

    @discord.ui.button(label="Add Amount")
    async def add_amount(self, button: discord.ui.Button, interaction: discord.Interaction):
        
        task_key = self.taskKey()

        try:
            message = await interaction.channel.send("Enter the value to add to the amount:")
            response = await bot.wait_for("message", check=lambda m: m.author == interaction.user and m.channel == interaction.channel)
            value = int(response.content)

            teams.addProgress(self.guild, self.teamName, task_key, str(value))

            embed = self.create_embed()
            await interaction.response.edit_message(content=None, embed=embed, view=self)
            await message.delete()
            await response.delete()
            await interaction.followup.send(f"Added {value} to the amount.")
        except ValueError:
            await interaction.followup.send("Invalid input. Please enter a valid number.")

    def create_embed(self):
        brd = board.load(self.guild)
        tm = teams.loadTeamBoard(self.guild, self.teamName)

        task_key = self.taskKey()
        task = brd.getTileByName(task_key)
        t = tm.getTile(task_key)

        if isinstance(self.count_tasks[self.task_index], list):
            section_key = task_key.split(".")[0]
            section_task = brd.getTileByName(section_key)

            embed = discord.Embed(title="Count Task", description=section_task.name, color=discord.Color.green())
            embed.add_field(name="Description", value=section_task.description, inline=False)

            subcounter_description = f"**Subcounter:**\n{task.name}:\n"
            embed.add_field(name="\u200b", value=subcounter_description, inline=False)
            self.next_subsection.disabled = False
        else:
            embed = discord.Embed(title="Count Task", description=task.name, color=discord.Color.green())
            embed.add_field(name="Description", value=task.description, inline=False)
            self.next_subsection.disabled = True

        embed.add_field(name="Goal", value=task.required)
        embed.add_field(name="Progress", value=t.progress)

        return embed




@bot.command()
async def setup(ctx, team):

    brd = board.load(ctx.guild)
    allcounts = brd.getCountTiles()

    # Split into sections
    tsk_dict = {}
    for n in allcounts:
        if "." in n:
            group = n.split(".")[0]
            if group in tsk_dict:
                tsk_dict[group].append(n)
            else:
                tsk_dict[group] = [n]
        else:
            tsk_dict[n] = None

    count_tasks = []
    for sl, grp in tsk_dict.items():
        if grp is not None:
            count_tasks.append(grp)
        else:
            count_tasks.append(sl)

    if count_tasks:
        view = TaskView(ctx.guild, team, count_tasks)
        embed = view.create_embed()
        message = await ctx.send(embed=embed, view=view)
        await view.wait()

    else:
        await ctx.send("No count tasks available.")




@bot.command()
async def bingo(ctx: discord.ext.commands.Context, *args):
    """ Administer the Bingo """

    await bingobot_admin.command(ctx, args) 



logging.basicConfig(level=logging.ERROR)
bingodata.initData("./")

bot.run(gTOKEN)
