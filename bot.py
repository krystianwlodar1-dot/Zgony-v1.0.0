import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import tasks, commands
import asyncio
import json
import os

TOKEN = os.getenv("DISCORD_TOKEN")  # Discord token z Railway secrets
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))  # ID kanału Discord

characters = {
    "Agnieszka": "https://cyleria.pl/index.php?subtopic=characters&name=Agnieszka",
    "Miekka Parowka": "https://cyleria.pl/index.php?subtopic=characters&name=Miekka+Parowka",
    "Gazowany Kompot": "https://cyleria.pl/index.php?subtopic=characters&name=Gazowany+Kompot",
    "Negocjator": "https://cyleria.pl/index.php?subtopic=characters&name=Negocjator",
    "Negocjatorka": "https://cyleria.pl/index.php?subtopic=characters&name=Negocjatorka",
    "Astma": "https://cyleria.pl/index.php?subtopic=characters&name=Astma",
    "Jestem Karma": "https://cyleria.pl/index.php?subtopic=characters&name=Jestem Karma",
    "Pan Trezer": "https://cyleria.pl/index.php?subtopic=characters&name=Pan Trezer",
    "Mistrz Negocjacji": "https://cyleria.pl/index.php?subtopic=characters&name=Mistrz+Negocjacji"
}

# Wczytanie poprzednich zgonów z pliku
if os.path.exists("deaths.json"):
    with open("deaths.json", "r") as f:
        last_deaths = set(tuple(d) for d in json.load(f))
else:
    last_deaths = set()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user}')
    check_deaths.start()

@tasks.loop(minutes=1)
async def check_deaths():
    url = "https://cyleria.pl/index.php?subtopic=killstatistics"
    try:
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        # Wyszukujemy wszystkie wiersze tabeli zgonów
        death_rows = soup.select("table.TableContent tr")[1:]  # pomijamy nagłówek
        new_deaths = []

        for row in death_rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            char_name = cols[0].text.strip()
            killer_info = cols[1].text.strip()
            level_info = cols[2].text.strip()

            if char_name in characters and (char_name, killer_info, level_info) not in last_deaths:
                last_deaths.add((char_name, killer_info, level_info))
                new_deaths.append((char_name, killer_info, level_info))

        # Zapisujemy zgony do pliku
        with open("deaths.json", "w") as f:
            json.dump([list(d) for d in last_deaths], f)

        # Wysyłamy embed na Discord
        if new_deaths:
            channel = bot.get_channel(CHANNEL_ID)
            for char_name, killer_info, level_info in new_deaths:
                embed = discord.Embed(
                    title="💀 Postać pokonana!",
                    description=f'**{char_name}** pokonany(a) na poziomie **{level_info}** przez **{killer_info}**',
                    color=0xff0000
                )
                await channel.send(embed=embed)

    except Exception as e:
        print("Błąd podczas sprawdzania zgonów:", e)

bot.run(TOKEN)
