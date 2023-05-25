
import os
import json
from bingo import bingodata, tiles, board
from bingo.teamdata import *
from PIL import Image #pip install pillow
from io import BytesIO

# Save/Load Files

def loadTeamBoard(server, team):
	ret = None
	if os.path.exists(bingodata._teamFile(server, team)):
		with open(bingodata._teamFile(server, team), "r") as f:
			d = json.load(f)

		ret = BoardStatus(d)
	else:
		ret = BoardStatus()

	return ret


def saveTeamBoard(server, teamSlug, teamBoard):
	d = teamBoard.toDict()

	with open(bingodata._teamFile(server, teamSlug), "w") as f:
		json.dump(d, f)


def renameTeam(server, oldSlug, newSlug):
	tls = loadTeamBoard(server, oldSlug)
	saveTeamBoard(server, newSlug, tls)
	try:
		os.remove(bingodata._teamFile(server, oldSlug))
	except:
		pass

def resetTeam(server, teamSlug):
	saveTeamBoard(server, teamSlug, BoardStatus())




# Modify

def _subtileChanged(brd, tmData, tileName, subtile):

	brdTile = brd.getTileByName(tileName)
	tileStatus = tmData.getTile(tileName)

	ret = []

	if tileStatus.status() == ApproveStatus.Disputed:
		# Tile already in dispute
		return []

	if brdTile.isComplete(tileStatus):
		if tileStatus.status() != ApproveStatus.Approved:
			ret += _approveTile(brd, tmData, tileName)
	else:
		if tileStatus.status() == ApproveStatus.Approved:
			_unapproveTile(brd, tmData, tileName)

	tmData.setTile(tileName, tileStatus)

	return ret


def _onTileStatusChange(brd, tmData, tileName):
	if "." in tileName:
		# Check if parent tiles are completed

		split = tileName.split(".")
		parentTile = ".".join(split[0:-1])
		return _subtileChanged(brd, tmData, parentTile, split[-1])

	return []


def _approveTile(brd, tmData, tileName, mod = "BingoBot"):

	if tmData.approve(tileName, mod):
		return [tileName] + _onTileStatusChange(brd, tmData, tileName)

	return []

def _unapproveTile(brd, tmData, tileName, mod = "BingoBot"):

	if tmData.unapprove(tileName, mod):
		_onTileStatusChange(brd, tmData, tileName)

def _disputeTile(brd, tmData, tileName, mod = "BingoBot"):

	if tmData.dispute(tileName, mod):
		_onTileStatusChange(brd, tmData, tileName)

def _resolveTile(brd, tmData, tileName, mod = "BingoBot"):

	if tmData.resolveDispute(tileName, mod):
		_onTileStatusChange(brd, tmData, tileName)


def approveTile(server, team, tileName, mod = "BingoBot"):
	brd = board.load(server)
	tmData = loadTeamBoard(server, team)

	ret = _approveTile(brd, tmData, tileName, mod)

	saveTeamBoard(server, team, tmData)

	return ret

def unapproveTile(server, team, tileName, mod = "BingoBot"):
	brd = board.load(server)
	tmData = loadTeamBoard(server, team)

	_unapproveTile(brd, tmData, tileName, mod)

	saveTeamBoard(server, team, tmData)

def disputeTile(server, team, tileName, mod = "BingoBot"):
	brd = board.load(server)
	tmData = loadTeamBoard(server, team)

	_disputeTile(brd, tmData, tileName, mod)

	saveTeamBoard(server, team, tmData)

def resolveTile(server, team, tileName, mod = "BingoBot"):
	brd = board.load(server)
	tmData = loadTeamBoard(server, team)

	_resolveTile(brd, tmData, tileName, mod)

	saveTeamBoard(server, team, tmData)


def _setProgress(brd, tmData, tileName, progress):
	tld = brd.getTileByName(tileName)

	t = tmData.getTile(tileName)
	t.progress = progress
	tmData.setTile(tileName, t)

	print(f"Trace: {tileName} {progress} {tld.isComplete(t)}")

	if tld.isComplete(t): 
		if t.status != ApproveStatus.Approved:
			_approveTile(brd, tmData, tileName, "BingoBot")
			return True
	else:
		if t.status == ApproveStatus.Approved:
			_unapproveTile(brd, tmData, tileName, "BingoBot")

	return False


def _addProgress(brd, tmData, tileName, progress):
	tld = brd.getTileByName(tileName)

	t = tmData.getTile(tileName)
	t.progress = tld.mergeProgress(t.progress, progress)
	tmData.setTile(tileName, t)

	if tld.isComplete(t): 
		if t.status() != ApproveStatus.Approved:
			_approveTile(brd, tmData, tileName, "BingoBot")
	else:
		if t.status() == ApproveStatus.Approved:
			_unapproveTile(brd, tmData, tileName, "BingoBot")



def setProgress(server, team, tileName, progress):
	tmData = loadTeamBoard(server, team)
	brd = board.load(server)

	_setProgress(brd, tmData, tileName, progress)

	saveTeamBoard(server, team, tmData)


def addProgress(server, team, tileName, progress):
	tmData = loadTeamBoard(server, team)
	brd = board.load(server)

	_addProgress(brd, tmData, tileName, progress)

	saveTeamBoard(server, team, tmData)




def boardString(server, team):
	brd = board.load(server)
	tmd = loadTeamBoard(server, team)

	tstrs = []

	# Todo: It's fixed 5x5 currently
	matrix = [[0]*5 for i in range(5)]

	for sl,td in brd.subtiles.items():
		matrix[td.row][td.col] = tmd.getTile(sl).status()

	ret = ""
	chars = [" ", "C", "A", "D"]
	for row in matrix:
		ret += "| "
		for square in row:
			ret += f"{chars[square]} | "
		ret += "\n"

	return ret

def fillProgressBoard(teamData, board, server):
	#boardsize = (1428,2000)
	completesize = (200,200)
	#tilesize = (286,232)
	#boardstartpoint = (0,600)
	boardRows = 5
	boardCols = 5
	#empty array
	completed =  [[0 for i in range(boardCols)] for j in range(boardRows)]
	points = 0
	backgound = Image.open(bingodata._boardImgFile(server))
	overlay = Image.open(bingodata._completeImgFile(server))
	overlay = overlay.resize(completesize)
	boardImg = backgound.copy()
	for tileName,tileData in board.subtiles.items():
		# Get team progress on that tile
		tmTile = teamData.getTile(tileName)
		#if tile completed
		if tmTile.status() == 2:
			col = tileData.col
			row = tileData.row
			completed[col][row] = 1
			boardImg.paste(overlay, (43+(col*286),610+(row*232)), overlay)
	bonusCol = 0
	bonusRow = 0
	for i in range(boardCols):
		for j in range(boardRows):
			if completed[i][j] == 1:
				points += 1
				bonusRow += 1
		if bonusRow == boardRows:
			points += 3
		bonusRow = 0

	for j in range(boardRows):
		for i in range(boardCols):
			if completed[i][j] == 1:
				bonusCol += 1
		if bonusCol == boardCols:
			points += 3
		bonusCol = 0



	bytes = BytesIO()
	boardImg.save(bytes, format="PNG")
	bytes.seek(0)
	return bytes, points
