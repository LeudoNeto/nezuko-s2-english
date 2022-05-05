import asyncio
from discord.ext import commands
import discord
import random
import asyncio

def random_love():
    love = random.randint(0, 100)
    return(love)

eightballresponses = [
    "Certainly.",
    "Definitely.",
    "No doubts.",
    "Yes, definitely.",
    "You can trust in this.",
    "In my view, yes.",
    "It's the most likely.",
    "Yes.",
    "My sources say yes.",
    "Don't count on it",
    "My answer is no.",
    "My sources say no.",
    "Very doubtful."
]

class funny(commands.Cog):
  """
  Very fun commands. Try them all!

  """
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    
  @commands.Cog.listener()
  async def on_message(self, msg):
    self.bot.mention = ["nezuko", "nezukos2"]
    mention = self.bot.mention
    if msg.author.bot:
      return
    if any(word in msg.content.lower() for word in mention):
      emoji="❤"
      await msg.add_reaction(emoji)
      await self.bot.process_commands(msg)

  @commands.command(aliases=['lovecalculator'])
  async def love(self, ctx, member: discord.Member=None):
    """
    Calculate your possibility of romance with another user
    
    """
    calc_love = random_love()
    if member is None:
      message = "First you need to tag someone!"
      await ctx.reply(message, mention_author=False)
    elif member is ctx.author:
      message = "∞ [█████████████████████]\n**You have enough self-esteem to love yourself.**"
      await ctx.reply(message, mention_author=False)
    else:
      if calc_love == 0:
        love_messsage = f"{calc_love}% [ . . . . . . . . . . ]\n🚫 There is no compatibility between **{ctx.author.name}** and **{member.name}**"
      elif 1 <= calc_love <= 10:
        love_messsage = f"{calc_love}% [█ . . . . . . . . . ]\n🙅‍♀️ The compatibility between **{ctx.author.name}** and **{member.name}** is so much low"
      elif 11 <= calc_love <= 20:
        love_messsage = f"{calc_love}% [█ . . . . . . . . . ]\n🤔 The compatibility between **{ctx.author.name}** and **{member.name}** is very low"
      elif 21 <= calc_love <= 30:
        love_messsage = f"{calc_love}% [██ . . . . . . . ]\n😶 The compatibility between **{ctx.author.name}** and **{member.name}** is low"
      elif 31 <= calc_love <= 40:
        love_messsage = f"{calc_love}% [███ . . . . . . ]\n💌 The compatibility between **{ctx.author.name}** and **{member.name}** is short"
      elif 41 <= calc_love <= 50:
        love_messsage = f"{calc_love}% [████ . . . . . ]\n💑 The compatibility between **{ctx.author.name}** and **{member.name}** is normal"
      elif 51 <= calc_love <= 60:
        love_messsage = f"{calc_love}% [█████ . . . . ]\n❤️ The compatibility between **{ctx.author.name}** and **{member.name}** it's reasonable"
      elif 61 <= calc_love <= 70:
        love_messsage = f"{calc_love}% [██████ . . . ]\n💕 The compatibility between **{ctx.author.name}** and **{member.name}** is decent"
      elif 71 <= calc_love <= 80:
        love_messsage = f"{calc_love}% [███████ . . ]\n💝 The compatibility between **{ctx.author.name}** and **{member.name}** is very decent"
      elif 81 <= calc_love <= 90:
        love_messsage = f"{calc_love}% [████████ . ]\n💘 The compatibility between **{ctx.author.name}** and **{member.name}** is very good"
      elif 91 <= calc_love <= 99:
        love_messsage = f"{calc_love}% [█████████]\n💞 The compatibility between **{ctx.author.name}** and **{member.name}** it's incredibly good"
      elif calc_love == 100:
        love_messsage = f"{calc_love}% [██████████]\n💖 The compatibility between **{ctx.author.name}** and **{member.name}** is perfect"
    embed = discord.Embed(description = f"{love_messsage}", color = 0xff9999)
    await ctx.reply(embed = embed, mention_author=False)

  #Usado de https://github.com/iiSakuu/Marshmallow
  @commands.command(aliases=['shipname'])
  async def ship(self, ctx, member : discord.Member, member2 : discord.Member = None):
        """
        Find out what the ship name would look like between two users 💘
        """

        if member2 is None:
            member2 = ctx.author

        if len(member.display_name) < 4:
            N = len(member.display_name) / 2

            firstmember = member.display_name
            firstship = firstmember[0:int(N)]

            secondmember = member2.display_name
            secondship = secondmember[0:4]

        elif len(member2.display_name) < 4 :
            N = len(member2.display_name) / 2

            firstmember = member.display_name
            firstship = firstmember[0:4]

            secondmember = member2.display_name
            secondship = secondmember[0:int(N)]

        else:

            firstmember = member.display_name
            firstship = firstmember[0:4]

            secondmember = member2.display_name
            secondship = secondmember[0:4]

        shipname = firstship + secondship

        embed = discord.Embed(
            description=f'{member.display_name} + {member2.display_name} = **{shipname}** 💘',
            colour=0xffb5f7
            )

        await ctx.send(embed=embed)

  @commands.command(name ='8ball', aliases=['ball8'])
  async def _8ball(self, ctx, *, question):
    """
    Ask a question and I'll give you the answer.
    """
    eightball = discord.Embed(
        title='Your question:',
        description=f'{question}',
        color=discord.Colour.random()
        )
    eightball.add_field(
        name='My answer:',
        value=f'||{(random.choice(eightballresponses))}||'
      )

    await ctx.reply('🎱 Shaking...', embed=eightball, mention_author=False)

  @commands.command(aliases=['choice'])
  async def choose(self, ctx, *, msg: str):
    """
    Give me options and I'll choose for you.

    """
    await ctx.reply(f'➡️ I choose... **{(random.choice(msg.split()))}**', mention_author=False)

  @commands.command(aliases=['roll'])
  async def dice(self, ctx):
    """
    Roll some dice.
    """
    message = await ctx.send("How many dice do you want to roll?")
    await message.add_reaction("1️⃣")
    await message.add_reaction("2️⃣")
    await message.add_reaction("3️⃣")

    check = lambda r, u: u == ctx.author and str(r.emoji) in "1️⃣2️⃣3️⃣"  # r=reaction, u=user

    dado_1 = random.randint(1,6)
    dado_2 = random.randint(1,6)
    dado_3 = random.randint(1,6)

    try:
        reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=10)
    except asyncio.TimeoutError:
        await message.edit(content="⌛ you took too long to decide")
        return

    if str(reaction.emoji) == "1️⃣":
        embed = discord.Embed(title=f"Rolled 1 dice:\n🎲 : {dado_1}", color=ctx.author.color)
        await ctx.send(embed=embed)
        return
    elif str(reaction.emoji) == "2️⃣":
        embed = discord.Embed(title=f"Rolled 2 dice:\n🎲 : {dado_1} 🎲 : {dado_2}", color=ctx.author.color)
        await ctx.send(embed=embed)
        return
    elif str(reaction.emoji) == "3️⃣":
        embed = discord.Embed(title=f"Rolled 3 dice:\n🎲 : {dado_1} 🎲 : {dado_2} 🎲 : {dado_3}", color=ctx.author.color)
        await ctx.send(embed=embed)
        return

async def setup(bot: commands.Bot):
  await bot.add_cog(funny(bot))