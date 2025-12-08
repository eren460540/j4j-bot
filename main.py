import discord
from discord.ext import commands
import aiohttp
import os
import json

# ============================================
# ENVIRONMENT
# ============================================
DISCORD_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://join4join.xyz/api/v1"

# ============================================
# LOCAL DEV STATS
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
# DISCORD BOT
# ============================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

COLOR = 0x7B2CBF  # DARK NEON PURPLE


# ============================================
# CYBERPUNK EMBED
# ============================================
def cyber_embed(title, desc):
    e = discord.Embed(
        title=title,
        description=desc,
        color=COLOR
    )
    e.set_footer(text="Join4Join Bot • Cyberpunk Edition")
    return e


# ============================================
# JOIN4JOIN API
# ============================================
class Join4JoinAPI:
    def __init__(self):
        self.secret_key = API_KEY

    async def _post(self, endpoint, body):
        headers = {"Authorization": self.secret_key}
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

    async def buy(self, user_id, coins, invite, language, alt):
        return await self._post("join4join/buy", {
            "user_id": user_id,
            "coins": coins,
            "invite": invite,
            "filter_language": language,
            "filter_account": alt
        })

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

    header = "🌌💜🛸  ACCOUNT REGISTRATION  🛸💜🌌\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if res.get("message") == "This user has already an account.":
        return await ctx.send(embed=cyber_embed(
            header,
            "🛸 You already have a **Join4Join account**.\nYou're ready to use all features!"
        ))

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(
            header,
            f"❌ Registration Failed\n`{res.get('message')}`"
        ))

    stats = load_stats()
    stats["registered_users"] += 1
    save_stats(stats)

    coins = res["data"]["coins"]

    await ctx.send(embed=cyber_embed(
        header,
        f"✅ **Account Created Successfully!**\n\n💰 Starting Coins: **{coins}**"
    ))


# -------------------------------
# !coins
# -------------------------------
@bot.command()
async def coins(ctx):
    uid = str(ctx.author.id)
    res = await api.get_user(uid)

    header = "💰⚡👾  COIN BALANCE  👾⚡💰\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(
            header,
            "❌ You must register first using `!register`."
        ))

    coins = res["data"]["coins"]

    await ctx.send(embed=cyber_embed(
        header,
        f"💰 Your current balance:\n**{coins} coins**"
    ))


# -------------------------------
# !daily
# -------------------------------
@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    res = await api.daily(uid)

    header = "🎁🌌💜  DAILY REWARD  💜🌌🎁\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ {res}"))

    data = res["data"]

    if not data["ready"]:
        return await ctx.send(embed=cyber_embed(
            header,
            f"⏳ Not ready yet.\nTry again in **{data['remaining_time']} ms**."
        ))

    await ctx.send(embed=cyber_embed(
        header,
        f"🎉 You claimed **{data['amount']} coins**!"
    ))


# -------------------------------
# !farm
# -------------------------------
@bot.command()
async def farm(ctx):
    uid = str(ctx.author.id)
    res = await api.farm(uid)

    header = "🌱👾💜  FARMING ACTIVATED  💜👾🌱\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ `{res.get('message')}`"))

    stats = load_stats()
    if uid not in stats["farmed_users"]:
        stats["farmed_users"].append(uid)
        save_stats(stats)

    msg = (
        "🧬 Your farming session is now active!\n"
        "🚀 Click below to start farming and earning coins:\n\n"
        "**[START FARMING](https://join4join.xyz/?aff=1317419437854560288)**\n\n"
        "🧠 Make sure you're logged into your account first."
    )

    await ctx.send(embed=cyber_embed(header, msg))


# -------------------------------
# !buy
# -------------------------------
@bot.command()
async def buy(ctx, coins: int, invite: str, language: str, altfilter: str):
    header = "🧪🚀💜  AD PURCHASE  💜🚀🧪\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # EXTRACT REAL INVITE CODE
    raw = invite.strip()

    if "discord.gg/" in raw:
        raw = raw.split("discord.gg/")[1].split("/")[0]
    elif "discord.com/invite/" in raw:
        raw = raw.split("discord.com/invite/")[1].split("/")[0]
    elif "invite/" in raw:
        raw = raw.split("invite/")[1].split("/")[0]

    invite_code = raw

    alt_bool = altfilter.lower() in ["yes", "true", "y"]

    res = await api.buy(str(ctx.author.id), coins, invite_code, language, alt_bool)

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(
            header, f"❌ Error:\n`{res.get('message')}`"
        ))

    if "link" in res:
        return await ctx.send(embed=cyber_embed(
            header,
            f"🔗 Click to confirm your advertisement:\n**[CONFIRM AD]({res['link']})**"
        ))

    await ctx.send(embed=cyber_embed(
        header,
        "📢 Your advertisement is now **LIVE**!"
    ))


