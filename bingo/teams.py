
import os
import json
from bingo import bingodata, tiles, board, discordbingo, WOM


class TmTileStatus:
	Incomplete = 0
	Finished = 1
	Approved = 2


class TmTile:
	status = TmTileStatus.Incomplete
	completed_by = ""
	approved_by = []
	approved_links = []
	evidence_links = []
	progress = ""
	subtiles = {}

	def __init__(self, d = None):
		if not d:
			d = {"status": 0, "completed_by": "", "approved_by": [], "approved_links": [], "evidence_links": [], "progress": ""}

		self.status = d["status"]
		self.completed_by = d["completed_by"]
		self.approved_by = d["approved_by"]
		self.approved_links = d["approved_links"]
		self.evidence_links = d["evidence_links"]
		self.progress = d["progress"]
		self.subtiles = {}
		if "subtiles" in d:
			for sl, t in d["subtiles"].items():
				self.subtiles[sl] = TmTile(t)

	def toDict(self):
		ret = {"status": self.status, "completed_by": self.completed_by, "approved_by": self.approved_by, "approved_links": self.approved_links, "evidence_links": self.evidence_links, "progress": self.progress}
		if self.subtiles:
			ret["subtiles"] = {}
			for sl, t in self.subtiles.items():
				ret["subtiles"][sl] = t.toDict()

		return ret

	def basicString(self):
		match self.status:
			case TmTileStatus.Incomplete:
				return f"Tile incomplete"
			case TmTileStatus.Finished:
				return "Awaiting approval"
			case TmTileStatus.Approved:
				return "Tile Completed!"

	def getSubtile(self, subtile):
		tns = subtile.split(".")
		if tns[0] not in self.subtiles:
			return TmTile()

		if len(tns) > 1:
			return self.subtiles[tns[0]].getSubtile(".".join(tns[1:]))
		else:
			return self.subtiles[tns[0]]

	def setSubtile(self, subtile, d):
		tns = subtile.split(".")

		if len(tns) > 1:
			if tns[0] not in self.subtiles:
				self.subtiles[tns[0]] = TmTile()
			self.subtiles[tns[0]].setSubtile(".".join(tns[1:]), d)
		else:
			self.subtiles[tns[0]] = d

def getTile(tm, tile):
	tns = tile.split(".")
	if tns[0] not in tm:
		return TmTile()

	if len(tns) > 1:
		return tm[tns[0]].getSubtile(".".join(tns[1:]))
	else:
		return tm[tns[0]]

def setTile(tm, tile, d):
	tns = tile.split(".")

	if len(tns) > 1:
		if tns[0] not in tm:
			tm[tns[0]] = TmTile()
		tm[tns[0]].setSubtile(".".join(tns[1:]), d)
	else:
		tm[tns[0]] = d





def loadTeamTiles(server, team):
	ret = {}
	if os.path.exists(bingodata._teamFile(server, team)):
		with open(bingodata._teamFile(server, team), "r") as f:
			d = json.load(f)

		for sl, tl in d.items():
			ret[sl] = TmTile(tl)

	return ret


def saveTeamTiles(server, team, tld):
	d = {}

	for sl, tl in tld.items():
		d[sl] = tl.toDict()

	with open(bingodata._teamFile(server, team), "w") as f:
		json.dump(d, f)


def renameTeam(server, old, new):
	tls = loadTeamTiles(server, old)
	saveTeamTiles(server, new, tls)
	try:
		os.remove(bingodata._teamFile(server, old))
	except:
		pass



def addEvidence(server, team, tile, evidence):
	tm = loadTeamTiles(server, team)

	# if not tile in tm:
	# 	tm[tile] = TmTile()

	# tm[tile].evidence_links.appnd(evidence)

	saveTeamTiles(server, team, tm)


def onApproved(server, team, tile, mod):
    print(f"{str(mod)} approved tile {tile} for team {team}")

def onUnapproved(server, team, tile, mod):
    print(f"{str(mod)} unapproved tile {tile} for team {team}")


def _addApprovalInternal(server, tm, tile, mod, link = None):
	t = getTile(tm, tile)

	if t.status is not TmTileStatus.Approved:
		t.status = TmTileStatus.Approved
		onApproved(server, "???", tile, mod)

	if link:
		t.approved_links.append(link)

	if not str(mod) in t.approved_by:
		t.approved_by.append(str(mod))

	setTile(tm, tile, t)

	if "." in tile:
		split = tile.split(".")
		parentTile = ".".join(split[0:-1])
		subtileApproved(server, tm, parentTile, split[-1])


