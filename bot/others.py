import discord
from discord.ext import commands
import time

class others(commands.Cog):
  """
  Other commands, nothing extraordinary.

  """
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.command(name="ping", aliases = ['latency'])
  async def ping(self, ctx: commands.Context):
        """
        Pong!

        """
        start_time = time.time()
        
        message = await ctx.send("Testing ping...")
        
        typings = time.monotonic()
        await ctx.trigger_typing()
        typinge = time.monotonic()
        typingms = round((typinge - typings) * 1000)
        
        end_time = time.time()
        
        embed = discord.Embed(
          title="🏓 Pong",
            description=(f'Ping: **{round(self.bot.latency * 1000)}ms**\nAPI: **{round((end_time - start_time) * 1000)}ms**\nWriting: **{typingms}ms**'),
            color=0xfbf9fa
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/933420163326423041/3507f298a2c64325b6843d4e7c6fe4b2.png?width=465&height=473")
        await ctx.send(embed=embed)
  
  @commands.command(name="git",aliases = ['github'])
  async def git(self, ctx: commands.Context):
        """
        Source of the bot
        """
        await ctx.send("You cann review my source at: https://github.com/LeudoNeto/nezuko-s2-english")
  
  @commands.command(name="invite",aliases = ['convidar'])
  async def invite(self, ctx: commands.Context):
      """
      URL for inviting me to a server

      """
      embed = discord.Embed(
          title="Want to invite me to a server?",
          description="Here you get the URL for it:",
          color=0xfbf9fa,
      )
      embed.add_field(
          name="Nezuko s2",
          value="[Invite me](https://discord.com/api/oauth2/authorize?client_id=933420163326423041&permissions=0&scope=bot)",
          inline=True
      )
      #embed.set_image(url="banner_url"
      #)
      await ctx.send("I sent the URL here and in your DM", delete_after = 10)
      await ctx.author.send(embed=embed)
      await ctx.send(embed=embed)

  @commands.command(aliases=['si', 'server']) #From https://github.com/cree-py/RemixBot/blob/master/cogs/info.py
  async def serverinfo(self, ctx):
        '''Basic server info.'''
        guild = ctx.guild
        guild_age = (ctx.message.created_at - guild.created_at).days
        created_at = f"Server created at {guild.created_at.strftime('%b %d %Y │ %H:%M')}.\nThis was {guild_age} days ago!"

        em = discord.Embed(description=created_at, color=0xfbf9fa)
        em.add_field(name='Owner', value=guild.owner, inline=False)
        em.add_field(name='Members', value=len(guild.members), inline=False)
        em.add_field(name='Roles', value=len(guild.roles))
        em.add_field(name='Text channels', value=len(guild.text_channels))
        em.add_field(name='Voice channels', value=len(guild.voice_channels))


        em.set_thumbnail(url=None or guild.icon)
        em.set_author(name=guild.name, icon_url=None or guild.icon)
        await ctx.send(embed=em)

  #@commands.command(aliases=["topgg"])
  #async def vote(self, ctx: commands.Context):
  #    """
  #    Nezuko s2's profile on topgg
  #    """
  #    embed = discord.Embed(
  #        title="Support me on top.gg",
  #        description="Consider voting me on top.gg plz",
  #        color=0xfbf9fa,
  #    )
  #    embed.add_field(
  #        name="Nezuko s2 on top.gg",
  #        value="[Top.gg](url)",
  #        inline=True
  #    )
  #    embed.set_image(url="url_banner"
  #    )
  #    await ctx.send("Sending my profile on top.gg", delete_after = 10)
  #    await ctx.author.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(others(bot))