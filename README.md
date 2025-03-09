# challenge-ds
Web Scraping Test

# Sports Betting Scraper 🏀

A Python scraper using Selenium to extract sports betting data.

## Features
- Scrapes game data (moneylines, spreads, over/unders)
- Parses event times to UTC ISO format
- Outputs results as JSON

## Usage
```bash
# Install dependencies
pip install requirements.txt

# Run scraper (example for basketball)
python parse_veri_bet.py
```

## Output
Generates JSON with fields like `sport_league`, `event_date_utc`, `team1`, `team2`, `line_type`, and `price`.

---

Built with 🐍 by Edson.
