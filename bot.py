import requests
import discord
from discord.ext import tasks, commands
import json
import os

# -------------------------
# ENV
# -------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
PVP_WEBHOOK = os.getenv("PVP_WEBHOOK")

# -------------------------
# Twoje postacie
# -------------------------
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

# -------------------------
# Historia zgonów
# -------------------------
if os.path.exists("zgony1.json"):
    with open("zgony1.json", "r") as f:
        last_deaths = set(json.load(f))
else:
    last_deaths = set()

# -------------------------
# Discord
# -------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Zgony1 online")

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🤖 Zgony1 uruchomiony",
            description="Bot monitoruje zgony Twoich postaci na Cylerii.",
            color=0x00FF00
        )
        await channel.send(embed=embed)

    check_deaths.start()

# -------------------------
# Main loop
# -------------------------
@tasks.loop(minutes=1)
async def check_deaths():
    url = "https://cyleria.pl/ajax/killstatistics.php"

    try:
        data = requests.get(url, timeout=10).json()
        channel = bot.get_channel(CHANNEL_ID)

        for entry in data:
            try:
                nick = entry["player"]
                level = str(entry["level"])
                killers = entry["killed_by"]

                if nick not in characters:
                    continue

                death_id = f"{nick}-{level}-{killers}"
                if death_id in last_deaths:
                    continue

                last_deaths.add(death_id)

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
                    requests.post(PVP_WEBHOOK, json={"embeds":[embed.to_dict()]})
                else:
                    await channel.send(embed=embed)

            except:
                pass

        with open("zgony1.json","w") as f:
            json.dump(list(last_deaths), f)

    except Exception as e:
        print("API error:", e)

# -------------------------
bot.run(TOKEN)
