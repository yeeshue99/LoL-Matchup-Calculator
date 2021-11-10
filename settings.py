from pathlib import Path

API_KEY = ""
BASE_DIR = Path(__file__).resolve().parent
DATA_DRAGON_DIR = BASE_DIR / "data_dragon"
CACHED_PLAYER_FORMAT = "cachedPlayers{}.data"
CACHED_PLAYERS_DIR = BASE_DIR / "cachedPlayers"
CHAMPION_DATA_FILE = DATA_DRAGON_DIR / "champions.json"
CHAMPION_DATA_URL = "http://ddragon.leagueoflegends.com/cdn/11.21.1/data/en_US/champion.json"
CHAMPION_IMAGE_DIR = DATA_DRAGON_DIR / "champion"
CREATE_NEW_MODEL = True
DATABASE_NAME = "database.sqlite"
MATCH_REGION = "AMERICAS"
MODEL_DIR = BASE_DIR / "model"
PATCHES_JSON_URL = "http://cdn.merakianalytics.com/riot/lol/resources/patches.json"
REGION = "NA1"
SLEEP_TIMER = 1
TRAINING_SPLIT = .8
LEAGUE_TIERS = ["DIAMOND", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"]
LEAGUE_UPPER_TIERS = LEAGUE_TIERS[:3]
LEAGUE_DIVISIONS = ["I", "II", "III", "IV"]
LEAGUE_QUEUE = "RANKED_SOLO_5x5"
DATABASE_LOGGING_FILE = BASE_DIR / "database.log"
LOGGING_TIMEOUT = 60*30