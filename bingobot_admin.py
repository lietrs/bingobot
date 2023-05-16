
import discord
from discord.ext import commands
import asyncio
import logging

from bingo import discordbingo, commands, tiles


goodReaction = "\N{White Heavy Check Mark}"
badReaction = "\N{Negative Squared Cross Mark}"


async def bingo_who(ctx: discord.ext.commands.Context, auth, args):
	"""Basic user diagnostics"""

	u = ctx.author
	uauth = auth
	if ctx.message.mentions:
		u = ctx.message.mentions[0]
		uauth = discordbingo.userGetPermLevels(u)

	retstr = f"User {u.name} (ID: {u.id})"
	for r, t in uauth.items():
		if t:
			retstr += f"\n{commands.PermLevel.strings[r]} in {t}"
		else:
			retstr += f"\n{commands.PermLevel.strings[r]}"

	await ctx.reply(retstr)


async def bingo_init(ctx: discord.ext.commands.Context, auth, args):
	"""Initialise a new bingo"""

	if not ctx.author == ctx.guild.owner:
		raise discordbingo.PermissionDenied()

	async with ctx.typing():
		await discordbingo.bingoInit(ctx, ctx.guild.me, ctx.author)

		# TODO: Initialise data files
		# TODO: Initialise tiles data

	await ctx.send("Bingo initialised, see audit channel for log.")
	await ctx.message.add_reaction(goodReaction)


async def bingo_cleanup(ctx: discord.ext.commands.Context, auth, args):
	"""Initialise a new bingo"""

	if not ctx.author == ctx.guild.owner:
		raise discordbingo.PermissionDenied()

	async with ctx.typing():
		await discordbingo.bingoCleanup(ctx)

	await ctx.message.add_reaction(goodReaction)


async def bingo_start(ctx: discord.ext.commands.Context, auth, args):
	"""Start the bingo!"""
	
	if max(auth.keys()) < commands.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	await ctx.message.add_reaction(goodReaction)


async def bingo_end(ctx: discord.ext.commands.Context, auth, args):
	"""End the bingo :'("""
	
	if max(auth.keys()) < commands.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	await ctx.message.add_reaction(goodReaction)



async def bingo_teams(ctx: discord.ext.commands.Context, auth, args):
	""" Administer bingo teams """
	
	await bingo_teams_list(ctx, auth, args)


async def bingo_teams_list(ctx: discord.ext.commands.Context, auth, args):
	""" Administer bingo teams """
	
	teams = discordbingo.listTeams(ctx.guild)

	retstr = f"{len(teams)} team(s) in the bingo: "
	for t in teams: 
		cpt = discord.utils.get(ctx.guild.roles, name=discordbingo.names.captainRole(t))
		u = discordbingo.getTeamMembers(ctx.guild, t)

		ustr = []
		for usr in u:
			if cpt in usr.roles:
				ustr.append(usr.name + " (c)")
			else:
				ustr.append(usr.name)

		if not ustr:
			retstr += f"\n{t} = Nobody :'("
		else:
			retstr += f"\n{t} = " + ", ".join(ustr)

	await ctx.send(retstr)


async def bingo_teams_add(ctx: discord.ext.commands.Context, auth, args):
	"""Add a team"""

	if max(auth.keys()) < commands.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	async with ctx.typing():
		await discordbingo.addTeam(ctx, args[0], args[1])

	await ctx.message.add_reaction(goodReaction)


async def bingo_teams_rename(ctx: discord.ext.commands.Context, auth, args):
	"""Rename a team"""

	if max(auth.keys()) < commands.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	team = args[0]
	newslug = args[1]
	newname = args[2]

	async with ctx.typing():
		await discordbingo.renameTeam(ctx, team, newslug, newname)

	await ctx.message.add_reaction(goodReaction)


async def bingo_teams_remove(ctx: discord.ext.commands.Context, auth, args):
	"""Remove a team"""

	if max(auth.keys()) < commands.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	async with ctx.typing():
		await discordbingo.removeTeam(ctx, args[0])

	await ctx.message.add_reaction(goodReaction)



async def bingo_players(ctx: discord.ext.commands.Context, auth, args):
	"""Add/delete players from the bingo"""
	await bingo_teams_list(ctx, auth, args)

async def bingo_players_list(ctx: discord.ext.commands.Context, auth, args):
	"""List all the participants of the bingo"""
	await bingo_teams_list(ctx, auth, args)


async def bingo_players_add(ctx: discord.ext.commands.Context, auth, args):
	"""Add a player to the bingo"""

	if max(auth.keys()) < commands.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	if len(args) < 2:
		await ctx.send("Usage: !bingo players add TEAMNAME PLAYER")
		return

	team = args[0]
	player = discordbingo.identifyPlayer(ctx, args[1])

	if not player:
		await ctx.send(f"Sorry, couldn't find a player `{player}`")
		return

	async with ctx.typing():
		await discordbingo.addPlayer(ctx, team, player)

	await ctx.message.add_reaction(goodReaction)


