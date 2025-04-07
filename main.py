import discord
import asyncio
import os
import asyncpg
import ssl

TOKEN = os.environ.get("DISCORD_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
KARTOFFEL_EMOJI = '🥔'
TARGET_USERNAME = 'counting#5250'

# 👤 Bekannte Aliasnamen, die zählen sollen
SPECIAL_USERS = ['fwog#0001', 'sonicer', 'haiiiiix3']
TRIGGER_PHRASE = 'potato emoji'

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.members = True

client = discord.Client(intents=intents)

db_pool = None  # global DB pool


async def init_db():
    global db_pool

    # SSL fix for Railway
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


async def increment_potato_count(username):
    async with db_pool.acquire() as conn:
        await conn.execute("""
        INSERT INTO potato_counter (username, count)
        VALUES ($1, 1)
        ON CONFLICT (username)
        DO UPDATE SET count = potato_counter.count + 1
        """, username)


async def get_potato_count(username):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
        SELECT count FROM potato_counter WHERE username = $1
        """, username)
        return row['count'] if row else 0


async def get_top_potato_counts(limit=5):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
        SELECT username, count FROM potato_counter
        ORDER BY count DESC
        LIMIT $1
        """, limit)
        return rows


@client.event
async def on_ready():
    print(f'✅ Bot is running as {client.user}')
    await init_db()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 📘 Hilfe-Befehl
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

    # 📊 Count-Befehl
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

    # ✅ Neue Funktion: "potato emoji" im Text von einem SPECIAL_USER
    if TRIGGER_PHRASE in message.content.lower():
        author_full = str(message.author)  # z. B. fwog#0001
        author_name = message.author.name.lower()  # z. B. sonicer

        if author_full in SPECIAL_USERS or author_name in [name.lower() for name in SPECIAL_USERS]:
            try:
                await message.add_reaction(KARTOFFEL_EMOJI)
                print(f'✅ Reagiert mit 🥔 auf Nachricht von {message.author} (Trigger: potato emoji)')
                await increment_potato_count(author_full)
            except discord.HTTPException as e:
                print(f'⚠️ Fehler beim Reagieren auf SPECIAL_USER: {e}')
            return

    # 🍟 Standard: counting#5250 reagiert auf 🥔-Nachricht
    if KARTOFFEL_EMOJI in message.content:
        await asyncio.sleep(2)
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


# 🚀 Bot starten
client.run(TOKEN)