# -------------------------------
# !pay
# -------------------------------
@bot.command()
async def pay(ctx, receiver_id: str, coins: int):
    header = "💸🌌⚡  COIN TRANSFER  ⚡🌌💸\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    res = await api.pay(receiver_id, str(ctx.author.id), coins)

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ Error:\n`{res}`"))

    if "link" in res:
        return await ctx.send(embed=cyber_embed(
            header,
            f"🔗 Confirm transfer:\n**[CONFIRM TRANSFER]({res['link']})**"
        ))

    await ctx.send(embed=cyber_embed(
        header,
        f"💸 Successfully sent **{coins} coins** to `{receiver_id}`!"
    ))


# -------------------------------
# !info
# -------------------------------
@bot.command()
async def info(ctx, guild_id: str = None):
    header = "📡🧬💜  SERVER INFORMATION  💜🧬📡\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    gid = guild_id or str(ctx.guild.id)
    res = await api.info(gid)

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ `{res}`"))

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
async def check(ctx, guild_id: str = None):
    header = "🧪💜🧬  LEAVE CHECK  🧬💜🧪\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    gid = guild_id or str(ctx.guild.id)
    res = await api.check(gid, str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ `{res}`"))

    status = "✅ You can leave this server." if res["data"]["check"] else "❌ You cannot leave yet."

    await ctx.send(embed=cyber_embed(header, status))


# -------------------------------
# !checkall
# -------------------------------
@bot.command()
async def checkall(ctx):
    header = "📜🌌💜  LEAVEABLE SERVERS  💜🌌📜\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    res = await api.checkall(str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ `{res}`"))

    ids = res["data"]["check"]

    if not ids:
        return await ctx.send(embed=cyber_embed(header, "❌ You cannot leave any servers yet."))

    msg = "\n".join(f"• `{g}`" for g in ids)

    await ctx.send(embed=cyber_embed(header, msg))


# -------------------------------
# !devstats
# -------------------------------
@bot.command()
async def devstats(ctx):
    header = "📊👾💜  DEVELOPER STATS  💜👾📊\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    stats = load_stats()
    reg = stats["registered_users"]
    farms = len(stats["farmed_users"])
    est_coins = reg * 3

    msg = (
        f"🧍 **Registered Users:** {reg}\n"
        f"🌱 **Users Who Entered Farming:** {farms}\n\n"
        f"💰 **Estimated Dev Coins:** {est_coins}\n"
        "(Backend handles real farming coins.)"
    )

    await ctx.send(embed=cyber_embed(header, msg))


# -------------------------------
# !j4jhelp
# -------------------------------
@bot.command()
async def j4jhelp(ctx):
    header = "📘🛸💜  COMMAND MENU  💜🛸📘\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    msg = (
        f"{header}\n"
        "**👾 ACCOUNT COMMANDS**\n"
        "• `!register` – Create your J4J account\n"
        "  Example: `!register`\n\n"
        
        "• `!coins` – Check your balance\n"
        "  Example: `!coins`\n\n"
        
        "• `!daily` – Claim your daily reward\n"
        "  Example: `!daily`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**🌱 FARMING COMMANDS**\n"
        "• `!farm` – Open farming page (affiliate link)\n"
        "  Example: `!farm`\n\n"

        "• `!check` – Check leave eligibility\n"
        "  Example: `!check`\n\n"

        "• `!checkall` – List all safely leavable servers\n"
        "  Example: `!checkall`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**📢 ADVERTISEMENT COMMANDS**\n"
        "• `!buy <coins> <invite> <language> <yes/no>`\n"
        "  Example: `!buy 3 discord.gg/6nRx3KWG en yes`\n"
        "  Languages: `en`, `fr`, `tr`, `all`\n"
        "  Alt filter: `yes` or `no`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**💸 COIN TRANSFER**\n"
        "• `!pay <user_id> <amount>`\n"
        "  Example: `!pay 123456789012345678 15`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**📡 SERVER INFORMATION**\n"
        "• `!info` – Info about this server\n"
        "• `!info <guild>` – Info about any server\n"
        "  Example: `!info 123456789012345678`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**👑 DEVELOPER COMMANDS**\n"
        "• `!devstats` – See your affiliate stats\n"
        "  Example: `!devstats`\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💜 **Join4Join Cyberpunk Edition – All systems online.**"
    )

    await ctx.send(embed=cyber_embed("📘 Command Menu", msg))


# ============================================
# RUN BOT
# ============================================
bot.run(DISCORD_TOKEN)
