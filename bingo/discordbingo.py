
import discord
from discord.ext import commands
import asyncio
import logging

from bingo import commands



class names:
	auditChannel = "bingo-audit"
	adminRole = "bingo-admin"
	modRole = "bingo-mod"
	ownerRole = "bingo-owner"
	adminChat = "bingo-admins"
	modChat = "bingo-mods"
	adminCategory = "Bingo - Admin"

	def memberRole(team):
		return f"{team}-member"

	def captainRole(team):
		return f"{team}-captain"

	def teamCategory(team):
		return f"Bingo - {team}"

	def teamChat(team):
		return f"{team}-chat"

	def teamSubmissionsChan(team):
		return f"{team}-submissions"

	def teamVC(team):
		return f"{team}-vc"



class PermissionDenied(Exception):
	pass

class NoTeamFound(Exception):
	pass




def userGetPermLevels(user):
	ret = {}

	# Todo: should make this so it uses the names class
	for r in user.roles:
		newpl = commands.PermLevel.Nothing
		match r.name.split('-'):
			case ["bingo", "admin"]:
				ret[commands.PermLevel.Admin] = ""
			case ["bingo", "mod"]:
				ret[commands.PermLevel.Mod] = ""
			case ["bingo", "owner"]:
				ret[commands.PermLevel.Owner] = ""
			case [team, "member"]:
				ret[commands.PermLevel.Player] = team
			case [team, "captain"]:
				ret[commands.PermLevel.Captain] = team

	return ret


def ctxGetPermLevels(ctx):
	ret = userGetPermLevels(ctx.author)

	if ctx.guild.owner == ctx.author and not commands.PermLevel.Owner in ret: 
		ret[commands.PermLevel.Owner] = ""

	return ret


async def auditLog(ctx, message):
	auditch = discord.utils.get(ctx.guild.channels, name=names.auditChannel)

	m = F"[{str(ctx.author)} in {ctx.channel.name}]: {message}"

	# Todo: Log to file

	await auditch.send(m)


def identifyPlayer(ctx, pname):
	p = None 

	if pname.startswith("<@"):
		pid = pname[2:-1]
		p = ctx.guild.get_member(int(pid))
	else:
		p = ctx.guild.get_member_named(pname)

	return p


async def bingoInit(ctx, bot, owner):
	newrolenames = [names.adminRole, names.ownerRole, names.modRole]
	newroles = []

	for r in newrolenames:
		rr = discord.utils.get(ctx.guild.roles, name=r)
		try:
			if not rr:
				rr = await ctx.guild.create_role(name=r)
		except:
			print(f"Failed to create {r} role")

		newroles.append(rr)

	[adminRole, ownerRole, modRole] = newroles

	if ownerRole:
		await bot.add_roles(ownerRole)
		await owner.add_roles(ownerRole)

	modOverwrites = {
		ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
		adminRole: discord.PermissionOverwrite(read_messages=True),
		ownerRole: discord.PermissionOverwrite(read_messages=True),
		modRole: discord.PermissionOverwrite(read_messages=True)
	}

	adminOverwrites = {
		ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
		adminRole: discord.PermissionOverwrite(read_messages=True),
		ownerRole: discord.PermissionOverwrite(read_messages=True)
	}

	category = None
	adminchat = discord.utils.get(ctx.guild.channels, name=names.adminChat)
	if adminchat:
		category = adminchat.category
	else:
		try:
			category = await ctx.guild.create_category(names.adminCategory, overwrites=modOverwrites)
		except:
			print("Failed to create category")

	newchannels = [(names.adminChat, adminOverwrites), (names.modChat, {}), (names.auditChannel, {})]

	if category:
		for n, ovr in newchannels:
			try:
				await ctx.guild.create_text_channel(n, category=category, overwrites=ovr)
			except:
				print(f"Failed to create {n} chat")
				raise

	await auditLog(ctx, f"Bingo was initialised by the guild owner")


async def bingoCleanup(ctx):

	for ch in [names.adminChat, names.modChat]:
		chan = discord.utils.get(ctx.guild.channels, name=ch)
		try:
			await chan.delete()
		except:
			pass

	await auditLog(ctx, "Channels deleted. Audit log is retained, please delete manually")

	for r in [names.adminRole, names.ownerRole, names.modRole]:
		rol = discord.utils.get(ctx.guild.roles, name=r)
		try:
			await rol.delete()
		except:
			pass





