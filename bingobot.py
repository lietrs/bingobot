
import discord
from discord.ext import commands, tasks
import asyncio
import logging
import re 
import os, json
from PIL import Image #pip install pillow

import bingobot_admin
from bingo import bingodata, board, teams, discordbingo, WOM, tiles


# Settings

with open("token.txt", 'r') as fp:
    gTOKEN = fp.readline()

gPREFIX = "!"


# Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

description = '''Discord osrs bot'''
bot = commands.Bot(intents=intents, command_prefix=gPREFIX, description='Bingo time',  case_insensitive=True)

gAPPROVEREACT = '✅'
gDISPUTEREACT = '🏴󠁧󠁢󠁳󠁣󠁴󠁿'


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

def isTeamChannel(ctx):
    spl = ctx.channel.name.split("-")
    team = "-".join(spl[0:-1])

    if discordbingo.isTeamName(ctx.guild, team):
        return team
    return ""


@bot.command()
async def mvp(ctx: discord.ext.commands.Context, *args):
    teamNameSlug = isTeamChannel(ctx)
    teamName = discordbingo.getTeamDisplayName(ctx.guild, teamNameSlug)
    if teamName == "":
        return # Not in a team channel

    brd = board.load(ctx.guild)

    if len(args):
        skill = args[0]
        WOM.WOMc.updateData(skill)
        WOMData = WOM.WOMc.getTeamData(skill, teamName)
        MVP = WOMData.MVP
        await ctx.send(f"The {skill} mvp is {MVP}")
    else:
        skills = brd.getXpTiles()

        ret = []
        for skill in skills:
            WOM.WOMc.updateData(skill)
            WOMData = WOM.WOMc.getTeamData(skill, teamName)
            MVP = WOMData.MVP
            ret.append(f"The {skill} mvp is {MVP}")
        await ctx.send("\n".join(ret))


@bot.command()
async def xp(ctx: discord.ext.commands.Context, *args):
    teamNameSlug = isTeamChannel(ctx)
    teamName = discordbingo.getTeamDisplayName(ctx.guild, teamNameSlug)
    if teamName == "":
        return # Not in a team channel
    updateAllXPTiles(ctx.guild)
    brd = board.load(ctx.guild)
    tmd = teams.loadTeamBoard(ctx.guild, teamNameSlug)
    XPTiles = brd.getXpTiles()
    

    if len(args):
        skill = args[0]
        
        if skill in XPTiles:
            skillTile = brd.getTileByName(skill)
            await ctx.send(f"{skillTile.skill}: {skillTile.progressString(tmd.getTile(skill))}")
        else:
            WOM.WOMc.updateData(skill)
            WOMData = WOM.WOMc.getTeamData(skill, teamName)
            xp = WOMData.TotalXP
            formatxp = tiles.formatXP(xp)
            await ctx.send(f"{skill}: {formatxp} xp")
            return
    else:
        skills = brd.getXpTiles()

        ret = []
        for skill in skills:
            skillTile = brd.getTileByName(skill)
            ret.append(f"{skillTile.skill}: {skillTile.progressString(tmd.getTile(skill))}")
        if ret:
            await ctx.send("\n".join(ret))



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
    channel = await bot.fetch_channel(payload.channel_id)

    if not discordbingo.PermLevel.Admin in perms and not discordbingo.PermLevel.Mod in perms:
        await channel.send(f'{user.name} you are not a mod!')
        return

    if discordbingo.PermLevel.Player in perms:
        if team == perms[discordbingo.PermLevel.Player]:
            await channel.send(f'{user.name} you are in that team!')
            return

    teams.approveTile(guild, team, tile, user)
    await discordbingo.auditLogGuild(guild, user, f"Approved tile {tile} for team {team}")


async def isBingoTaskUnapproved(bot, payload):
    team, tile = await isBotApprovalPost(bot, payload)
    if not team:
        return

    # Check user permissions
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    perms = discordbingo.userGetPermLevels(user)
    channel = await bot.fetch_channel(payload.channel_id)

    if not discordbingo.PermLevel.Admin in perms and not discordbingo.PermLevel.Mod in perms:
        await channel.send(f'{user.name} you are not a mod!')
        return

    if discordbingo.PermLevel.Player in perms:
        if team == perms[discordbingo.PermLevel.Player]:
            await channel.send(f'{user.name} you are in that team!')
            return

    teams.unapproveTile(guild, team, tile, user)
    await discordbingo.auditLogGuild(guild, user, f"Removed approval on tile {tile} for team {team}")


