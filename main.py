import discord
import asyncio
import os
import asyncpg
import ssl

TOKEN = os.environ.get("DISCORD_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
KARTOFFEL_EMOJI = '🥔'
TARGET_USERNAME = 'counting#5250'

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.members = True

client = discord.Client(intents=intents)

db_pool = None  # globale DB-Verbindung


async def init_db():
    global db_pool

    # SSL-Fix für Railway
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    db_pool = await asyncpg.create_pool(dsn=DATABASE_URL, ssl=ssl_context)

    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS kartoffel_counter (
            username TEXT PRIMARY KEY,
            count INTEGER NOT NULL
        )
        """)


async def increment_kartoffel_count(username):
    async with db_pool.acquire() as conn:
        await conn.execute("""
        INSERT INTO kartoffel_counter (username, count)
        VALUES ($1, 1)
        ON CONFLICT (username)
        DO UPDATE SET count = kartoffel_counter.count + 1
        """, username)


async def get_kartoffel_count(username):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
        SELECT count FROM kartoffel_counter WHERE username = $1
        """, username)
        return row['count'] if row else 0


async def get_top_kartoffel_counts(limit=5):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
        SELECT username, count FROM kartoffel_counter
        ORDER BY count DESC
        LIMIT $1
        """, limit)
        return rows


@client.event
async def on_ready():
    print(f'✅ Bot gestartet als {client.user}')
    await init_db()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!kartoffelcount"):
        parts = message.content.strip().split()
        if len(parts) == 2:
            username = parts[1]
            count = await get_kartoffel_count(username)
            await message.channel.send(f'🥔 {username} hat {count} Kartoffel-Reaktionen erhalten.')
        else:
            top_users = await get_top_kartoffel_counts()
            if not top_users:
                await message.channel.send("📉 Noch keine Kartoffeln verteilt.")
                return
            top_msg = '\n'.join([f"{row['username']}: {row['count']}" for row in top_users])
            await message.channel.send(f'🥔 Kartoffel-Topliste:\n{top_msg}')
        return

    if KARTOFFEL_EMOJI in message.content:
        await asyncio.sleep(2)
        refreshed_message = await message.channel.fetch_message(message.id)

        for reaction in refreshed_message.reactions:
            async for user in reaction.users():
                if str(user) == TARGET_USERNAME:
                    try:
                        await refreshed_message.add_reaction(KARTOFFEL_EMOJI)
                        print(f'✅ Reagiere mit {KARTOFFEL_EMOJI} auf Nachricht von {message.author}')
                        await increment_kartoffel_count(str(message.author))
                    except discord.HTTPException as e:
                        print(f'⚠️ Fehler beim Reagieren: {e}')
                    return


# 🚀 Starte den Bot
client.run(TOKEN)
