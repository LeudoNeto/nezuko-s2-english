import asyncio
import functools
import itertools
import math
import random
import urllib
import discord
import youtube_dl
from discord.ext import commands
import re
from discord.ui import Button, View
from pytube import Playlist
from config import bot_prefix

youtube_dl.utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**`{0.title}`** by **`{0.uploader}`**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))
        else:
            duration.append('LIVE')

        return ', '.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        em = (discord.Embed(description='```css\n{0.source.title}\n```'.format(self), color=discord.Color.from_rgb(244,127,255))
                 .add_field(name='⏱️ Duration:', value=f"`{self.source.duration}`", inline = True)
                 .add_field(name='🎵 Artist:', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .set_thumbnail(url=self.source.thumbnail)
                 .set_footer(text=f"Requested by {self.requester.name}", icon_url=f"{self.requester.avatar}"))
        em.set_author(
            name=f" Tocando agora: ",
            icon_url = "https://images-ext-2.discordapp.net/external/wCoxd5EKV3CrmZ6HlEaIS0F-Ggsdk9MyzoLFRVFefsY/https/images-ext-1.discordapp.net/external/DkPCBVBHBDJC8xHHCF2G7-rJXnTwj_qs78udThL8Cy0/%253Fv%253D1/https/cdn.discordapp.com/emojis/859459305152708630.gif")
        return em


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]

    def move(self, index1: int, index2:int):
        if index1 == index2:
            raise ValueError("You aren't changinf the music place")
        if not (0 < index1 <= self.__len__()) or not (0 < index2 <= (self.__len__()+1)):
            raise IndexError("At least one of the numbers you provided doesn't equate to any song on the list")
        if index1 < index2:
            self._queue.insert(index2,self._queue[index1-1])
            del self._queue[index1-1]
        else:
            self._queue.insert(index2-1,self._queue[index1-1])
            del self._queue[index1]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                self.current = await self.songs.get()
                    
            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)

            leave = Button(label='Leave', style=discord.ButtonStyle.red, emoji='🚪')
            pause = Button(label='Pause', emoji='⏸')
            resume = Button(label='Resume', style=discord.ButtonStyle.green, emoji='⏯')
            skip = Button(label='Skip', style=discord.ButtonStyle.blurple, emoji='⏩')
            queue = Button(label='Queue', style=discord.ButtonStyle.blurple, emoji='📋')

            self.leave_button = leave
            self.pause_button = pause
            self.resume_button = resume
            self.skip_button = skip
            self.queue_button = queue

            async def leave_callback(interaction):

                if not self._ctx.author.voice or not self._ctx.author.voice.channel or self._ctx.author.voice.channel != self._ctx.guild.me.voice.channel:
                    return await interaction.response.send_message('You are not on my voice channel', ephemeral=True)

                dest = self._ctx.author.voice.channel
                em = discord.Embed(title=f":zzz: Disconnected from  {dest}", color = interaction.user.color)
                em.set_footer(text=f"Requested by {interaction.user}") 
                await interaction.response.edit_message(embed=self.current.create_embed(),view=None)
                await interaction.channel.send(embed=em)
                await self._ctx.voice_state.stop()

            async def pause_callback(interaction):
                self._ctx.message.guild.voice_client.pause()
                atual = self.current.create_embed()
                atual.set_footer(text=atual.footer.text+f"\nSong paused by {interaction.user.name}", icon_url=f"{interaction.user.avatar}")
                await interaction.response.edit_message(embed=atual,view=self.viewcomresume)

            async def resume_callback(interaction):
                self._ctx.message.guild.voice_client.resume()
                atual = self.current.create_embed()
                atual.set_footer(text=atual.footer.text+f"\nSong resumed by {interaction.user.name}", icon_url=f"{interaction.user.avatar}")
                await interaction.response.edit_message(embed=atual,view=self.viewcompause)
            
            async def skip_callback(interaction):
                await interaction.response.edit_message(embed=self.current.create_embed(),view=None)
                await interaction.message.add_reaction('⏭')
                em = discord.Embed(title=f"Song skipped ⏭", color = interaction.user.color)
                em.set_footer(text=f"by {interaction.user}") 
                await interaction.channel.send(embed=em)
                self._ctx.voice_state.skip()
            
            async def queue_callback(interaction):
                page = 1
                if len(self._ctx.voice_state.songs) == 0:
                    return await interaction.response.send_message('The queue is empty.', ephemeral=True)

                items_per_page = 10
                pages = math.ceil(len(self._ctx.voice_state.songs) / items_per_page)

                start = (page - 1) * items_per_page
                end = start + items_per_page

                queue = ''
                for i, song in enumerate(self._ctx.voice_state.songs[start:end], start=start):
                    queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n`{1.source.duration}`\n\n'.format(i + 1, song)

                embed = (discord.Embed(description='**{} Tracks:**\n\n{}'.format(len(self._ctx.voice_state.songs), queue))
                     .set_footer(text='Reading page {}/{}'.format(page, pages)))
                await interaction.message.add_reaction('📋')
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            self.leave_button.callback = leave_callback
            self.pause_button.callback = pause_callback
            self.resume_button.callback = resume_callback
            self.skip_button.callback = skip_callback
            self.queue_button.callback = queue_callback

            self.viewcompause = View()
            self.viewcomresume = View()

            self.viewcompause.add_item(leave)
            self.viewcompause.add_item(pause)
            self.viewcompause.add_item(skip)
            self.viewcompause.add_item(queue)

            self.viewcomresume.add_item(leave)
            self.viewcomresume.add_item(resume)
            self.viewcomresume.add_item(skip)
            self.viewcomresume.add_item(queue)

            self.now_playing = await self.current.source.channel.send(embed=self.current.create_embed(),view=self.viewcompause)

            await self.next.wait()

            before = (discord.Embed(description='```css\n{0.source.title}\n```'.format(self.current), color=discord.Color.from_rgb(244,127,255))
                 .set_thumbnail(url=self.current.source.thumbnail)
                 .set_footer(text=f"Requested by {self.current.requester.name}", icon_url=f"{self.current.requester.avatar}"))
            before.set_author(
                name=f"📀 Played before: ")

            await self.now_playing.edit(embed=before,view=None)

            self.current = None

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Music Loaded")


    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command cannot be used in DMs.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error has occurred: {}'.format(str(error)))

    @commands.command(help="Join the voice channel.", name="join", aliases = ["j"], invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)          

        ctx.voice_state.voice = await destination.connect()

        em = discord.Embed(title=f"✅ I joined the channel  {destination}", color = ctx.author.color)
        em.set_footer(text=f"Requested by {ctx.author.name}")  
        await ctx.send(embed=em)

    @commands.command(help="Summons the bot in a channel", name="summon", aliases = ["s","chamar"])
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):

        if not channel and not ctx.author.voice:
            raise VoiceError('You are not on a voice channel / did not specify the channel for me to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            em = discord.Embed(title=f"✅ I was summoned to the channel  {destination}", color = ctx.author.color)
            em.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=em)

        ctx.voice_state.voice = await destination.connect()

    @commands.command(help="Leave the voice channel.", name="leave", aliases = ["l"])
    async def _leave(self, ctx: commands.Context):

        if not ctx.voice_state.voice:
            return await ctx.send("I'm not connected to any voice channel.")

        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send('You are not connected to any voice channel.')

        if ctx.author.voice.channel != ctx.guild.me.voice.channel:
            return await ctx.send("You are not on my voice channel.")

        dest = ctx.author.voice.channel
        await ctx.voice_state.stop()
        em = discord.Embed(title=f":zzz: Disconnected from  {dest}", color = ctx.author.color)
        em.set_footer(text=f"Requested by {ctx.author.name}")            
        await ctx.send(embed=em)


