import os
import json
import aiohttp
import discord
from discord.ext import commands

# ============================================
# ENVIRONMENT (Railway)
# ============================================
DISCORD_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://join4join.xyz/api/v1"

if not DISCORD_TOKEN:
    raise RuntimeError("Missing TOKEN env var")
if not API_KEY:
    raise RuntimeError("Missing API_KEY env var")

# ============================================
# LOCAL DEV STATS (PURELY VISUAL)
# ============================================
STATS_FILE = "devstats.json"

if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w") as f:
        json.dump({"registered_users": 0, "farmed_users": []}, f)


def load_stats():
    with open(STATS_FILE, "r") as f:
        return json.load(f)


def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ============================================
# DISCORD BOT SETUP
# ============================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

COLOR = 0x6F2DBD  # dark neon purple


# ============================================
# EMBED HELPER
# ============================================
def cyber_embed(title: str, desc: str) -> discord.Embed:
    embed = discord.Embed(title=title, description=desc, color=COLOR)
    embed.set_footer(text="Join4Join Bot • Cyberpunk Edition")
    return embed


# ============================================
# JOIN4JOIN API WRAPPER
# ============================================
class Join4JoinAPI:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    async def _post(self, endpoint: str, body: dict):
        """POST JSON with Authorization header."""
        url = f"{BASE_URL}/{endpoint}"
        headers = {
            "Authorization": self.secret_key,
            "Content-Type": "application/json"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as resp:
                text = await resp.text()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    # Show the raw text so you can see what the API returned
                    return {"success": False, "message": f"Invalid JSON: {text}"}

    async def create_user(self, user_id: str):
        # API expects user_id in JSON body
        return await self._post("user/create", {"user_id": user_id})

    async def get_user(self, user_id: str):
        # Their server rejects GET; use POST with JSON body
        return await self._post("user/get", {"user_id": user_id})

    async def farm(self, user_id: str):
        return await self._post("join4join/farm", {"user_id": user_id})

    async def daily(self, user_id: str):
        return await self._post("join4join/daily", {"user_id": user_id})

    async def buy(self, user_id: str, coins: int, invite: str, language: str, alt: bool):
        return await self._post(
            "join4join/buy",
            {
                "user_id": user_id,
                "coins": coins,
                "invite": invite,
                "filter_language": language,
                "filter_account": alt,
            },
        )

    async def pay(self, receiver: str, donator: str, coins: int):
        return await self._post(
            "join4join/pay",
            {
                "user_receiver": receiver,
                "user_donator": donator,
                "coins": coins,
            },
        )

    async def info(self, guild_id: str):
        return await self._post("join4join/info", {"guild_id": guild_id})

    async def check(self, guild_id: str, user_id: str):
        return await self._post(
            "join4join/check", {"guild_id": guild_id, "user_id": user_id}
        )

    async def checkall(self, user_id: str):
        return await self._post("join4join/check/all", {"user_id": user_id})


api = Join4JoinAPI(API_KEY)


# ============================================
# SMALL HELPERS
# ============================================
def ms_to_hm(ms: int):
    """Convert milliseconds to (hours, minutes)."""
    total_seconds = ms // 1000
    total_minutes = total_seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return hours, minutes


# ============================================
# EVENTS
# ============================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        activity=discord.Game("Join4Join • !j4jhelp")
    )


# ============================================
# COMMANDS
# ============================================

# -------------------------------
# !register
# -------------------------------
@bot.command()
async def register(ctx):
    uid = str(ctx.author.id)
    res = await api.create_user(uid)

    title = "🪐 Account Registration"

    # If already registered, API usually sends message like this:
    if res.get("message") == "This user has already an account.":
        desc = "You already have a **Join4Join** account!\nYou can use all commands normally."
        return await ctx.send(embed=cyber_embed(title, desc))

    if not res.get("success"):
        desc = f"❌ Error: {res.get('message', 'Unknown error')}"
        return await ctx.send(embed=cyber_embed(title, desc))

    # Count locally for pretty dev stats (does NOT affect real rewards)
    stats = load_stats()
    stats["registered_users"] += 1
    save_stats(stats)

    coins = res["data"]["coins"]
    desc = (
        "✅ Your **Join4Join account** has been created!\n\n"
        f"💰 Starting Balance: **{coins} coins**"
    )
    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !coins
