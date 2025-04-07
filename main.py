import discord
import asyncio
import os
import asyncpg
import ssl

# 🔐 Umgebungsvariablen von Railway
TOKEN = os.environ.get("DISCORD_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

# 🥔 Einstellungen
KARTOFFEL_EMOJI = '🥔'
TARGET_USERNAME = 'counting#5250'
TRIGGER_PHRASE = 'potato emoji'
SPECIAL_USERS = ['fwog#0001', 'haiiiiix3', 'sonicer']  # Unterstützte Nutzernamen

# 🎛️ Intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.members = True

client = discord.Client(intents=intents)
db_pool = None  # globale Datenbankverbindung


# 📦 Initialisiere Datenbank
async def init_db():
    global db_pool
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


# 🔍 Einzelnen Count abrufen
async def get_potato_count(username):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
        SELECT count FROM potato_counter WHERE username = $1
        """, username)
        return row['count'] if row else 0


# 🏆 Topliste abrufen
async def get_top_potato_counts(limit=5):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
        SELECT username, count FROM potato_counter
        ORDER BY count DESC
        LIMIT $1
        """, limit)
        return rows


# ✅ Bot gestartet
@client.event
async def on_ready():
    print(f'✅ Bot is running as {client.user}')
    await init_db()


# 💬 Nachrichtenbehandlung
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # ℹ️ Hilfe-Befehl
    if message.content.startswith("!potatohelp"):
        help_text = (
            "🥔 **Potato Bot Commands** 🥔\n\n"
            "`!potatohelp` - Zeigt diese Hilfe an\n"
            "`!potatocount` - Zeigt die Top-User mit den meisten 🥔-Reaktionen\n"
            "`!potatocount <username#1234>` - Zeigt die 🥔-Anzahl für einen bestimmten User\n\n"
            "Dieser Bot reagiert mit 🥔, wenn `counting#5250` auf Nachrichten mit 🥔 reagiert\n"
            "und auch, wenn bestimmte Nutzer etwas mit 'potato emoji' schreiben."
        )
        await message.channel.send(help_text)
        return

    # 📊 Statistiken anzeigen
    if message.content.startswith("!potatocount"):
        parts = message.content.strip().split()
        if len(parts) == 2:
            username = parts[1]
            count = await get_potato_count(username)
            await message.channel.send(f'🥔 {username} hat {count} potato reaction(s) erhalten.')
        else:
            top_users = await get_top_potato_counts()
            if not top_users:
                await message.channel.send("📉 Es wurden noch keine 🥔-Reaktionen gezählt.")
                return
            top_msg = '\n'.join([f"{row['username']}: {row['count']}" for row in top_users])
            await message.channel.send(f'🥔 **Top Potato Leaderboard**:\n{top_msg}')
        return

    # 🆕 Nachricht enthält "potato emoji" von erlaubtem Nutzer
    if (
        TRIGGER_PHRASE in message.content.lower()
        and (
            str(message.author) in SPECIAL_USERS
            or message.author.name.lower() in [name.lower() for name in SPECIAL_USERS]
        )
    ):
        try:
            await message.add_reaction(KARTOFFEL_EMOJI)
            print(f'✅ "{TRIGGER_PHRASE}" erkannt von {message.author} – 🥔 hinzugefügt')
            await increment_potato_count(str(message.author))
        except discord.HTTPException as e:
            print(f'⚠️ Fehler beim Reagieren: {e}')
        return

    # 🤖 counting#5250 reagiert auf 🥔-Nachricht
    if KARTOFFEL_EMOJI in message.content:
        await asyncio.sleep(2)
        refreshed_message = await message.channel.fetch_message(message.id)

        for reaction in refreshed_message.reactions:
            async for user in reaction.users():
                if str(user) == TARGET_USERNAME:
                    try:
                        await refreshed_message.add_reaction(KARTOFFEL_EMOJI)
                        print(f'✅ {TARGET_USERNAME} reagierte – 🥔 ebenfalls hinzugefügt')
                        await increment_potato_count(str(message.author))
                    except discord.HTTPException as e:
                        print(f'⚠️ Fehler bei Auto-Reaction: {e}')
                    return


# 🚀 Bot starten
client.run(TOKEN)
