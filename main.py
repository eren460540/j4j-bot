import discord
from discord.ext import commands
import aiohttp
import os
import json

# ============================================
# ENVIRONMENT (Railway)
# ============================================
DISCORD_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://join4join.xyz/api/v1"

# ============================================
# LOCAL DEV STATS (DOES NOT AFFECT REAL REWARDS)
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
# DISCORD BOT SETUP
# ============================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

COLOR = 0x6f2dbd  # Cyberpunk neon-purple


# ============================================
# CYBERPUNK EMBED BUILDER
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
# JOIN4JOIN API WRAPPER
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
            "You already have a **Join4Join account**.\nYou can use all commands normally!"
        ))

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(
            header,
            f"❌ **Registration Failed**\nReason: `{res.get('message')}`"
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
        f"Your current balance:\n\n💰 **{coins} coins**"
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
        f"🎉 You have claimed **{data['amount']} coins**!"
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
        return await ctx.send(embed=cyber_embed(
            header,
            f"❌ Error: `{res.get('message')}`"
        ))

    stats = load_stats()
    if uid not in stats["farmed_users"]:
        stats["farmed_users"].append(uid)
        save_stats(stats)

    msg = (
        f"{header}\n\n"
        "🧬 Your farming session is now active.\n"
        "🚀 Click below to begin farming:\n\n"
        "**[START FARMING](https://join4join.xyz/dashboard/join4join/farm)**\n\n"
        "🧠 Make sure you're logged into the correct account."
    )

    await ctx.send(embed=cyber_embed("🌱 Farming Activated", msg))


# -------------------------------
# !buy
# -------------------------------
@bot.command()
async def buy(ctx, coins: int, invite: str, language: str, alt: str = "no"):
    header = "🧪🚀💜  AD PURCHASE  💜🚀🧪\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    alt_bool = alt.lower() in ["yes", "true", "y"]

    if "discord.gg/" in invite or "discord.com/invite/" in invite:
        invite = invite.split("/")[-1]

    res = await api.buy(str(ctx.author.id), coins, invite, language, alt_bool)

    if not res.get("success"):
        return await ctx.send(embed=cyber_embed(header, f"❌ Error: `{res.get('message')}`"))

    if "link" in res:
        return await ctx.send(embed=cyber_embed(
            header,
            f"🔗 **Click to confirm your advertisement:**\n[CONFIRM AD]({res['link']})"
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
        return await ctx.send(embed=cyber_embed(header, f"❌ Error: `{res}`"))

    if "link" in res:
        return await ctx.send(embed=cyber_embed(
            header,
            f"🔗 Confirm transfer:\n[CONFIRM TRANSFER]({res['link']})"
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
        return await ctx.send(embed=cyber_embed(header, f"❌ Error: `{res}`"))

    d = res["data"]

    msg = (
        f"**🛰️ Name:** {d['name']}\n"
        f"**🔗 Invite:** {d['invite']}\n"
        f"**📢 Ad Running:** {d['ad']}\n"
        f"**👥 Bought Members:** {d['invitation_request']}\n"
        f"**🚀 Remaining Invites:** {d['invitation_update']}"
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
        return await ctx.send(embed=cyber_embed(header, f"❌ Error: `{res}`"))

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
        return await ctx.send(embed=cyber_embed(header, f"❌ Error: `{res}`"))

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
        f"🧍 Registered Users: **{reg}**\n"
        f"🌱 Farming Users: **{farms}**\n\n"
        f"💰 Estimated Dev Coins: **{est_coins}**\n"
        f"(*real farming coins handled by Join4Join backend*)"
    )

    await ctx.send(embed=cyber_embed(header, msg))


# -------------------------------
# !j4jhelp
# -------------------------------
@bot.command()
async def j4jhelp(ctx):
    header = "📘🛸💜  COMMAND MENU  💜🛸📘\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    msg = (
        "**👾 ACCOUNT COMMANDS**\n"
        "`!register` – create your account\n"
        "`!coins` – view coins\n"
        "`!daily` – claim daily reward\n\n"

        "**🌱 FARMING**\n"
        "`!farm` – link farming session\n"
        "`!check` – leave check\n"
        "`!checkall` – list leaveable servers\n\n"

        "**📢 ADVERTISING**\n"
        "`!buy <coins> <invite> <lang> <yes/no>`\n"
        "Example: `!buy 3 6nRx3KWG en yes`\n\n"

        "**💸 TRANSFERS**\n"
        "`!pay <user_id> <coins>`\n\n"

        "**👑 DEVELOPER**\n"
        "`!devstats` – view dev reward stats\n"
    )

    await ctx.send(embed=cyber_embed(header, msg))


# ============================================
# RUN BOT
# ============================================
bot.run(DISCORD_TOKEN)
