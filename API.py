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
        if (len(list(CACHED_PLAYERS_DIR.iterdir())) > 0):
            players = API.loadPlayerQueueFromDisk()
        else:
            players = []
            # league = lol_watcher.league.challenger_by_queue(REGION, LEAGUE_QUEUE)
            # players.append(league["entries"])
            # print("Challenger league loaded.")
            # time.sleep(SLEEP_TIMER)
            # league = lol_watcher.league.grandmaster_by_queue(REGION, LEAGUE_QUEUE)
            # players.append(league["entries"])
            # print("Grandmaster league loaded.")
            # time.sleep(SLEEP_TIMER)
            league = lol_watcher.league.masters_by_queue(REGION, LEAGUE_QUEUE)
            players += league["entries"]
            print("Masters queue loaded")
            time.sleep(SLEEP_TIMER)
            for tier in LEAGUE_UPPER_TIERS:
                for division in LEAGUE_DIVISIONS:
                    # continue
                    for page in range(1,6):
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
    def main():
        API.loadMatches()
        

if __name__ == "__main__":
    API.main()