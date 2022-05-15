import os
import html
import discord
from discord.ext import commands
import re
import random
from hanspell import spell_checker
from dotenv import load_dotenv
from discord import utils
from emojiLink import emoji_dict, emoji_names_mood, emoji_names_answer, emoji_names_say
from name import name_list
from question import question

emoji_regex = re.compile(r'<:\w*:\d*>')

load_dotenv()
token = os.environ.get('token')

class Bot(commands.Bot):
    def __init__(self):
        self.command_prefix='!'
        self.fight_embed=False
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=intents)

    async def on_ready(self):
        await logging(f'{self.user}로 로그인함 (ID: {self.user.id})')
        await self.change_presence(activity=discord.Game(name="광질"))
        
        global options1, options2, options3
        options1, options2, options3 = [], [], []
        for name in emoji_names_mood:
            options1.append(discord.SelectOption(label=name,value=name))
        for name in emoji_names_answer:
            options2.append(discord.SelectOption(label=name,value=name))
        for name in emoji_names_say:
            options3.append(discord.SelectOption(label=name,value=name))
        # self.music = []
        # async for message in self.get_channel(962604153891323934).history():
        #     if message.content.startswith('> '): #and message.author.id == self.application_id
        #         self.music.append(message.content)
        # print("MusicArr Added :\n" + "\n".join(self.music))

    async def on_message(self, msg):
        if msg.author.bot or msg.author.id == self.user.id:
            return

        #'E' command
        if msg.content == 'e' or msg.content == 'E' or msg.content == 'ㄷ':
            await msg.delete()
            view = EmoteButtons()
            emote_msg = await msg.channel.send(view=view, delete_after=5)
            await view.wait()
            if view.value:
                await emote_msg.delete()
            return

        #enlarge emoticon with image_embed
        if msg.content.startswith('<:'):
            emoji = emoji_regex.findall(msg.content)[0]
            if emoji == msg.content:
                await msg.delete()
                await msg.channel.send(embed=image_embed(
                        msg.author, f"https://cdn.discordapp.com/emojis/{msg.content.split(':')[2][:-1]}.png"))
                return

        #Direct Emoji command
        if msg.content in emoji_dict:
            await msg.delete()
            await msg.channel.send(embed=image_embed(msg.author, emoji_dict[msg.content]))
            return

        #Emoji Testing
        if msg.content == '!emojitest':
            for emoji in emoji_dict.keys():
                await msg.channel.send(embed=image_embed(msg.author, emoji_dict[emoji]))
            return

        #Team
        if msg.content == '!내전':
            channel = msg.author.voice.channel
            if channel:
                if self.fight_embed:
                    await self.fight_embed.delete()
                member = channel.members
                player = []
                for user in member:
                    if user.id in name_list:
                        player.append(name_list[user.id])
                    else:
                        player.append(user.name)

                embed = discord.Embed(title=f"내전 ({len(player)}명)",description=", ".join(sorted(player)),color=0xff0000)
                random.shuffle(player)
                embed.add_field(name="Team1", value=" / ".join(sorted(player[:int(len(player) / 2)])), inline=False)
                embed.add_field(name="Team2", value=" / ".join(sorted(player[int(len(player) / 2):])), inline=True)
                self.fight_embed = await msg.reply(embed=embed)
            else:
                await msg.reply('보이스채널에 있어야합니다')

        #Spell check command
        if msg.content.startswith("!검사") and msg.reference is not None:
            target_msg = await msg.channel.fetch_message(msg.reference.message_id)
            checked_spell = spell_check(utils.remove_markdown(target_msg.content))
            if checked_spell:
                await target_msg.reply(checked_spell)

        if msg.content.startswith("!검사 "):
            checked_spell = spell_check(utils.remove_markdown(msg.content[4:]))
            if checked_spell:
                await msg.reply(checked_spell)

        #Question
        if msg.content.startswith('!질문 '):
            await msg.delete()
            if re.compile('\d ').match(msg.content[4:6]):
                await msg.channel.send(f"***> {msg.author.name}***{question(msg.content[6:], msg.content[4])}")
            elif re.compile('\d\d ').match(msg.content[4:7]):
                if int(msg.content[4:6]) > 69:
                    await msg.channel.send('!질문 (1~69) (~하는 것)')
                else:
                    await msg.channel.send(f"***> {msg.author.name}***{question(msg.content[7:], msg.content[4:6])}")
            else:
                await msg.channel.send('!질문 (1~69) (~하는 것)')

class EmoteButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='바들바들동물콘',style=discord.ButtonStyle.green,row=0)
    async def button0(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(view=DropdownView(), ephemeral=True)
        self.value = True
        self.stop()

class Dropdown1(discord.ui.Select):
    def __init__(self):
        self.row = 0
        super().__init__(placeholder='기분을말해요', options=options1)
    
    async def callback(self, interaction: discord.Interaction):
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[self.values[0]]))

class Dropdown2(discord.ui.Select):
    def __init__(self):
        self.row = 1
        super().__init__(placeholder='대답해요', options=options2)
    
    async def callback(self, interaction: discord.Interaction):
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[self.values[0]]))

class Dropdown3(discord.ui.Select):
    def __init__(self):
        self.row = 2
        super().__init__(placeholder='생각을말해요', options=options3)
    
    async def callback(self, interaction: discord.Interaction):
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[self.values[0]]))

class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown1())
        self.add_item(Dropdown2())
        self.add_item(Dropdown3())

    # @discord.ui.button(label='기분을말해요',style=discord.ButtonStyle.blurple,row=0,disabled=True)
    # async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     self.children[1].disabled = False
    #     self.children[2].disabled = False
    #     button.disabled = True

    #     self.remove_item(self.children[3])
    #     self.add_item(Dropdown1())
    #     await interaction.response.edit_message(view=self)

bot = Bot()

#make embed includes image
def image_embed(author, url):
    embed = discord.Embed(color=author.color)
    embed.set_author(name=author.display_name, icon_url=author.avatar.url)
    embed.set_image(url=url)
    return embed

#log detail terminal and specific text channel
async def logging(detail):
    print(f"Logging: {detail}")
    await bot.get_channel(962604153891323934).send(str(detail))

#string to spell-checked string with discord markdown
def spell_check(str):
    str = str.replace('\n', "<br>")
    result = spell_checker.check(str)
    if result.errors == 0:
        return '감지된 오타가 없습니다.'
        
    rt_str = []
    for sentence in str.split(): #sentence
        check = spell_checker.check(sentence).words
        words = []
        for word, value in check.items(): #word = 비오듯, value = 1

            if word == "<span":
                continue
            if word[0:20] == "class='violet_text'>":
                words.append(f"~~{word[20:]}~~")
                continue

            #통과, 맞춤법, 띄어쓰기, 표준어, 통계적교정
            if value == 0 or value == 2:
                words.append(f"{word}")
            elif value == 1:
                words.append(f"**{word}**")
            else:
                words.append(f"[?]")
                
        words = " ".join(words)
        if len(check) != 1:
            rt_str.append(f"__{words}__")
        else:
            rt_str.append(f"{words}")
    
    rt_str = " ".join(rt_str)
    rt_str = html.unescape(rt_str).replace("<br>", "\n")
    rt_str = re.sub(r'<.*>', "", rt_str)
    return rt_str

bot.run(token)