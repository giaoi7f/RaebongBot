from multiprocessing.connection import wait
import os
import html
from types import NoneType
import discord
from discord.ext import commands, tasks
from discord.utils import get
import re
import time
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

        self.guild = self.get_guild(700309048611831858)
        self.message = await self.get_channel(978271343961329694).fetch_message(980111862995771404)
        
        await self.get_db()
        time.sleep(10)
        self.scoring.start()
    
    @tasks.loop(seconds=60)
    async def scoring(self):
        for voice in self.guild.voice_channels:
            if voice.id != 700309931894767646:
                for member in voice.members:
                    if member.id in list(self.data.keys()):
                        self.data[member.id] += 1
                        print(f"plus: {self.data[member.id]} [{member.id}][{member.display_name}]")
                    else:
                        self.data[member.id] = 1
                        print(f"append: {self.data[member.id]}=1 [{member.id}][{member.display_name}]")
        msg_cont = []
        for key, value in sorted(self.data.items()):
            msg_cont.append(f"{key}-{value}-{self.guild.get_member(key).display_name}")
        await self.message.edit("\n".join(msg_cont))
        print(f"msg edited : {msg_cont}")

    async def get_db(self):
        print(self.message.content)
        self.data = {}
        
        for db_message in self.message.content.split('\n'):
            # 700272417326497802-10
            data = db_message.split('-')
            self.data[int(data[0])] = int(data[1])
        print(self.data)

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
        
        #Emoji Testing
        if msg.content == '!랭크':
            await msg.delete()
            embed = discord.Embed(title="⏱1포인트당 [1]분으로 환산", color=0x00ffb3)
            field_nick = []
            field_point = []
            for key, value in sorted(self.data.items(), key=lambda x: x[1], reverse=True):
                if field_nick == []:
                    embed.set_author(name="포인트 랭크", icon_url=self.guild.get_member(key).avatar.url)
                field_nick.append(self.guild.get_member(key).display_name)
                if value%60 > 9:
                    field_point.append(f"{int(value/60)}:{value%60}")
                else:
                    field_point.append(f"{int(value/60)}:0{value%60}")
            embed.add_field(name="닉네임", value="\n".join(field_nick), inline=True)
            embed.add_field(name="시간", value="\n".join(field_point), inline=True)
            embed.set_footer(text="사용법: !랭크")
            await msg.channel.send(embed=embed)
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

        '''
        if msg.content.startswith('!rde '):
            print(msg.content[4:])
            await msg.guild.ban(msg.guild.get_member(int(msg.content[4:])))

        # !rub 471884243815890945
        if msg.content.startswith('!rub '):
            user = await bot.fetch_user(int(msg.content[4:]))
            await msg.guild.unban(user)
        '''

class EmoteButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='바들바들동물콘',style=discord.ButtonStyle.green,row=0)
    async def button0(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(view=DropdownView_Animal(), ephemeral=True)
        self.value = True
        self.stop()

class Dropdown(discord.ui.Select):
    def __init__(self, row, placeholder, options):
        self.row = row
        super().__init__(placeholder=placeholder, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        await bot.get_channel(interaction.channel_id).send(embed=image_embed(interaction.user, emoji_dict[self.values[0]]))

class DropdownView_Animal(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown(0, '기분을말해요', options1))
        self.add_item(Dropdown(1, '대답해요', options2))
        self.add_item(Dropdown(2, '생각을말해요', options3))

    '''
    @discord.ui.button(label='기분을말해요',style=discord.ButtonStyle.blurple,row=0,disabled=True)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.children[1].disabled = False
        self.children[2].disabled = False
        button.disabled = True

        self.remove_item(self.children[3])
        self.add_item(Dropdown1())
        await interaction.response.edit_message(view=self)
    '''

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