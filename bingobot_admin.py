
import nextcord
from nextcord.ext import commands
import asyncio
import logging
import re

from bingo import discordbingo, commands, tiles, bingodata, teams, board


goodReaction = "\N{White Heavy Check Mark}"
badReaction = "\N{Negative Squared Cross Mark}"


async def bingo_who(ctx: nextcord.ext.commands.Context, auth, args):
	"""Basic user diagnostics"""

	u = ctx.author
	uauth = auth
	if ctx.message.mentions:
		u = ctx.message.mentions[0]
		uauth = discordbingo.userGetPermLevels(u)

	retstr = f"User {u.name} (ID: {u.id})"
	for r, t in uauth.items():
		if t:
			retstr += f"\n{discordbingo.PermLevel.strings[r]} in {t}"
		else:
			retstr += f"\n{discordbingo.PermLevel.strings[r]}"

	await ctx.reply(retstr)


async def bingo_init(ctx: nextcord.ext.commands.Context, auth, args):
	"""Initialise a new bingo

	Creates the basic channels and roles required for the bingo"""

	# if not ctx.author == ctx.guild.owner:
	# 	raise discordbingo.PermissionDenied()

	async with ctx.typing():
		await discordbingo.bingoInit(ctx, ctx.guild.me, ctx.author)

		bingodata.initServer(ctx.guild)

		# TODO: Initialise tiles data

	await ctx.send("Bingo initialised, see audit channel for log.")
	await ctx.message.add_reaction(goodReaction)


async def bingo_cleanup(ctx: nextcord.ext.commands.Context, auth, args):
	"""Initialise a new bingo

	Removes all the bingo specific channels, teams should be deleted first"""

	# if not ctx.author == ctx.guild.owner:
	# 	raise discordbingo.PermissionDenied()

	async with ctx.typing():
		await discordbingo.bingoCleanup(ctx)

	await ctx.message.add_reaction(goodReaction)


async def bingo_start(ctx: nextcord.ext.commands.Context, auth, args):
	"""Start the bingo!

	This sets the status to started, which is used to make sure normal people can't see the tiles early"""
	
	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	status = bingodata.getBingoStatus(ctx.guild)
	status["started"] = True
	bingodata.setBingoStatus(ctx.guild, status)

	await ctx.message.add_reaction(goodReaction)


async def bingo_end(ctx: nextcord.ext.commands.Context, auth, args):
	"""End the bingo :'(

	Currently only sets the ended flag, doesn't stop any commands functioning"""
	
	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	status = bingodata.getBingoStatus(ctx.guild)
	status["ended"] = True
	bingodata.setBingoStatus(ctx.guild, status)

	await ctx.message.add_reaction(goodReaction)



async def bingo_teams(ctx: nextcord.ext.commands.Context, auth, args):
	""" Administer bingo teams """
	
	await bingo_teams_list(ctx, auth, args)


async def bingo_teams_list(ctx: nextcord.ext.commands.Context, auth, args):
	""" List the bingo teams

	Usage: !bingo teams list"""
	
	teams = discordbingo.listTeams(ctx.guild)

	retstr = f"{len(teams)} team(s) in the bingo: "
	for t in teams: 
		cpt = nextcord.utils.get(ctx.guild.roles, name=discordbingo.names.captainRole(t))
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


async def bingo_teams_add(ctx: nextcord.ext.commands.Context, auth, args):
	"""Add a team

	Usage: !bingo teams add SLUG NAME

	SLUG - the team name "slug". This is how the channels and files are named, no special characters please
	NAME - The name they actually want, that can be anything"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	async with ctx.typing():
		await discordbingo.addTeam(ctx, args[0], args[1])

	await ctx.message.add_reaction(goodReaction)


async def bingo_teams_rename(ctx: nextcord.ext.commands.Context, auth, args):
	"""Rename a team

	Usage: !bingo teams rename OLDSLUG NEWSLUG NEWNAME

	OLDSLUG - the current team name (as at the start of their text channel)
	NEWSLUG - What the new team name should be
	NEWNAME - The new display name"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	team = args[0]
	newslug = args[1]
	newname = args[2]

	async with ctx.typing():
		await discordbingo.renameTeam(ctx, team, newslug, newname)
		teams.renameTeam(team, newslug)

	await ctx.message.add_reaction(goodReaction)


