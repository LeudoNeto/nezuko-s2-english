#pip install -U git+https://github.com/Rapptz/discord.py    in terminal
import discord
from discord.ext import commands
from config import bot_prefix

intents = discord.Intents.all()

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension('music')
        await self.load_extension('others')
        await self.load_extension('funny')
        await self.load_extension('help')

bot = MyBot(command_prefix=bot_prefix, intents=intents, help_command=None, allowed_mentions=discord.AllowedMentions(roles=False, users=True, everyone=False, replied_user=True))

#on_ready: When active, sends message saying that it was connected
@bot.event
async def on_ready():
    print(f'Fui conectado como {bot.user}')
    await bot.change_presence(activity=discord.Game(name=f'+help | Bot do GDG 🎵'))


#on message: When reveived any message, sends the user and the message content.
@bot.listen()
async def on_message(message):
    print(f'Mensagem de {message.author}: {message.content}')

bot.run('seu-token-aqui') #replace seu-token-aqui with yout bot token (If u don't know how to get it, read the README.md)