msg = "32145"
print('''await msg.channel.send(embed=image_embed(msg.author, f"https://cdn.discordapp.com/emojis/{msg.content.split(':')[2][:-1]}.png"))''')