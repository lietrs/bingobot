
import os
import json
from bingo import bingodata
import math




class Tile:
	name = ""
	description = ""
	col = 0
	row = 0

	def __init__(self, d = None):
		self.name = ""
		self.description = ""
		self.col = 0
		self.row = 0

		if d:
			self.name = d["name"]
			self.description = d["description"]
			if "col" in d:
				self.col = d["col"]
				self.row = d["row"]


	def toDict(self):
		return {"type": "basic", "name": self.name, "description": self.description, "col": self.col, "row": self.row}

	def basicString(self):
		return f"{self.name} - {self.description}"

	def progressString(self, tmd):
		statstr = ["In progress", "Awaiting approval", "Completed!"]
		return statstr[tmd.status]

	def about(self):
		return f"Name: {self.name}\nDescription: {self.description}\nBoard Location: {self.col},{self.row}"

	def isComplete(self, tmd):
		return tmd.status == 2

	def mergeProgress(self, A, B):
		return A


def indentStr(str):
	return "\t" + str.replace("\n", "\n\t")

class TileSet(Tile):
	subtiles = {}

	def __init__(self, d = None):
		super().__init__(d)
		if d:
			self.subtiles = {}
			for sl, t in d["subtiles"].items():
				self.subtiles[sl] = tileFromJson(t)
		else:
			self.subtiles = {}

	def toDict(self):
		ret = super().toDict()
		ret["type"] = "set"
		ret["subtiles"] = {}
		for sl, t in self.subtiles.items(): 
			td = t.toDict()
			del td["col"]
			del td["row"]
			ret["subtiles"][sl] = td

		return ret

	def basicString(self):
		ret = super().basicString()
		for sl, t in self.subtiles.items():
			ret += "\n" + indentStr(f"[{sl}] " + t.basicString())

		return ret

	def progressString(self, tmd):
		ret = super().progressString(tmd)
		tstrs = []
		countApproved = 0

		for sl,td in self.subtiles.items():
			ps = "Not started"
			if sl in tmd.subtiles:
				ps = td.progressString(tmd.subtiles[sl])
				if tmd.subtiles[sl].status == 2:
					countApproved += 1
			tstrs.append(indentStr(f"{td.name}: {ps}"))

		ret += "\n" + "\n".join(tstrs)
		return ret

	def about(self):
		ret = super().about()
		ret += "\nSubtiles: " + ", ".join(self.subtiles.keys())
		return ret

	def mergeProgress(self, A, B):
		ret = {}
		for sl, t in self.subtiles():
			if sl in A and sl in B:
				ret[sl] = t.mergeProgress(A[sl], B[sl])
			elif sl in A:
				ret[sl] = A[sl]
			elif sl in B:
				ret[sl] = B[sl]
		return ret

	def getTileByName(self, subTileName):
		tns = subTileName.split(".")
		if len(tns) > 1:
			if isinstance(self.subtiles[tns[0]], TileSet):
				return self.subtiles[tns[0]].getTileByName(".".join(tns[1:]))
			else:
				# Error: Tried to access subtile, not a tile set
				return None
		else:
			return self.subtiles[tns[0]]

	def setTileByName(self, subTileName, tile):
		tns = subTileName.split(".")
		if len(tns) > 1:
			if isinstance(self.subtiles[tns[0]], TileSet):
				self.subtiles[tns[0]].setTileByName(".".join(tns[1:]), tile)
			else:
				# Error: Tried to access subtile, not a tile set
				return None
		else:
			self.subtiles[tns[0]] = tile

	def removeTile(self, subTileName):
		tns = subTileName.split(".")
		if len(tns) > 1:
			if isinstance(self.subtiles[tns[0]], TileSet):
				self.subtiles[tns[0]].removeTile(".".join(tns[1:]))
			else:
				# Error: Tried to access subtile, not a tile set
				return None
		else:
			del self.subtiles[tns[0]]
	
	def getTilesOfType(self, tileClass, path = ""):
		ret = []
		for stn, stt in self.subtiles.items():
			if isinstance(stt, tileClass):
				ret.append(path + stn)
			elif isinstance(stt, TileSet):
				ret.extend(stt.getTilesOfType(tileClass, path + stn + "."))
		return ret

	def getXpTiles(self):
		return self.getTilesOfType(XPTile)
	
	def getCountTiles(self):
		return self.getTilesOfType(CountTile)


	def findTileByDescription(self, description):
		for stn, stt in self.subtiles.items():
			if stt.description == description:
				return stn
			elif isinstance(stt, TileSet):
				ret = stt.findTileByDescription(description)
				if ret:
					return stn + "." + ret
		return None



