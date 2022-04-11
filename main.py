import os
import discord
from discord.ext import commands
import re
import hanspell
from dotenv import load_dotenv
from discord.ui import view
from emojiLink import emoji_dict, emoji_name, emoji_name_1

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

        if msg.content == 'e' or msg.content == 'E' or msg.content == 'ㄷ':
            await msg.delete()
            emote_view = EmoteButtons()
            emote_msg = await msg.channel.send(view=emote_view)
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
    def __init__(self, *, timeout=10):
        super().__init__(timeout=timeout)
        self.value = None
    
    def on_timeout(self):
        self.value = True
        self.stop()
    
    @discord.ui.button(label=emoji_name_1[0],style=discord.ButtonStyle.gray,row=0)
    async def button0(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[1],style=discord.ButtonStyle.gray,row=0)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[2],style=discord.ButtonStyle.gray,row=0)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[3],style=discord.ButtonStyle.gray,row=1)
    async def button3(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[4],style=discord.ButtonStyle.gray,row=1)
    async def button4(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[5],style=discord.ButtonStyle.gray,row=1)
    async def button5(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[6],style=discord.ButtonStyle.gray,row=2)
    async def button6(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[7],style=discord.ButtonStyle.gray,row=2)
    async def button7(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[8],style=discord.ButtonStyle.gray,row=2)
    async def button8(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[9],style=discord.ButtonStyle.gray,row=3)
    async def button9(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[10],style=discord.ButtonStyle.gray,row=3)
    async def button10(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=emoji_name_1[11],style=discord.ButtonStyle.gray,row=3)
    async def button11(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[button.label]))
        self.stop()
    @discord.ui.button(label=1,style=discord.ButtonStyle.blurple,row=4,disabled=True)
    async def menu1(self, interaction: discord.Interaction, button: discord.ui.Button):
        children = self.children
        for i in range(0, 12):
            children[i].label = emoji_name[0][i]
        for i in range(12, 16):
            children[i].disabled = False
        button.disabled = True
        await interaction.response.edit_message(view=self)
    @discord.ui.button(label=2,style=discord.ButtonStyle.blurple,row=4)
    async def menu2(self, interaction: discord.Interaction, button: discord.ui.Button):
        children = self.children
        for i in range(0, 12):
            children[i].label = emoji_name[1][i]
        for i in range(12, 16):
            children[i].disabled = False
        button.disabled = True
        await interaction.response.edit_message(view=self)
    @discord.ui.button(label=3,style=discord.ButtonStyle.blurple,row=4)
    async def menu3(self, interaction: discord.Interaction, button: discord.ui.Button):
        children = self.children
        for i in range(0, 12):
            children[i].label = emoji_name[2][i]
        for i in range(12, 16):
            children[i].disabled = False
        button.disabled = True
        await interaction.response.edit_message(view=self)
    @discord.ui.button(label=4,style=discord.ButtonStyle.blurple,row=4)
    async def menu4(self, interaction: discord.Interaction, button: discord.ui.Button):
        children = self.children
        for i in range(0, 12):
            children[i].label = emoji_name[3][i]
        for i in range(12, 16):
            children[i].disabled = False
        button.disabled = True
        await interaction.response.edit_message(view=self)

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