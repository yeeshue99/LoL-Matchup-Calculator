from settings import *
from collections import defaultdict

import sqlite3


class Database:
    @staticmethod
    def unwrapPlayer(player):
        return (player["id"], player["puuid"], player["name"], 0)

    @staticmethod
    def aggregateMatchData(match):
        try:
            matchData = {}
            matchInfo = match["info"]
            team1 = matchInfo["teams"][0]["teamId"]
            matchData[team1] = {}

            team2 = matchInfo["teams"][1]["teamId"]
            matchData[team2] = {}

            matchData[team1]["players"] = []
            matchData[team2]["players"] = []

            matchData["matchId"] = match["metadata"]["matchId"]

            for player in matchInfo["participants"]:
                matchData[player["teamId"]]["players"].append(
                    {
                        "championName": player["championName"],
                        "lane": player["lane"],
                        "championId": player["championId"],
                    }
                )
                if player["win"] and not "sideWon" in matchData:
                    matchData["sideWon"] = player["teamId"]

            return matchData
        except IndexError:
            print("Index error occured while trying to process match data. Skipping...")

    @staticmethod
    def unwrapMatchData(matchId, matchData):
        championList = []
        for team in [100, 200]:
            for player in matchData[team]["players"]:
                championList.append(player["championId"])
        if max(championList) > 887:
            print("Invalid match data. Champion ID larger than expected. Skipping...")
            raise TypeError
        championList.insert(0, matchId)
        championList.append(matchData["sideWon"])
        returnable = (championList)
        return (
            returnable
        )

    @staticmethod
    def addMatch(matchId):
        try:
            SQL = "insert into matches values (?, ?);"

            conn = sqlite3.connect(DATABASE_NAME)
            cur = conn.cursor()

            cur.execute(SQL, (matchId, False))

            conn.commit()

            conn.close()
        except sqlite3.IntegrityError:
            print(f"Integrity error occured while adding match for matchId: {matchId}")
            raise sqlite3.IntegrityError

    @staticmethod
    def addMatchData(matchId, data):
        try:
            SQL = "insert into matchData values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"

            conn = sqlite3.connect(DATABASE_NAME)
            cur = conn.cursor()

            matchData = Database.aggregateMatchData(data)

            cur.execute(SQL, Database.unwrapMatchData(matchId, matchData))

            conn.commit()

            conn.close()

            print(f"Added match for matchId: {matchId}")
        except sqlite3.IntegrityError:
            print(
                f"Integrity error occured while adding matchdata for matchId: {matchId}"
            )
            raise sqlite3.IntegrityError
        except KeyError:
            print(f"Key error occured when trying to decode match data. Skipping...")
        except ValueError:
            print(f"Error occured while trying to decode match data. Skipping...")
        except TypeError:
            print(f"Error occured while trying to decode match data. Skipping...")
            

    @staticmethod
    def getMatchData():
        SQL = "select * from matchData;"

        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()

        result = cur.execute(SQL).fetchall()
        return result

    @staticmethod
    def addUser(player):
        try:
            SQL = "insert into users values (?, ?, ?, ?);"

            conn = sqlite3.connect(DATABASE_NAME)
            cur = conn.cursor()

            cur.execute(SQL, Database.unwrapPlayer(player))

            conn.commit()

            conn.close()

            print(f"Added player: {player['name']}")
        except sqlite3.IntegrityError:
            print(
                f"Integrity error occured while adding user for userId: {player['name']}"
            )
            
    @staticmethod 
    def getMatchDataCount():
        SQL = "SELECT COUNT(*) FROM matchData;"

        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()

        result = cur.execute(SQL).fetchall()
        return result
    
    @staticmethod
    def startLoggingDatabaseData(printProgress=False):
        import datetime
        import time
        while True:
            with open(DATABASE_LOGGING_FILE, 'a') as f:
                databaseCount = Database.getMatchDataCount()[0][0]
                loggingString = f"{datetime.datetime.now()}\t\t{Database.getMatchDataCount()[0][0]}\n"
                if (printProgress):
                    print(loggingString)
                f.write(loggingString)
            time.sleep(LOGGING_TIMEOUT)

    @staticmethod
    def plotDatabaseData(): 
        import datetime
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import numpy as np
        import re
        
        with open(DATABASE_LOGGING_FILE, 'r') as f:
            data = f.readlines()
            
        # parse the string
        database_date_sizes_list = re.findall(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{6})\t\t(\d+)', "".join(data))

        # parse the dates
        dates = []
        for datestring in database_date_sizes_list:
            dates.append(datetime.datetime.strptime(datestring[0], '%Y-%m-%d %H:%M:%S.%f'))

        # convert to numpy array
        dates = np.array(dates)

        # convert to size
        sizes = np.array([int(s[1])/1000 for s in database_date_sizes_list])
        
        # plot the data
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.plot(dates, sizes, "-b", label="matches")
        plt.ylabel("Database size")
        plt.legend()
        plt.xlabel("Sampled Date")
        plt.show()

if __name__ == "__main__":
    Database.plotDatabaseData()
