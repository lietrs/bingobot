
import nextcord
from nextcord.ext import commands, tasks
import asyncio
import logging
import re 
import os, json
from PIL import Image #pip install pillow
from datetime import datetime


import bingobot_admin
from bingo import bingodata, board, teams, discordbingo, tiles, approve_interaction


# Settings

with open("token.txt", 'r') as fp:
    gTOKEN = fp.readline()

gPREFIX = "!"
gBOTREADY = False


# Bot
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True

description = '''Discord osrs bot'''
bot = commands.Bot(intents=intents, command_prefix=gPREFIX, description='Bingo time',  case_insensitive=True)

gAPPROVEREACT = '✅'
gDISPUTEREACT = '🏴󠁧󠁢󠁳󠁣󠁴󠁿'


@bot.event
async def on_ready():
    global gBOTREADY
    if not gBOTREADY:
        gBOTREADY = True
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')
    




@bot.command()
async def mvp(ctx: nextcord.ext.commands.Context, *args):
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
async def xp(ctx: nextcord.ext.commands.Context, *args):
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




async def onBingoTaskApproved(bot, payload):
    channel = await bot.fetch_channel(payload.channel_id)

    spl = channel.name.split("-")
    team = "-".join(spl[0:-1])
    if spl[-1] != "submissions":
        return

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if not discordbingo.userIsMod(user):
        # Todo: Log - Non mod attempting to approve
        return

    if discordbingo.userGetTeam(user) == team:
        # Todo: Log - Mod attempting to approve their own team
        return

    message = await channel.fetch_message(payload.message_id)
    
    tmData = teams.loadTeamBoard(guild, team)
    tile = tmData.lookupLink(str(message.id))
    approve = False
    count = 0

    if tile is None:
        tile, approved, count = await approve_interaction.prompt(guild, message, "Approving Submission")
    else:
        approved, count = await approve_interaction.promptKnownTile(guild, message, "Approving Submission")

    if not approved:
        # Cancelled
        return

    if count:
        await discordbingo.addProgress(guild, team, tile, count, str(user), message)
    else:
        await discordbingo.approveTile(guild, team, tile, str(user), message)


async def onBingoTaskUnapproved(bot, payload):
    channel = await bot.fetch_channel(payload.channel_id)

    spl = channel.name.split("-")
    team = "-".join(spl[0:-1])
    if spl[-1] != "submissions":
        return

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if not discordbingo.userIsMod(user):
        # Todo: Log - Non mod attempting to approve
        return

    if discordbingo.userGetTeam(user) == team:
        # Todo: Log - Mod attempting to approve their own team
        return

    message = await channel.fetch_message(payload.message_id)

    tmData = teams.loadTeamBoard(guild, team)
    tile = tmData.lookupLink(str(message.id))

    if tile is None:
        # Wasn't previously approved? 
        return

    brd = board.load(guild)
    td = brd.getTileByName(tile)

    if isinstance(td, tiles.CountTile):
        # Currently no way to link the amount of progress to a particular submission
        # Mods will need to reapprove and enter a negative amount
        pass
    else:
        await discordbingo.unapproveTile(guild, team, tile, str(user), message)



async def onBingoTaskDisputed(bot, payload):
    channel = await bot.fetch_channel(payload.channel_id)

    spl = channel.name.split("-")
    team = "-".join(spl[0:-1])
    if spl[-1] != "submissions":
        return

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if not discordbingo.userIsMod(user):
        # Todo: Log - Non mod attempting to approve
        return

    message = await channel.fetch_message(payload.message_id)
    
    tmData = teams.loadTeamBoard(guild, team)
    tile = tmData.lookupLink(str(message.id))

    if tile is None:
        # Wasn't previously approved? 
        return

    brd = board.load(guild)
    td = brd.getTileByName(tile)

    if isinstance(td, tiles.CountTile):
        # Currently no way to link the amount of progress to a particular submission
        # For now dispute the entire tile
        await discordbingo.disputeTile(guild, team, tile, str(user), message)
    else:
        await discordbingo.disputeTile(guild, team, tile, str(user), message)


