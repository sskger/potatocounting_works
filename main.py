import discord
import asyncio
import os

# 🔐 Ersetze diesen Token durch deinen eigenen Bot-Token
from dotenv import load_dotenv
load_dotenv("DISCORD_TOKEN")
KARTOFFEL_EMOJI = '🥔'
TARGET_USERNAME = 'counting#5250'  # Name und Discriminator (z. B. counting#5250)

# ➕ Notwendige Intents aktivieren
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Bot gestartet als {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Prüfe, ob 🥔 im Nachrichtentext vorkommt
    if KARTOFFEL_EMOJI in message.content:
        await asyncio.sleep(2)  # Warte 5 Sekunden, damit der Zielnutzer reagieren kann

        # Lade die Nachricht neu, um aktuelle Reaktionen zu prüfen
        refreshed_message = await message.channel.fetch_message(message.id)

        # Durchlaufe alle Reaktionen
        for reaction in refreshed_message.reactions:
            async for user in reaction.users():
                # Prüfe, ob der gewünschte Nutzer reagiert hat
                if str(user) == TARGET_USERNAME:
                    try:
                        await refreshed_message.add_reaction(KARTOFFEL_EMOJI)
                        print(f'✅ Reagiere mit {KARTOFFEL_EMOJI} auf Nachricht von {message.author}')
                    except discord.HTTPException as e:
                        print(f'⚠️ Fehler beim Reagieren: {e}')
                    return  # Nur einmal reagieren

# 🚀 Starte den Bot
client.run(TOKEN)

------------------------
