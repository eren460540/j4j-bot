import discord
from discord.ext import commands
import aiohttp
import os
import json
import math

# ========================================================
# ENVIRONMENT VARIABLES
# ========================================================
DISCORD_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://join4join.xyz/api/v1"

# ========================================================
# LOCAL DEV REWARD TRACKER (does NOT affect real rewards)
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

CYBER_PURPLE = 0x8A2BE2


def cyber(title, desc):
    e = discord.Embed(title=title, description=desc, color=CYBER_PURPLE)
    e.set_footer(text="Join4Join Bot • Cyberpunk Edition")
    return e


# ========================================================
# JOIN4JOIN API — NOW FULLY CORRECT
# ========================================================
class J4J:
    def __init__(self):
        self.key = API_KEY

        self.headers = {
            "Authorization": self.key,
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }

    async def _post(self, endpoint, body):
        url = f"{BASE_URL}/{endpoint}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=body,             # FIXED: API now receives JSON properly
                headers=self.headers,
            ) as res:
                try:
                    return await res.json()
                except:
                    text = await res.text()
                    return {"success": False, "message": "Invalid JSON", "raw": text}

    async def _get(self, endpoint, params):
        url = f"{BASE_URL}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers) as res:
                try:
                    return await res.json()
                except:
                    text = await res.text()
                    return {"success": False, "message": "Invalid JSON", "raw": text}

    # API FUNCTIONS
    async def create_user(self, uid):
        return await self._post("user/create", {"user_id": uid})

    async def get_user(self, uid):
        return await self._get("user/get", {"user_id": uid})

    async def daily(self, uid):
        return await self._post("join4join/daily", {"user_id": uid})

    async def farm(self, uid):
        return await self._post("join4join/farm", {"user_id": uid})

    # BUY: You want dashboard only
    async def buy(self):
        return {"success": True}

    async def pay(self, receiver, donator, coins):
        return await self._post("join4join/pay", {
            "user_receiver": receiver,
            "user_donator": donator,
            "coins": coins
        })

    async def info(self, gid):
        return await self._post("join4join/info", {"guild_id": gid})

    async def check(self, gid, uid):
        return await self._post("join4join/check", {"guild_id": gid, "user_id": uid})

    async def checkall(self, uid):
        return await self._post("join4join/check/all", {"user_id": uid})


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

    await ctx.send(embed=cyber(
        "🛸 Account Created",
        f"✅ Successfully created your account!\n💰 Starting coins: **{coins}**"
    ))


# ------------------------ COINS ------------------------
@bot.command()
async def coins(ctx):
    uid = str(ctx.author.id)
    res = await api.get_user(uid)

    if not res.get("success"):
        return await ctx.send(embed=cyber("💰 Balance", "❌ You must register first."))

    bal = res["data"]["coins"]
    await ctx.send(embed=cyber("💰 Balance", f"Your coins: **{bal}**"))


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
            f"⏳ Not ready.\nTry again in **{hours}h {minutes % 60}m**"
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

    return await ctx.send(embed=cyber(
        "🌱 Farming Activated",
        "Your farming session is active!\n\n"
        "**[CLICK HERE TO START FARMING](https://join4join.xyz/?aff=1317419437854560288)**"
    ))


# ------------------------ BUY ------------------------
@bot.command()
async def buy(ctx):
    # You requested: !buy should ONLY show dashboard
    return await ctx.send(embed=cyber(
        "📢 Advertisement Dashboard",
        "**[OPEN DASHBOARD](https://join4join.xyz/dashboard)**"
    ))


# ------------------------ PAY ------------------------
@bot.command()
async def pay(ctx, receiver: str, coins: int):
    uid = str(ctx.author.id)
    res = await api.pay(receiver, uid, coins)

    if not res.get("success"):
        return await ctx.send(embed=cyber("💸 Transfer", f"❌ {res}"))

    return await ctx.send(embed=cyber(
        "💸 Transfer Complete",
        f"Sent **{coins} coins** to `{receiver}`."
    ))


# ------------------------ INFO ------------------------
@bot.command()
async def info(ctx, gid: str = None):
    gid = gid or str(ctx.guild.id)
    res = await api.info(gid)

    if not res.get("success"):
        return await ctx.send(embed=cyber("📡 Info", "❌ Error."))

    d = res["data"]

    await ctx.send(embed=cyber(
        "📡 Server Information",
        f"**Name:** {d['name']}\n"
        f"**Invite:** {d['invite']}\n"
        f"**Ad running:** {d['ad']}\n"
        f"**Bought:** {d['invitation_request']}\n"
        f"**Remaining:** {d['invitation_update']}"
    ))


# ------------------------ CHECK ------------------------
@bot.command()
async def check(ctx, gid: str = None):
    gid = gid or str(ctx.guild.id)
    res = await api.check(gid, str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=cyber("🧪 Leave Check", "❌ Error."))

    msg = "✅ You can leave this server." if res["data"]["check"] else "❌ You cannot leave yet."

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
        return await ctx.send(embed=cyber("📜 Leaveable Servers", "You cannot leave any servers yet."))

    formatted = "\n".join(f"• `{g}`" for g in ids)

    await ctx.send(embed=cyber("📜 Leaveable Servers", formatted))


# ------------------------ DEVSTATS ------------------------
@bot.command()
async def devstats(ctx):
    stats = load_stats()
    coins = stats["registered_users"] * 3
    farms = len(stats["farmed_users"])

    await ctx.send(embed=cyber(
        "👾 Developer Stats",
        f"👥 Registered users: **{stats['registered_users']}**\n"
        f"🌱 Farming users: **{farms}**\n"
        f"💰 Estimated coins: **{coins}**"
    ))


# ------------------------ HELP ------------------------
@bot.command()
async def j4jhelp(ctx):
    await ctx.send(embed=cyber(
        "📘 Command Menu",
        "**ACCOUNT COMMANDS**\n"
        "`!register` — Create your account\n"
        "`!coins` — View balance\n"
        "`!daily` — Claim daily reward\n\n"
        "**FARMING**\n"
        "`!farm`\n"
        "`!check <server-id>`\n"
        "`!checkall`\n\n"
        "**ADS**\n"
        "`!buy` — Opens dashboard\n\n"
        "**COINS**\n"
        "`!pay <user_id> <amount>`\n\n"
        "**SERVER**\n"
        "`!info`\n\n"
        "**DEVELOPER**\n"
        "`!devstats`"
    ))


# ========================================================
# RUN BOT
# ========================================================
bot.run(DISCORD_TOKEN)
