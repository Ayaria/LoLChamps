#bot2.py
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
from riotwatcher import LolWatcher, ApiError
import pandas as pd
import plotly.figure_factory as ff
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# Update Riot API Key Manually
RIOT_API = os.getenv('RIOT_KEY')
watcher = LolWatcher(RIOT_API)
my_region = 'na1'
# Version
latest = watcher.data_dragon.versions_for_region(my_region)['n']['champion']
# Champion Dictionary
static_champ_list = watcher.data_dragon.champions(latest, False, 'en_US')
champ_dict = {}
for i in static_champ_list['data']:
    champ = static_champ_list['data'][i]
    champ_dict[champ['key']] = champ['id']
# Summoner Spell Dictionary
spell_dict = {}
static_spell_list = watcher.data_dragon.summoner_spells(latest)
for i in static_spell_list['data']:
    spell = static_spell_list['data'][i]
    spell_dict[spell['key']] = spell['name']
# Item Dictionary
item_dict = {}
static_item_list = watcher.data_dragon.items(latest)
for i in static_item_list['data']:
    item = static_item_list['data'][i]
    item_dict[i] = item['name']

bot = commands.Bot(command_prefix='!')
@bot.command(name='bday', help='Responds with a birthday message')
async def bday(ctx):
    await ctx.send(content=f'Happy Birthday!! <:eyes:294956739688923136>', file=discord.File('birthday.jpg'))

@bot.command(name='roll', help='Rolls a number between 1 and the given number. If no input is given, then default is 100')
async def roll(ctx, num=100):
    await ctx.send(random.randint(1, int(num)))

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!') 

@bot.command(name='create-channel', help="Creates a channel with the given input. If no input is given, default is 'garbage'.")
@commands.has_role('admin')
async def create_channel(ctx, channel_name='garbage'):
    guild = ctx.guild
    channel = discord.utils.get(guild.channels, name=channel_name)
    if not channel:
        print(f'Creating a new channel: {channel_name}')
        await guild.create_text_channel(channel_name)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send("You do not have the correct role for this command.")

@bot.command(name='champ', help="Gives the information of a specific league champion, e.g. !champ Katarina.")
async def champ(ctx, champ=False):
    if champ == False:
        await ctx.send(content='Please specify a champion, e.g. !lol Katarina')
        return
    
@bot.command(name='sr', help="Gives data using the specified summoner.")
async def sr(ctx, smr):
    try:
        response = watcher.summoner.by_name(my_region, smr)
    except ApiError as err:
        if err.response.status_code == 429:
            await ctx.send(content='We should retry in {} seconds'.format(err.response.headers['Retry-After']))
            await ctx.send(content='this retry-after is handled by default by the RiotWatcher library')
            await ctx.send(content='future requests wait until the retry-after time passes')
            print('We should retry in {} seconds.'.format(err.response.headers['Retry-After']))
            print('this retry-after is handled by default by the RiotWatcher library')
            print('future requests wait until the retry-after time passes')
        elif err.response.status_code == 404:
            await ctx.send(content=f'Summoner {smr} not found.')
            print(f'Summoner {smr} not found.')
        else:
            raise
        
    ranked = watcher.league.by_summoner(my_region, response['id'])[0]
    tier = ranked['tier']
    rank = ranked['rank']
    lp = ranked['leaguePoints']
    wins = ranked['wins']
    losses = ranked['losses']
    winrate = int(wins / (wins + losses) * 100)
    name = response['name']
    await ctx.send(content=f'{name}: {tier} {rank} {lp}LP')
    await ctx.send(content=f'W/L: {wins}W {losses}L {winrate}%WR')
    my_matches = watcher.match.matchlist_by_account(my_region, response['accountId'])
    length = min(3, len(my_matches['matches']))
    if length == 0:
        await ctx.send(content='No Match History')
        return
    for i in range(1, length+1):
        match = my_matches['matches'][i-1]
        match_detail = watcher.match.by_id(my_region, match['gameId'])
        sumNames = []
        for summoner in match_detail['participantIdentities']:
            sumNames.append(summoner['player']['summonerName'])
        participants = []
        for row in match_detail['participants']:
            player_row = {}
            player_row["Name"] = sumNames[0]
            sumNames.pop(0)
            player_row['Champion'] = champ_dict[str(row['championId'])]
            player_row['Spell1'] = spell_dict[str(row['spell1Id'])]
            player_row['Spell2'] = spell_dict[str(row['spell2Id'])]
            player_row['Win'] = row['stats']['win']
            player_row['KDA'] = str(row['stats']['kills']) + "/" + str(row['stats']['deaths']) + "/" + str(row['stats']['assists'])
            player_row['Damage'] = row['stats']['totalDamageDealt']
            player_row['Gold'] = row['stats']['goldEarned']
            player_row['Level'] = row['stats']['champLevel']
            player_row['CS'] = row['stats']['totalMinionsKilled']
            #player_row['item0'] = item_dict[str(row['stats']['item0'])]
            #player_row['item1'] = item_dict[str(row['stats']['item1'])]
            #player_row['item2'] = item_dict[str(row['stats']['item2'])]
            #player_row['item3'] = item_dict[str(row['stats']['item3'])]
            #player_row['item4'] = item_dict[str(row['stats']['item4'])]
            #player_row['item5'] = item_dict[str(row['stats']['item5'])]
            participants.append(player_row)
        # print dataframe
        df = pd.DataFrame(participants)
        fig = ff.create_table(df)
        fig.update_layout(width=1500)
        fig.write_image("table.png", scale=2)
        print(df)
        await ctx.send(content=f'Match {i}')
        await ctx.send(file=discord.File("table.png")) #content=df

bot.run(TOKEN)