def _removeApprovalInternal(server, tm, tile, mod):
	t = getTile(tm, tile)

	if str(mod) in t.approved_by:
		t.approved_by[:] = [x for x in t.approved_by if not x == str(mod)]

	if not t.approved_by:
		t.status = TmTileStatus.Incomplete 
		onUnapproved(server, "???", tile, mod)

	setTile(tm, tile, t)

	if "." in tile:
		split = tile.split(".")
		parentTile = ".".join(split[0:-1])
		subtileUnapproved(server, tm, parentTile, split[-1])


def subtileApproved(server, tm, tile, subtile):
	brd = board.load(server)

	brdTile = brd.getTileByName(tile)
	tmTile = getTile(tm, tile)

	if brdTile.isComplete(tmTile):
		if tmTile.status is not TmTileStatus.Approved:
			tmTile.status = TmTileStatus.Approved
			onApproved(server, "???", tile, "BingoBot")

			if "." in tile:
				split = tile.split(".")
				parentTile = ".".join(split[0:-1])
				_removeApprovalInternal(server, tm, parentTile, "BingoBot", None)

	setTile(tm, tile, tmTile)

def subtileUnapproved(server, tm, tile, subtile):
	brd = board.load(server)

	brdTile = brd.getTileByName(tile)
	tmTile = getTile(tm, tile)

	if not brdTile.isComplete(tmTile):
		if tmTile.status is TmTileStatus.Approved:
			tmTile.status = TmTileStatus.Incomplete
			onUnapproved(server, "???", tile, "BingoBot")

			if "." in tile:
				split = tile.split(".")
				parentTile = ".".join(split[0:-1])
				_addApprovalInternal(server, tm, parentTile, "BingoBot", None)

	setTile(tm, tile, tmTile)


def addApproval(server, team, tile, mod, link = None):
	tm = loadTeamTiles(server, team)

	_addApprovalInternal(server, tm, tile, mod, link)

	saveTeamTiles(server, team, tm)


def removeApproval(server, team, tile, mod):
	tm = loadTeamTiles(server, team)

	_removeApprovalInternal(server, tm, tile, mod)

	saveTeamTiles(server, team, tm)


def setProgress(server, team, tile, progress, link = None):
	tm = loadTeamTiles(server, team)
	brd = board.load(server)
	tld = brd.getTileByName(tile)

	t = getTile(tm, tile)
	t.progress = progress
	setTile(tm, tile, t)

	if tld.isComplete(t): 
		if t.status is not TmTileStatus.Approved:
			_addApprovalInternal(server, tm, tile, "BingoBot")
	else:
		if t.status is TmTileStatus.Approved:
			_removeApprovalInternal(server, tm, tile, "BingoBot")

	saveTeamTiles(server, team, tm)

def setStatus(server, team, tile, staus):
	tm = loadTeamTiles(server, team)

	t = getTile(tm, tile)
	t.status = status 
	setTile(tm, tile, t)

	saveTeamTiles(server, team, tm)


def addProgress(server, team, tile, progress, link = None):
	tm = loadTeamTiles(server, team)
	brd = board.load(server)
	tld = brd.getTileByName(tile)

	t = getTile(tm, tile)
	t.progress = tld.mergeProgress(t.progress, progress)
	setTile(tm, tile, t)

	# Todo: Check if negative progress can be added
	if tld.isComplete(t): 
		if t.status is not TmTileStatus.Approved:
			_addApprovalInternal(server, tm, tile, "BingoBot")

	saveTeamTiles(server, team, tm)


def getTeamProgress(server, team):
	return loadTeamTiles(server, team)

def updateAllXPTiles(server):
	brd = board.load(server)
	xpTiles = brd.getXpTileNames()
	for tnm in xpTiles:
		xpTile = brd.getTileByName(tnm)
		skill = xpTile.skill
		WOM.WOMc.updateData(skill)
		teams = discordbingo.listTeams(server)
		for team in teams:
			tmpData = WOM.WOMc.getTeamData(skill, discordbingo.getTeamDisplayName(server, team))
			totalXP = tmpData.getTotalXP()
			setProgress(server, team, tnm, totalXP)
			print(f"{team} has {totalXP} xp gained in {skill}")
		print("^^^^^^^^^^^^^^^^^^^^")