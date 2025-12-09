import discord
from discord.ext import commands
import aiohttp
import os
import json
import math

# ========================================================
# ENVIRONMENT
# ========================================================
DISCORD_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://join4join.xyz/api/v1"

# ========================================================
# DEVSTATS LOCAL TRACKING (DOES NOT AFFECT REAL REWARDS)
# ========================================================
if not os.path.exists("devstats.json"):
    with open("devstats.json", "w") as f:
        json.dump({"registered_users": 0, "farmed_users": []}, f)

def load_stats():
    with open("devstats.json", "r") as f:
        return json.load(f)

def save_stats(data):
    with open("devstats.json", "w") as f:
        json.dump(data, f, indent=4)

# ========================================================
# DISCORD BOT
# ========================================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

PURPLE = 0x8A2BE2  # neon purple cyberpunk


# ========================================================
# CYBERPUNK EMBED MAKER
# ========================================================
def cyber(title, desc):
    embed = discord.Embed(title=title, description=desc, color=PURPLE)
    embed.set_footer(text="Join4Join Bot • Cyberpunk Edition")
    return embed


# ========================================================
# J4J API CLIENT — NOW 100% CORRECT
# ========================================================
class J4J:
    def __init__(self):
        self.key = API_KEY
        self.headers = {
            "Authorization": self.key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

    async def _post(self, endpoint, data):
        url = f"{BASE_URL}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps(data), headers=self.headers) as res:
                try:
                    return await res.json()
                except:
                    return {"success": False, "message": "Invalid JSON"}

    async def _get(self, endpoint, params):
        url = f"{BASE_URL}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers) as res:
                try:
                    return await res.json()
                except:
                    return {"success": False, "message": "Invalid JSON"}

    # Correct method (from repo)
    async def create_user(self, user_id):
        return await self._post("user/create", {"user_id": user_id})

    async def get_user(self, user_id):
        return await self._get("user/get", {"user_id": user_id})

    async def farm(self, user_id):
        return await self._post("join4join/farm", {"user_id": user_id})

    async def daily(self, user_id):
        return await self._post("join4join/daily", {"user_id": user_id})

    async def buy(self):
        # You want !buy to ONLY open dashboard link
        return {"success": True}

    async def pay(self, receiver, donator, coins):
        return await self._post("join4join/pay", {
            "user_receiver": receiver,
            "user_donator": donator,
            "coins": coins
        })

    async def info(self, guild_id):
        return await self._post("join4join/info", {"guild_id": guild_id})

    async def check(self, guild_id, user_id):
        return await self._post("join4join/check", {"guild_id": guild_id, "user_id": user_id})

    async def checkall(self, user_id):
        return await self._post("join4join/check/all", {"user_id": user_id})

api = J4J()


# ========================================================
# COMMANDS
# ========================================================

# ------------------------ REGISTER ------------------------
@bot.command()
async def register(ctx):
    uid = str(ctx.author.id)
    res = await api.create_user(uid)

    if res.get("message") == "This user has already an account.":
        return await ctx.send(embed=cyber("🛸 Account Registration",
                                          "You already have an account!"))

    if not res.get("success"):
        return await ctx.send(embed=cyber("🛸 Account Registration",
                                          f"❌ Error: {res.get('message')}"))

    stats = load_stats()
    stats["registered_users"] += 1
    save_stats(stats)

    coins = res["data"]["coins"]

    await ctx.send(embed=cyber("🛸 Account Created",
                               f"✅ Your account is ready!\n💰 Starting coins: **{coins}**"))


# ------------------------ COINS ------------------------
@bot.command()
async def coins(ctx):
    uid = str(ctx.author.id)
    res = await api.get_user(uid)

    if not res.get("success"):
        return await ctx.send(embed=cyber("💰 Balance", "❌ You must register first."))

    balance = res["data"]["coins"]

    await ctx.send(embed=cyber("💰 Balance",
                               f"Your coins: **{balance}**"))


# ------------------------ DAILY ------------------------
@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    res = await api.daily(uid)

    if not res.get("success"):
        return await ctx.send(embed=cyber("🎁 Daily", f"❌ {res}"))

    data = res["data"]

    if not data["ready"]:
        seconds = data["remaining_time"] / 1000
        minutes = math.floor(seconds / 60)
        hours = math.floor(minutes / 60)

        return await ctx.send(embed=cyber(
            "🎁 Daily Reward",
            f"⏳ Not ready.\nCome back in **{hours}h {minutes % 60}m**"
        ))

    await ctx.send(embed=cyber("🎁 Daily Reward",
                               f"🎉 You claimed **{data['amount']} coins!**"))


# ------------------------ FARM ------------------------
@bot.command()
async def farm(ctx):
    uid = str(ctx.author.id)
    res = await api.farm(uid)

    if not res.get("success"):
        return await ctx.send(embed=cyber("🌱 Farming", f"❌ {res.get('message')}"))

    stats = load_stats()
    if uid not in stats["farmed_users"]:
        stats["farmed_users"].append(uid)
        save_stats(stats)

    # ONLY link to farming page
    return await ctx.send(embed=cyber(
        "🌱 Farming Activated",
        "Your farming is activated!\n\n"
        "**[CLICK HERE TO START FARMING](https://join4join.xyz/?aff=1317419437854560288)**"
    ))


# ------------------------ BUY ------------------------
@bot.command()
async def buy(ctx):
    # You want NO parameters → only dashboard link
    return await ctx.send(embed=cyber(
        "📢 Create Advertisement",
        "**[OPEN DASHBOARD](https://join4join.xyz/dashboard)**"
    ))


# ------------------------ PAY ------------------------
@bot.command()
async def pay(ctx, receiver: str, coins: int):
    uid = str(ctx.author.id)
    res = await api.pay(receiver, uid, coins)

    if not res.get("success"):
        return await ctx.send(embed=cyber("💸 Pay", f"❌ {res}"))

    return await ctx.send(embed=cyber("💸 Transfer Complete",
                                     f"Sent **{coins} coins** to `{receiver}`."))


# ------------------------ INFO ------------------------
@bot.command()
async def info(ctx, guild_id: str = None):
    gid = guild_id or str(ctx.guild.id)
    res = await api.info(gid)

    if not res.get("success"):
        return await ctx.send(embed=cyber("📡 Info", "❌ Error fetching server info."))

    d = res["data"]

    await ctx.send(embed=cyber("📡 Server Info",
                               f"**Name:** {d['name']}\n"
                               f"**Invite:** {d['invite']}\n"
                               f"**Ad running:** {d['ad']}\n"
                               f"**Bought:** {d['invitation_request']}\n"
                               f"**Remaining:** {d['invitation_update']}"))


# ------------------------ CHECK ------------------------
@bot.command()
async def check(ctx, guild_id: str = None):
    gid = guild_id or str(ctx.guild.id)
    res = await api.check(gid, str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=cyber("🧪 Leave Check", "❌ Error."))

    can = res["data"]["check"]

    msg = "✅ You may leave this server." if can else "❌ You cannot leave yet."

    await ctx.send(embed=cyber("🧪 Leave Check", msg))


# ------------------------ CHECKALL ------------------------
@bot.command()
async def checkall(ctx):
    uid = str(ctx.author.id)
    res = await api.checkall(uid)

    if not res.get("success"):
        return await ctx.send(embed=cyber("📜 Leaveable Servers", "❌ Error."))

    ids = res["data"]["check"]

    if not ids:
        return await ctx.send(embed=cyber("📜 Leaveable Servers", "No servers available."))

    lines = "\n".join(f"• `{g}`" for g in ids)

    await ctx.send(embed=cyber("📜 Leaveable Servers", lines))


# ------------------------ DEVSTATS ------------------------
@bot.command()
async def devstats(ctx):
    stats = load_stats()
    est = stats["registered_users"] * 3

    farms = len(stats["farmed_users"])

    await ctx.send(embed=cyber(
        "👾 Developer Stats",
        f"👥 Registered: **{stats['registered_users']}**\n"
        f"🌱 Farmers: **{farms}**\n"
        f"💰 Estimated coins: **{est}**"
    ))


# ------------------------ HELP ------------------------
@bot.command()
async def j4jhelp(ctx):
    await ctx.send(embed=cyber(
        "📘 Command Menu",
        "**ACCOUNT**\n"
        "`!register`\n"
        "`!coins`\n"
        "`!daily`\n\n"
        "**FARMING**\n"
        "`!farm`\n"
        "`!check <server-id>`\n"
        "`!checkall`\n\n"
        "**ADS**\n"
        "`!buy` → Opens dashboard\n\n"
        "**COINS**\n"
        "`!pay <user_id> <amount>`\n\n"
        "**SERVER**\n"
        "`!info`\n\n"
        "**DEV**\n"
        "`!devstats`"
    ))





@bot.command()
async def testraw(ctx):
    import aiohttp, json

    url = "https://join4join.xyz/api/v1/user/create"
    headers = {
        "Authorization": API_KEY,
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0"
    }

    body = json.dumps({"user_id": str(ctx.author.id)})

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=body) as r:
            text = await r.text()
            await ctx.send(f"RAW RESPONSE:\n```{text[:1800]}```")







# ========================================================
# RUN BOT
# ========================================================
bot.run(DISCORD_TOKEN)
