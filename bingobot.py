
import discord
from discord.ext import commands
import asyncio
import logging
import re 
import os, json

import bingobot_admin
from bingo import bingodata, board, teams, discordbingo
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
async def on_raw_reaction_add(payload):
    if str(payload.emoji) == '✅':
        await isBingoTaskApproved(bot, payload)

@bot.event
async def on_raw_reaction_remove(payload):
    if str(payload.emoji) == '✅':
        await isBingoTaskUnapproved(bot, payload)



@bot.command()
async def addteam(ctx: discord.ext.commands.Context, *, teamname):

    # Check if owner
    # Check team doesn't already exist
    # think that's it

    await discordbingo.addTeam(ctx, discordbingo.slugify(teamname), teamname)

@bot.command()
async def renameteam(ctx: discord.ext.commands.Context, oldName, newName):

    # Check if owner
    # Check team doesn't already exist
    # think that's it

    await discordbingo.renameTeam(ctx, discordbingo.slugify(oldName), discordbingo.slugify(newName), newName)


@bot.command()
async def addplayers(ctx: discord.ext.commands.Context):
    file= os.path.join(bingodata._serverDir(ctx.guild), "allplayers.json")
    if os.path.exists(file):
        with open(file, "r") as f:
            d = json.load(f)

        for team, players in d.items():
            print(f"Add team {team}")
            teamslug = discordbingo.slugify(team)
            await discordbingo.addTeam(ctx, teamslug, team)

            for player in players:
                user = ctx.guild.get_member_named(player)
                if not user:
                    await ctx.send(f"\tPlayer {player} isn't in the server. Please add {teamslug}-member permission manually")
                else:
                    print(f"\tAdding player {user.name}")
                    await discordbingo.addPlayer(ctx, teamslug, user)


@bot.command()
async def startbingo(ctx: discord.ext.commands.Context):

    # check if owner

    teams = discordbingo.listTeams(ctx.guild)

    for team in teams:
        await bingobot_admin.bingo_teams_createapprovechannel(ctx, None, [team])




@bot.command()
async def progress(ctx: discord.ext.commands.Context, *args):
    """ Administer the Bingo """

    if len(args) >= 1:
        team = args[0]
    else:
        team = "-".join(ctx.channel.name.split("-")[0:-1])

    brd = board.load(ctx.guild)
    tmd = teams.getTeamProgress(ctx.guild, team)

    tstrs = []

    for sl,td in brd.tiles.items():
        ps = "0"
        if sl in tmd:
            ps = str(tmd[sl].status)
        tstrs.append(f"{td.row},{td.col}: {ps}")

    await ctx.send("\n".join(tstrs))


@bot.command()
async def bingo(ctx: discord.ext.commands.Context, *args):
    """ Administer the Bingo """

    await bingobot_admin.command(ctx, args) 



logging.basicConfig(level=logging.ERROR)
bingodata.initData("./")

bot.run(gTOKEN)
