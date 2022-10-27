
import datetime
import os
import re
import sqlite3
import time

import discord
from discord import FFmpegOpusAudio, NotFound, app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from track import album, all_album, names

from emojiLink import emoji_dict

emoji_regex = re.compile(r'<:\w*:\d*>')
mention_regex = re.compile('<@(?P<ID>[0-9]+)>')
emoticon_regex = re.compile('<:(?P<NAME>.+):(?P<ID>[0-9]+)>')

load_dotenv()
TOKEN = os.environ.get('token')
GUILD = discord.Object(id=os.environ.get('guild'))

class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=".", intents=discord.Intents.all())

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync()

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name="진화"))
        
        self.con = sqlite3.connect("userdata.db")
        self.c = self.con.cursor()
        self.scoring.start()
        self.daily_task.start()

        self.queue = []

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
        print("minute loop")
        if not self.queue:
            for guild in self.guilds:
                await guild.get_member(bot.application_id).move_to(None)

        for member in self.get_guild(700309048611831858).members:
            if not member.voice:
                continue
            if member.voice.afk:
                continue
            self.c.execute(f"SELECT * FROM userdata WHERE id={member.id}")
            if self.c.fetchone():
                history = self.c.execute(f"SELECT * FROM userdata WHERE id={member.id}").fetchone()[2].split('-')
                history[-1] = str(int(history[-1]) + 1)
                self.c.execute(f"UPDATE userdata SET history='{'-'.join(history)}' WHERE id={member.id}")
                self.c.execute(f"UPDATE userdata SET score=score+1 WHERE id={member.id}")
            else:
                self.c.execute(f"UPDATE userdata SET history='0-0-0-0-0-0-0-0-0-0-0-0-0-0' WHERE id={member.id}")
                self.c.execute(f"UPDATE userdata SET score=1 WHERE id={member.id}")
        self.con.commit()
        
    async def on_message(self, msg):
        # Except invalid user and logging msg
        if msg.author.bot or msg.author.id == self.user.id:
            return
        print(f"[{msg.author}]: \"{msg.content}\"")

        # Enlarge emoticon with image_embed
        if msg.content.startswith('<:'):
            emoji = emoji_regex.findall(msg.content)[0]
            if emoji == msg.content:
                await msg.delete()
                await msg.channel.send(embed=image_embed(
                        msg.author, f"https://cdn.discordapp.com/emojis/{msg.content.split(':')[2][:-1]}.png"))
                return

        # Direct Emoji command
        if msg.content in emoji_dict:
            await msg.delete()
            await msg.channel.send(embed=image_embed(msg.author, emoji_dict[msg.content]))
            return

bot = Bot()

#make embed includes image
def image_embed(author, url):
    embed = discord.Embed(color=author.color)
    embed.set_author(name=author.display_name, icon_url=author.avatar.url)
    embed.set_image(url=url)
    return embed

def make_graph(user_history, user_id):
    history = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for index, num in enumerate(reversed(user_history.split('-'))):
        history[-index-1] = int(num)
    mult = sorted(history)[13]/10
    n = []
    for i in range(1, 11):
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
    week = ['월', '화', '수', '목', '금', '토', '일', '월', '화', '수', '목', '금', '토', '일']
    weekday = datetime.datetime.today().weekday() + 1
    week = week[weekday:]+week[:weekday]
    return f":globe_with_meridians: **최근 액티브타임 [<@{str(user_id)}> <t:{int(time.time())}:D>]**```\n"+ '\n'.join(n) + f"\nㅤ     {' '.join(week)}```"

