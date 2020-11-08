# bot.py

import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
intents = discord.Intents.default()
intents.members = True  
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, id=int(GUILD))
    print(f'{client.user} has connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})')
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')

@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(f'Hi {member.name}, welcome to the test server!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == 'lorem ipsum':
        await message.channel.send(content='lorem ipsum copypasta goes here')
    if 'happy birthday' in message.content.lower():
        await message.channel.send(content=f'Happy Birthday!! <:eyes:294956739688923136>', file=discord.File('birthday.jpg'))

client.run(TOKEN)
