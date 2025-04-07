import discord
import asyncio
import os
import asyncpg
import ssl

# ✅ Token & DB-Verbindung aus Railway-Umgebungsvariablen
TOKEN = os.environ.get("DISCORD_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
KARTOFFEL_EMOJI = '🥔'
TARGET_USERNAME = 'counting#5250'
SPECIAL_USER = 'fwog#0001'
TRIGGER_PHRASE = 'potato emoji'

# ✅ Discord Intents aktivieren
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.members = True

client = discord.Client(intents=intents)

# ✅ Globale Datenbankverbindung
db_pool = None


# 📦 Initialisiere Datenbank
async def init_db():
    global db_pool

    # 🔐 Railway erfordert modifiziertes SSL-Context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    db_pool = await asyncpg.create_pool(dsn=DATABASE_URL, ssl=ssl_context)

    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS potato_counter (
            username TEXT PRIMARY KEY,
            count INTEGER NOT NULL
        )
        """)


# ➕ Zähler erhöhen
async def increment_potato_count(username):
    async with db_pool.acquire() as conn:
        await conn.execute("""
        INSERT INTO potato_counter (username, count)
        VALUES ($1, 1)
        ON CONFLICT (username)
        DO UPDATE SET count = potato_counter.count + 1
        """, username)


# 🔍 Zähler abfragen
async def get_potato_count(username):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
        SELECT count FROM potato_counter WHERE username = $1
        """, username)
        return row['count'] if row else 0


# 🏆 Topliste abfragen
async def get_top_potato_counts(limit=5):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
        SELECT username, count FROM potato_counter
        ORDER BY count DESC
        LIMIT $1
        """, limit)
        return rows


# 🟢 Bot ist bereit
@client.event
async def on_ready():
    print(f'✅ Bot is running as {client.user}')
    await init_db()


# 💬 Nachrichten-Handler
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 📘 Hilfe anzeigen
    if message.content.startswith("!potatohelp"):
        help_text = (
            "🥔 **Potato Bot Commands** 🥔\n\n"
            "`!potatohelp` - Show this help message\n"
            "`!potatocount` - Show the top users with the most 🥔 reactions\n"
            "`!potatocount <username#1234>` - Show the number of 🥔 reactions for a specific user\n\n"
            "This bot reacts with a 🥔 emoji if a specific user (`counting#5250`) reacts to potato messages.\n"
            "It also keeps track of how many times each user was potato-reacted. 🧮"
        )
        await message.channel.send(help_text)
        return

    # 📊 Count abfragen
    if message.content.startswith("!potatocount"):
        parts = message.content.strip().split()
        if len(parts) == 2:
            username = parts[1]
            count = await get_potato_count(username)
            await message.channel.send(f'🥔 {username} has received {count} potato reaction(s).')
        else:
            top_users = await get_top_potato_counts()
            if not top_users:
                await message.channel.send("📉 No potato reactions recorded yet.")
                return
            top_msg = '\n'.join([f"{row['username']}: {row['count']}" for row in top_users])
            await message.channel.send(f'🥔 Top Potato Leaderboard:\n{top_msg}')
        return

    # 🆕 fwog#0001 schreibt irgendwas mit "potato emoji"
    if str(message.author) == SPECIAL_USER and TRIGGER_PHRASE in message.content.lower():
        try:
            await message.add_reaction(KARTOFFEL_EMOJI)
            print(f'✅ fwog#0001 hat eine Nachricht mit „potato emoji“ geschrieben – 🥔 Reaktion hinzugefügt')
            await increment_potato_count(str(message.author))
        except discord.HTTPException as e:
            print(f'⚠️ Fehler beim Reagieren auf fwog-Nachricht: {e}')
        return

    # 🧠 counting#5250 reagiert auf Nachricht mit 🥔
    if KARTOFFEL_EMOJI in message.content:
        await asyncio.sleep(2)  # kurze Pause, damit Reaktionen gesetzt werden können
        refreshed_message = await message.channel.fetch_message(message.id)

        for reaction in refreshed_message.reactions:
            async for user in reaction.users():
                if str(user) == TARGET_USERNAME:
                    try:
                        await refreshed_message.add_reaction(KARTOFFEL_EMOJI)
                        print(f'✅ Reacted with {KARTOFFEL_EMOJI} to a message from {message.author}')
                        await increment_potato_count(str(message.author))
                    except discord.HTTPException as e:
                        print(f'⚠️ Reaction error: {e}')
                    return


# 🚀 Starte den Bot (wird von Railway automatisch ausgeführt)
client.run(TOKEN)
