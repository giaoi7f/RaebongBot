import os
import discord
from discord.ext import commands
import re
from dotenv import load_dotenv
from emojiLink import emoji_dict

emoji_regex = re.compile(r'<:\w*:\d*>')

load_dotenv()
token = os.environ.get('token')

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=intents)

    async def on_ready(self):
        print(f'{self.user}로 로그인함 (ID: {self.user.id})')
        await self.change_presence(activity=discord.Game(name="광질"))

    async def on_message(self, msg):
        if msg.author.bot or msg.author.id == self.user.id:
            return
    
        if msg.content == "e" or msg.content == "E":
            await msg.delete()
            emote_view = EmoteButtons()
            emote_msg = await msg.channel.send(view=emote_view, delete_after=15)
            await emote_view.wait()
            if emote_view.value:
                await emote_msg.delete()
            return
    
        if msg.content.startswith('<:'):
            emoji = emoji_regex.findall(msg.content)[0]
            if emoji == msg.content:
                await msg.delete()
                await msg.channel.send(embed=image_embed(
                        msg.author, f"https://cdn.discordapp.com/emojis/{msg.content.split(':')[2][:-1]}.png"))
                return
        
        if msg.content in emoji_dict:
            await msg.delete()
            await msg.channel.send(embed=image_embed(msg.author, emoji_dict[msg.content]))
            return

class EmoteButtons(discord.ui.View):
    def __init__(self, *, timeout=15):
        super().__init__(timeout=timeout)
        self.value = None
    
    @discord.ui.button(label="푸하하",style=discord.ButtonStyle.gray)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict["푸하하"]))
        self.stop()
    @discord.ui.button(label="두려워요",style=discord.ButtonStyle.gray)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict["두려워요"]))
        self.stop()
    @discord.ui.button(label="애애앵",style=discord.ButtonStyle.gray)
    async def button3(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict["애애앵"]))
        self.stop()
    @discord.ui.button(label="안아줘요",style=discord.ButtonStyle.gray)
    async def button4(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict["안아줘요"]))
        self.stop()

bot = Bot()

def image_embed(author, url):
    embed = discord.Embed(color=author.color)
    embed.set_author(name=author.display_name, icon_url=author.avatar.url)
    embed.set_image(url=url)
    return embed

async def logging(detail):
    print(f"Logging: {detail}")
    await bot.get_channel(962604153891323934).send(str(detail))

bot.run(token)