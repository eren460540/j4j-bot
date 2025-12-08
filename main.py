import discord
from discord.ext import commands
import aiohttp
import os
import json

# ============================================
# ENVIRONMENT VARIABLES
# ============================================
DISCORD_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://join4join.xyz/api/v1"

# ============================================
# LOCAL DEV REWARD TRACKER
# ============================================
if not os.path.exists("devstats.json"):
    with open("devstats.json", "w") as f:
        json.dump({"registered_users": 0, "farmed_users": []}, f)

def load_stats():
    with open("devstats.json", "r") as f:
        return json.load(f)

def save_stats(data):
    with open("devstats.json", "w") as f:
        json.dump(data, f, indent=4)


# ============================================
# BOT SETUP
# ============================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

CYBER_COLOR = 0x6f2dbd  # Neon purple cyber theme


def cyber_embed(title, desc):
    e = discord.Embed(title=title, description=desc, color=CYBER_COLOR)
    e.set_footer(text="Join4Join Bot • Cyberpunk Edition")
    return e


# ============================================
# JOIN4JOIN API WRAPPER
# ============================================
class Join4JoinAPI:
    def __init__(self):
        self.secret = API_KEY

    async def _post(self, endpoint, body):
        headers = {"Authorization": self.secret}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/{endpoint}", json=body, headers=headers) as r:
                try:
                    return await r.json()
                except:
                    return {"success": False, "message": "Invalid JSON"}

    async def create_user(self, user_id):
        return await self._post("user/create", {"user_id": user_id})

    async def get_user(self, user_id):
        return await self._post("user/get", {"user_id": user_id})

    async def farm(self, user_id):
        return await self._post("join4join/farm", {"user_id": user_id})

    async def daily(self, user_id):
        return await self._post("join4join/daily", {"user_id": user_id})

    async def pay(self, receiver, donor, coins):
        return await self._post("join4join/pay", {
            "user_receiver": receiver,
            "user_donator": donor,
            "coins": coins
        })

    async def info(self, guild_id):
        return await self._post("join4join/info", {"guild_id": guild_id})

    async def check(self, guild_id, user_id):
        return await self._post("join4join/check", {"guild_id": guild_id, "user_id": user_id})

    async def checkall(self, user_id):
        return await self._post("join4join/check/all", {"user_id": user_id})


api = Join4JoinAPI()


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

    header = "🌌💜🛸 ACCOUNT REGISTRATION 🛸💜🌌"

    if res.get("message") == "This user has already an account.":
        return await ctx.send(embed=cyber_embed(header, "You already have a **Join4Join account**."))

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ `{res.get('message')}`"))

    stats = load_stats()
    stats["registered_users"] += 1
    save_stats(stats)

    coins = res["data"]["coins"]

    await ctx.send(embed=cyber_embed(
        header,
        f"✅ **Account Created!**\n💰 Starting Coins: **{coins}**"
    ))


# -------------------------------
# !coins
# -------------------------------
@bot.command()
async def coins(ctx):
    uid = str(ctx.author.id)
    res = await api.get_user(uid)

    header = "💰⚡👾 COIN BALANCE 👾⚡💰"

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, "❌ Register using `!register`."))
    
    bal = res["data"]["coins"]
    await ctx.send(embed=cyber_embed(header, f"💰 **Your Balance:** {bal} coins"))


