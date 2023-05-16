
import os
from bingo import bingodata


gTILES = {}


class Tile:
	slug = ""
	name = ""
	description = ""
	board_x = 0
	board_y = 0

	def toDict(self):
		return {"type": "basic", "name": self.name, "description": self.description, "board": {"x": self.board_x, "y": self.board_y}}

	def fromDict(self, d):
		self.slug = d["slug"]
		self.name = d["name"]
		self.description = d["description"]
		self.board_x = d["board"]["x"]
		self.board_y = d["board"]["y"]

	def basicString(self):
		return f"[{self.slug}] {self.name} - {self.description}"


class XPTile(Tile):
	skill = ""
	required = 0

	def toDict(self):
		ret = super().toDict()
		ret["skill"] = skill
		ret["required"] = required
		ret["type"] = "xp"

	def fromDict(self, d):
		super().fromDict(d)
		self.skill = d["skill"]
		self.required = d["required"]

	def basicString(self):
		return f"{super().basicString()} ({self.required} {self.skill} xp required)"


class CountTile(Tile):
	required = 0

	def toDict(self):
		ret = super().toDict()
		ret["required"] = required
		ret["type"] = "count"

	def fromDict(self, d):
		super().fromDict(d)
		self.required = d["required"]

	def basicString(self):
		return f"{super().basicString()} ({self.required} required)"


class ItemsTile(Tile):
	items = []

	def toDict(self):
		ret = super().toDict()
		ret["items"] = items
		ret["type"] = "items"

	def fromDict(self, d):
		super().fromDict(d)
		self.items = d["items"]

	def basicString(self):
		itemList = ", ".join(self.items)
		return f"{super().basicString()} ({itemList})"





def initFile(server):
	saveFile(server)



def reloadFile(server):
	pass

def saveFile(server):
	pass



def editTile(server, tile):
	gTILES[tile.slug] = tile
	saveFile(server)

def renameTile(server, oldSlug, newSlug):
	t = gTILES[oldSlug]
	del gTILES[oldSlug]
	gTILES[newSlug] = t

def removeTile(server, tile):
	del gTILES[tile]

def all():
	return gTILES