async def bingo_teams_remove(ctx: nextcord.ext.commands.Context, auth, args):
	"""Remove a team

	Usage: !bingo teams remove TEAM

	TEAM - the team name (as at the start of their text channel)"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	async with ctx.typing():
		await discordbingo.removeTeam(ctx, args[0])

	await ctx.message.add_reaction(goodReaction)



async def bingo_players(ctx: nextcord.ext.commands.Context, auth, args):
	"""Add/delete players from the bingo"""

	await bingo_teams_list(ctx, auth, args)

async def bingo_players_list(ctx: nextcord.ext.commands.Context, auth, args):
	"""List all the participants of the bingo

	Usage: !bingo players list"""

	await bingo_teams_list(ctx, auth, args)


async def bingo_players_add(ctx: nextcord.ext.commands.Context, auth, args):
	"""Add a player to the bingo

	Usage: !bingo players add TEAM PLAYER

	TEAM - the team name (as at the start of their text channel)
	PLAYER - A player name. Can tag players, or use just a username, or username#1234"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
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


async def bingo_players_remove(ctx: nextcord.ext.commands.Context, auth, args):
	"""Removes a player from the bingo

	Usage: !bingo players remove PLAYER

	PLAYER - A player name. Can tag players, or use just a username, or username#1234"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
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


async def bingo_teams_progress(ctx: nextcord.ext.commands.Context, auth, args):
	"""retrieve details on team progress

	Usage: !bingo teams progress TEAM

	TEAM - the team name (as at the start of their text channel)"""

	if max(auth.keys()) < discordbingo.PermLevel.Mod:
		raise discordbingo.PermissionDenied()

	if len(args) < 1:
		await ctx.send("Usage: !bingo teams progress TEAMNAME")
		return

	team = args[0]

	brd = board.load(ctx.guild)
	tmd = teams.loadTeamBoard(ctx.guild, args[0])

	tstrs = []

	for sl,td in brd.subtiles.items():
		tstrs.append(f"{td.name}: {td.progressString(tmd.getTile(sl))}")

	await ctx.send("\n".join(tstrs))


async def bingo_teams_board(ctx: nextcord.ext.commands.Context, auth, args):
	"""retrieve details on team progress

	Usage: !bingo teams board TEAM

	TEAM - the team name (as at the start of their text channel)"""

	if max(auth.keys()) < discordbingo.PermLevel.Mod:
		raise discordbingo.PermissionDenied()

	if len(args) < 1:
		await ctx.send("Usage: !bingo teams board TEAMNAME")
		return

	team = args[0]

	ret = teams.boardString(ctx.guild, team)

	await ctx.send("\n```" + ret + "```")




async def bingo_tiles(ctx: nextcord.ext.commands.Context, auth, args):
	""" Administer bingo tiles """

	await bingo_tiles_list(ctx, auth, args)


async def bingo_tiles_list(ctx: nextcord.ext.commands.Context, auth, args):
	""" List bingo tiles 

	Usage: !bingo tiles list"""

	brd = board.load(ctx.guild)

	retstr = f"{len(brd.subtiles)} tile(s):"
	for sl, t in brd.subtiles.items():
		retstr += f"\n[{sl}] {t.basicString()}"

	await ctx.send(retstr)


async def bingo_tiles_list_xp(ctx: nextcord.ext.commands.Context, auth, args):
	""" List bingo XP tiles 

	Usage: !bingo tiles list xp"""

	brd = board.load(ctx.guild)
	xptiles = brd.getXpTiles()

	retstr = f"{len(xptiles)} tile(s):"
	for sl in xptiles:
		retstr += f"\n[{sl}] {brd.getTileByName(sl).basicString()}"

	await ctx.send(retstr)


async def bingo_tiles_list_count(ctx: nextcord.ext.commands.Context, auth, args):
	""" List bingo Count tiles 

	Usage: !bingo tiles list count"""

	brd = board.load(ctx.guild)
	cntiles = brd.getCountTiles()

	retstr = f"{len(cntiles)} tile(s):"
	for sl in cntiles:
		retstr += f"\n[{sl}] {brd.getTileByName(sl).basicString()}"

	await ctx.send(retstr)


async def bingo_tiles_find_description(ctx: nextcord.ext.commands.Context, auth, args):
	""" Find a bingo tile by description 

	Usage: !bingo tiles find description DESCRIPTION"""

	brd = board.load(ctx.guild)
	tln = brd.findTileByDescription(args[0])

	await ctx.send(f"\n[{tln}] {brd.getTileByName(tln).basicString()}")


async def bingo_tiles_add(ctx: nextcord.ext.commands.Context, auth, args):
	""" Add bingo tiles - Basic tile

	Usage: !bingo tiles add basic SLUG NAME DESCRIPTION X Y"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	# Usage: !bingo tiles add SLUG NAME DESCRIPTION X Y
	if len(args) < 5:
		await ctx.send("Usage: !bingo tiles add basic SLUG NAME DESCRIPTION X Y")
		return

	t = tiles.Tile()
	t.name, t.description = args[1:3]
	t.board_x = int(args[3])
	t.board_y = int(args[4])

	board.addTile(ctx.guild, args[0], t)

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_add_any(ctx: nextcord.ext.commands.Context, auth, args):
	""" Add bingo tiles - AnyOf tile

	Usage: !bingo tiles add any SLUG NAME DESCRIPTION X Y"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	# Usage: !bingo tiles add SLUG NAME DESCRIPTION X Y
	if len(args) < 5:
		await ctx.send("Usage: !bingo tiles add any SLUG NAME DESCRIPTION X Y")
		return

	t = tiles.TileAnyOf()
	t.name, t.description = args[1:3]
	t.board_x = int(args[3])
	t.board_y = int(args[4])

	board.addTile(ctx.guild, args[0], t)

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_add_all(ctx: nextcord.ext.commands.Context, auth, args):
	""" Add bingo tiles - AllOf tile

	Usage: !bingo tiles add any SLUG NAME DESCRIPTION X Y"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	# Usage: !bingo tiles add SLUG NAME DESCRIPTION X Y
	if len(args) < 5:
		await ctx.send("Usage: !bingo tiles add any SLUG NAME DESCRIPTION X Y")
		return

	t = tiles.TileAllOf()
	t.name, t.description = args[1:3]
	t.board_x = int(args[3])
	t.board_y = int(args[4])

	board.addTile(ctx.guild, args[0], t)

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_add_xp(ctx: nextcord.ext.commands.Context, auth, args):
	""" Add bingo tiles - XP tile

	Usage: !bingo tiles add xp SKILL XPREQUIRED DESCRIPTION X Y"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	if len(args) < 5:
		await ctx.send("Usage: !bingo tiles add xp SKILL XP DESCRIPTION X Y")
		return

	t = tiles.XPTile()
	t.slug = args[0]
	t.name = args[0]
	t.skill = args[0]
	t.required = int(args[1])
	t.description = args[2]
	t.board_x = int(args[3])
	t.board_y = int(args[4])

	board.addTile(ctx.guild, args[0], t)

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_add_multi(ctx: nextcord.ext.commands.Context, auth, args):
	""" Add bingo tiles - Multiple counts required

	Usage: !bingo tiles add multi SLUG NAME DESCRIPTION QTY X Y"""
	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	# Usage: !bingo tiles add SLUG NAME DESCRIPTION X Y
	if len(args) < 6:
		await ctx.send("Usage: !bingo tiles add multi SLUG NAME DESCRIPTION QTY X Y")
		return

	t = tiles.CountTile()
	t.slug, t.name, t.description = args[0:3]
	t.required = int(args[3])
	t.board_x = int(args[4])
	t.board_y = int(args[5])

	board.addTile(ctx.guild, args[0], t)

	await ctx.message.add_reaction(goodReaction)

async def bingo_tiles_add_items(ctx: nextcord.ext.commands.Context, auth, args):
	""" Add bingo tiles - Multiple Items Required

	Usage: !bingo tiles add items SLUG NAME DESCRIPTION X Y ITEM1 ITEM2 ..."""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	if len(args) < 6:
		await ctx.send("Usage: !bingo tiles additems  SLUG NAME DESCRIPTION X Y")
		return

	t = tiles.ItemsTile()
	t.slug, t.name, t.description = args[0:3]
	t.board_x = int(args[3])
	t.board_y = int(args[4])
	t.items = args[5:]

	board.addTile(ctx.guild, args[0], t)

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_remove(ctx: nextcord.ext.commands.Context, auth, args):
	""" Remove bingo tiles 

	Usage: !bingo tiles remove TILE

	TILE - The name of the tile to get information on. For tile names use `!bingo tiles list`"""

	board.removeTile(ctx.guild, args[0])


async def bingo_tiles_approve(ctx: nextcord.ext.commands.Context, auth, args):
	""" Mark bingo tile status 

	Usage: !bingo approve TEAM TILE [MOD]

	TEAM - the team name (as at the start of their text channel)
	TILE - The name of the tile to get information on. For tile names use `!bingo tiles list`
	MOD  - The name of the mod to approve on behalf of (default is message author)"""

	if max(auth.keys()) < discordbingo.PermLevel.Mod:
		raise discordbingo.PermissionDenied()

	if len(args) < 2:
		await ctx.send("Usage: !bingo tiles approve TEAM TILE")
		return

	team = args[0]
	tile = args[1]
	mod = ctx.author
	if len(args) > 2:
		mod = discordbingo.identifyPlayer(ctx, args[2])

	link = ctx.message.id

	teams.approveTile(ctx.guild, team, tile, str(mod))

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_dispute(ctx: nextcord.ext.commands.Context, auth, args):
	""" Mark bingo tile status 

	Usage: !bingo dispute TEAM TILE [MOD]

	TEAM - the team name (as at the start of their text channel)
	TILE - The name of the tile to get information on. For tile names use `!bingo tiles list`
	MOD  - The name of the mod to approve on behalf of (default is message author)"""

	if max(auth.keys()) < discordbingo.PermLevel.Admin:
		raise discordbingo.PermissionDenied()

	if len(args) < 2:
		await ctx.send("Usage: !bingo dispute TEAM TILE")
		return

	team = args[0]
	tile = args[1]
	mod = ctx.author
	if len(args) > 2:
		mod = discordbingo.identifyPlayer(ctx, args[2])

	teams.disputeTile(ctx.guild, team, tile, str(mod))

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_unapprove(ctx: nextcord.ext.commands.Context, auth, args):
	""" Mark bingo tile status 

	Usage: !bingo unapprove TEAM TILE [MOD]

	TEAM - the team name (as at the start of their text channel)
	TILE - The name of the tile to get information on. For tile names use `!bingo tiles list`
	MOD  - The name of the mod to remove approval of"""

	if max(auth.keys()) < discordbingo.PermLevel.Mod:
		raise discordbingo.PermissionDenied()

	if len(args) < 2:
		await ctx.send("Usage: !bingo unapprove TEAM TILE")
		return

	team = args[0]
	tile = args[1]
	mod = ctx.author
	if len(args) > 2:
		mod = discordbingo.identifyPlayer(ctx, args[2])

	teams.unapproveTile(ctx.guild, team, tile, str(mod))

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_resolve(ctx: nextcord.ext.commands.Context, auth, args):
	""" Mark bingo tile status 

	Usage: !bingo resolve TEAM TILE [MOD]

	TEAM - the team name (as at the start of their text channel)
	TILE - The name of the tile to get information on. For tile names use `!bingo tiles list`
	MOD  - The name of the mod to remove dispute of"""

	if max(auth.keys()) < discordbingo.PermLevel.Mod:
		raise discordbingo.PermissionDenied()

	if len(args) < 2:
		await ctx.send("Usage: !bingo resolve TEAM TILE")
		return

	team = args[0]
	tile = args[1]
	mod = ctx.author
	if len(args) > 2:
		mod = discordbingo.identifyPlayer(ctx, args[2])

	teams.resolveTile(ctx.guild, team, tile, str(mod))

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_approvers(ctx: nextcord.ext.commands.Context, auth, args):
	""" Get the list of mods who approved a tile 

	Usage: !bingo approvers TEAM TILE

	TEAM - the team name (as at the start of their text channel)
	TILE - The name of the tile to get information on. For tile names use `!bingo tiles list`"""

	if max(auth.keys()) < discordbingo.PermLevel.Mod:
		raise discordbingo.PermissionDenied()

	if len(args) < 2:
		await ctx.send("Usage: !bingo tiles approvers TEAM TILE")
		return

	team = args[0]
	tile = args[1]

	teamBoard = teams.loadTeamBoard(ctx.guild, team)
	tld = teamBoard.getTile(tile)

	message = ""

	if tld.approved_by:
		message += "Approved by: " + ", ".join(tld.approved_by)
	else:
		message += "No approvers"

	if tld.disputed_by:
		message += "\nDisputed by: " + ", ".join(tld.disputed_by)

	await ctx.send(message)


async def bingo_tiles_setprogress(ctx: nextcord.ext.commands.Context, auth, args):
	""" Set progress for a bingo tile 

	Usage: !bingo tiles setprogress TEAM TILE PROGRESS

	TEAM - the team name (as at the start of their text channel)
	TILE - The name of the tile to get information on. For tile names use `!bingo tiles list` 
	PROGRESS - Depends on the type of the tile. For xp and multi/count tiles this is a number. For items it's the name of the item """

	if max(auth.keys()) < discordbingo.PermLevel.Mod:
		raise discordbingo.PermissionDenied()

	if len(args) < 3:
		await ctx.send("Usage: !bingo tiles setprogress TEAM TILE PROGRESS")
		return

	team = args[0]
	tile = args[1]
	progress = args[2]

	teams.setProgress(ctx.guild, team, tile, progress, ctx.message.id)

	await ctx.message.add_reaction(goodReaction)


