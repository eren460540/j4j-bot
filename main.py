import discord
from discord.ext import commands
import aiohttp
import os

# -------------------------
# LOAD VARIABLES FROM RAILWAY
# -------------------------
DISCORD_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

BASE_URL = "https://join4join.xyz/api/v1"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# -------------------------
# JOIN4JOIN API WRAPPER (AUTH HEADER VERSION)
# -------------------------
class Join4JoinAPI:
    def __init__(self):
        self.secret_key = API_KEY

    async def _post(self, endpoint: str, params: dict):
        headers = {"Authorization": self.secret_key}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/{endpoint}",
                json=params,
                headers=headers
            ) as r:
                return await r.json()

    async def create_user(self, user_id):
        return await self._post("user/create", {"user_id": user_id})

    async def get_user(self, user_id):
        return await self._post("user/get", {"user_id": user_id})

    async def buy(self, user_id, coins, invite, lang, alt):
        return await self._post("join4join/buy", {
            "user_id": user_id,
            "coins": coins,
            "invite": invite,
            "filter_language": lang,
            "filter_account": alt
        })

    async def farm(self, user_id):
        return await self._post("join4join/farm", {"user_id": user_id})

    async def pay(self, receiver, donator, coins):
        return await self._post("join4join/pay", {
            "user_receiver": receiver,
            "user_donator": donator,
            "coins": coins
        })

    async def info(self, guild_id):
        return await self._post("join4join/info", {"guild_id": guild_id})

    async def check(self, guild_id, user_id):
        return await self._post("join4join/check", {
            "guild_id": guild_id,
            "user_id": user_id
        })

    async def daily(self, user_id):
        return await self._post("join4join/daily", {"user_id": user_id})

    async def check_all(self, user_id):
        return await self._post("join4join/check/all", {"user_id": user_id})


api = Join4JoinAPI()


# -------------------------
# COMMANDS
# -------------------------

@bot.command()
async def register(ctx):
    res = await api.create_user(str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(f"❌ API Error: `{res}`")

    if not res["success"]:
        msg = res.get("message", "Unknown error")
        return await ctx.send(f"❌ Could not register: {msg}")

    await ctx.send(f"✅ Account created! You now have **{res['data']['coins']} coins**.")


@bot.command()
async def coins(ctx):
    res = await api.get_user(str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(f"❌ API Error: `{res}`")

    if not res["success"]:
        return await ctx.send("❌ You don't have an account yet. Use `!register`.")

    await ctx.send(f"💰 You have **{res['data']['coins']} coins**.")


@bot.command()
async def daily(ctx):
    res = await api.daily(str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(f"❌ API Error: `{res}`")

    data = res["data"]

    if not data["ready"]:
        return await ctx.send(f"⏳ Wait **{data['remaining_time']} ms** to claim again.")

    await ctx.send(f"🎁 You claimed **{data['amount']} coins**!")


@bot.command()
async def farm(ctx):
    """
    Clean version of farm command:
    Activates farming affiliation + explains clearly what to do.
    """
    res = await api.farm(str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(f"❌ API Error: `{res}`")

    await ctx.send(
        "🌱 **Farming Activated!**\n"
        "You are now affiliated with this bot — you will earn coins normally AND the developer earns rewards.\n\n"
        "👉 Go to **https://join4join.xyz** and open the **Farm** page to start joining servers.\n"
        "This is where actual farming happens now."
    )


@bot.command()
async def buy(ctx, coins: int, invite: str, language: str, alt: bool = False):
    res = await api.buy(str(ctx.author.id), coins, invite, language, alt)

    if "success" not in res:
        return await ctx.send(f"❌ API Error: `{res}`")

    if not res["success"]:
        return await ctx.send("❌ Failed to buy the ad.")

    if "link" in res:
        return await ctx.send(f"🔗 Confirm your ad purchase: {res['link']}")

    await ctx.send("🎉 Ad purchased successfully!")


@bot.command()
async def pay(ctx, receiver_id: str, coins: int):
    res = await api.pay(receiver_id, str(ctx.author.id), coins)

    if "success" not in res:
        return await ctx.send(f"❌ API Error: `{res}`")

    if not res["success"]:
        return await ctx.send("❌ Transfer failed.")

    if "link" in res:
        return await ctx.send(f"🔗 Confirm transfer: {res['link']}")

    await ctx.send(f"💸 Sent **{coins} coins** to `{receiver_id}`!")


@bot.command()
async def info(ctx, guild_id: str = None):
    guild_id = guild_id or str(ctx.guild.id)
    res = await api.info(guild_id)

    if "success" not in res:
        return await ctx.send(f"❌ API Error: `{res}`")

    if not res["success"]:
        return await ctx.send("❌ Could not retrieve server info.")

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

    if "success" not in res:
        return await ctx.send(f"❌ API Error: `{res}`")

    await ctx.send(f"🚪 Can leave: **{res['data']['check']}**")


@bot.command()
async def checkall(ctx):
    res = await api.check_all(str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(f"❌ API Error: `{res}`")

    ids = res["data"]["check"]

    if not ids:
        return await ctx.send("❌ No servers you can leave at the moment.")

    msg = "\n".join(f"- `{gid}`" for gid in ids)

    await ctx.send(f"📜 **Servers you can leave:**\n{msg}")


# -------------------------
# START BOT
# -------------------------
bot.run(DISCORD_TOKEN)
