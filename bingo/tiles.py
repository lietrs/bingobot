
import os
import json
from bingo import bingodata


gTILES = {}


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

	def toDict(self):
		return {"type": "basic", "name": self.name, "description": self.description, "board": {"x": self.board_x, "y": self.board_y}}

	def basicString(self):
		return f"{self.name} - {self.description}"


class XPTile(Tile):
	skill = ""
	required = 0

	def __init__(self, d):
		super().__init__(d)
		self.skill = d["skill"]
		self.required = d["required"]

	def toDict(self):
		ret = super().toDict()
		ret["skill"] = skill
		ret["required"] = required
		ret["type"] = "xp"

	def basicString(self):
		return f"{super().basicString()} ({self.required} {self.skill} xp required)"


class CountTile(Tile):
	required = 0

	def __init__(self, d):
		super().__init__(d)
		self.required = d["required"]

	def toDict(self):
		ret = super().toDict()
		ret["required"] = required
		ret["type"] = "count"

	def basicString(self):
		return f"{super().basicString()} ({self.required} required)"


class ItemsTile(Tile):
	items = []

	def __init__(self, d):
		super().__init__(d)
		self.items = d["items"]

	def toDict(self):
		ret = super().toDict()
		ret["items"] = items
		ret["type"] = "items"

	def basicString(self):
		itemList = ", ".join(self.items)
		return f"{super().basicString()} ({itemList})"





def initFile(server):
	saveFile(server)



def loadFile(server):
	with open(bingodata._fieldsFile(server), "r") as f:
		d = json.load(f)

	ret = {}

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

def saveFile(server, tld):
	d = {}
	for s, tl in tld.items():
		d[s] = tl.toDict()

	with open(bingodata._fieldsFile(server), "w") as f:
		json.dump(d, f)


def editTile(server, tile):
	tiles = loadFile(server)
	tiles[tile.slug] = tile
	saveFile(server, tiles)

def renameTile(server, oldSlug, newSlug):
	tiles = loadFile(server)
	t = tiles[oldSlug]
	del tiles[oldSlug]
	tiles[newSlug] = t
	saveFile(server, tiles)

def removeTile(server, tile):
	tiles = loadFile(server)
	del tiles[tile]
	saveFile(server, tiles)


def all(server):
	return loadFile(server)