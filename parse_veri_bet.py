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

# chrome options for headless scraping
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--log-level=3')
options.add_argument('--disable-logging')

driver = webdriver.Chrome(options=options)
url = f'https://sportsbetting.dog/picks/basketball'
driver.get(url)

@dataclass
class Item:
    sport_league: str = ''     # sport, e.g., basketball, baseball
    event_date_utc: str = ''   # ISO format datetime in UTC
    team1: str = ''            # home team or team 1
    team2: str = ''            # away team or team 2
    pitcher: str = ''          # only used for baseball (optional)
    period: str = ''           # e.g., full game, 1st half, etc.
    line_type: str = ''        # moneyline, spread, etc.
    price: str = ''            # betting odds, like -133 or +110
    side: str = ''             # which side the bet is on (team1 or team2)
    team: str = ''             # team associated with the bet
    spread: float = 0.0        # point spread, e.g., -1.5

# function to clean up and parse game times into UTC
def parse_game_time(game_time: str) -> str:
    # look for time and date pattern
    cleaned_time = re.search(r'(\d{1,2}:\d{2} [APM]+) \((\d{1,2}/\d{1,2}/\d{4})', game_time)
    
    if not cleaned_time:
        raise ValueError(f"unexpected time format: {game_time}")

    time_part = cleaned_time.group(1)
    date_part = cleaned_time.group(2)

    # convert date and time string to datetime object
    dt = datetime.strptime(f"{date_part} {time_part}", "%m/%d/%Y %I:%M %p")

    # adjust time to UTC
    dt_utc = dt - timedelta(hours=5)

    # return ISO format datetime
    return dt_utc.replace(tzinfo=timezone.utc).isoformat()

# main scraper function
def scrape_cards():
    wait = WebDriverWait(driver, 20)  # waits for elements to load, max 20 seconds
    items = []  # store all scraped items
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'card')))  # wait for game cards
        time.sleep(2)  # extra buffer, just in case (could be more elegant with better waits)

        cards = driver.find_elements(By.CLASS_NAME, 'card')  # grab all game cards

        for card in cards:
            try:
                card_header = card.find_element(By.CLASS_NAME, 'card-header')  # sport/league name

                # most of the divs on the website dont have proper identification, so im using a template approach
                games = card.find_elements(By.XPATH, ".//div[contains(@class, 'card-body')]/div[1]/div[1]/div")

                for game in games:
                    # print(game.text) (disabled) for debugging
                    gamedata = game.text.splitlines()  # split into string array for better parsing

                    if len(gamedata) < 13:  # skip anything that doesn't have the expected data
                        continue

                    # add all team bets to items list
                    items.append(Item(
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
                    ))

                    items.append(Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='FULL GAME',
                        line_type='moneyline',
                        price=gamedata[8],
                        side=gamedata[7],
                        team=gamedata[7],
                        spread=0
                    ))

                    items.append(Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='FULL GAME',
                        line_type='spread',
                        price=re.sub(r'[()]', '', gamedata[4]),
                        side=gamedata[1],
                        team=gamedata[1],
                        spread=gamedata[3]
                    ))

                    items.append(Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='FULL GAME',
                        line_type='spread',
                        price=re.sub(r'[()]', '', gamedata[10]),
                        side=gamedata[7],
                        team=gamedata[7],
                        spread=gamedata[9]
                    ))

                    items.append(Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='FULL GAME',
                        line_type='over',
                        price= re.search(r'[-+]?\d*\.?\d+', gamedata[6]).group(),
                        side='over',
                        team='total',
                        spread=re.sub(r'[()]', '', gamedata[5])
                    ))

                    items.append(Item(
                        sport_league=card_header.text,
                        event_date_utc=parse_game_time(gamedata[0]),
                        team1=gamedata[1],
                        team2=gamedata[7],
                        pitcher='',
                        period='FULL GAME',
                        line_type='over',
                        price= re.search(r'[-+]?\d*\.?\d+', gamedata[11]).group(),
                        side='over',
                        team='total',
                        spread=re.sub(r'[()]', '', gamedata[10])
                    ))

            except Exception as e:
                continue  # ignore errors in individual cards, move to next one
    except Exception as e:
        print("Error while scraping:", e)

    # convert items list to JSON format and print
    json_output = json.dumps([item.__dict__ for item in items], indent=2)
    print(json_output)

scrape_cards()
