import requests
import discord
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
import json
import os
import re

# ================================
# ENV
# ================================
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
PVP_WEBHOOK = os.getenv("PVP_WEBHOOK")

URL = "https://cyleria.pl/index.php?subtopic=killstatistics"

# ================================
# TWOJE POSTACIE
# ================================
characters = [
    "Agnieszka",
    "Miekka Parowka",
    "Gazowany Kompot",
    "Negocjator",
    "Negocjatorka",
    "Astma",
    "Jestem Karma",
    "Pan Trezer",
    "Mistrz Negocjacji",
    "Gohumag",
    "Corcia Tatulcia"
]

# ================================
# HISTORIA
# ================================
if os.path.exists("zgony1.json"):
    with open("zgony1.json", "r") as f:
        last_deaths = set(json.load(f))
else:
    last_deaths = set()

# ================================
# DISCORD
# ================================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("ZGONY1 ONLINE")

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🟢 ZGONY1 wystartował",
            description="Bot monitoruje zgony Twoich postaci na Cylerii.",
            color=0x00FF00
        )
        await channel.send(embed=embed)

    check_deaths.start()

# ================================
# PARSER
# ================================
def parse_row(text):
    # Przykład:
    # Kasai śmierć na poziomie 1027 przez a burning hunter, an ancient dragon, Veduque
    m = re.search(r"(.+?) śmierć na poziomie (\d+) przez (.+)", text)
    if not m:
        return None

    return {
        "nick": m.group(1).strip(),
        "level": m.group(2),
        "killers": m.group(3).strip()
    }

# ================================
# LOOP
# ================================
@tasks.loop(minutes=1)
async def check_deaths():
    try:
        html = requests.get(URL, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        table = soup.find("table")
        if not table:
            print("Nie znaleziono tabeli zgonów")
            return

        rows = table.find_all("tr")[1:]  # pomijamy nagłówek
        channel = bot.get_channel(CHANNEL_ID)

        for row in rows:
            text = row.get_text(" ", strip=True)
            data = parse_row(text)

            if not data:
                continue

            nick = data["nick"]
            level = data["level"]
            killers = data["killers"]

            if nick not in characters:
                continue

            death_id = f"{nick}-{level}-{killers}"
            if death_id in last_deaths:
                continue

            last_deaths.add(death_id)

            is_pvp = any(x in killers for x in ["White Skull", "Black Skull", "Red Skull"])

            nick_display = f"🟢 **{nick}**"

            killer_parts = killers.replace(" oraz ", ", ").split(",")
            formatted_killers = []

            for k in killer_parts:
                k = k.strip()
                if any(x in k for x in ["White Skull", "Black Skull", "Red Skull"]):
                    formatted_killers.append(f"🔴 **{k}**")
                else:
                    formatted_killers.append(k)

            killers_display = ", ".join(formatted_killers)

            embed = discord.Embed(
                title="💀 ZGON",
                description=f"{nick_display} poległ na poziomie **{level}**\n\n**Zabójcy:** {killers_display}",
                color=0x00FF00 if is_pvp else 0xFF0000
            )

            if is_pvp and PVP_WEBHOOK:
                requests.post(PVP_WEBHOOK, json={"embeds": [embed.to_dict()]})
            else:
                await channel.send(embed=embed)

        with open("zgony1.json", "w") as f:
            json.dump(list(last_deaths), f)

    except Exception as e:
        print("Błąd:", e)

# ================================
bot.run(TOKEN)