@bot.tree.command()
async def 랭킹(interaction: discord.Interaction) -> None:
    """디코 지박령들을 일렬로 세워서 누가 더 병1신3인8지 알아보아요"""
    c = sqlite3.connect("userdata.db").cursor()
    embed = discord.Embed(title="⏱1분당 1포인트 획득 가능", color=0x00ffb3)
    embed.set_author(name="포인트 랭킹", icon_url=interaction.user.avatar.url)
    field_value = []
    for user_id, user_score, _ in c.execute(f"SELECT * FROM userdata ORDER BY score DESC LIMIT 20").fetchall():
        if user_score%60 > 9:
            field_value.append(f"`{user_score}`<@{user_id}> - **[{int(user_score/60)}시간 {user_score%60}분]**")
        else:
            field_value.append(f"`{user_score}`<@{user_id}> - **[{int(user_score/60)}시간 0{user_score%60}분]**")
    embed.add_field(name="TOP 20", value="\n".join(field_value))
    await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def 플탐(interaction: discord.Interaction) -> None:
    """최근 14일동안의 시간을 갈아넣은걸 한 눈으로 볼 수 있어요"""
    c = sqlite3.connect("userdata.db").cursor()
    await interaction.response.send_message(make_graph(c.execute(f"SELECT * FROM userdata WHERE id={interaction.user.id}").fetchone()[2], interaction.user.id))

@bot.tree.command()
@app_commands.describe(number='메세지 개수(1000개 이하)를 입력하거나 메세지 ID를 입력하세요')
async def 청소(interaction: discord.Interaction, number: str) -> None:
    """꼴도보기 싫은 족깣튼 메세지들을 한 방에 청소할 수 있ㅇ요"""
    if not interaction.guild.get_member(interaction.user.id).guild_permissions.manage_messages:
        await interaction.response.send_message(':no_entry: **메세지 관리** 권한이 없습니다', ephemeral=True)
        return
            
    if not number.isdecimal():
        await interaction.response.send_message(':no_entry: 파라미터는 정수 형태여야 합니다', ephemeral=True)
        return

    number = abs(int(number))
    if number > 1001:
        try:
            reference = await interaction.channel.fetch_message(number)
            history = interaction.channel.history(before=interaction.message, after=reference)
            message_list = [message async for message in history] + [reference]
            number = len(message_list)
        except(NotFound):
            await interaction.response.send_message(':no_entry: ID와 일치하는 메세지를 찾을 수 없습니다', ephemeral=True)
            return
    
    channel = bot.get_channel(interaction.channel.id)
    user_id = interaction.user.id
    await interaction.response.send_message(f"메세지 **`{number}`**개를 삭제합니다", ephemeral=True)
    await interaction.channel.purge(limit=number)
    await channel.send(f"<@{user_id}>: **{channel.name}**에서 메세지 **`{number}`**개를 삭제했습니다")

# M U S I C P L A Y E R