# -------------------------------
@bot.command()
async def coins(ctx):
    uid = str(ctx.author.id)
    res = await api.get_user(uid)

    title = "💰 Balance"

    if not res.get("success"):
        desc = "❌ You must register first with `!register`."
        return await ctx.send(embed=cyber_embed(title, desc))

    coins_value = res["data"]["coins"]
    desc = f"Your current balance is:\n\n💜 **{coins_value} coins**"
    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !daily
# -------------------------------
@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    res = await api.daily(uid)

    title = "🎁🌌💜 Daily Reward 💜🌌🎁"

    if not res.get("success"):
        desc = f"❌ {res.get('message', 'Unknown error')}"
        return await ctx.send(embed=cyber_embed(title, desc))

    data = res["data"]

    if not data["ready"]:
        hours, minutes = ms_to_hm(data["remaining_time"])
        desc = (
            "⏳ Not ready yet.\n"
            f"Try again in **{hours}h {minutes}m**."
        )
        return await ctx.send(embed=cyber_embed(title, desc))

    desc = f"🎉 You have claimed **{data['amount']} coins**!"
    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !farm
# -------------------------------
@bot.command()
async def farm(ctx):
    uid = str(ctx.author.id)
    res = await api.farm(uid)

    title = "🌱💜 Farming Activated 💜🌱"

    if not res.get("success"):
        desc = f"❌ Error: {res.get('message', 'Unknown error')}"
        return await ctx.send(embed=cyber_embed(title, desc))

    # Local tracking (visual only)
    stats = load_stats()
    if uid not in stats["farmed_users"]:
        stats["farmed_users"].append(uid)
        save_stats(stats)

    # Use your affiliate link here
    aff_link = "https://join4join.xyz/?aff=1317419437854560288"

    desc = (
        "🌱 Your farming session is now **active**!\n\n"
        f"🚀 Click **[HERE]({aff_link})** to start farming on the website.\n\n"
        "Make sure you are logged in on Join4Join so your rewards and dev rewards count."
    )
    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !buy  (JUST OPEN DASHBOARD LINK)
# -------------------------------
@bot.command()
async def buy(ctx):
    title = "🧪🚀💜 Ad Dashboard 💜🚀🧪"
    dashboard_link = "https://join4join.xyz/dashboard"

    desc = (
        "📢 Ad purchases are handled on the **Join4Join dashboard**.\n\n"
        f"Click **[HERE]({dashboard_link})** to create or manage your ads.\n\n"
        "Once your ad is live, users from the platform will start joining your server."
    )
    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !pay (no confirm link message)
# -------------------------------
@bot.command()
async def pay(ctx, receiver_id: str, coins: int):
    title = "💸 Coin Transfer"

    res = await api.pay(receiver_id, str(ctx.author.id), coins)

    if not res.get("success"):
        desc = f"❌ Error: {res.get('message', 'Unknown error')}"
        return await ctx.send(embed=cyber_embed(title, desc))

    # Even if API returns a link, we just tell "done" as requested
    desc = f"✅ Successfully sent **{coins} coins** to `{receiver_id}`."
    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !info
# -------------------------------
@bot.command()
async def info(ctx, guild_id: str = None):
    title = "📡 Server Information"

    gid = guild_id or str(ctx.guild.id)
    res = await api.info(gid)

    if not res.get("success"):
        desc = f"❌ Error: {res.get('message', 'Unknown error')}"
        return await ctx.send(embed=cyber_embed(title, desc))

    d = res["data"]

    desc = (
        f"**🪐 Name:** {d.get('name', 'Unknown')}\n"
        f"**🔗 Invite:** {d.get('invite', 'No invite')}\n"
        f"**📢 Ad Running:** {d.get('ad', 'no')}\n"
        f"**👥 Bought Members:** {d.get('invitation_request', 0)}\n"
        f"**🚀 Remaining Invites:** {d.get('invitation_update', 0)}"
    )
    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !check