async def bingo_tiles_addprogress(ctx: nextcord.ext.commands.Context, auth, args):
	""" Add progress to a bingo tile 

	Usage: !bingo tiles addprogress TEAM TILE PROGRESS

	TEAM - the team name (as at the start of their text channel)
	TILE - The name of the tile to get information on. For tile names use `!bingo tiles list` 
	PROGRESS - Depends on the type of the tile. For xp and multi/count tiles this is a number. For items it's the name of the item """

	if max(auth.keys()) < discordbingo.PermLevel.Mod:
		raise discordbingo.PermissionDenied()

	if len(args) < 3:
		await ctx.send("Usage: !bingo tiles addprogress TEAM TILE PROGRESS")
		return

	team = args[0]
	tile = args[1]
	progress = args[2]

	teams.addProgress(ctx.guild, team, tile, progress, ctx.message.id)

	await ctx.message.add_reaction(goodReaction)




async def bingo_tiles_about(ctx: nextcord.ext.commands.Context, auth, args):
	""" Gives extra info about a bingo tile

	Usage: !bingo tiles about TILE

	TILE - The name of the tile to get information on. For tile names use `!bingo tiles list` """
	
	tile = args[0]
	brd = board.load(ctx.guild)
	tld = brd.getTileByName(tile)

	await ctx.send(tld.about())


