
import os
import json
from bingo import bingodata, tiles


class Board:
	tiles = {}

	def __init__(self, d = None):
		self.tiles = {}
		if d:
			for sl, t in d["tiles"].items():
				self.tiles[sl] = tiles.tileFromJson(t)

	def toDict(self):
		ret = {}
		ret["tiles"] = {}
		for sl, t in self.tiles.items():
			ret["tiles"][sl] = t.toDict()

		return ret

	def getTileByName(self, tileName):
		tns = tileName.split(".")
		if len(tns) > 1:
			if isinstance(self.tiles[tns[0]], tiles.TileSet):
				return self.tiles[tns[0]].getTileByName(".".join(tns[1:]))
			else:
				# Error: Tried to access subtile, not a tile set
				return None
		else:
			return self.tiles[tns[0]]

	def setTileByName(self, tileName, tile):
		tns = tileName.split(".")
		if len(tns) > 1:
			if isinstance(self.tiles[tns[0]], tiles.TileSet):
				self.tiles[tns[0]].setTileByName(".".join(tns[1:]), tile)
			else:
				# Error: Tried to access subtile, not a tile set
				return None
		else:
			self.tiles[tns[0]] = tile


	def removeTile(self, tileName):
		tns = tileName.split(".")
		if len(tns) > 1:
			if isinstance(self.tiles[tns[0]], tiles.TileSet):
				self.tiles[tns[0]].removeTile(".".join(tns[1:]))
			else:
				# Error: Tried to access subtile, not a tile set
				return None
		else:
			del self.tiles[tns[0]]



def initFile(server):
	save(server, Board())


def load(server):
	ret = None
	if os.path.exists(bingodata._fieldsFile(server)):
		with open(bingodata._fieldsFile(server), "r") as f:
			d = json.load(f)

		ret = Board(d)

	return ret

def save(server, brd):
	with open(bingodata._fieldsFile(server), "w") as f:
		json.dump(brd.toDict(), f)


def addTile(server, tileName, tile):
	brd = load(server)
	brd.setTileByName(tileName, tile)
	save(server, brd)



def editTile(server, tileName, tile):
	brd = load(server)
	brd.setTileByName(tileName, tile)
	save(server, brd)

# def renameTile(server, oldSlug, newSlug):
# 	brd = load(server)
# 	t = tiles[oldSlug]
# 	del tiles[oldSlug]
# 	tiles[newSlug] = t
# 	save(server, brd)

def removeTile(server, tile):
	brd = load(server)
	brd.removeTile(tile)
	save(server, brd)