async def isBingoTaskDisputed(bot, payload):
    team, tile = await isBotApprovalPost(bot, payload)
    if not team:
        return

    # Check user permissions
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    perms = discordbingo.userGetPermLevels(user)
    channel = await bot.fetch_channel(payload.channel_id)

    if not discordbingo.PermLevel.Admin in perms:
        await channel.send(f'{user.name} you are not a admin!')
        return

    teams.disputeTile(guild, team, tile, user)
    await discordbingo.auditLogGuild(guild, user, f"Disputed tile {tile} for team {team}")


async def isBingoTaskResolved(bot, payload):
    team, tile = await isBotApprovalPost(bot, payload)
    if not team:
        return

    # Check user permissions
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    perms = discordbingo.userGetPermLevels(user)
    channel = await bot.fetch_channel(payload.channel_id)

    if not discordbingo.PermLevel.Admin in perms:
        await channel.send(f'{user.name} you are not a admin!')
        return

    teams.resolveTile(guild, team, tile, user)
    await discordbingo.auditLogGuild(guild, user, f"Resolved tile {tile} for team {team}")




@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) == gAPPROVEREACT:
        await isBingoTaskApproved(bot, payload)
    elif str(payload.emoji) == gDISPUTEREACT:
        await isBingoTaskDisputed(bot, payload)

@bot.event
async def on_raw_reaction_remove(payload):
    if str(payload.emoji) == gAPPROVEREACT:
        await isBingoTaskUnapproved(bot, payload)
    elif str(payload.emoji) == gDISPUTEREACT:
        await isBingoTaskResolved(bot, payload)

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
    if not discordbingo.ctxIsAdmin(ctx):
        return
    intervalTasks.start(ctx.guild)

@bot.command()
async def updateWOM(ctx: discord.ext.commands.Context):
    if not discordbingo.ctxIsAdmin(ctx):
        return

    WOM.WOMg.updateGroup()
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
    if not discordbingo.ctxIsMod(ctx):
        return

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
async def renameteam(ctx, oldTeam, newTeam):

    if not discordbingo.ctxIsAdmin(ctx):
        return

    oldSlug = discordbingo.slugify(oldTeam)
    newSlug = discordbingo.slugify(newTeam)

    await discordbingo.renameTeam(ctx, oldSlug, newSlug, newTeam)
    teams.renameTeam(ctx.guild, oldSlug, newSlug)


@bot.command()
async def aaa(ctx):
    """ testing """
    if str(ctx.author.id) == "631886189493747723":
        # Very important do not delete
        await ctx.send("aaaaaaaaaaaaaaa")
    else:
        await ctx.send("aaa")
    




@bot.command()
async def progress(ctx: discord.ext.commands.Context, *args):
    print("--------------")
    teamName = isTeamChannel(ctx)
    if teamName == "":
        return # Not in a team channel

    # Load the "board" of tiles
    brd = board.load(ctx.guild)

    # Load the team specific progress
    tmData = teams.loadTeamBoard(ctx.guild, teamName)

    bytes, points = teams.fillProgressBoard(tmData, brd, ctx.guild)
    dBoard = discord.File(bytes, filename="boardImg.png")


    for tileName,tileData in brd.subtiles.items():
        # Get team progress on that tile
        tmTile = tmData.getTile(tileName)

        print(f"{tileData.description} at row {tileData.row} column {tileData.col} is status {tmTile.status()}")

        # Status() returns: 
        # 0 - Incomplete
        # 2 - Approved
        # 3 - Disputed
        #
        # Of those, only "Approved" should count as the tile being done
    
    await ctx.send(f"{teamName}'s' board with {points} points", file=dBoard,)



@bot.command()
async def bingo(ctx: discord.ext.commands.Context, *args):
    """ Administer the Bingo """

    if not discordbingo.ctxIsAdmin(ctx):
        return

    await bingobot_admin.command(ctx, args) 



logging.basicConfig(level=logging.ERROR)
bingodata.initData("./")

bot.run(gTOKEN)
