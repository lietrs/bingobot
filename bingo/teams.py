
import os
import json
from bingo import bingodata, tiles


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

	def __init__(self, d = None):
		if not d:
			d = {"status": 0, "completed_by": "", "approved_by": [], "approved_links": [], "evidence_links": [], "progress": ""}

		self.status = d["status"]
		self.completed_by = d["completed_by"]
		self.approved_by = d["approved_by"]
		self.approved_links = d["approved_links"]
		self.evidence_links = d["evidence_links"]
		self.progress = d["progress"]

	def toDict(self):
		return {"status": self.status, "completed_by": self.completed_by, "approved_by": self.approved_by, "approved_links": self.approved_links, "evidence_links": self.evidence_links, "progress": self.progress}

	def basicString(self):
		match self.status:
			case TmTileStatus.Incomplete:
				return f"Tile incomplete"
			case TmTileStatus.Finished:
				return "Awaiting approval"
			case TmTileStatus.Approved:
				return "Tile Completed!"




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
		os.remove(bingodata._teamFile(server, team))
	except:
		pass



def addEvidence(server, team, tile, evidence):
	tm = loadTeamTiles(server, team)

	if not tile in tm:
		tm[tile] = TmTile()

	tm[tile].evidence_links.appnd(evidence)

	saveTeamTiles(server, team, tm)



def setProgress(server, team, tile, progress):
	tm = loadTeamTiles(server, team)

	if not tile in tm:
		tm[tile] = TmTile()

	tm[tile].progress = progress

	saveTeamTiles(server, team, tm)


def addApproval(server, team, tile, mod, link = None):
	tm = loadTeamTiles(server, team)

	if not tile in tm:
		tm[tile] = TmTile()

	tm[tile].status = TmTileStatus.Approved

	if link:
		tm[tile].approved_links.append(link)

	if not mod in tm[tile].approved_by:
		tm[tile].approved_by.append(mod)

	saveTeamTiles(server, team, tm)


def addProgress(server, team, tile, progress, link = None):
	tm = loadTeamTiles(server, team)
	tld = tiles.all(server)[tile]

	if not tile in tm:
		tm[tile] = TmTile()

	if link:
		tm[tile].evidence_links.append(link)


	tm[tile].progress = tld.mergeProgress(tm[tile].progress, progress)

	saveTeamTiles(server, team, tm)

def setProgress(server, team, tile, progress, link = None):
	tm = loadTeamTiles(server, team)
	tld = tiles.all(server)[tile]

	if not tile in tm:
		tm[tile] = TmTile()

	if link:
		tm[tile].evidence_links.append(link)

	tm[tile].progress = progress

	saveTeamTiles(server, team, tm)


def getTeamProgress(server, team):
	return loadTeamTiles(server, team)