# -------------------------------
@bot.command()
async def check(ctx, guild_id: str = None):
    title = "🧪 Leave Check"

    gid = guild_id or str(ctx.guild.id)
    res = await api.check(gid, str(ctx.author.id))

    if not res.get("success"):
        desc = f"❌ Error: {res.get('message', 'Unknown error')}"
        return await ctx.send(embed=cyber_embed(title, desc))

    if res["data"]["check"]:
        desc = "✅ You can leave this server **without losing coins**."
    else:
        desc = "❌ You **cannot** leave this server yet without losing coins."

    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !checkall
# -------------------------------
@bot.command()
async def checkall(ctx):
    title = "📜 Leaveable Servers"

    res = await api.checkall(str(ctx.author.id))

    if not res.get("success"):
        desc = f"❌ Error: {res.get('message', 'Unknown error')}"
        return await ctx.send(embed=cyber_embed(title, desc))

    ids = res["data"]["check"]

    if not ids:
        desc = "You currently have **no servers** you can leave safely."
        return await ctx.send(embed=cyber_embed(title, desc))

    lines = []
    for gid in ids:
        guild_obj = bot.get_guild(int(gid)) if gid.isdigit() else None
        name = guild_obj.name if guild_obj else "Unknown Server"
        lines.append(f"• **{name}** (`{gid}`)")

    desc = "\n".join(lines)
    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !devstats
# -------------------------------
@bot.command()
async def devstats(ctx):
    title = "📊 Developer Stats"

    stats = load_stats()
    reg = stats.get("registered_users", 0)
    farms = len(stats.get("farmed_users", []))

    # According to docs: 3 coins per user created (real system side).
    est_dev_coins = reg * 3

    desc = (
        f"🧍 Registered via `!register`: **{reg}**\n"
        f"🌱 Users who ran `!farm`: **{farms}**\n\n"
        f"💰 Estimated **developer coins** from registrations: **{est_dev_coins}**\n"
        "_(Real rewards are calculated on Join4Join itself.)_"
    )

    await ctx.send(embed=cyber_embed(title, desc))


# -------------------------------
# !j4jhelp
# -------------------------------
@bot.command()
async def j4jhelp(ctx):
    title = "📘 Join4Join Command Menu"

    desc = (
        "**👾 ACCOUNT**\n"
        "• `!register` – Create or link your Join4Join account\n"
        "• `!coins` – Check your current coin balance\n"
        "• `!daily` – Claim your daily reward\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**🌱 FARMING**\n"
        "• `!farm` – Activate farming & open your affiliate farming page\n"
        "  Example: `!farm`\n\n"
        "• `!check` – Check if you can leave the **current** server safely\n"
        "  Example: `!check`\n\n"
        "• `!check <server-id>` – Check another server by ID\n"
        "  Example: `!check 123456789012345678`\n\n"
        "• `!checkall` – List all servers you can leave safely\n"
        "  Example: `!checkall`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**📢 ADVERTISEMENT**\n"
        "• `!buy` – Open the Join4Join dashboard to create/manage ads\n"
        "  Example: `!buy`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**💸 COIN TRANSFER**\n"
        "• `!pay <user-id> <amount>` – Send coins to another user\n"
        "  Example: `!pay 123456789012345678 10`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**📡 SERVER INFO**\n"
        "• `!info` – Info about the current server\n"
        "• `!info <server-id>` – Info about another server\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**👑 DEV UTILITY**\n"
        "• `!devstats` – Show local dev stats (visual estimate of rewards)\n\n"
        "💜 All real coins & dev rewards are handled by **join4join.xyz**."
    )

    await ctx.send(embed=cyber_embed(title, desc))


# ============================================
# RUN BOT
# ============================================
bot.run(DISCORD_TOKEN)