async def onBingoTaskResolved(bot, payload):
    channel = await bot.fetch_channel(payload.channel_id)

    spl = channel.name.split("-")
    team = "-".join(spl[0:-1])
    if spl[-1] != "submissions":
        return

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if not discordbingo.userIsMod(user):
        # Todo: Log - Non mod attempting to approve
        return

    message = await channel.fetch_message(payload.message_id)
    
    tmData = teams.loadTeamBoard(guild, team)
    tile = tmData.lookupLink(str(message.id))

    if tile is None:
        # Wasn't previously approved? 
        return

    await discordbingo.resolveTile(guild, team, tile, str(user), message)



@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) == gAPPROVEREACT:
        await onBingoTaskApproved(bot, payload)
    elif str(payload.emoji) == gDISPUTEREACT:
        await onBingoTaskDisputed(bot, payload)

@bot.event
async def on_raw_reaction_remove(payload):
    if str(payload.emoji) == gAPPROVEREACT:
        await onBingoTaskUnapproved(bot, payload)
    elif str(payload.emoji) == gDISPUTEREACT:
        await onBingoTaskResolved(bot, payload)






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
    guild = ctx.guild
    if str(ctx.author.id) == "631886189493747723":
        # Very important do not delete
        guild = ctx.guild
        await ctx.send("aaaaaaaaaaaaaaa")
    else:
        await ctx.send("aaa")
    




@bot.command()
async def progress(ctx: nextcord.ext.commands.Context, *args):
    teamName = isTeamChannel(ctx)
    if teamName == "":
        return # Not in a team channel

    # Load the "board" of tiles
    brd = board.load(ctx.guild)

    # Load the team specific progress
    tmData = teams.loadTeamBoard(ctx.guild, teamName)

    bytes, points = teams.fillProgressBoard(tmData, brd, ctx.guild)
    dBoard = nextcord.File(bytes, filename="boardImg.png")

    embed = nextcord.Embed(title=f"{teamName}'s Board", description=f"{points} points")
    embed.color = nextcord.Color.blue()
    embed.set_image(url="attachment://boardImg.png")
    await ctx.send(embed=embed, file=dBoard)


@bot.command()
async def standings(ctx: nextcord.ext.commands.Context, *args):
    teamNames = discordbingo.listTeams(ctx.guild)
    
    for teamName in teamNames:  
        if teamName == "":
            return # Not in a team channel
        teamName = discordbingo.getTeamDisplayName(ctx.guild, teamName)
        # Load the "board" of tiles
        brd = board.load(ctx.guild)

        # Load the team specific progress
        tmData = teams.loadTeamBoard(ctx.guild, teamName)

        bytes, points = teams.fillProgressBoard(tmData, brd, ctx.guild)
        dBoard = nextcord.File(bytes, filename="boardImg.png")

        embed = nextcord.Embed(title=f"{teamName}'s Board", description=f"{points} points")
        embed.color = nextcord.Color.blue()
        embed.set_image(url="attachment://boardImg.png")
        await ctx.send(embed=embed, file=dBoard)


@bot.command()
async def bingostart(ctx: nextcord.ext.commands.Context, *args):
    auth = discordbingo.ctxGetPermLevels(ctx)

    if not discordbingo.PermLevel.Owner in auth:
        return

    for team in discordbingo.listTeams(ctx.guild):
        await bingobot_admin.bingo_teams_createapprovechannel(ctx, auth, [team])
        await sendCountTileSetup(ctx.guild, team)


@bot.command()
async def bingo(ctx: nextcord.ext.commands.Context, *args):
    """ Administer the Bingo """

    if not discordbingo.ctxIsAdmin(ctx):
        return

    await bingobot_admin.command(ctx, args) 


logging.basicConfig(level=logging.ERROR)
bingodata.initData("./")

bot.run(gTOKEN)
