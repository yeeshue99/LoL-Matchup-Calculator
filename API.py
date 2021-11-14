from riotwatcher import LolWatcher, ApiError
from settings import *
from database import Database
import time
import sqlite3
from dataFetch import calculateStartTime, downloadChampionBasicData
from utils import generateRandomlyFromList, chunks

class API:
    @staticmethod
    def savePlayerQueueToDisk(saveCopy):
        print("="*10)
        print("Application exit signal received. Caching loaded players...")
        import pickle
        i = 0
        for l in chunks(saveCopy, 100):
            with open(CACHED_PLAYERS_DIR / f"{str(i)}", 'wb') as filehandle:
                pickle.dump(l, filehandle)
            i += 1
            print(f"saved chunk {i}")
        import sys
        print("="*10)
        sys.exit()
        
    @staticmethod
    def loadPlayerQueueFromDisk():
        players = []
        firstPass = True
        for pth in CACHED_PLAYERS_DIR.iterdir():
            with open(pth, "rb") as filehandle:
                import pickle
                l = pickle.load(filehandle)
                if (firstPass):
                    try:
                        lol_watcher = LolWatcher(API_KEY)
                        id = l[0]["summonerId"]
                        acc = lol_watcher.summoner.by_id(REGION, id)
                        firstPass = False
                    except ApiError as err:
                        if err.response.status_code == 403:
                            print("API Key invalid. Please request a new one and try again.")
                            import sys
                            sys.exit()
                players += l
                del l
            pth.unlink()
            print(f"read chunk from {filehandle.name}")
        return players
    
    @staticmethod
    def getMatchesFromAccount(acc, start):
        lol_watcher = LolWatcher(API_KEY)
        count = 0
        try:
            matches = lol_watcher.match.matchlist_by_puuid(
                MATCH_REGION, acc["puuid"], count=100, start=start, type="ranked", queue=[420], start_time=calculateStartTime()
            )
        except ApiError as err:
                if err.response.status_code == 429:
                        print("We should retry in {} seconds.".format(err.response.headers["Retry-After"]))
                        print("this retry-after is handled by default by the RiotWatcher library")
                        print("future requests wait until the retry-after time passes")
                elif err.response.status_code == 404:
                    print("Match id not found. Skipping")
                    return
                elif err.response.status_code == 503:
                    print("Invalid request. Skipping...")
                    return
                elif err.response.status_code == 500:
                    print("Server error for url. Skipping...")
                    return
                else:
                    raise
        time.sleep(SLEEP_TIMER)
        count = 0
        failCount = 0
        if len(matches) == 0:
            return -1
        for matchId in generateRandomlyFromList(matches):
            try:
                print(f"for player: {acc['name']} ({start+count}/{start+100})")
                count += 1
                match = lol_watcher.match.by_id(MATCH_REGION, matchId)
                time.sleep(SLEEP_TIMER)
                Database.addMatchData(matchId, match)
            except ApiError as err:
                if err.response.status_code == 429:
                        print("We should retry in {} seconds.".format(err.response.headers["Retry-After"]))
                        print("this retry-after is handled by default by the RiotWatcher library")
                        print("future requests wait until the retry-after time passes")
                elif err.response.status_code == 404:
                    print("Match id not found. Skipping")
                elif err.response.status_code == 503:
                    print("Invalid request. Skipping...")
                elif err.response.status_code == 500:
                    print("Server error for url. Skipping...")
                else:
                    raise
            except sqlite3.IntegrityError:
                failCount += 1
                print(f"Alloted integrity failures: {failCount}/25")
                if (failCount > 25):
                    print("Too many integrity errors. Skipping...")
                    failCount = 0
                    break
            except Exception as e:
                raise e
            except BaseException as e:
                raise e
        return 0

    @staticmethod
    def loadMatches():
        lol_watcher = LolWatcher(API_KEY)
        if (len(list(CACHED_PLAYERS_DIR.iterdir())) > 1):
            players = API.loadPlayerQueueFromDisk()
        else:
            players = []
            league = lol_watcher.league.challenger_by_queue(REGION, LEAGUE_QUEUE)
            players.append(league["entries"])
            print("Challenger league loaded.")
            time.sleep(SLEEP_TIMER)
            league = lol_watcher.league.grandmaster_by_queue(REGION, LEAGUE_QUEUE)
            players.append(league["entries"])
            print("Grandmaster league loaded.")
            time.sleep(SLEEP_TIMER)
            league = lol_watcher.league.masters_by_queue(REGION, LEAGUE_QUEUE)
            players += league["entries"]
            print("Masters queue loaded")
            time.sleep(SLEEP_TIMER)
            for tier in LEAGUE_UPPER_TIERS:
                for division in LEAGUE_DIVISIONS:
                    # continue
                    for page in range(1,11):
                        players += lol_watcher.league.entries(region=REGION, queue=LEAGUE_QUEUE, tier=tier, division=division, page=page)
                        print(f"Loaded {tier} {division}, page {page}")
                        time.sleep(SLEEP_TIMER)
        print(f"Players in queue:{len(players)}")
        randomPlayers = generateRandomlyFromList(players)
        saveCopy = list(randomPlayers).copy()
        for player in randomPlayers:
            id = player["summonerId"]

            acc = lol_watcher.summoner.by_id(REGION, id)
            time.sleep(SLEEP_TIMER)
            Database.addUser(acc)
            start = -100
            for i in range(20):
                start += 100
                try:
                    print(f"Loading games {start} to {start + 100} for player {acc['name']}")
                    returnCode = API.getMatchesFromAccount(acc, start)
                    if (returnCode == -1):
                        print("No more games to load! Skipping...")
                        break
                    print()
                except ApiError as err:
                    if err.response.status_code == 429:
                        print(
                            "We should retry in {} seconds.".format(
                                err.response.headers["Retry-After"]
                            )
                        )
                        print(
                            "this retry-after is handled by default by the RiotWatcher library"
                        )
                        print("future requests wait until the retry-after time passes")
                        import sys
                        sys.exit()
                    elif err.response.status_code == 403:
                        print("API expired. Quitting...")
                        API.savePlayerQueueToDisk(saveCopy)
                    elif err.response.status_code == 404:
                        print("Match id not found.")
                    elif err.response.status_code == 503:
                        print("Server failed!")
                    else:
                        raise
                except KeyboardInterrupt:
                    API.savePlayerQueueToDisk(saveCopy)
                except Exception as e:
                    API.savePlayerQueueToDisk(saveCopy)
                except BaseException as e:
                    API.savePlayerQueueToDisk(saveCopy)
            saveCopy.remove(player)
            print(f"Players in queue:{len(players)}")
    
    @staticmethod
    def playerSummary(player, position, saveToFile=False, fileName=None):
        lol_watcher = LolWatcher(API_KEY)
        start=0
        acc = lol_watcher.summoner.by_name(REGION, player)
        time.sleep(SLEEP_TIMER)
        matches = []
        print("Loading matches 0-99")
        newSet = lol_watcher.match.matchlist_by_puuid(
                MATCH_REGION, acc["puuid"], count=100, start=start, type="ranked", queue=[420], start_time=calculateStartTime(number=10)
            )
        time.sleep(SLEEP_TIMER)
        matches += newSet
        print("Loading matches 100-199")
        newSet = lol_watcher.match.matchlist_by_puuid(
                MATCH_REGION, acc["puuid"], count=100, start=start+100, type="ranked", queue=[420], start_time=calculateStartTime(number=10)
            )
        time.sleep(SLEEP_TIMER)
        matches += newSet
        print("Loading matches 200-299")
        newSet = lol_watcher.match.matchlist_by_puuid(
                MATCH_REGION, acc["puuid"], count=100, start=start+200, type="ranked", queue=[420], start_time=calculateStartTime(number=10)
            )
        time.sleep(SLEEP_TIMER)
        matches += newSet
        
        puuid = acc["puuid"]
        count=0
        from collections import defaultdict
        champions = defaultdict(int)
        kills = []
        deaths = []
        assists = []
        kda = []
        vs = []
        vspm = []
        goldEarned = []
        gameTime = []
        gpm = []
        cs = []
        cspm = []
        
        for matchId in matches: 
            try:
                match = lol_watcher.match.by_id(MATCH_REGION, matchId)
                playerData = API.findPlayer(match, puuid)
                if (playerData["gameEndedInEarlySurrender"]):
                    continue
                if (not API.comparePosition(playerData["individualPosition"], position)):
                    continue
                print(f"for player: {acc['name']} ({start+count}/{start+100})")
                count += 1
                champions[playerData['championName']]+=1
                k = playerData['kills']
                d = playerData['deaths']
                a = playerData['assists']
                kills.append(k)
                deaths.append(d)
                assists.append(a)
                if (d == 0):
                    kda.append(k+a)
                else:
                    kda.append((k+a)/d)
                vs.append(playerData['visionScore'])
                vspm.append(playerData['visionScore'] / (playerData['timePlayed'] / 60))
                goldEarned.append(playerData['goldEarned'])
                gameTime.append(playerData['timePlayed'] / 60)
                gpm.append(playerData['goldEarned'] / (playerData['timePlayed'] / 60))
                cs.append(playerData['totalMinionsKilled'] + playerData['neutralMinionsKilled'])
                cspm.append((playerData['totalMinionsKilled'] + playerData['neutralMinionsKilled']) / (playerData['timePlayed'] / 60))
                time.sleep(SLEEP_TIMER)
                # Database.addMatchData(matchId, match)
            except ApiError as err:
                if err.response.status_code == 429:
                        print("We should retry in {} seconds.".format(err.response.headers["Retry-After"]))
                        print("this retry-after is handled by default by the RiotWatcher library")
                        print("future requests wait until the retry-after time passes")
                elif err.response.status_code == 404:
                    print("Match id not found. Skipping")
                elif err.response.status_code == 503:
                    print("Invalid request. Skipping...")
                elif err.response.status_code == 500:
                    print("Server error for url. Skipping...")
                else:
                    raise
        
        if (saveToFile):
            import sys
            print("Saving to file: " + fileName)
            f = open(fileName, 'w')
            sys.stdout = f
        print("="*20)
        print(f"Summary for player: {player}:")
        print(f"Total games over the last {10} patches: {count}")
        print(f"Total unique champions played: {len(champions)}")
        print()
        print(f"All champions played:")
        for key, value in dict(sorted(champions.items(), key=lambda item: item[1], reverse=True)).items():
            print(f"\t{key}: {value}")
        print()
        print(f"Kill stats:")
        print(f"\tHighest number of kills: {max(kills)}")
        print(f"\tLowest number of kills: {min(kills)}")
        print(f"\tAverage number of kills: {sum(kills)/len(kills)}")
        print()
        print(f"Death stats:")
        print(f"\tHighest number of deaths: {max(deaths)}")
        print(f"\tLowest number of deaths: {min(deaths)}")
        print(f"\tAverage number of deaths: {sum(deaths)/len(deaths)}")
        print()
        print(f"Assist stats:")
        print(f"\tHighest number of assists: {max(assists)}")
        print(f"\tLowest number of assists: {min(assists)}")
        print(f"\tAverage number of assists: {sum(assists)/len(assists)}")
        print()
        print(f"KDA stats:")
        print(f"\tHighest KDA: {max(kda)}")
        print(f"\tLowest KDA: {min(kda)}")
        print(f"\tAverage KDA: {sum(kda)/len(kda)}")
        print()
        print(f"Vision score stats:")
        print(f"\tHighest vision score: {max(vs)}")
        print(f"\tLowest Vvision score: {min(vs)}")
        print(f"\tAverage vision score: {sum(vs)/len(vs)}")
        print()
        print(f"VS/min stats:")
        print(f"\tHighest VS/min: {max(vspm)}")
        print(f"\tLowest VS/min: {min(vspm)}")
        print(f"\tAverage VS/min: {sum(vspm)/len(vspm)}")
        print()
        print(f"Gold stats:")
        print(f"\tHighest gold earned: {max(goldEarned)}")
        print(f"\tLowest gold earned: {min(goldEarned)}")
        print(f"\tAverage gold earned: {sum(goldEarned)/len(goldEarned)}")
        print()
        print(f"Game time stats:")
        print(f"\tLongest game: {max(gameTime)} mins")
        print(f"\tShortest game: {min(gameTime)} mins")
        print(f"\tAverage game time: {sum(gameTime)/len(gameTime)} mins")
        print()
        print(f"GPM stats:")
        print(f"\tHighest gpm: {max(gpm)}")
        print(f"\tLowest gpm: {min(gpm)}")
        print(f"\tAverage gpm: {sum(gpm)/len(gpm)}")
        print()
        print(f"CS stats:")
        print(f"\tMost CS: {max(cs)}")
        print(f"\tLeast CS: {min(cs)}")
        print(f"\tAverage CS: {sum(cs)/len(cs)}")
        print()
        print(f"CS/min stats:")
        print(f"\tHighest CS/min: {max(cspm)}")
        print(f"\tLowest CS/min: {min(cspm)}")
        print(f"\tAverage CS/min: {sum(cspm)/len(cspm)}")
        print()
        if (saveToFile):
            sys.stdout = sys.__stdout__
            f.close()
    
    @staticmethod
    def findPlayer(matchData, puuid):
        info = matchData["info"]
        participants = info["participants"]
        for player in participants:
            if player["puuid"] == puuid:
                return player
        return None
    
    @staticmethod
    def comparePosition(playerPosition, position):
        player = playerPosition.upper()
        pos = position.upper()
        if (pos == "SUPPORT"):
            pos = "UTILITY"
        if (pos == "MID"):
            pos = "MIDDLE"
        if (pos == "BOT"):
            pos = "BOTTOM"
        return player == pos
    
    @staticmethod            
    def getChampion(championId):
        def searchForChampionById(championList, championId):
            for key, value in championList.items():
                if value["key"] == str(championId):
                    return key
            return None
        
        if (not CHAMPION_DATA_FILE.is_file()):
            downloadChampionBasicData()
        
        with open(CHAMPION_DATA_FILE, "rb") as filehandle:
            import json
            data = json.load(filehandle)
            champion = searchForChampionById(data["data"], championId)
            if champion:
                print(f"Champion found: {champion}")
                print("="*10)
                print(data['data'][champion])
            else:
                print("No matching champion found")

    @staticmethod
    def downloadMatches():
        API.loadMatches()
    
    @staticmethod
    def printPlayerSummary(player, position, saveToFile=False, fileName = None):
        API.playerSummary(player, position, saveToFile, fileName)

    @staticmethod
    def main(args):
        if args[1] == "download":
            API.downloadMatches()
        elif args[1] == "summary":
            if args[4] == "-f":
                API.printPlayerSummary(args[2], args[3], saveToFile=True, fileName = args[5])
            else:
                API.printPlayerSummary(args[2])
            
        else:
            print("Invalid command")


if __name__ == "__main__":
    # import sys
    # args = sys.argv
    players = { "Sinrow": "Top",
                "Chaos42042": "Jungle", 
                "Lordfowl": "Middle",
                "electron700508": "Bottom",
                "ivorycharming": "Support",
                
                "YouMadBroskii18": "Top",
                "Azareal": "Jungle",
                "yeeshue1999": "Mid",
                "Irís": "Bottom",
                "Rudy310": "Support",}
    from datetime import date
    today = date.today()
    d1 = today.strftime("%d-%m-%Y")
    for player, position in players.items():
        args = ["API.py", "summary", player, position, "-f", f"PlayerSummaries/{player}({d1}).txt"]
        API.main(args)