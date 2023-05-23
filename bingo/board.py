
import os
import json
from bingo import bingodata, tiles

class Board(tiles.TileSet):
	def __init__(self, d = None):
		self.subtiles = {}
		if d:
			for sl, t in d["tiles"].items():
				self.subtiles[sl] = tiles.tileFromJson(t)

	def toDict(self):
		ret = {}
		ret["tiles"] = {}
		for sl, t in self.subtiles.items():
			ret["tiles"][sl] = t.toDict()

		return ret


# File Loading/Saving

def initFile(server):
	save(server, Board())

def load(server):
	ret = None
	if os.path.exists(bingodata._fieldsFile(server)):
		with open(bingodata._fieldsFile(server), "r") as f:
			d = json.load(f)

		ret = Board(d)
	else:
		ret = Board(None)

	return ret

def save(server, brd):
	with open(bingodata._fieldsFile(server), "w") as f:
		json.dump(brd.toDict(), f)


# Tile Functions

def addTile(server, tileName, tile):
	brd = load(server)
	brd.setTileByName(tileName, tile)
	save(server, brd)

def editTile(server, tileName, tile):
	brd = load(server)
	brd.setTileByName(tileName, tile)
	save(server, brd)

def renameTile(server, oldSlug, newSlug):
	brd = load(server)
	t = brd.getTileByName(oldSlug)
	brd.removeTile(oldSlug)
	brd.setTileByName(newSlug, t)
	save(server, brd)

def removeTile(server, tile):
	brd = load(server)
	brd.removeTile(tile)
	save(server, brd)

