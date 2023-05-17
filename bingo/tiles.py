
import os
import json
from bingo import bingodata
import math




class Tile:
	name = ""
	description = ""
	board_x = 0
	board_y = 0

	def __init__(self, d = None):
		if d:
			self.name = d["name"]
			self.description = d["description"]
			self.board_x = d["board"]["x"]
			self.board_y = d["board"]["y"]
		else:
			self.name = ""
			self.description = ""
			self.board_x = 0
			self.board_y = 0


	def toDict(self):
		return {"type": "basic", "name": self.name, "description": self.description, "board": {"x": self.board_x, "y": self.board_y}}

	def basicString(self):
		return f"{self.name} - {self.description}"

	def progressString(self, status, progress):
		statstr = ["In progress", "Awaiting approval", "Completed!"]
		return statstr[status]

	def about(self):
		return f"Name: {self.name}\nDescription: {self.description}\nBoard Location: {self.board_x},{self.board_y}"

	def mergeProgress(self, A, B):
		return A



def formatXP(amount):
	amount = int(amount)
	
	if amount >= 1000000:
		return str(math.floor(amount / 10000) / 100) + "M"
	elif amount >= 1000:
		return str(math.floor(amount / 100) / 10) + "K"
	else:
		return str(amount)


class XPTile(Tile):
	skill = ""
	required = 0

	def __init__(self, d = None):
		super().__init__(d)
		self.skill = ""
		self.required = 0

		if d:
			self.skill = d["skill"]
			self.required = d["required"]

	def toDict(self):
		ret = super().toDict()
		ret["skill"] = self.skill
		ret["required"] = self.required
		ret["type"] = "xp"

		if self.name == "":
			self.name = f"{formatXP(self.required)} {self.skill}"

		return ret

	def basicString(self):
		return f"{super().basicString()} ({self.required} {self.skill} xp required)"

	def progressString(self, status, progress):
		if status > 0:
			return super().progressString(status, progress)
		else:
			pct = str(math.floor(int(progress) / self.required * 1000) / 10)

			return f"{formatXP(progress)} / {formatXP(self.required)} ({pct}%)"

	def about(self):
		return super().about() + f"\nXP Requirement: {formatXP(self.required)} {self.skill}"

	def mergeProgress(self, A, B):
		return str(int(A)+int(B))


class CountTile(Tile):
	required = 0

	def __init__(self, d = None):
		super().__init__(d)
		self.required = 0
		if d:
			self.required = d["required"]

	def toDict(self):
		ret = super().toDict()
		ret["required"] = self.required
		ret["type"] = "count"

		return ret

	def basicString(self):
		return f"{super().basicString()} ({self.required} required)"

	def progressString(self, status, progress):
		if status > 0:
			return super().progressString(status, progress)
		else:
			pct = str(math.floor(int(progress) / self.required * 1000) / 10)
			return f"{progress} / {self.required} ({pct}%)"

	def about(self):
		return super().about() + f"\nRequirement: {self.required}"

	def mergeProgress(self, A, B):
		return str(int(A)+int(B))

class ItemsTile(Tile):
	items = []

	def __init__(self, d = None):
		super().__init__(d)
		self.items = []
		if d:
			self.items = d["items"]

	def toDict(self):
		ret = super().toDict()
		ret["items"] = self.items
		ret["type"] = "items"

		return ret

	def basicString(self):
		itemList = ", ".join(self.items)
		return f"{super().basicString()} ({itemList})"

	def progressString(self, status, progress):
		if status > 0:
			return super().progressString(status, progress)
		else:
			done = progress.split(",")
			cnt = 0
			txt = []

			for i in self.items:
				if i in done:
					cnt += 1
					txt.append(f"~{i}~")
				else:
					txt.append(i)

			itemlist = ", ".join(txt)
			return f"{cnt} out of {len(self.items)} ({itemlist})"

	def about(self):
		return super().about() + f"\nRequirement: {', '.join(self.items)}"


	def mergeProgress(self, A, B):
		ret = []
		for i in self.items:
			if (i in A) or (i in B):
				ret.append(i)

		return ",".join(ret)







def initFile(server):
	saveFile(server)



#Todo: In memory copy of tile data
def loadTiles(server):
	ret = {}
	if os.path.exists(bingodata._fieldsFile(server)):
		with open(bingodata._fieldsFile(server), "r") as f:
			d = json.load(f)

		for s, td in d.items():
			match td["type"]:
				case "basic":
					ret[s] = Tile(td)
				case "xp":
					ret[s] = XPTile(td)
				case "count":
					ret[s] = CountTile(td)
				case "items":
					ret[s] = ItemsTile(td)

	return ret

def saveTiles(server, tld):
	d = {}
	for s, tl in tld.items():
		d[s] = tl.toDict()

	with open(bingodata._fieldsFile(server), "w") as f:
		json.dump(d, f)



def editTile(server, tile):
	tiles = loadTiles(server)
	tiles[tile.slug] = tile
	saveTiles(server, tiles)

def renameTile(server, oldSlug, newSlug):
	tiles = loadTiles(server)
	t = tiles[oldSlug]
	del tiles[oldSlug]
	tiles[newSlug] = t
	saveTiles(server, tiles)

def removeTile(server, tile):
	tiles = loadTiles(server)
	del tiles[tile]
	saveTiles(server, tiles)


def all(server):
	return loadTiles(server)