async def bingo_players_remove(ctx: discord.ext.commands.Context, auth, args):
	"""Removes a player from the bingo"""

	if max(auth.keys()) < commands.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	if len(args) < 1:
		await ctx.send("Usage: !bingo players remove PLAYER")
		return

	player = discordbingo.identifyPlayer(ctx, args[0])

	if not player:
		await ctx.send(f"Sorry, couldn't find a player `{player}`")
		return

	async with ctx.typing():
		await discordbingo.removePlayer(ctx, player)

	await ctx.message.add_reaction(goodReaction)


async def bingo_teams_setcaptain(ctx: discord.ext.commands.Context, auth, args):
	"""Add a player to the bingo"""

	if max(auth.keys()) < commands.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	if len(args) < 2:
		await ctx.send("Usage: !bingo teams setcaptain TEAMNAME PLAYER")
		return

	team = args[0]
	player = discordbingo.identifyPlayer(ctx, args[1])

	if not player:
		await ctx.send(f"Sorry, couldn't find a player `{player}`")
		return

	async with ctx.typing():
		await discordbingo.setCaptain(ctx, team, player)

	await ctx.message.add_reaction(goodReaction)







async def bingo_tiles(ctx: discord.ext.commands.Context, auth, args):
	""" Administer bingo tiles """

	await bingo_tiles_list(ctx, auth, args)


async def bingo_tiles_list(ctx: discord.ext.commands.Context, auth, args):
	""" List bingo tiles """

	tls = tiles.all()

	retstr = f"{len(tls)} tile(s):"
	for sl, t in tls.items():
		retstr += f"\n{t.basicString()}"

	await ctx.send(retstr)


async def bingo_tiles_add(ctx: discord.ext.commands.Context, auth, args):
	""" Add bingo tiles """

	if max(auth.keys()) < commands.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	# Usage: !bingo tiles add SLUG NAME DESCRIPTION X,Y
	if len(args) < 4:
		await ctx.send("Usage: !bingo tiles add SLUG NAME DESCRIPTION X Y")
		return

	t = tiles.Tile()
	t.slug, t.name, t.description = args[0:3]
	t.board_x = int(args[3])
	t.board_y = int(args[4])

	tiles.editTile(ctx.guild, t)

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_add_xp(ctx: discord.ext.commands.Context, auth, args):
	""" Add bingo tiles """

	await ctx.send("Add bingo tile")


async def bingo_tiles_add_multi(ctx: discord.ext.commands.Context, auth, args):
	""" Add bingo tiles """

	await ctx.send("Add bingo tile")


async def bingo_tiles_add_items(ctx: discord.ext.commands.Context, auth, args):
	""" Add bingo tiles """

	await ctx.send("Add bingo tile")


async def bingo_tiles_reload(ctx: discord.ext.commands.Context, auth, args):
	""" Add bingo tiles """

	await ctx.send("Add bingo tile")

async def bingo_tiles_remove(ctx: discord.ext.commands.Context, auth, args):
	""" Remove bingo tiles """

	tiles.removeTile(ctx.guild, args[0])




bingo_commands = {
	"who": bingo_who,
    "init": (commands.PermLevel.Owner, bingo_init),
    "cleanup": (commands.PermLevel.Owner, bingo_cleanup),
    "start": (commands.PermLevel.Admin, bingo_start),
    "end": (commands.PermLevel.Admin, bingo_end),
    "teams": (commands.PermLevel.Mod, {
    	"": bingo_teams,
    	"list": bingo_teams_list,
    	"add": (commands.PermLevel.Admin, bingo_teams_add),
    	"remove": (commands.PermLevel.Admin, bingo_teams_remove),
    	"rename": (commands.PermLevel.Admin, bingo_teams_rename),
    	"setcaptain": (commands.PermLevel.Admin, bingo_teams_setcaptain)
    }),
    "players": (commands.PermLevel.Mod, {
    	"": bingo_players,
    	"list": bingo_players_list,
    	"add": (commands.PermLevel.Admin, bingo_players_add),
    	"remove": (commands.PermLevel.Admin, bingo_players_remove)
    }),
    "tiles": (commands.PermLevel.Mod, {
        "": bingo_tiles,
        "list": bingo_tiles_list,
        "reload": (commands.PermLevel.Admin, bingo_tiles_reload),
        "add": (commands.PermLevel.Admin, {
        	"basic": bingo_tiles_add,
        	"xp": bingo_tiles_add_xp,
        	"multi": bingo_tiles_add_multi,
        	"items": bingo_tiles_add_items
        }),
        "remove": (commands.PermLevel.Admin, bingo_tiles_remove)
    })
}

async def command(ctx: discord.ext.commands.Context, args):
	"""Administrator tools for managing the bingo"""
	auth = discordbingo.ctxGetPermLevels(ctx)
	mauth = max(auth.keys())

	if mauth < commands.PermLevel.Captain:
		print(f"Denied. {auth}")
		return # Silently fail

	try:
		f, ar, hlp = commands.Lookup(mauth, bingo_commands, args)

		if hlp:
			await ctx.reply(commands.HelpString(mauth, f, ar))
		elif not f:
			await ctx.reply(f"Unknown command! Try `!bingo elp")
		else:
			await f(ctx, auth, ar)

	except discordbingo.PermissionDenied:
		await ctx.reply("Permission denied.")

	except:
		await ctx.message.add_reaction(badReaction)
		raise