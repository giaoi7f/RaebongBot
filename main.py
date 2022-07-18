import datetime
import html
import os
import random
import re
import sqlite3
import time

import discord
from discord import utils
from discord.ext import commands, tasks
from dotenv import load_dotenv

from emojiLink import (emoji_dict, emoji_names_answer, emoji_names_mood,
                       emoji_names_say)
from hanspell import spell_checker
from name import name_list

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
        
        await self.ban_word_refresh()

        global options1, options2, options3
        options1, options2, options3 = [], [], []
        for name in emoji_names_mood:
            options1.append(discord.SelectOption(label=name,value=name))
        for name in emoji_names_answer:
            options2.append(discord.SelectOption(label=name,value=name))
        for name in emoji_names_say:
            options3.append(discord.SelectOption(label=name,value=name))
        
        self.con = sqlite3.connect("userdata.db")
        self.c = self.con.cursor()
        self.scoring.start()
        self.daily_task.start()
    
    #History Daily apply
    @tasks.loop(hours=24)
    async def daily_task(self):
        print('DAILY TASK STARTED!')
        for data in self.c.execute(f"SELECT * FROM userdata").fetchall():
            self.c.execute(f"UPDATE userdata SET history='{'-'.join(data[2].split('-')[1:] + ['0'])}' WHERE id={data[0]}")
        self.con.commit()
        
    #History Daily apply Timer
    @daily_task.before_loop
    async def wait_until_midnight(self):
        now = datetime.datetime.now().astimezone()
        next_run = now.replace(hour=0, minute=0, second=0)
        if next_run < now:
            next_run += datetime.timedelta(days=1)
        print(next_run)
        await discord.utils.sleep_until(next_run)

    #Add scores loop all active user
    @tasks.loop(seconds=60)
    async def scoring(self):
        for voice in self.get_guild(700309048611831858).voice_channels:
            if voice.id != 700309931894767646:
                for member in voice.members:
                    self.c.execute(f"SELECT * FROM userdata WHERE id={member.id}")
                    if self.c.fetchone():
                        history = self.c.execute(f"SELECT * FROM userdata WHERE id={member.id}").fetchone()[2].split('-')
                        history[-1] = str(int(history[-1]) + 1)
                        self.c.execute(f"UPDATE userdata SET history='{'-'.join(history)}' WHERE id={member.id}")
                        self.c.execute(f"UPDATE userdata SET score=score+1 WHERE id={member.id}")
                    else:
                        self.c.execute(f"UPDATE userdata SET history='0-0-0-0-0-0-0' WHERE id={member.id}")
                        self.c.execute(f"UPDATE userdata SET score=1 WHERE id={member.id}")
        self.con.commit()

    async def ban_word_refresh(self):
        self.ban = []
        async for message in self.get_channel(982274318522277948).history(limit=200):
            self.ban.append(message.content)

    async def on_message(self, msg):
        if msg.author.bot or msg.author.id == self.user.id:
            return

        print(f"msg.content: '{msg.content}'")

        #Ban words
        for ban in self.ban:
            if ban in msg.content:
                await msg.delete()
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
        
        #Banword refresh
        if msg.content == '!금칙어':
            await msg.delete()
            await self.ban_word_refresh()
            ban = ", ".join(self.ban)
            await msg.channel.send(f"```diff\n- 금칙어\n{ban}```")
            return

        #All Players Ranking
        if msg.content == '!랭킹':
            await msg.delete()
            embed = discord.Embed(title="⏱1분당 1포인트 획득 가능", color=0x00ffb3)
            embed.set_author(name="포인트 랭킹", icon_url=msg.author.avatar.url)
            field_value = []
            for user_id, user_score, _ in self.c.execute(f"SELECT * FROM userdata ORDER BY score DESC LIMIT 20").fetchall():
                if user_score%60 > 9:
                    field_value.append(f"`{user_score}`<@{user_id}> - **[{int(user_score/60)}시간 {user_score%60}분]**")
                else:
                    field_value.append(f"`{user_score}`<@{user_id}> - **[{int(user_score/60)}시간 0{user_score%60}분]**")
            embed.add_field(name="TOP 20", value="\n".join(field_value))
            embed.set_footer(text="✓사용법: !랭킹")
            await msg.channel.send(embed=embed)
            return

        #View Self Rank
        # c.execute(f"SELECT * FROM userdata WHERE id={}").fetchall()
        if msg.content == '!플탐':
            await msg.delete()
            await msg.channel.send(make_graph(self.c.execute(f"SELECT * FROM userdata WHERE id={msg.author.id}").fetchone()[2], msg.author.id))
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
            return

        #Spell check command
        if msg.content.startswith("!검사") and msg.reference is not None:
            target_msg = await msg.channel.fetch_message(msg.reference.message_id)
            checked_spell = spell_check(utils.remove_markdown(target_msg.content))
            if checked_spell:
                await target_msg.reply(checked_spell)
            return

        if msg.content.startswith("!검사 "):
            checked_spell = spell_check(utils.remove_markdown(msg.content[4:]))
            if checked_spell:
                await msg.reply(checked_spell)
            return

        #Remove message
        if msg.content == '!제거' or msg.content == '!삭제':
            await msg.delete()
            if msg.reference is None:
                await msg.channel.send(':information_source: **`답장`**기능과 함께 사용해주세요')
                return
            if not msg.guild.get_member(msg.author.id).guild_permissions.manage_messages:
                await msg.channel.send(':no_entry: **메세지 관리** 권한이 없습니다')
                return
            reference = await msg.channel.fetch_message(msg.reference.message_id)
            history = msg.channel.history(before=msg, after=reference)
            message_list = [message async for message in history] + [reference]
            message_list_num = len(message_list)
            if message_list_num > 99:
                await msg.channel.send(':no_entry: 최대 100개의 메세지를 삭제할 수 있습니다')
                return
            await msg.channel.send(f'<@{msg.author.id}>: **{msg.channel.name}**에서 메세지 **`{message_list_num}`**개를 삭제했습니다.')
            await msg.channel.delete_messages(message_list)
            return
        

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

def make_graph(user_history, user_id):
    history = [0, 0, 0, 0, 0, 0, 0]
    for index, num in enumerate(reversed(user_history.split('-'))):
        history[-index-1] = int(num)
    mult = sorted(history)[6]/6
    n = []
    for i in range(1, 7):
        m = []
        for j in history:
            if j >= i*mult:
                m.append(' ▉')
            else:
                m.append(' ㅤ')
        row = int(i*mult/60)
        if row > 9:
            n.append(f"{str(row)}시간{''.join(m)}")
        else:
            n.append(f"{str(row)}시간 {''.join(m)}")
    n.reverse()
    week = ['월', '화', '수', '목', '금', '토', '일']
    weekday = datetime.datetime.today().weekday() + 1
    week = week[weekday:]+week[:weekday]
    return f":globe_with_meridians: **최근 액티브타임 [<@{str(user_id)}> <t:{int(time.time())}:D>]**```\n"+ '\n'.join(n) + f"\nㅤ     {' '.join(week)}```"

bot.run(token)
