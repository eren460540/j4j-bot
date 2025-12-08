import discord
from discord.ext import commands
import aiohttp
import os
import json

# ======================================================
# LOAD ENVIRONMENT VARIABLES (Railway)
# ======================================================
DISCORD_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://join4join.xyz/api/v1"

# ======================================================
# LOCAL DEV STATS STORAGE (SAFE - DOES NOT AFFECT REAL DEV REWARDS)
# ======================================================
if not os.path.exists("devstats.json"):
    with open("devstats.json", "w") as f:
        json.dump({
            "registered_users": 0,
            "farmed_users": []
        }, f)

def load_stats():
    with open("devstats.json", "r") as f:
        return json.load(f)

def save_stats(data):
    with open("devstats.json", "w") as f:
        json.dump(data, f, indent=4)


# ======================================================
# DISCORD BOT SETUP
# ======================================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

COLOR = 0x6f2dbd  # Dark neon purple


# ======================================================
# API WRAPPER (CORRECT FOR DEV REWARDS)
# ======================================================
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


# ======================================================
# EMBED HELPER
# ======================================================
def embed(title, desc, color=COLOR):
    e = discord.Embed(title=title, description=desc, color=color)
    e.set_footer(text="Join4Join Bot • Powered by API")
    return e


# ======================================================
# COMMANDS
# ======================================================

@bot.command()
async def register(ctx):
    res = await api.create_user(str(ctx.author.id))

    # Already registered
    if res.get("message") == "This user has already an account.":
        return await ctx.send(embed=embed(
            "ℹ️ Already Registered",
            "You already have a Join4Join account.\nYou can use the bot normally!",
            COLOR
        ))

    # Error
    if not res.get("success"):
        return await ctx.send(embed=embed("❌ Registration Failed", res.get("message", "Unknown error"), 0xE74C3C))

    # New registration → you get +3 real dev coins
    stats = load_stats()
    stats["registered_users"] += 1
    save_stats(stats)

    coins = res["data"]["coins"]
    await ctx.send(embed=embed("✅ Account Created", f"You now have **{coins} coins**!"))


@bot.command()
async def coins(ctx):
    res = await api.get_user(str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=embed("❌ Error", "You must register first using `!register`."))

    await ctx.send(embed=embed("💰 Your Coins", f"You currently have **{res['data']['coins']} coins**."))


@bot.command()
async def daily(ctx):
    res = await api.daily(str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=embed("❌ Error", str(res)))

    d = res["data"]

    if not d["ready"]:
        return await ctx.send(embed=embed("⏳ Not Ready", f"Try again in **{d['remaining_time']} ms**."))

    await ctx.send(embed=embed("🎁 Daily Reward", f"You received **{d['amount']} coins**!"))


@bot.command()
async def farm(ctx):
    uid = str(ctx.author.id)
    res = await api.farm(uid)

    if not res.get("success"):
        return await ctx.send(embed=embed("❌ Error", str(res)))

    # Track unique affiliates (for dev rewards)
    stats = load_stats()
    if uid not in stats["farmed_users"]:
        stats["farmed_users"].append(uid)
        save_stats(stats)

    msg = (
        "🌱 **Farming Activated!**\n\n"
        "Your farming session is now linked to this bot.\n"
        "To actually farm and earn coins, go to the farming website:\n\n"
        "**🌐 https://join4join.xyz/farm**\n\n"
        "Make sure you're logged into the correct account."
    )

    await ctx.send(embed=embed("🌱 Farming Started", msg))


# ======================================================
# FIXED !BUY COMMAND WITH CLEAN INVITE + YES/NO FILTER
# ======================================================
@bot.command()
async def buy(ctx, coins: int, invite: str, language: str, alt: str = "no"):
    # Convert yes/no → boolean
    alt_bool = alt.lower() in ["yes", "true", "y"]

    # Extract invite code automatically
    if "discord.gg/" in invite or "discord.com/invite/" in invite:
        invite = invite.split("/")[-1]

    res = await api.buy(str(ctx.author.id), coins, invite, language, alt_bool)

    if not res.get("success"):
        return await ctx.send(embed=embed("❌ Error", res.get("message", "Unknown error")))

    if "link" in res:
        return await ctx.send(embed=embed("🔗 Confirm Purchase", f"[Click here to confirm]({res['link']})"))

    await ctx.send(embed=embed("📢 Ad Purchased", "Your Join4Join ad is now active!"))


