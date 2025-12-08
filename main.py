import discord
from discord.ext import commands
import aiohttp
import os

# -------------------------
# LOAD VARIABLES FROM RAILWAY
# -------------------------
DISCORD_TOKEN = os.getenv("TOKEN")      # Your Discord bot token from Railway
API_KEY = os.getenv("API_KEY")          # Your Join4Join API key from Railway

BASE_URL = "https://join4join.xyz/api/v1"

intents = discord.Intents.default()
intents.message_content = True  # prevents warning
bot = commands.Bot(command_prefix="!", intents=intents)


# -------------------------
# JOIN4JOIN API WRAPPER
# -------------------------
class Join4JoinAPI:
    def __init__(self):
        self.secret_key = API_KEY

    async def _post(self, endpoint: str, params: dict):
        params["secret_key"] = self.secret_key
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/{endpoint}", params=params) as r:
                return await r.json()

    async def _get(self, endpoint: str, params: dict):
        params["secret_key"] = self.secret_key
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/{endpoint}", params=params) as r:
                return await r.json()

    # USER ENDPOINTS
    async def create_user(self, user_id):
        return await self._post("user/create", {"user_id": user_id})

    async def get_user(self, user_id):
        return await self._get("user/get", {"user_id": user_id})

    # BUY AD
    async def buy(self, user_id, coins, invite, lang, alt):
        return await self._post("join4join/buy", {
            "user_id": user_id,
            "coins": coins,
            "invite": invite,
            "filter_language": lang,
            "filter_account": str(alt).lower()
        })

    # FARM SERVERS
    async def farm(self, user_id):
        return await self._post("join4join/farm", {"user_id": user_id})

    # SEND COINS
    async def pay(self, receiver, donator, coins):
        return await self._post("join4join/pay", {
            "user_receiver": receiver,
            "user_donator": donator,
            "coins": coins
        })

    # SERVER INFO
    async def info(self, guild_id):
        return await self._post("join4join/info", {"guild_id": guild_id})

    # CHECK LEAVE
    async def check(self, guild_id, user_id):
        return await self._post("join4join/check", {
            "guild_id": guild_id,
            "user_id": user_id
        })

    # CLAIM DAILY
    async def daily(self, user_id):
        return await self._post("join4join/daily", {"user_id": user_id})

    # CHECK ALL SERVERS CAN LEAVE
    async def check_all(self, user_id):
        return await self._post("join4join/check/all", {"user_id": user_id})


api = Join4JoinAPI()


# -------------------------
# COMMANDS
# -------------------------
@bot.command()
async def register(ctx):
    res = await api.create_user(str(ctx.author.id))
    if not res["success"]:
        return await ctx.send("❌ Could not register. You may already have an account.")
    await ctx.send(f"✅ Registered! You have **{res['data']['coins']} coins**.")


@bot.command()
async def coins(ctx):
    res = await api.get_user(str(ctx.author.id))
    if not res["success"]:
        return await ctx.send("❌ You don't have an account. Use `!register`.")
    await ctx.send(f"💰 You have **{res['data']['coins']} coins**.")


@bot.command()
async def daily(ctx):
    res = await api.daily(str(ctx.author.id))
    if not res["success"]:
        return await ctx.send("❌ Could not claim daily.")
    data = res["data"]
    if not data["ready"]:
        return await ctx.send(f"⏳ Wait **{data['remaining_time']} ms** to claim again.")
    await ctx.send(f"🎁 You received **{data['amount']} coins**!")


@bot.command()
async def farm(ctx):
    res = await api.farm(str(ctx.author.id))
    if not res["success"]:
        return await ctx.send("❌ Could not get farm servers.")
    servers = res["data"]
    if not servers:
        return await ctx.send("🌿 No servers available to farm right now.")
    msg = "\n".join(f"- `{s}`" for s in servers)
    await ctx.send(f"🌱 Farm these servers:\n{msg}")


@bot.command()
async def buy(ctx, coins: int, invite: str, language: str, alt: bool = False):
    res = await api.buy(str(ctx.author.id), coins, invite, language, alt)
    if not res["success"]:
        return await ctx.send("❌ Could not buy the ad.")
    if "link" in res:
        return await ctx.send(f"🔗 Confirm your purchase: {res['link']}")
    await ctx.send("🎉 Ad purchased automatically!")


@bot.command()
async def pay(ctx, receiver_id: str, coins: int):
    donor_id = str(ctx.author.id)
    res = await api.pay(receiver_id, donor_id, coins)
    if not res["success"]:
        return await ctx.send("❌ Transfer failed.")
    if "link" in res:
        return await ctx.send(f"🔗 Confirm here: {res['link']}")
    await ctx.send(f"💸 Sent **{coins} coins** to `{receiver_id}`!")


@bot.command()
async def info(ctx, guild_id: str = None):
    guild_id = guild_id or str(ctx.guild.id)
    res = await api.info(guild_id)
    if not res["success"]:
        return await ctx.send("❌ Could not fetch server info.")
    data = res["data"]
    await ctx.send(
        f"📌 **Server Info**\n"
        f"Name: {data['name']}\n"
        f"Invite: {data['invite']}\n"
        f"Ad Running: {data['ad']}\n"
        f"Bought Members: {data['invitation_request']}\n"
        f"Remaining Invites: {data['invitation_update']}"
    )


@bot.command()
async def check(ctx, guild_id: str = None):
    guild_id = guild_id or str(ctx.guild.id)
    res = await api.check(guild_id, str(ctx.author.id))
    if not res["success"]:
        return await ctx.send("❌ Could not check leave status.")
    await ctx.send(f"🚪 Can leave: **{res['data']['check']}**")


@bot.command()
async def checkall(ctx):
    res = await api.check_all(str(ctx.author.id))
    if not res["success"]:
        return await ctx.send("❌ Could not check servers.")
    ids = res["data"]["check"]
    if not ids:
        return await ctx.send("❌ No servers you can leave.")
    msg = "\n".join(f"- `{gid}`" for gid in ids)
    await ctx.send(f"📜 Servers you can leave:\n{msg}")


# -------------------------
# START BOT
# -------------------------
bot.run(DISCORD_TOKEN)
