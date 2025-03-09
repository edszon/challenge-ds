from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timezone, timedelta
import re
import json

# chrome driver settings
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--log-level=3')
options.add_argument('--disable-logging')

driver = webdriver.Chrome(options=options)

# dataclass to store game data, fields have default values so it won’t break if something’s missing
@dataclass
class Item:
    sport_league: str = ''
    event_date_utc: str = ''
    team1: str = ''
    team2: str = ''
    pitcher: str = ''
    period: str = 'FULL GAME' #default
    line_type: str = ''
    price: str = ''
    side: str = ''
    team: str = ''
    spread: float = 0.0

# empty list to collect all scraped data
items = []

# parses game time from scraped text, cleans it up and converts to ISO format with UTC timezone
def parse_game_time(game_time: str) -> str:
    cleaned_time = re.sub(r'\s+ML.*$', '', game_time)
    time_part, date_part = cleaned_time.split(' (')
    date_part = date_part.rstrip(')')
    dt = datetime.strptime(f"{date_part} {time_part}", "%m/%d/%Y %I:%M %p")
    dt_utc = dt - timedelta(hours=5)
    return dt_utc.replace(tzinfo=timezone.utc).isoformat()

# main scraper function for extracting game data from a given sport page
def scrape_cards(sport: str):
    url = f'https://sportsbetting.dog/picks/{sport}'
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    try:
        # waits for the main game cards to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'card')))
        time.sleep(2)  # extra buffer

        # grabs all game cards
        cards = driver.find_elements(By.CLASS_NAME, 'card')
        
        for card in cards:
            try:
                card_header = card.find_element(By.CLASS_NAME, 'card-header')
                games = card.find_elements('xpath', ".//div[contains(@class, 'card-body')]/div[1]/div[1]/div")
                for game in games:
                    gamedata = game.text.splitlines()  # converts game text to array
                    # creates items for moneyline bets
                    ml1 = Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='FULL GAME',
                        line_type='moneyline',
                        price=gamedata[2],
                        side=gamedata[1],
                        team=gamedata[1],
                        spread=0
                    )
                    ml2 = Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='',
                        line_type='moneyline',
                        price=gamedata[8],
                        side=gamedata[7],
                        team=gamedata[7],
                        spread=0
                    )
                    # creates items for spreads and over/unders
                    s1 = Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='',
                        line_type='spread',
                        price=re.sub(r'[()]', '', gamedata[4]),
                        side=gamedata[1],
                        team=gamedata[1],
                        spread=float(gamedata[3])
                    )
                    s2 = Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='',
                        line_type='spread',
                        price=re.sub(r'[()]', '', gamedata[10]),
                        side=gamedata[7],
                        team=gamedata[7],
                        spread=float(gamedata[9])
                    )
                    over = Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='',
                        line_type='over/under',
                        price=re.sub(r'[()]', '', gamedata[6]),
                        side='over',
                        team='total',
                        spread=float(re.sub(r'^[OU]\s+', '', gamedata[5]).strip())
                    )
                    under = Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='',
                        line_type='over/under',
                        price=re.sub(r'[()]', '', gamedata[12]),
                        side='under',
                        team='total',
                        spread=float(re.sub(r'^[OU]\s+', '', gamedata[11]).strip())
                    )
                    # adds all items to the list
                    items.extend([s1, s2, over, under])

            except:
                continue  # skips broken cards
    except Exception as e:
        print("error while scraping:", e)

# runs the scraper for basketball games
scrape_cards('basketball')

# converts all items to JSON and prints them out
items_json = json.dumps([item.__dict__ for item in items], indent=2)
print(items_json)
