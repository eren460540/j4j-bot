import discord
from discord.ext import commands
import aiohttp

# -------------------------
# CONFIG
# -------------------------
API_KEY = "8b896494aaf147f6a98d56de86999740"
DISCORD_TOKEN = "MTQ0NzYyNjE4MTA1MzY0NDgzMg.GNG7Eb.DGLYPYD_G8oKcacJYYTIXT8wt4LJRigbDwHz0g"
BASE_URL = "https://join4join.xyz/api/v1"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# -------------------------
# API WRAPPER
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

    # USER
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

    # PAY COINS
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

    # DAILY REWARD
    async def daily(self, user_id):
        return await self._post("join4join/daily", {"user_id": user_id})

    # CHECK ALL SERVERS
    async def check_all(self, user_id):
        return await self._post("join4join/check/all", {"user_id": user_id})


api = Join4JoinAPI()


# -------------------------
# COMMANDS
# -------------------------

@bot.command()
async def register(ctx):
    """Register the user in Join4Join"""
    res = await api.create_user(str(ctx.author.id))

    if not res["success"]:
        return await ctx.send("❌ Failed to register. Maybe you already have an account?")

    coins = res["data"]["coins"]
    await ctx.send(f"✅ Registered! You have **{coins} coins**.")


@bot.command()
async def coins(ctx):
    """Show user coins"""
    res = await api.get_user(str(ctx.author.id))

    if not res["success"]:
        return await ctx.send("❌ You don't have an account. Use `!register`.")

    coins = res["data"]["coins"]
    await ctx.send(f"💰 You have **{coins} coins**.")


@bot.command()
async def daily(ctx):
    """Claim daily reward"""
    res = await api.daily(str(ctx.author.id))

    if not res["success"]:
        return await ctx.send("❌ Error claiming daily.")

    data = res["data"]

    if not data["ready"]:
        return await ctx.send(f"⏳ You must wait **{data['remaining_time']} ms**.")

    await ctx.send(f"🎁 You received **{data['amount']} coins**!")


@bot.command()
async def farm(ctx):
    """Get farm servers"""
    res = await api.farm(str(ctx.author.id))

    if not res["success"]:
        return await ctx.send("❌ Could not fetch farm servers.")

    servers = res["data"]

    if not servers:
        return await ctx.send("🌿 No servers to farm right now.")

    msg = "\n".join(f"- `{guild}`" for guild in servers)
    await ctx.send(f"🌱 Farm these servers:\n{msg}")


@bot.command()
async def buy(ctx, coins: int, invite: str, language: str, alt: bool = False):
    """Buy an ad"""
    res = await api.buy(str(ctx.author.id), coins, invite, language, alt)

    if not res["success"]:
        return await ctx.send("❌ Could not buy the ad.")

    if "link" in res:
        return await ctx.send(f"🔗 Confirm your purchase: {res['link']}")

    await ctx.send("🎉 Ad purchased automatically!")


@bot.command()
async def pay(ctx, receiver_id: str, coins: int):
    """Transfer coins"""
    donor_id = str(ctx.author.id)

    res = await api.pay(receiver_id, donor_id, coins)

    if not res["success"]:
        return await ctx.send("❌ Failed to send coins.")

    if "link" in res:
        return await ctx.send(f"🔗 Confirm transfer: {res['link']}")

    await ctx.send(f"💸 Sent **{coins} coins** to `{receiver_id}`!")


@bot.command()
async def info(ctx, guild_id: str = None):
    """Get info about a guild"""
    guild_id = guild_id or str(ctx.guild.id)
    res = await api.info(guild_id)

    if not res["success"]:
        return await ctx.send("❌ Could not get server info.")

    data = res["data"]

    await ctx.send(
        f"📌 **Server Info**\n"
        f"Name: {data['name']}\n"
        f"Invite: {data['invite']}\n"
        f"Ad Running: {data['ad']}\n"
        f"Requested: {data['invitation_request']}\n"
        f"Left to invite: {data['invitation_update']}"
    )


@bot.command()
async def check(ctx, guild_id: str = None):
    """Check if user can leave a server"""
    guild_id = guild_id or str(ctx.guild.id)
    res = await api.check(guild_id, str(ctx.author.id))

    if not res["success"]:
        return await ctx.send("❌ Error checking server.")

    status = res["data"]["check"]
    await ctx.send(f"🚪 Can leave: **{status}**")


@bot.command()
async def checkall(ctx):
    """Check all servers user can leave"""
    res = await api.check_all(str(ctx.author.id))

    if not res["success"]:
        return await ctx.send("❌ Error checking servers.")

    ids = res["data"]["check"]
    if not ids:
        return await ctx.send("❌ No servers you can leave.")

    msg = "\n".join(f"- `{gid}`" for gid in ids)
    await ctx.send(f"📜 Servers you can leave:\n{msg}")


# -------------------------
# RUN BOT
# -------------------------
bot.run(DISCORD_TOKEN)