def listTeams(guild):
	ret = []
	for r in guild.roles:
		n = r.name.split('-')
		if len(n) == 2 and n[1] == "member":
			ret.append(n[0])

	return ret




async def addTeam(ctx, teamSlug, teamName):
	guild = ctx.guild

	role = await guild.create_role(name = names.memberRole(teamSlug))
	cptRole = await guild.create_role(name = names.captainRole(teamSlug))
	modRole = discord.utils.get(guild.roles, name=names.modRole)
	adminRole = discord.utils.get(guild.roles, name=names.adminRole)
	ownerRole = discord.utils.get(guild.roles, name=names.ownerRole)

	overwrites = {
		guild.default_role: discord.PermissionOverwrite(read_messages=False),
		role: discord.PermissionOverwrite(read_messages=True),
		modRole: discord.PermissionOverwrite(read_messages=True),
		adminRole: discord.PermissionOverwrite(read_messages=True),
		ownerRole: discord.PermissionOverwrite(read_messages=True)
	}

	category = await guild.create_category(names.teamCategory(teamName), overwrites=overwrites)
	await guild.create_text_channel(names.teamChat(teamSlug), category=category)
	await guild.create_text_channel(names.teamSubmissionsChan(teamSlug), category=category)
	await guild.create_voice_channel(names.teamVC(teamSlug), category=category)

	await auditLog(ctx, f"Team `{teamSlug}` added")


async def removeTeam(ctx, teamSlug):

	chat = discord.utils.get(ctx.guild.channels, name=names.teamChat(teamSlug))

	if not chat:
		raise NoTeamFound()

	for r in [names.memberRole(teamSlug), names.captainRole(teamSlug)]:
		rol = discord.utils.get(ctx.guild.roles, name=r)
		try:
			await rol.delete()
		except:
			pass

	cat = chat.category

	for ch in [names.teamChat(teamSlug), names.teamVC(teamSlug), names.teamSubmissionsChan(teamSlug)]:
		chan = discord.utils.get(ctx.guild.channels, name=ch)
		try:
			await chan.delete()
		except:
			pass

	try:
		await cat.delete()
	except:
		pass

	await auditLog(ctx, f"Team `{teamSlug}` deleted")


def getTeamMembers(guild, teamSlug):
	role = discord.utils.get(guild.roles, name=names.memberRole(teamSlug))

	if not role:
		raise NoTeamFound()

	return role.members


async def renameTeam(ctx, teamSlug, newTeamSlug, newTeamName):
	# Collect all the previous roles/channels
	memberRole = discord.utils.get(ctx.guild.roles, name=names.memberRole(teamSlug))

	if not memberRole:
		raise NoTeamFound()

	captainRole = discord.utils.get(ctx.guild.roles, name=names.captainRole(teamSlug))
	cat = discord.utils.get(ctx.guild.channels, name=names.teamChat(teamSlug)).category


	# Rename everything
	await memberRole.edit(name=names.memberRole(newTeamSlug))
	await captainRole.edit(name=names.captainRole(newTeamSlug))
	for ch in [names.teamChat, names.teamVC, names.teamSubmissionsChan]:
		chan = discord.utils.get(ctx.guild.channels, name=ch(teamSlug))

		await chan.edit(name=ch(newTeamSlug))

	await cat.edit(name=names.teamCategory(newTeamName))

	await auditLog(ctx, f"Team `{teamSlug}` renamed to `{newTeamSlug}` - '{newTeamName}'")


async def addPlayer(ctx, teamSlug, player):
	role = discord.utils.get(ctx.guild.roles, name=names.memberRole(teamSlug))

	if not role:
		raise NoTeamFound()

	await player.add_roles(role)

	await auditLog(ctx, f"Player `{player.name}` added to team `{teamSlug}`")


async def removePlayer(ctx, player):

	for r in player.roles:
		if r.name.endswith("-member"):
			await player.remove_roles(r)

	await auditLog(ctx, f"Player `{player.name}` removed from the bingo")


async def setCaptain(ctx, teamSlug, player):
	role = discord.utils.get(ctx.guild.roles, name=names.captainRole(teamSlug))

	if not role:
		raise NoTeamFound()

	for p in role.members:
		p.remove_roles(role)

	await player.add_roles(role)

	await auditLog(ctx, f"Player `{player.name}` set as captain of team `{teamSlug}`")
