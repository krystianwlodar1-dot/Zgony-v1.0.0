import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import tasks, commands
import json
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
PVP_WEBHOOK = os.getenv("PVP_WEBHOOK")

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
    "Gohumag"
]

if os.path.exists("zgony1.json"):
    with open("zgony1.json", "r") as f:
        last_deaths = set(json.load(f))
else:
    last_deaths = set()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Zgony1 działa!")
    check_deaths.start()

@tasks.loop(minutes=1)
async def check_deaths():
    url = "https://cyleria.pl/index.php?subtopic=killstatistics"

    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text("\n")

        new_deaths = []

        for line in text.split("\n"):
            for name in characters:
                if name in line and "śmierć na poziomie" in line:
                    try:
                        part1, killers = line.split(" przez ", 1)
                        nick, level = part1.split(" śmierć na poziomie ")

                        death_id = f"{nick}-{level}-{killers}"

                        if death_id not in last_deaths:
                            last_deaths.add(death_id)
                            new_deaths.append((nick.strip(), level.strip(), killers.strip()))
                    except:
                        pass

        with open("zgony1.json", "w") as f:
            json.dump(list(last_deaths), f)

        channel = bot.get_channel(CHANNEL_ID)

        for nick, level, killers in new_deaths:
            is_pvp = "White Skull" in killers or "Black Skull" in killers or "Red Skull" in killers

            nick_colored = f"🟢 **{nick}**"

            killer_list = []
            for k in killers.replace(" oraz ", ", ").split(","):
                k = k.strip()
                if "White Skull" in k or "Black Skull" in k or "Red Skull" in k:
                    killer_list.append(f"🔴 **{k}**")
                else:
                    killer_list.append(k)

            killers_formatted = ", ".join(killer_list)

            embed = discord.Embed(
                title="💀 ZGON POSTACI",
                description=f"{nick_colored} poległ na poziomie **{level}**\n\n**Zabójcy:** {killers_formatted}",
                color=0x00FF00 if is_pvp else 0xFF0000
            )

            if is_pvp and PVP_WEBHOOK:
                try:
                    requests.post(PVP_WEBHOOK, json={"embeds": [embed.to_dict()]})
                except Exception as e:
                    print("Webhook error:", e)
            else:
                await channel.send(embed=embed)

    except Exception as e:
        print("Błąd:", e)

bot.run(TOKEN)