class TileAnyOf(TileSet):
	
	def toDict(self):
		ret = super().toDict()
		ret["type"] = "any"
		return ret

	def isComplete(self, tm):
		for brdTileName, brdTile in self.subtiles.items():
			if brdTileName in tm.subtiles:
				if brdTile.isComplete(tm.subtiles[brdTileName]):
					return True
		return False


class TileAllOf(TileSet):
	
	def toDict(self):
		ret = super().toDict()
		ret["type"] = "all"
		return ret

	def progressString(self, tmd):
		tstrs = []
		countApproved = 0

		for sl,td in self.subtiles.items():
			ps = "Not started"
			if sl in tmd.subtiles:
				ps = td.progressString(tmd.subtiles[sl])
				if tmd.subtiles[sl].status == 2:
					countApproved += 1
			tstrs.append(indentStr(f"{td.name}: {ps}"))

		ret = f"{countApproved} out of {len(self.subtiles)} completed\n" + "\n".join(tstrs)
		return ret

	def isComplete(self, tm):
		for brdTileName, brdTile in self.subtiles.items():
			if brdTileName in tm.subtiles:
				if not brdTile.isComplete(tm.subtiles[brdTileName]):
					return False
			else:
				return False
		return True



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

	def progressString(self, tmd):
		if tmd.status > 0:
			return super().progressString(tmd)
		else:
			pint = 0
			if tmd.progress:
				pint = int(tmd.progress)
			pct = str(math.floor(pint / self.required * 1000) / 10)

			return f"{formatXP(pint)} / {formatXP(self.required)} ({pct}%)"

	def about(self):
		return super().about() + f"\nXP Requirement: {formatXP(self.required)} {self.skill}"

	def mergeProgress(self, A, B):
		if not A: 
			A = "0"
		if not B:
			B = "0"
		return str(max(int(A),int(B)))


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

	def progressString(self, tmd):
		if tmd.status > 0:
			return super().progressString(tmd)
		else:
			pint = 0
			if tmd.progress:
				pint = int(tmd.progress)
			pct = str(math.floor(pint / self.required * 1000) / 10)
			return f"{pint} / {self.required} ({pct}%)"

	def about(self):
		return super().about() + f"\nRequirement: {self.required}"

	def mergeProgress(self, A, B):
		if A == "":
			A = "0"
		if B == "":
			B = "0"
		return str(int(A)+int(B))

# class ItemsTile(Tile):
# 	items = []

# 	def __init__(self, d = None):
# 		super().__init__(d)
# 		self.items = []
# 		if d:
# 			self.items = d["items"]

# 	def toDict(self):
# 		ret = super().toDict()
# 		ret["items"] = self.items
# 		ret["type"] = "items"

# 		return ret

# 	def basicString(self):
# 		itemList = ", ".join(self.items)
# 		return f"{super().basicString()} ({itemList})"

# 	def progressString(self, tmd):
# 		if status > 0:
# 			return super().progressString(tmd)
# 		else:
# 			done = tmd.progress.split(",")
# 			cnt = 0
# 			txt = []

# 			for i in self.items:
# 				if i in done:
# 					cnt += 1
# 					txt.append(f"~{i}~")
# 				else:
# 					txt.append(i)

# 			itemlist = ", ".join(txt)
# 			return f"{cnt} out of {len(self.items)} ({itemlist})"

# 	def about(self):
# 		return super().about() + f"\nRequirement: {', '.join(self.items)}"


# 	def mergeProgress(self, A, B):
# 		ret = []
# 		for i in self.items:
# 			if (i in A) or (i in B):
# 				ret.append(i)

# 		return ",".join(ret)



def tileFromJson(js):
	match js["type"]:
		case "basic":
			ret = Tile(js)
		case "xp":
			ret = XPTile(js)
		case "count":
			ret = CountTile(js)
		# case "items":
		# 	ret = ItemsTile(js)
		case "set":
			ret = TileSet(js)
		case "all":
			ret = TileAllOf(js)
		case "any":
			ret = TileAnyOf(js)

	return ret