async def bingo_tiles_progress(ctx: nextcord.ext.commands.Context, auth, args):
	""" Overall progress of all teams on a bingo tile

	Usage: !bingo tiles progress TILE

	TILE - The name of the tile to retrieve progress on"""
	
	tile = args[0]
	brd = board.load(ctx.guild)
	tld = brd.getTileByName(tile)

	res = []

	for t in discordbingo.listTeams(ctx.guild):
		tmd = teams.loadTeamBoard(ctx.guild, t)
		ps = tld.progressString(tmd.getTile(tile))

		res.append(f"{t}: {ps}")

	await ctx.send("\n".join(res))


async def bingo_tiles_createapprovalpost(ctx: nextcord.ext.commands.Context, auth, args):
	""" Create dummy approval post

	Usage: !bingo tiles createapprovalpost TEAM TILE

	TEAM - the team name (as at the start of their text channel)
	TILE - The name of the tile to retrieve progress on"""

	team = args[0]
	tile = args[1]

	brd = board.load(ctx.guild)
	tld = brd.getTileByName(tile)

	message = await ctx.send(f"[{team}:{tile}] {tld.name}")
	# await message.add_reaction('✅')
	# await message.add_reaction('🏴󠁧󠁢󠁳󠁣󠁴󠁿')



async def bingo_teams_createapprovechannel(ctx: nextcord.ext.commands.Context, auth, args):
	""" Create dummy approval post

	Usage: !bingo teams createapprovalpost TEAM

	TEAM - the team name (as at the start of their text channel)"""

	teamSlug = args[0]

	chat = nextcord.utils.get(ctx.guild.channels, name=discordbingo.names.teamChat(teamSlug))

	if not chat:
		raise NoTeamFound()

	modRole = nextcord.utils.get(ctx.guild.roles, name=discordbingo.names.modRole)
	adminRole = nextcord.utils.get(ctx.guild.roles, name=discordbingo.names.adminRole)
	ownerRole = nextcord.utils.get(ctx.guild.roles, name=discordbingo.names.ownerRole)

	cat = chat.category
	overwrites = {
		ctx.guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
		modRole: nextcord.PermissionOverwrite(read_messages=True),
		adminRole: nextcord.PermissionOverwrite(read_messages=True),
		ownerRole: nextcord.PermissionOverwrite(read_messages=True)
	}

	chan = await ctx.guild.create_text_channel(discordbingo.names.teamApproval(teamSlug), category=cat, overwrites=overwrites)

	brd = board.load(ctx.guild)

	# Todo: Should really be nested correctly, this depth limits. 
	for sl, t in brd.subtiles.items():
		if isinstance(t, tiles.TileSet):
			for sl2, t2 in t.subtiles.items():
				if isinstance(t2, tiles.TileSet):
					for sl3, t3 in t2.subtiles.items():
						# await chan.send(f"[{teamSlug}:{sl}.{sl2}.{sl3}] {t3.name}")
						if isinstance(t3, tiles.XPTile) or isinstance(t3, tiles.CountTile):
							continue
						await chan.send(f"{t3.description}")
				elif isinstance(t2, tiles.XPTile) or isinstance(t2, tiles.CountTile):
					pass
				else:
					# await chan.send(f"[{teamSlug}:{sl}.{sl2}] {t2.name}")
					await chan.send(f"{t2.description}")
		elif isinstance(t, tiles.XPTile) or isinstance(t, tiles.CountTile):
			pass
		else:
			# await chan.send(f"[{teamSlug}:{sl}] {t.name}")
			await chan.send(f"{t.description}")


