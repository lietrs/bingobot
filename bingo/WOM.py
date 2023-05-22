import requests #pip install requests
import csv
import pandas as pd #pip install pandas
from io import StringIO
import time
import json

class WOMcomp:
	
    def __init__(self, id:str):
        self.id = id
        self.DataTeamLists = {}
        
    
    def makeAPIUrl(self, skill:str):
        self.url = f"https://api.wiseoldman.net/v2/competitions/{self.id}/csv?table=teams&metric={skill}"

    def updateData(self, skill:str):
        self.makeAPIUrl(skill)
        DataApi = requests.get(self.url)
        if DataApi.status_code == 200:
            '''convert data into list of lines'''
            DataStr = DataApi.text
            DataList = DataStr.splitlines()
            DataTeamLists = []
            '''remove header and add data in WOMCompTeamData'''
            Lines = len(DataList)
            
            for Line in range(Lines):
                if Line != 0:
                    tempList = DataList[Line].split(",")
                    DataTeamLists.append(WOMCompTeamData(tempList[0], tempList[1], tempList[2], tempList[3], tempList[4], tempList[5], skill))
            self.DataTeamLists = DataTeamLists
        else:
            print("error: api data was wrong")
    
    def getTeamData(self, skill:str, teamName:str):
        if not self.DataTeamLists:
            self.updateData(skill)
        Lines = len(self.DataTeamLists)
        for Line in range(Lines):
            if self.DataTeamLists[Line].teamName == teamName:
                return self.DataTeamLists[Line]

    

class WOMCompTeamData:
    def __init__(self, rank, teamName, PlayerAmount, TotalXP, AvgXP, MVP, skill):
        self.rank = rank
        self.teamName = teamName
        self.PlayerAmount = PlayerAmount
        self.TotalXP = TotalXP
        self.AvgXP = AvgXP
        self.MVP = MVP
        self.skill = skill

    def getTotalXP(self):
        return self.TotalXP
    
    def getSkill(self):
        return self.skill
    
    def getTeamName(self):
        return self.teamName

class WOMGroup:
    
    def __init__(self, id:str):
        self.id = id
        
    def updateUser(self, user:str, data:pd.DataFrame = []):
        assert type(user) is str
        time.sleep(1.5)
        print('{user} ({row}/{ttl})'.format(user=user,
                                            row=data.u_count.loc[user] + 1,
                                            ttl=data.u_count.max() + 1))
        try:
            r = requests.post('https://api.wiseoldman.net/v2/players/{}'.format(user), timeout=10)
            print('status: {}'.format(r.status_code))
        except requests.ReadTimeout as t:
            print('Timeout Error')
            return 408

    def updateGroup(self):
        # Get list of users
        users = []
        tmp_r = requests.get('https://api.wiseoldman.net/v2/groups/{}'.format(self.id))
        tmp_j = tmp_r.json()
        tmp_m = [x['player']['username'] for x in tmp_j['memberships']]
        users += tmp_m 
        users = pd.DataFrame(pd.Series(users).unique(), columns=['user'])
        users['u_count'] = users.index
        users = users.set_index('user')
        for x in users.index.tolist():
            self.__class__.updateUser(self,x, users)
            
#init

# with open("./config/WOM.json", 'r') as f:
#     WOMjson = json.load(f)
#     WOMid = WOMjson['competition id']
#     WOMgid = WOMjson['group id']

# WOMg = WOMGroup(WOMgid)
# WOMc = WOMcomp(WOMid)

