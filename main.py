import discord
from discord.ext import commands
import aiohttp
import os
import json

# ------------------------------------------
# LOAD VARIABLES FROM RAILWAY
# ------------------------------------------
DISCORD_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://join4join.xyz/api/v1"

# ------------------------------------------
# LOAD / SAVE DEV STATS
# ------------------------------------------
if not os.path.exists("devstats.json"):
    with open("devstats.json", "w") as f:
        json.dump({"registered_users": 0, "farm_activations": 0}, f)

def load_stats():
    with open("devstats.json") as f:
        return json.load(f)

def save_stats(stats):
    with open("devstats.json", "w") as f:
        json.dump(stats, f, indent=4)

stats = load_stats()

# ------------------------------------------
# DISCORD BOT SETUP
# ------------------------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ------------------------------------------
# JOIN4JOIN API WRAPPER (AUTH HEADER)
# ------------------------------------------
class Join4JoinAPI:
    def __init__(self):
        self.secret_key = API_KEY

    async def _post(self, endpoint: str, params: dict):
        headers = {"Authorization": self.secret_key}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/{endpoint}", json=params, headers=headers
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


# ------------------------------------------
# EMBED HELPER
# ------------------------------------------
def pretty_embed(title, description, color=0x2ECC71):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    embed.set_footer(text="Join4Join Bot • Powered by API")
    return embed


# ------------------------------------------
# COMMANDS
# ------------------------------------------

@bot.command()
async def register(ctx):
    res = await api.create_user(str(ctx.author.id))

    if "success" not in res:
        embed = pretty_embed("❌ API Error", f"`{res}`", color=0xE74C3C)
        return await ctx.send(embed=embed)

    if not res["success"]:
        embed = pretty_embed("❌ Registration Failed", res.get("message", "Unknown error"), 0xE74C3C)
        return await ctx.send(embed=embed)

    # Track developer stats
    stats = load_stats()
    stats["registered_users"] += 1
    save_stats(stats)

    coins = res["data"]["coins"]
    embed = pretty_embed("✅ Registration Complete", f"You now have **{coins} coins**!")
    await ctx.send(embed=embed)


@bot.command()
async def coins(ctx):
    res = await api.get_user(str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(embed=pretty_embed("❌ API Error", f"`{res}`", 0xE74C3C))

    if not res["success"]:
        return await ctx.send(embed=pretty_embed("❌ Not Registered", "Use `!register` first.", 0xE74C3C))

    amount = res["data"]["coins"]
    embed = pretty_embed("💰 Your Coins", f"You currently have **{amount} coins**.")
    await ctx.send(embed=embed)


@bot.command()
async def daily(ctx):
    res = await api.daily(str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(embed=pretty_embed("❌ API Error", f"`{res}`", 0xE74C3C))

    data = res["data"]
    if not data["ready"]:
        ms = data["remaining_time"]
        return await ctx.send(embed=pretty_embed("⏳ Not Ready", f"Try again in **{ms} ms**."))

    embed = pretty_embed("🎁 Daily Reward", f"You received **{data['amount']} coins**!")
    await ctx.send(embed=embed)


@bot.command()
async def farm(ctx):
    res = await api.farm(str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(embed=pretty_embed("❌ API Error", f"`{res}`", 0xE74C3C))

    # Track developer stats
    stats = load_stats()
    stats["farm_activations"] += 1
    save_stats(stats)

    embed = pretty_embed(
        "🌱 Farming Activated",
        "Your farming session has been activated.\n\n"
        "**Go to the Join4Join website to start farming:**\n"
        "🔗 https://join4join.xyz\n\n"
        "👉 Farming is done on the website now. Your affiliation is active!"
    )

    await ctx.send(embed=embed)


@bot.command()
async def pay(ctx, receiver_id: str, coins: int):
    res = await api.pay(receiver_id, str(ctx.author.id), coins)

    if "success" not in res:
        return await ctx.send(embed=pretty_embed("❌ API Error", f"`{res}`", 0xE74C3C))

    if not res["success"]:
        return await ctx.send(embed=pretty_embed("❌ Transfer Failed", "Could not send coins.", 0xE74C3C))

    if "link" in res:
        return await ctx.send(embed=pretty_embed("🔗 Confirmation Required", f"[Click here to confirm transfer]({res['link']})"))

    embed = pretty_embed("💸 Transfer Complete", f"Sent **{coins} coins** to `{receiver_id}`!")
    await ctx.send(embed=embed)


@bot.command()
async def info(ctx, guild_id: str = None):
    guild_id = guild_id or str(ctx.guild.id)
    res = await api.info(guild_id)

    if "success" not in res:
        return await ctx.send(embed=pretty_embed("❌ API Error", f"`{res}`", 0xE74C3C))

    data = res["data"]

    embed = pretty_embed(
        f"📌 Server Info: {data['name']}",
        f"**Invite:** {data['invite']}\n"
        f"**Ad Running:** {data['ad']}\n"
        f"**Bought Members:** {data['invitation_request']}\n"
        f"**Remaining Invites:** {data['invitation_update']}"
    )

    await ctx.send(embed=embed)


@bot.command()
async def check(ctx, guild_id: str = None):
    guild_id = guild_id or str(ctx.guild.id)
    res = await api.check(guild_id, str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(embed=pretty_embed("❌ API Error", f"`{res}`", 0xE74C3C))

    status = res["data"]["check"]
    embed = pretty_embed("🚪 Leave Check", f"Can you leave this server? **{status}**")
    await ctx.send(embed=embed)


@bot.command()
async def checkall(ctx):
    res = await api.check_all(str(ctx.author.id))

    if "success" not in res:
        return await ctx.send(embed=pretty_embed("❌ API Error", f"`{res}`", 0xE74C3C))

    ids = res["data"]["check"]

    if not ids:
        return await ctx.send(embed=pretty_embed("❌ No Servers", "You cannot leave any servers yet."))

    msg = "\n".join(f"- `{gid}`" for gid in ids)
    
    embed = pretty_embed("📜 Servers You Can Leave", msg)
    await ctx.send(embed=embed)


# ------------------------------------------
# 📊 NEW COMMAND: !devstats
# Shows how many affiliate users & farm activations you earned.
# ------------------------------------------
@bot.command()
async def devstats(ctx):
    stats = load_stats()

    embed = discord.Embed(
        title="👑 Developer Stats",
        description=(
            f"**Registered Users:** {stats['registered_users']}\n"
            f"**Farm Activations:** {stats['farm_activations']}\n\n"
            f"💰 **Estimated Dev Coins Earned:**\n"
            f"- From registrations: `{stats['registered_users'] * 3}`\n"
            f"- From farming: `{stats['farm_activations'] * 0.10}`\n"
            f"- **Total:** `{(stats['registered_users'] * 3) + (stats['farm_activations'] * 0.10)}`"
        ),
        color=0xF1C40F
    )
    embed.set_footer(text="Join4Join Developer Earnings")

    await ctx.send(embed=embed)


# ------------------------------------------
# START BOT
# ------------------------------------------
bot.run(DISCORD_TOKEN)