@bot.command()
async def pay(ctx, receiver_id: str, coins: int):
    res = await api.pay(receiver_id, str(ctx.author.id), coins)

    if not res.get("success"):
        return await ctx.send(embed=embed("❌ Error", str(res)))

    if "link" in res:
        return await ctx.send(embed=embed("🔗 Confirm Transfer", f"[Click here to confirm]({res['link']})"))

    await ctx.send(embed=embed("💸 Transfer Complete", f"Sent **{coins} coins** to `{receiver_id}`!"))


@bot.command()
async def info(ctx, guild_id: str = None):
    gid = guild_id or str(ctx.guild.id)
    res = await api.info(gid)

    if not res.get("success"):
        return await ctx.send(embed=embed("❌ Error", str(res)))

    d = res["data"]

    msg = (
        f"**Name:** {d['name']}\n"
        f"**Invite:** {d['invite']}\n"
        f"**Ad Running:** {d['ad']}\n"
        f"**Bought Members:** {d['invitation_request']}\n"
        f"**Remaining Invites:** {d['invitation_update']}"
    )

    await ctx.send(embed=embed("📌 Server Info", msg))


@bot.command()
async def check(ctx, guild_id: str = None):
    gid = guild_id or str(ctx.guild.id)
    res = await api.check(gid, str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=embed("❌ Error", str(res)))

    await ctx.send(embed=embed("🚪 Leave Check", f"Can you leave? **{res['data']['check']}**"))


@bot.command()
async def checkall(ctx):
    res = await api.checkall(str(ctx.author.id))

    if not res.get("success"):
        return await ctx.send(embed=embed("❌ Error", str(res)))

    ids = res["data"]["check"]

    if not ids:
        return await ctx.send(embed=embed("📜 Leaveable Servers", "You cannot leave any servers yet."))

    msg = "\n".join(f"- `{g}`" for g in ids)
    await ctx.send(embed=embed("📜 Servers You Can Leave", msg))


# ======================================================
# DEVELOPER STATS (SAFE)
# ======================================================
@bot.command()
async def devstats(ctx):
    stats = load_stats()

    reg = stats["registered_users"]
    farm_users = len(stats["farmed_users"])

    est_dev_coins = reg * 3  # REAL dev coins come from Join4Join backend

    msg = (
        f"🧍 **Registered Users:** {reg}\n"
        f"🌱 **Affiliated Farming Users:** {farm_users}\n\n"
        f"💰 **Estimated Dev Coins Earned:** `{est_dev_coins}`\n"
        f"(Real farm coins are handled by Join4Join automatically.)"
    )

    await ctx.send(embed=embed("👑 Developer Stats", msg))


# ======================================================
# HELP MENU (STYLE B, WITH EXAMPLES)
# ======================================================
@bot.command()
async def j4jhelp(ctx):
    msg = (
        "**👤 ACCOUNT COMMANDS**\n"
        "• `!register` – Create your account\n"
        "  *Example:* `!register`\n\n"
        "• `!coins` – Check your balance\n"
        "  *Example:* `!coins`\n\n"
        "• `!daily` – Claim daily coins\n"
        "  *Example:* `!daily`\n\n"

        "**🌱 FARMING COMMANDS**\n"
        "• `!farm` – Activate farming session\n"
        "  *Example:* `!farm`\n\n"
        "• `!check` – See if you can leave the current server\n"
        "  *Example:* `!check`\n\n"
        "• `!checkall` – List all servers you can leave\n"
        "  *Example:* `!checkall`\n\n"

        "**📢 ADVERTISING COMMANDS**\n"
        "• `!buy <coins> <invite> <language> <yes/no>`\n"
        "  *Example:* `!buy 3 6nRx3KWG en yes`\n"
        "  *(Languages: en / fr / tr / all)*\n\n"

        "**💸 COINS TRANSFER**\n"
        "• `!pay <user_id> <coins>` – Send coins\n"
        "  *Example:* `!pay 123456789012345678 5`\n\n"

        "**👑 DEVELOPER**\n"
        "• `!devstats` – View your developer earnings\n"
        "  *Example:* `!devstats`\n"
    )

    await ctx.send(embed=embed("🤖 Join4Join Bot Help Menu", msg))


# ======================================================
# RUN BOT
# ======================================================
bot.run(DISCORD_TOKEN)
