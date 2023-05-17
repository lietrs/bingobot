
import os
import json



DATADIR = ""


def initData(root):
	global DATADIR
	DATADIR = os.path.join(root, "data")
	os.makedirs(DATADIR, exist_ok=True)


def _serverDir(server):
	return os.path.join(DATADIR, str(server))


def _teamFile(server, team):
	return os.path.join(_serverDir(server), team + ".json")


def _fieldsFile(server):
	return os.path.join(_serverDir(server), "BingoFields.json")

def _bingoFile(server):
	return os.path.join(_serverDir(server), "status.json")


def initServer(server):
	os.makedirs(_serverDir(server), exist_ok=True)



# General bingo status stored data

def getBingoStatus(server):
	if os.path.exists(_bingoFile(server)):
		with open(_bingoFile(server), "r") as f:
			d = json.load(f)

		return d
	else:
		return {"started": False, "ended": False}

def setBingoStatus(server, status):

	with open(bingodata._teamFile(server), "w") as f:
		json.dump(status, f)

def isBingoStarted(server):
	st = getBingoStatus(server)
	return st["started"]

def isBingoEnded(server):
	st = getBingoStatus(server)
	return st["started"]

def isBingoActive(server):
	st = getBingoStatus(server)
	return st["started"] and not st["ended"]