# Pesquisa o que você quiser no youtube
    @commands.command(help="Search for something on youtube", name="search", aliases= ["syt"])
    async def syt(self, ctx, *, search):
        async with ctx.typing():
            query_string = urllib.parse.urlencode({
                    "search_query": search
            })
            html_content = urllib.request.urlopen(
                "http://youtube.com/results?" + query_string
            )
        
            search_content = re.findall(r"watch\?v=(\S{11})", html_content.read().decode())
            yt_search = "http://youtube.com/watch?v=" + search_content[0]
        
        await ctx.send("🔎 **That's what I found on Youtube. Is it what you were looking for?** 🕵️‍♀️\n" + yt_search)



    @commands.command(help="Adjust the volume of my music.", name="volume", aliases = ["vol"])
    async def _volume(self, ctx: commands.Context, *, volume:int):

        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send('You are not connected to any voice channels.')

        if not ctx.voice_state.is_playing:
            return await ctx.send('I am not connected to any voice channels.')

        if ctx.author.voice.channel != ctx.guild.me.voice.channel:
            return await ctx.send("I'm already on a different voice channel.")

        if volume > 200:
            return await ctx.send(':x: The volume must be between **0 e 200**')

        ctx.voice_client.source.volume = volume / 75
        em = discord.Embed(title=f"Volume set to **`{volume}%`**", color = ctx.author.color)
        em.set_footer(text=f"Requested by {ctx.author.name}")    
        await ctx.send(embed=em)

    @commands.command(help="Shows what is currently playing.", name="now", aliases=['n','np', 'current', 'playing'])
    async def _now(self, ctx: commands.Context):

        if not ctx.voice_state.voice:
            if ctx.voice_state.current:
                await ctx.send("I'm not playing anything at the moment, but when I left I was playing:")
                em = (discord.Embed(description='```css\n{0.source.title}\n```'.format(ctx.voice_state.current), color=discord.Color.from_rgb(244,127,255))
                    .add_field(name='⏱️ Duration:', value=f"`{ctx.voice_state.current.source.duration}`", inline = True)
                    .add_field(name='🎵 Artist:', value='[{0.source.uploader}]({0.source.uploader_url})'.format(ctx.voice_state.current))
                    .set_thumbnail(url=ctx.voice_state.current.source.thumbnail)
                    .set_footer(text=f"Requested by {ctx.voice_state.current.requester.name}", icon_url=f"{ctx.voice_state.current.requester.avatar}"))
                await ctx.send(embed=em)
            else:
                await ctx.send("I'm not playing anything.")

        else:
            if ctx.voice_state.current:
                await ctx.send(embed=ctx.voice_state.current.create_embed())
            else:
                await ctx.send("I'm not playing anything.")

    @commands.command(name='pause', help='Pauses the song.', aliases=["pa"])
    async def _pause(self, ctx):
        server = ctx.message.guild
        voice_channel = server.voice_client

        if ctx.author.voice.channel != ctx.guild.me.voice.channel:
            return await ctx.send("You are not on my voice channel.")

        voice_channel.pause()

        atual = ctx.voice_state.current.create_embed()
        atual.set_footer(text=atual.footer.text+f"\nSong paused by {ctx.author.name}", icon_url=f"{ctx.author.avatar}")
        await ctx.voice_state.now_playing.edit(embed=atual,view=ctx.voice_state.viewcomresume)

    @commands.command(name='resume', help="Resumes the song", aliases=["r"])
    async def _resume(self, ctx):
        server = ctx.message.guild
        voice_channel = server.voice_client

        if ctx.author.voice.channel != ctx.guild.me.voice.channel:
            return await ctx.send("You are not on my voice channel.")


        voice_channel.resume()
        
        atual = ctx.voice_state.current.create_embed()
        atual.set_footer(text=atual.footer.text+f"\nSong resumed by {ctx.author.name}", icon_url=f"{ctx.author.avatar}")
        await ctx.voice_state.now_playing.edit(embed=atual,view=ctx.voice_state.viewcompause)

    @commands.command(name="stop", help="Stops the queue.", aliases=["st"])
    async def _stop(self, ctx):

        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send('You are not connected to any voice channels.')

        if ctx.author.voice.channel != ctx.guild.me.voice.channel:
            return await ctx.send("You are not on my voice channel.")

        em = discord.Embed(title=f"🛑 Okay, I won't play any more songs.", color = ctx.author.color)
        em.set_footer(text=f"Requested by {ctx.author.name}", icon_url=f"{ctx.author.avatar}")
        await ctx.send(embed=em)
        await ctx.voice_state.stop()

    @commands.command(name='skip', help="Skips the current song.", aliases=["sk"])
    async def _skip(self, ctx: commands.Context):

        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send('You are not connected to any voice channels.')

        if not ctx.voice_state.is_playing:
            return await ctx.send("I'm not playling anything...")

        if ctx.author.voice.channel != ctx.guild.me.voice.channel:
            return await ctx.send("You are not on my voice channel.")

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id != ctx.voice_state.current.requester:
            if ctx.voice_state.current.requester not in ctx.author.voice.channel.members:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('Vote added, currently at **{}/3**'.format(total_votes))

        else:
            await ctx.send('You already voted to skip this song.')

    @commands.command(name='queue', help="Shows the current queue.", aliases=["q"])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('The queue is empty.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n`{1.source.duration}`\n\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} Tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Reading page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle', help="Randomizes the queue.", aliases=["sh"])
    async def _shuffle(self, ctx: commands.Context):


        if ctx.author.voice.channel != ctx.guild.me.voice.channel:
            return await ctx.send("You are not on my voice channel.")

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('The queue is empty.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove', help="Removes a song from the queue", aliases=["re"])
    async def _remove(self, ctx: commands.Context, index: int):


        if ctx.author.voice.channel != ctx.guild.me.voice.channel:
            return await ctx.send("You are not on my voice channel.")

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('The queue is empty.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='move', help="Moves a song from the queue", aliases=["mo"])
    async def _move(self, ctx: commands.Context, index1: int, index2: int):


        if ctx.author.voice.channel != ctx.guild.me.voice.channel:
            return await ctx.send("You are not on my voice channel.")

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('The queue is empty.')

        ctx.voice_state.songs.move(index1,index2)
        await ctx.message.add_reaction('✅')
        

    @commands.command(name='play', help="Adds a song in the queue.", aliases=["p"])
    async def _play(self, ctx: commands.Context, *, search: str = None):

        if not search:
            em = discord.Embed(title = "Maybe you don't know how to use the bot yet", description= f"Send {bot_prefix}help to get more help", color = ctx.author.color)
            em.add_field(name= "How to use:", value=f"{bot_prefix}{ctx.invoked_with} [Search or URL]\nThen I will search for what you sent and add it to the queue.\n")
            em.add_field(name= "Example:", value=f"{bot_prefix}{ctx.invoked_with} `Hey Jude` - Searchs for Hey Jude on You Tube and get the first song found, adding it to the queue",inline=False)
            
            nameandaliases = ["play","p"]
            nameandaliases.remove(ctx.invoked_with)
            em.add_field(name="Alternativo:", value=f'{bot_prefix}{nameandaliases[0]}',inline=False)

            await ctx.send(embed=em)

        else:

            if not ctx.voice_state.voice:
                ctx.voice_state.current = None
                await ctx.invoke(self._join)

            if 'playlist' in search:
                playlist = Playlist(search)
                url = playlist.video_urls[0]
                try:
                    source = await YTDLSource.create_source(ctx, url, loop=self.bot.loop)
                except YTDLError as e:
                    await ctx.send('**`ERRO`**: {}'.format(str(e)))
                else:
                    song = Song(source)

                    await ctx.voice_state.songs.put(song)
                em = discord.Embed(title = 'Added to queue',description=f':headphones: `{playlist.length} songs` from playlist `{playlist.title}` were added to queue', color = ctx.author.color)
                em.set_footer(text=f"Requested by {ctx.author.name}", icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=em)

                for url in list(playlist.video_urls)[1:]:
                    try:
                        source = await YTDLSource.create_source(ctx, url, loop=self.bot.loop)
                    except YTDLError as e:
                        await ctx.send('**`ERRO`**: {}'.format(str(e)))
                    else:
                        song = Song(source)

                        await ctx.voice_state.songs.put(song)

            else:
                async with ctx.typing():
                    try:
                        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
                    except YTDLError as e:
                        await ctx.send('**`ERRO`**: {}'.format(str(e)))
                    else:
                        song = Song(source)

                        await ctx.voice_state.songs.put(song)

                        em = discord.Embed(title = 'Added to queue',description=f':headphones: Queued: {str(source)}', color = ctx.author.color)
                        em.set_footer(text=f"Requested by {ctx.author.name}", icon_url=f"{ctx.author.avatar}")
                        await ctx.send(embed=em)

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channels.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("I'm already on a different voice channel.")

async def setup(bot):
    await bot.add_cog(music(bot))