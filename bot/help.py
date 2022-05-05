import discord
from discord.ext import commands
from discord.ui import Select,View
from config import bot_prefix

class HelpCommand(commands.HelpCommand):
    
    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f"__**{cog.qualified_name.capitalize()} commands**__", color = discord.Color.from_rgb(244,127,255))
        if cog.description:
            embed.description = cog.description
      
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=command.qualified_name, value=command.short_doc or "No description")
        
        embed.set_footer(text=f"{bot_prefix}{self.invoked_with}[command] for specific info.")
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=command.qualified_name, color = discord.Color.from_rgb(244,127,255))
        if command.help:
            embed.description = command.help
        
        embed.add_field(name="Usage:", value=f"```fix\n{bot_prefix}{command.qualified_name} {command.signature}\n```")
        embed.add_field(name="Alternatives:", value = "\t".join(f"`{bot_prefix}{aliase}`" for aliase in command.aliases), inline=False)

        await self.get_destination().send(embed=embed)

    async def send_bot_help(self, mapping):

        view = View()
        selection = Select(placeholder='Choose a category', options=[discord.SelectOption(label='Music',emoji='🎵',description='Music commands'),discord.SelectOption(label='Funny',emoji='😂',description='Funny commands'),discord.SelectOption(label='Others',emoji='⚙',description='Miscellaneous commands')])

        view.add_item(selection)

        embed = discord.Embed(color=discord.Color.from_rgb(244,127,255))
        embed.set_author(
            name=f" Help menu ",
            icon_url = "https://cdn.discordapp.com/avatars/933420163326423041/3507f298a2c64325b6843d4e7c6fe4b2.png?width=465&height=473")
        #embed.set_image(url="banner_url")
        #description = f"*support_url*"
        for cog, commands in mapping.items():
            if not cog:
                continue
            filtered = await self.filter_commands(commands, sort = True)
            if filtered:
                value = "\t".join(f"`{i.name}`" for i in commands)
                embed.add_field(name = cog.qualified_name, value = value, inline=False)
        embed.set_footer(text=f"{bot_prefix}{self.invoked_with}[command] for specific info.\n\n{bot_prefix}{self.invoked_with}[category] for category info, or\nselect it below:")
        
        await self.get_destination().send(embed=embed, view=view)

        async def select_callback(interaction):
            if selection.values[0] == 'Music':
                cog = list(mapping.keys())[0]

                embed = discord.Embed(title=f"__**{cog.qualified_name.capitalize()} commands**__", color = discord.Color.from_rgb(244,127,255))
                if cog.description:
                    embed.description = cog.description
            
                filtered = await self.filter_commands(cog.get_commands(), sort=True)
                for command in filtered:
                    embed.add_field(name=command.qualified_name, value=command.short_doc or "No description")

                await interaction.response.edit_message(embed=embed)

            if selection.values[0] == 'Funny':
                cog = list(mapping.keys())[1]

                embed = discord.Embed(title=f"__**{cog.qualified_name.capitalize()} commands**__", color = discord.Color.from_rgb(244,127,255))
                if cog.description:
                    embed.description = cog.description
            
                filtered = await self.filter_commands(cog.get_commands(), sort=True)
                for command in filtered:
                    embed.add_field(name=command.qualified_name, value=command.short_doc or "No description")

                await interaction.response.edit_message(embed=embed)

            if selection.values[0] == 'Others':
                cog = list(mapping.keys())[2]

                embed = discord.Embed(title=f"__**{cog.qualified_name.capitalize()} commands**__", color = discord.Color.from_rgb(244,127,255))
                if cog.description:
                    embed.description = cog.description
            
                filtered = await self.filter_commands(cog.get_commands(), sort=True)
                for command in filtered:
                    embed.add_field(name=command.qualified_name, value=command.short_doc or "No description")

                await interaction.response.edit_message(embed=embed)

        selection.callback = select_callback

async def setup(bot):
    bot.help_command = HelpCommand() 