bingo_commands = {
	"who": bingo_who,
	"init": (discordbingo.PermLevel.Owner, bingo_init),
	"cleanup": (discordbingo.PermLevel.Owner, bingo_cleanup),
	# "init": bingo_init,
	# "cleanup": bingo_cleanup,
	"start": (discordbingo.PermLevel.Admin, bingo_start),
	"end": (discordbingo.PermLevel.Admin, bingo_end),
	"teams": (discordbingo.PermLevel.Mod, {
		"": bingo_teams,
		"list": bingo_teams_list,
		"add": (discordbingo.PermLevel.Admin, bingo_teams_add),
		"remove": (discordbingo.PermLevel.Admin, bingo_teams_remove),
		"rename": (discordbingo.PermLevel.Admin, bingo_teams_rename),
		"progress": bingo_teams_progress,
		"createapprovechannel": bingo_teams_createapprovechannel
	}),
	"players": (discordbingo.PermLevel.Mod, {
		"": bingo_players,
		"list": bingo_players_list,
		"add": (discordbingo.PermLevel.Admin, bingo_players_add),
		"remove": (discordbingo.PermLevel.Admin, bingo_players_remove)
	}),
	"tiles": (discordbingo.PermLevel.Mod, {
		"": bingo_tiles,
		"list": {
			"": bingo_tiles_list,
			"xp": bingo_tiles_list_xp,
			"count": bingo_tiles_list_count
		},
		"about": bingo_tiles_about,
		"add": (discordbingo.PermLevel.Admin, {
			"basic": bingo_tiles_add,
			"xp": bingo_tiles_add_xp,
			"multi": bingo_tiles_add_multi,
			"items": bingo_tiles_add_items,
			"any": bingo_tiles_add_any,
			"all": bingo_tiles_add_all
		}),
		"find": {
			"": bingo_tiles,
			"description": bingo_tiles_find_description
		},
		"setprogress": bingo_tiles_setprogress,
		"addprogress": bingo_tiles_addprogress,
		"remove": (discordbingo.PermLevel.Admin, bingo_tiles_remove),
		"progress": bingo_tiles_progress,
		"createapprovalpost": bingo_tiles_createapprovalpost
	}),
	"board": bingo_teams_board,
	"approve": bingo_tiles_approve,
	"unapprove": bingo_tiles_unapprove,
	"dispute": bingo_tiles_dispute,
	"resolve": bingo_tiles_resolve,
	"approvers": bingo_tiles_approvers
}

async def command(ctx: nextcord.ext.commands.Context, args):
	"""Administrator tools for managing the bingo"""
	auth = discordbingo.ctxGetPermLevels(ctx)
	mauth = max(auth.keys())

	if mauth < discordbingo.PermLevel.Captain:
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
		await ctx.send("Permission denied.")
		raise

	except discordbingo.NoTeamFound:
		await ctx.send("Team name not recognised.")

	except:
		await ctx.message.add_reaction(badReaction)
		raise
