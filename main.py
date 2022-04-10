import os, discord, re
from dotenv import load_dotenv

client = discord.Client()
emojiRegex = re.compile(r'<:\w*:\d*>')

@client.event
async def on_ready():
    print(f'{client.user}로 로그인함')
    await client.change_presence(activity=discord.Game(name="광질"))

@client.event
async def on_message(msg):
    if msg.author.bot:
        return
    if msg.content.startswith('<:'):
        emoji = emojiRegex.findall(msg.content)[0]
        if emoji == msg.content:
            await msg.delete()
            url = f"https://cdn.discordapp.com/emojis/{msg.content.split(':')[2][:-1]}.png"
            embed = discord.Embed(color=msg.author.color)
            embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
            embed.set_image(url=url)
            await msg.channel.send(embed=embed)

load_dotenv()
client.run(os.environ.get('token'))