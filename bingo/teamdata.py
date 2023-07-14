
import os
import json


class ApproveStatus:
	Incomplete = 0
	Finished = 1
	Approved = 2
	Disputed = 3

	strings = ["Incomplete", "Awaiting Approval", "Complete", "Disputed"]


class TileStatus:
	approved_by = []
	disputed_by = []
	progress = ""
	subtiles = {}

	def __init__(self, d = None):
		if not d:
			d = {"approved_by": [], "disputed_by": [], "progress": ""}

		self.approved_by = d["approved_by"]
		self.disputed_by = d["disputed_by"]
		self.progress = d["progress"]
		self.subtiles = {}
		if "subtiles" in d:
			for sl, t in d["subtiles"].items():
				self.subtiles[sl] = TileStatus(t)

	def toDict(self):
		ret = {"approved_by": self.approved_by, "disputed_by": self.disputed_by, "progress": self.progress}
		if self.subtiles:
			ret["subtiles"] = {}
			for sl, t in self.subtiles.items():
				ret["subtiles"][sl] = t.toDict()

		return ret

	def status(self):
		ret = ApproveStatus.Incomplete
		if self.approved_by:
			ret = ApproveStatus.Approved
		if self.disputed_by:
			ret = ApproveStatus.Disputed
		return ret

	def basicString(self):
		return ApproveStatus.strings[self.status()]


	def getSubtile(self, subtileSlug):
		tns = subtileSlug.split(".")
		if tns[0] not in self.subtiles:
			return TileStatus()

		if len(tns) > 1:
			return self.subtiles[tns[0]].getSubtile(".".join(tns[1:]))
		else:
			return self.subtiles[tns[0]]

	def setSubtile(self, subtileSlug, d):
		tns = subtileSlug.split(".")

		if len(tns) > 1:
			if tns[0] not in self.subtiles:
				self.subtiles[tns[0]] = TileStatus()
			self.subtiles[tns[0]].setSubtile(".".join(tns[1:]), d)
		else:
			self.subtiles[tns[0]] = d

	def approve(self, mod = "BingoBot"):
		if not mod in self.approved_by:
			self.approved_by.append(str(mod))

	def unapprove(self, mod = "BingoBot"):
		if mod in self.approved_by:
			self.approved_by[:] = [x for x in self.approved_by if x != str(mod)]

	def unapprove_all(self, mod = "BingoBot"):
		self.approved_by = []

	def dispute(self, mod = "BingoBot"):
		if not mod in self.disputed_by:
			self.disputed_by.append(str(mod))

	def resolveDispute(self, mod = "BingoBot"):
		if mod in self.disputed_by:
			self.disputed_by[:] = [x for x in self.disputed_by if x != str(mod)]

	def resolveDispute_all(self, mod = "BingoBot"):
		self.disputed_by = []



class BoardStatus:

	def __init__(self, d = None):
		self.tiles = {}
		self.links = {}
		if d:
			for sl, tl in d["tiles"].items():
				self.tiles[sl] = TileStatus(tl)

			if "links" in d:
				self.links = d["links"]

	def toDict(self):
		tls = {}
		for sl, tl in self.tiles.items():
			tls[sl] = tl.toDict()

		return {"tiles": tls, "links": self.links}

	def getTile(self, tileName):
		tns = tileName.split(".")
		if tns[0] not in self.tiles:
			return TileStatus()

		if len(tns) > 1:
			return self.tiles[tns[0]].getSubtile(".".join(tns[1:]))
		else:
			return self.tiles[tns[0]]

	def setTile(self, tileName, d):
		tns = tileName.split(".")

		if len(tns) > 1:
			if tns[0] not in self.tiles:
				self.tiles[tns[0]] = TileStatus()
			self.tiles[tns[0]].setSubtile(".".join(tns[1:]), d)
		else:
			self.tiles[tns[0]] = d

	def lookupLink(self, link):
		if link in self.links:
			return self.links[link]

		return None

	def addLink(self, link, tile):
		self.links[link] = tile

	def removeLink(self, link):
		del self.links[link]

	def applyStatusChange(self, function, tileName, mod):
		t = self.getTile(tileName)

		beforeStatus = t.status()
		function(t, mod)
		self.setTile(tileName, t)

		return beforeStatus != t.status()


	def approve(self, tileName, mod = "BingoBot", evidence = None):
		if evidence and not evidence in self.links:
			self.links[evidence] = tileName

		return self.applyStatusChange(TileStatus.approve, tileName, mod)

	def unapprove(self, tileName, mod = "BingoBot", evidence = None):
		if evidence and not evidence in self.links:
			self.links[evidence] = tileName
			
		return self.applyStatusChange(TileStatus.unapprove, tileName, mod)

	def unapprove_all(self, tileName, mod = "BingoBot", evidence = None):
		if evidence and not evidence in self.links:
			self.links[evidence] = tileName
			
		return self.applyStatusChange(TileStatus.unapprove_all, tileName, mod)

	def dispute(self, tileName, mod = "BingoBot", evidence = None):
		if evidence and not evidence in self.links:
			self.links[evidence] = tileName
			
		return self.applyStatusChange(TileStatus.dispute, tileName, mod)

	def resolveDispute(self, tileName, mod = "BingoBot", evidence = None):
		if evidence and not evidence in self.links:
			self.links[evidence] = tileName
			
		return self.applyStatusChange(TileStatus.resolveDispute, tileName, mod)

	def resolveDispute_all(self, tileName, mod = "BingoBot", evidence = None):
		if evidence and not evidence in self.links:
			self.links[evidence] = tileName
			
		return self.applyStatusChange(TileStatus.resolveDispute_all, tileName, mod)