# -------------------------------
# !daily (HOURS + MINUTES)
# -------------------------------
@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    res = await api.daily(uid)

    header = "🎁🌌💜 DAILY REWARD 💜🌌🎁"

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ {res}"))

    data = res["data"]

    if not data["ready"]:
        ms = data["remaining_time"]
        sec = ms // 1000
        minutes = (sec // 60) % 60
        hours = sec // 3600

        return await ctx.send(embed=cyber_embed(
            header,
            f"⏳ Not ready.\nReturn in **{hours}h {minutes}m**."
        ))

    await ctx.send(embed=cyber_embed(header, f"🎉 You claimed **{data['amount']} coins**!"))


# -------------------------------
# !farm
# -------------------------------
@bot.command()
async def farm(ctx):
    uid = str(ctx.author.id)
    res = await api.farm(uid)

    header = "🌱👾💜 FARMING ACTIVATED 💜👾🌱"

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ `{res.get('message')}`"))

    stats = load_stats()
    if uid not in stats["farmed_users"]:
        stats["farmed_users"].append(uid)
        save_stats(stats)

    msg = "**[CLICK HERE TO START FARMING](https://join4join.xyz/?aff=1317419437854560288)**"

    await ctx.send(embed=cyber_embed(header, msg))


# -------------------------------
# !buy (JUST THE LINK — NOTHING ELSE)
# -------------------------------
@bot.command()
async def buy(ctx):
    header = "🧪🚀💜 AD PURCHASE 💜🚀🧪"

    embed = cyber_embed(
        header,
        "📢 Your ad is created.\n\n🔗 **Open dashboard:**\n[Click Here](https://join4join.xyz/dashboard)"
    )

    await ctx.send(embed=embed)


# -------------------------------
# !pay
# -------------------------------
@bot.command()
async def pay(ctx, receiver_id: str, coins: int):
    header = "💸🌌⚡ COIN TRANSFER ⚡🌌💸"

    res = await api.pay(receiver_id, str(ctx.author.id), coins)

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ `{res.get('message')}`"))

    await ctx.send(embed=cyber_embed(
        header,
        f"💸 Sent **{coins} coins** to `{receiver_id}`."
    ))


# -------------------------------
# !info
# -------------------------------
@bot.command()
async def info(ctx, server_id: str = None):
    header = "📡🧬💜 SERVER INFORMATION 💜🧬📡"

    gid = server_id or str(ctx.guild.id)

    res = await api.info(gid)

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ {res}"))

    d = res["data"]

    msg = (
        f"🛰️ **Name:** {d['name']}\n"
        f"🔗 **Invite:** {d['invite']}\n"
        f"📢 **Ad Running:** {d['ad']}\n"
        f"👥 **Bought Members:** {d['invitation_request']}\n"
        f"🚀 **Remaining Invites:** {d['invitation_update']}"
    )

    await ctx.send(embed=cyber_embed(header, msg))


# -------------------------------
# !check
# -------------------------------
@bot.command()
async def check(ctx, server_id: str = None):
    header = "🧪💜🧬 LEAVE CHECK 🧬💜🧪"

    gid = server_id or str(ctx.guild.id)
    res = await api.check(gid, str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ {res}"))

    if res["data"]["check"]:
        text = "✅ You can leave this server."
    else:
        text = "❌ You cannot leave yet."

    await ctx.send(embed=cyber_embed(header, text))


# -------------------------------
# !checkall (invalid servers hidden)
# -------------------------------
@bot.command()
async def checkall(ctx):
    header = "📜🌌💜 LEAVEABLE SERVERS 💜🌌📜"

    res = await api.checkall(str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ {res}"))

    ids = res["data"]["check"]

    msg = ""
    valid_found = False

    for gid in ids:
        # hide invalid ('server') entries
        if not gid.isdigit():
            continue

        valid_found = True
        guild = bot.get_guild(int(gid))
        if guild:
            msg += f"• **{guild.name}** (`{gid}`)\n"
        else:
            msg += f"• `{gid}` (bot not in server)\n"

    if not valid_found:
        msg = "❌ No valid servers can be left."

    await ctx.send(embed=cyber_embed(header, msg))


# -------------------------------
# !devstats
# -------------------------------
@bot.command()
async def devstats(ctx):
    header = "📊👾💜 DEVELOPER STATS 💜👾📊"

    stats = load_stats()
    reg = stats["registered_users"]
    farms = len(stats["farmed_users"])
    estimate = reg * 3

    msg = (
        f"🧍 **Registered Users:** {reg}\n"
        f"🌱 **Farming Users:** {farms}\n"
        f"💰 **Estimated Dev Coins:** {estimate}\n"
        "*(Real payout handled by Join4Join)*"
    )

    await ctx.send(embed=cyber_embed(header, msg))


# -------------------------------
# !j4jhelp
# -------------------------------
@bot.command()
async def j4jhelp(ctx):
    header = "📘🛸💜 COMMAND MENU 💜🛸📘"

    msg = (
        "**👾 ACCOUNT**\n"
        "`!register`\n"
        "`!coins`\n"
        "`!daily`\n\n"

        "**🌱 FARMING**\n"
        "`!farm`\n"
        "`!check <server-id>`\n"
        "`!checkall`\n\n"

        "**📢 ADS**\n"
        "`!buy` — opens dashboard\n\n"

        "**💸 PAYMENTS**\n"
        "`!pay <user-id> <coins>`\n\n"

        "**📡 SERVER INFO**\n"
        "`!info`\n"
        "`!info <server-id>`\n\n"

        "**👑 DEV**\n"
        "`!devstats`\n\n"

        "💜 All systems online."
    )

    await ctx.send(embed=cyber_embed(header, msg))


# ============================================
# RUN BOT
# ============================================
bot.run(DISCORD_TOKEN)
