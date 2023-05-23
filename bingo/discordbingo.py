
import discord
import discord.ext.commands
import asyncio
import logging
import re

from bingo import commands


def slugify(value):
	value = re.sub('[^\w\s-]', '', value).strip().lower()
	return re.sub('[-\s]+', '-', value)

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

	def teamApproval(team):
		return f"{team}-approvals"

	def teamSubmissionsChan(team):
		return f"{team}-submissions"

	def teamVC(team):
		return f"{team}-vc"



class PermLevel:
	strings = ["None", "User", "Player", "Captain", "Mod", "Admin", "Owner"]
	Nothing = 0
	User = 1 
	Player = 2
	Captain = 3
	Mod = 4
	Admin = 5
	Owner = 6






class PermissionDenied(Exception):
	pass

class NoTeamFound(Exception):
	pass




def userGetPermLevels(user):
	ret = {}

	# Todo: should make this so it uses the names class
	for r in user.roles:
		newpl = PermLevel.Nothing
		spl = r.name.split('-')
		match ["-".join(spl[0:-1]), spl[-1]]:
			case ["bingo", "admin"]:
				ret[PermLevel.Admin] = ""
			case ["bingo", "mod"]:
				ret[PermLevel.Mod] = ""
			case ["bingo", "owner"]:
				ret[PermLevel.Owner] = ""
			case [team, "member"]:
				ret[PermLevel.Player] = team
			case [team, "captain"]:
				ret[PermLevel.Captain] = team

	return ret


def ctxGetPermLevels(ctx):
	ret = userGetPermLevels(ctx.author)

	if ctx.guild.owner == ctx.author and not PermLevel.Owner in ret: 
		ret[PermLevel.Owner] = ""

	return ret


def ctxIsAdmin(ctx):
    perms = discordbingo.ctxGetPermLevels(ctx)
    
    if not PermLevel.Admin in perms and not PermLevel.Owner in perms:
        return False

    return True

async def auditLogGuild(guild, user, message):
	auditch = discord.utils.get(guild.channels, name=names.auditChannel)

	m = f"[{str(user)}]: {message}"

	# Todo: Log to file

	await auditch.send(m)


async def auditLog(ctx, message):
	auditch = discord.utils.get(ctx.guild.channels, name=names.auditChannel)

	m = f"[{str(ctx.author)} in {ctx.channel.name}]: {message}"

	# Todo: Log to file

	await auditch.send(m)



async def sendToTeam(guild, team, message):
	teamch = discord.utils.get(guild.channels, name=names.teamChat(team))

	await teamch.send(message)



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

	await auditLog(ctx, f"Bingo was initialised by the guild owner")


async def bingoCleanup(ctx):

	for ch in [names.adminChat, names.modChat]:
		chan = discord.utils.get(ctx.guild.channels, name=ch)
		try:
			await chan.delete()
		except:
			pass

	# await auditLog(ctx, "Channels deleted. Audit log is retained, please delete manually")

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
		if n[-1] == "member":
			ret.append("-".join(n[0:-1]))

	return ret

def getTeamDisplayName(guild, team):
	chat = discord.utils.get(guild.channels, name=names.teamChat(team))
	if not chat:
		raise NoTeamFound()
	return chat.category.name[len("Bingo - "):]

def isTeamName(guild, team):
	chat = discord.utils.get(guild.channels, name=names.teamChat(team))
	if not chat:
		return False
	return True




async def addTeam(ctx, teamSlug, teamName):
	guild = ctx.guild

	role = await guild.create_role(name = names.memberRole(teamSlug))
	# cptRole = await guild.create_role(name = names.captainRole(teamSlug))
	modRole = discord.utils.get(guild.roles, name=names.modRole)
	adminRole = discord.utils.get(guild.roles, name=names.adminRole)
	ownerRole = discord.utils.get(guild.roles, name=names.ownerRole)

	overwrites = {
		guild.default_role: discord.PermissionOverwrite(read_messages=False),
		role: discord.PermissionOverwrite(read_messages=True),
		modRole: discord.PermissionOverwrite(read_messages=False),
		adminRole: discord.PermissionOverwrite(read_messages=False),
		ownerRole: discord.PermissionOverwrite(read_messages=True)
	}

	overwritesSubmissions = {
		guild.default_role: discord.PermissionOverwrite(read_messages=False),
		role: discord.PermissionOverwrite(read_messages=True),
		modRole: discord.PermissionOverwrite(read_messages=True),
		adminRole: discord.PermissionOverwrite(read_messages=True),
		ownerRole: discord.PermissionOverwrite(read_messages=True)
	}

	category = await guild.create_category(names.teamCategory(teamName), overwrites=overwrites)
	await guild.create_text_channel(names.teamChat(teamSlug), category=category)
	await guild.create_text_channel(names.teamSubmissionsChan(teamSlug), category=category, overwrites=overwritesSubmissions)
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

	for ch in [names.teamChat(teamSlug), names.teamVC(teamSlug), names.teamSubmissionsChan(teamSlug), names.teamApproval(teamSlug)]:
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

	# captainRole = discord.utils.get(ctx.guild.roles, name=names.captainRole(teamSlug))
	cat = discord.utils.get(ctx.guild.channels, name=names.teamChat(teamSlug)).category


	# Rename everything
	await memberRole.edit(name=names.memberRole(newTeamSlug))
	# await captainRole.edit(name=names.captainRole(newTeamSlug))
	for ch in [names.teamChat, names.teamVC, names.teamSubmissionsChan, names.teamApproval]:
		chan = discord.utils.get(ctx.guild.channels, name=ch(teamSlug))

		try:
			await chan.edit(name=ch(newTeamSlug))
		except:
			pass

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


async def setOwner(ctx, user):
	role = discord.utils.get(ctx.guild.roles, name=names.ownerRole)

	await user.add_roles(role)

	await auditLog(ctx, f"Player `{player.name}` set as captain of team `{teamSlug}`")
