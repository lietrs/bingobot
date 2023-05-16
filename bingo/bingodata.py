
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



def initServer(server):
	os.makedirs(_serverDir(server), exist_ok=True)

