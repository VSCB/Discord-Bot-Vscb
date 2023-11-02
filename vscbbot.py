import os
import discord
import requests
from discord.ext import commands
import yt_dlp

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
REGION = 'tr1'

data_dragon_url = "https://ddragon.leagueoflegends.com/cdn/11.8.1/data/en_US/champion.json"
response = requests.get(data_dragon_url)
champions_data = response.json()['data']

# Create a dictionary mapping champion IDs to names
id_to_champion_name = {v['key']: k for k, v in champions_data.items()}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

song_queue = []

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')
@bot.command()
async def lesgo(ctx, *, query: str):
    global song_queue

    if bot.voice_clients and ctx.voice_client and ctx.voice_client.is_playing():
        song_queue.append(query)
        await ctx.send(f"{query} added to queue!")
    else:
        await play_song(ctx, query)


async def play_song(ctx, song: str):
    global song_queue

    def after_play(error):
        check_queue(ctx)

    try:
        channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await channel.connect()
        voice_client = ctx.voice_client

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song}", download=False)
            url = info['entries'][0]['url']
            voice_client.play(
                discord.FFmpegPCMAudio(executable="ffmpeg", source=url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'),
                after=after_play
            )

    except yt_dlp.utils.DownloadError:
        await ctx.send("I can not play this video")
    except AttributeError:
        await ctx.send("You are not in a voice channel")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


def check_queue(ctx):
    global song_queue

    if song_queue:
        next_song = song_queue.pop(0)
        ctx.bot.loop.create_task(play_song(ctx, next_song))
def check_queue(ctx):
    global song_queue

    if song_queue:
        next_song = song_queue.pop(0)
        ctx.bot.loop.create_task(play_song(ctx, next_song))
@bot.command()
async def skip(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        return await ctx.send("I am not playing any music!")
    
    ctx.voice_client.stop()
    await ctx.send("Stopping the music")

@bot.command()
async def stop(ctx):
    global song_queue

    song_queue.clear()

    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("I shut down everything. Try hard mode!")
    else:
        await ctx.send("I am not playing any music!")

@bot.event
async def on_message(message):
    # Skip if the message author is the bot
    if message.author == bot.user:
        return

    # Check for the specific message content
    if message.content.lower() == 'let\'s play':
        modRoleID = '805899351313743873'  # Replace with your role ID
        await message.channel.send(f'<@&{modRoleID}> lets go guys!')
     
    # You can arrange the bot to play a yotube video for special message
    if 'ronaldo gülüşü' in message.content.lower():
        await message.channel.send("https://www.youtube.com/watch?v=r4Lee0gT0fU")

    # Or you can arrange the bot to respond with special tag 
    if message.content.lower() == 'o defter':
        DefterID = '729709281364017263'  # Replace with your role ID
        await message.channel.send(f'<@{DefterID}> kapandı kankaaa (Yusuf açar ama raad)')

    await bot.process_commands(message)

#This part gets username as input and gives the player's most played chanpions with points
@bot.command()
async def lolrank(ctx, summoner_name: str):

    
    # Fetch the Summoner's ID using their Name
    summoner_url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={RIOT_API_KEY}"
    response = requests.get(summoner_url)
    
    if response.status_code != 200:
        await ctx.send("Error fetching summoner data.")
        return

    summoner_data = response.json()
    summoner_id = summoner_data['id']

    # Fetch Ranked Stats
    ranked_url = f"https://{REGION}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={RIOT_API_KEY}"
    ranked_response = requests.get(ranked_url)
    ranked_data = ranked_response.json()

    # Fetch Champion Mastery (taking top 5 champions as an example)
    mastery_url = f"https://{REGION}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}?api_key={RIOT_API_KEY}"
    mastery_response = requests.get(mastery_url)
    mastery_data = mastery_response.json()[:5]

    # Format the data for display
    ranked_info = ranked_data[0] if ranked_data else {}
    tier = ranked_info.get('tier', 'UNRANKED')
    rank = ranked_info.get('rank', '')
    wins = ranked_info.get('wins', 0)
    losses = ranked_info.get('losses', 0)

    
    mastery_info = "\n".join([f"{id_to_champion_name.get(str(champ['championId']), champ['championId'])} - Level {champ['championLevel']} - {champ['championPoints']} points" for champ in mastery_data])

    message = f"**{summoner_name}'s Stats:**\n"
    message += f"**Ranked**: {tier} {rank} - {wins}W/{losses}L\n"
    message += f"**Top Champion Masteries**:\n{mastery_info}"

    await ctx.send(message)

# This part takes steam id as input and gives most played games of that id 
@bot.command()
async def mostplayed(ctx, steam_id: str, count: int = 5):
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&format=json&include_appinfo=1"
    response = requests.get(url)
    data = response.json()
    
    if 'games' in data['response']:
        # Sort games by playtime (in descending order)
        games = sorted(data['response']['games'], key=lambda x: x['playtime_forever'], reverse=True)
        
        # Limit the number of games based on the count provided
        games = games[:count]

        # Build and send the message
        message = f"**Top {count} Most Played Games for {steam_id}**\n"
        for game in games:
            game_name = game['name']
            playtime_hours = game['playtime_forever'] // 60  # Convert from minutes to hours
            message += f"{game_name}: {playtime_hours} hours\n"
        
        await ctx.send(message)
    else:
        await ctx.send(f"Could not find games for Steam ID: `{steam_id}`.")

#This part gives brief information about spesific user's steam account
@bot.command()
async def steaminfo(ctx, steam_id: str):
    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}"
    response = requests.get(url)
    data = response.json()
    
    if data['response']['players']:
        player = data['response']['players'][0]
        persona_name = player.get('personaname', 'N/A')
        real_name = player.get('realname', 'N/A')
        profile_url = player.get('profileurl', 'N/A')
        avatar_url = player.get('avatarfull', 'N/A')
        last_logoff = player.get('lastlogoff', 'N/A')
        country = player.get('loccountrycode', 'N/A')
        
        # Build and send the message
        message = f"**Steam Info for {persona_name}**\n"
        message += f"Real Name: {real_name}\n"
        message += f"Profile URL: {profile_url}\n"
        message += f"Country: {country}\n"
        message += f"Last Logoff (UNIX Timestamp): {last_logoff}\n"
        message += f"Avatar: {avatar_url}"
        await ctx.send(message)
    else:
        await ctx.send(f"Could not find details for Steam ID: `{steam_id}`.")

# This part is used for getting user's steam ids
@bot.command()
async def getsteamid(ctx, custom_url: str):
    url = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={STEAM_API_KEY}&vanityurl={custom_url}"
    response = requests.get(url)
    data = response.json()
    
    if data['response']['success'] == 1:
        steam_id = data['response']['steamid']
        await ctx.send(f"The Steam ID for the custom URL `{custom_url}` is: `{steam_id}`")
    else:
        await ctx.send(f"Could not find a Steam ID for the custom URL `{custom_url}`.")


bot.run(TOKEN)