async def join(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.get_member(bot.application_id).move_to(interaction.user.voice.channel)
    else:
        try:
            await interaction.user.voice.channel.connect(self_deaf=True)
        except:
            await interaction.response.send_message(":x: 음성 채널을 찾을 수 없습니다 (보이스 채널 재접하면 해결됨)", ephemeral=True)

def check_playing(vc):
    try:
        return vc.is_playing()
    except:
        return True

def full_album(vc, name):
    for track in all_album[name]:
        bot.queue.append(f"./tracks/{name}/{track}.opus")
    if not check_playing(vc):
        print(bot.queue)
        vc.play(FFmpegOpusAudio(bot.queue[0]), after=lambda e: play_next(vc))

def play(vc, path):
    # path = "./tracks/그나음그/56.opus"
    bot.queue.append(path)
    if not check_playing(vc):
        print(bot.queue)
        vc.play(FFmpegOpusAudio(path), after=lambda e: play_next(vc))

def play_next(vc):
    print(bot.queue)
    if bot.queue:
        del bot.queue[0]
        if bot.queue:
            vc.play(FFmpegOpusAudio(bot.queue[0]), after=lambda e: play_next(vc))
            return

@bot.tree.command()
async def 넘기기(interaction: discord.Interaction) -> None:
    """다음 곡으로 넘겨요"""
    try:
        vc = interaction.guild.voice_client
        await vc.stop()
        play_next(vc)
    except TypeError or AttributeError:
        pass
    await interaction.response.send_message(f":track_next: **다음 곡으로 넘깁니다**\n>    남은 곡: `{len(bot.queue)-1}`개")

@bot.tree.command()
async def 끄기(interaction: discord.Interaction) -> None:
    """레봉의 작고 소중한 주크박스를 벌집으로 만들어요"""
    await interaction.guild.get_member(bot.application_id).move_to(None)
    await interaction.response.send_message("뽀각")
    try:
        vc = interaction.guild.voice_client
        bot.queue = []
        await vc.stop()
    except TypeError:
        pass

@bot.tree.command()
async def 곡정보(interaction: discord.Interaction) -> None:
    """현재 재생되는 곡의 정보를 돚거해와요"""
    if bot.queue:
        info = bot.queue[0].split('/') #['.', 'tracks', '싱글', 'チノカテ.opus']
        album = info[2]
        title = info[3][:-5]
        description = names[title]
        print(title)
        print(description)
        index = all_album[album].index(title)
        image = discord.File(f"./tracks/{album}.jpg", filename="image.jpg")
        embed = discord.Embed(title=title, description=description, color=interaction.user.color)
        embed.set_author(name=f"{album} {index+1}번 트랙", icon_url="https://i.imgur.com/eB4ivNH.jpg")
        embed.set_image(url="attachment://image.jpg")
        embed.set_footer(text=f"남은 곡: `{len(bot.queue)-1}`개")
        await interaction.response.send_message(file=image, embed=embed)
    else:
        await interaction.response.send_message("재생목록이 비어있어요", ephemeral=True)

@bot.tree.command()
@app_commands.describe(track='트랙을 재생목록에 추가해요. 빈 칸으로 두면 전체 추가')
async def 요루시카_여름풀(interaction: discord.Interaction, track: album['여름풀']="[ALL]") -> None:
    """[2017 1st Mini Album] 夏草が邪魔をする"""
    await join(interaction)
    if track == "[ALL]":
        full_album(interaction.guild.voice_client, '여름풀')
        await interaction.response.send_message(f":musical_note:  **여름풀**의 **`{len(all_album['여름풀'])}`**곡이 추가됨")
    else:
        play(interaction.guild.voice_client, f"./tracks/여름풀/{track}.opus")
        await interaction.response.send_message(f":musical_note:  **여름풀이 방해를 해** - **`{track}`**")

@bot.tree.command()
@app_commands.describe(track='트랙을 재생목록에 추가해요. 빈 칸으로 두면 전체 추가')
async def 요루시카_마케이누(interaction: discord.Interaction, track: album['마케이누']="[ALL]") -> None:
    """[2018 2nd Mini Album] 負け犬にアンコールはいらない"""
    await join(interaction)
    if track == "[ALL]":
        full_album(interaction.guild.voice_client, '마케이누')
        await interaction.response.send_message(f":musical_note:  **마케이누**의 **`{len(all_album['마케이누'])}`**곡이 추가됨")
    else:
        play(interaction.guild.voice_client, f"./tracks/마케이누/{track}.opus")
        await interaction.response.send_message(f":musical_note:  **패배자에게 앵콜은 필요 없어** - **`{track}`**")

@bot.tree.command()
@app_commands.describe(track='트랙을 재생목록에 추가해요. 빈 칸으로 두면 전체 추가')
async def 요루시카_그나음그(interaction: discord.Interaction, track: album['그나음그']="[ALL]") -> None:
    """[2019 1st Full Album] だから僕は音楽を辞めた"""
    await join(interaction)
    if track == "[ALL]":
        full_album(interaction.guild.voice_client, '그나음그')
        await interaction.response.send_message(f":musical_note:  **그나음그**의 **`{len(all_album['그나음그'])}`**곡이 추가됨")
    else:
        play(interaction.guild.voice_client, f"./tracks/그나음그/{track}.opus")
        await interaction.response.send_message(f":musical_note:  **그래서 나는 음악을 그만두었다** - **`{track}`**")

@bot.tree.command()
@app_commands.describe(track='트랙을 재생목록에 추가해요. 빈 칸으로 두면 전체 추가')
async def 요루시카_엘마(interaction: discord.Interaction, track: album['엘마']="[ALL]") -> None:
    """[2019 2nd Full Album] エルマ"""
    await join(interaction)
    if track == "[ALL]":
        full_album(interaction.guild.voice_client, '엘마')
        await interaction.response.send_message(f":musical_note:  **엘마**의 **`{len(all_album['엘마'])}`**곡이 추가됨")
    else:
        play(interaction.guild.voice_client, f"./tracks/엘마/{track}.opus")
        await interaction.response.send_message(f":musical_note:  **엘마** - **`{track}`**")
    
@bot.tree.command()
@app_commands.describe(track='트랙을 재생목록에 추가해요. 빈 칸으로 두면 전체 추가')
async def 요루시카_도작(interaction: discord.Interaction, track: album['도작']="[ALL]") -> None:
    """[2020 3rd Full Album] 盗作"""
    await join(interaction)
    if track == "[ALL]":
        full_album(interaction.guild.voice_client, '도작')
        await interaction.response.send_message(f":musical_note:  **도작**의 **`{len(all_album['도작'])}`**곡이 추가됨")
    else:
        play(interaction.guild.voice_client, f"./tracks/도작/{track}.opus")
        await interaction.response.send_message(f":musical_note:  **도작** - **`{track}`**")

@bot.tree.command()
@app_commands.describe(track='트랙을 재생목록에 추가해요. 빈 칸으로 두면 전체 추가')
async def 요루시카_전세(interaction: discord.Interaction, track: album['전세']="[ALL]") -> None:
    """[2021 Live] 前世"""
    await join(interaction)
    if track == "[ALL]":
        full_album(interaction.guild.voice_client, '전세')
        await interaction.response.send_message(f":musical_note:  **전세**의 **`{len(all_album['전세'])}`**곡이 추가됨")
    else:
        play(interaction.guild.voice_client, f"./tracks/전세/{track}.opus")
        await interaction.response.send_message(f":musical_note:  **전세** - **`{track}`**")

@bot.tree.command()
@app_commands.describe(track='트랙을 재생목록에 추가해요. 빈 칸으로 두면 전체 추가')
async def 요루시카_창작(interaction: discord.Interaction, track: album['창작']="[ALL]") -> None:
    """[2021 3rd Mini Album] 創作"""
    await join(interaction)
    if track == "[ALL]":
        full_album(interaction.guild.voice_client, '창작')
        await interaction.response.send_message(f":musical_note:  **창작**의 **`{len(all_album['창작'])}`**곡이 추가됨")
    else:
        play(interaction.guild.voice_client, f"./tracks/창작/{track}.opus")
        await interaction.response.send_message(f":musical_note:  **창작** - **`{track}`**")

@bot.tree.command()
@app_commands.describe(track='트랙을 재생목록에 추가해요. 빈 칸으로 두면 전체 추가')
async def 요루시카_싱글(interaction: discord.Interaction, track: album['싱글']="[ALL]") -> None:
    """[2021~ Single]"""
    await join(interaction)
    if track == "[ALL]":
        full_album(interaction.guild.voice_client, '싱글')
        await interaction.response.send_message(f":musical_note:  **싱글**의 **`{len(all_album['싱글'])}`**곡이 추가됨")
    else:
        play(interaction.guild.voice_client, f"./tracks/싱글/{track}.opus")
        await interaction.response.send_message(f":musical_note:  싱글 - **`{track}`**")

@bot.tree.command()
@app_commands.describe(track='트랙을 재생목록에 추가해요. 빈 칸으로 두면 전체 추가')
async def 요루시카_월광(interaction: discord.Interaction, track: album['월광']="[ALL]") -> None:
    """[2022 Live] 月光"""
    await join(interaction)
    if track == "[ALL]":
        full_album(interaction.guild.voice_client, '월광')
        await interaction.response.send_message(f":musical_note:  **월광**의 **`{len(all_album['월광'])}`**곡이 추가됨")
    else:
        play(interaction.guild.voice_client, f"./tracks/월광/{track}.opus")
        await interaction.response.send_message(f":musical_note:  **월광 재연** - **`{track}`**")


bot.run(TOKEN)