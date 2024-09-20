import discord
import os
from discord.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv 

# loading variables from .env file
load_dotenv()

# Setup MongoDB connection
client = MongoClient(os.getenv("CONNECTION_STRING"))
db = client['SpotBot']
collection = db['Spots']

# Create bot instance
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)  # Empty prefix means no "!"

# Function to increment both Spot and Caught counts
def update_spot_and_caught(spotter_id: int, caught_id: int):
    # Increment the "Spots" for the spotter
    collection.update_one(
        {'_id': spotter_id},
        {'$inc': {'Spots': 1}},
        upsert=True
    )
    
    # Increment the "Caughts" for the caught user
    collection.update_one(
        {'_id': caught_id},
        {'$inc': {'Caughts': 1}},
        upsert=True
    )

# React to "Spotted @[username]" message and update database
@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Handling "Spotted" messages
    if "Spotted" in message.content and message.mentions:
        # Check if an image is attached
        if message.attachments:
            for mentioned_user in message.mentions:
                # Update Spots for the spotter and Caughts for the mentioned user
                update_spot_and_caught(message.author.id, mentioned_user.id)

                # React to the message
                await message.add_reaction('✅')
        else:
            await message.channel.send("Please include an image with your spot!")
        return  # Exit after handling the "Spotted" message

    # Handling custom commands for SpotList and CaughtList
    if message.content.lower() == "spotlist":
        await send_spotlist(message.channel)
        return  # Exit after sending the SpotList
    elif message.content.lower() == "caughtlist":
        await send_caughtlist(message.channel)
        return  # Exit after sending the CaughtList

    # If none of the above conditions are met, don't process the message as a command
    # This prevents normal messages from being processed as commands
    return


# Function to send the SpotList leaderboard
async def send_spotlist(channel):
    top_spotters = collection.find().sort('Spots', -1).limit(5)
    leaderboard = "Top 5 Spotters:\n"
    
    for index, user in enumerate(top_spotters, start=1):
        member = await bot.fetch_user(user['_id'])
        spots_count = user.get('Spots', 0)  # Use get() to handle missing 'Spots' field
        leaderboard += f"{index}. {member.display_name} - {spots_count} Spots\n"
    
    await channel.send(leaderboard)


# Function to send the CaughtList leaderboard
async def send_caughtlist(channel):
    top_caughts = collection.find().sort('Caughts', -1).limit(5)
    leaderboard = "Top 5 Caught Users:\n"
    
    for index, user in enumerate(top_caughts, start=1):
        member = await bot.fetch_user(user['_id'])
        caughts_count = user.get('Caughts', 0)  # Use get() to handle missing 'Spots' field
        leaderboard += f"{index}. {member.display_name} - {caughts_count} Caughts\n"
    
    await channel.send(leaderboard)

# Run bot
bot.run(os.getenv("MY_KEY"))
