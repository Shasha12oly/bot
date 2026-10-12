"""
Clear all global Discord commands
"""
import asyncio
import discord
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def clear_commands():
    """Clear all global commands"""
    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        print("Clearing all global commands...")

        # Clear all global commands
        try:
            tree = client.tree
            await tree.clear_commands(guild=None)
            await tree.sync()
            print("✅ All global commands cleared successfully!")
            print("⏱️ Please wait 5-10 minutes for Discord to process the changes")
            print("🔄 Then restart your bot to re-sync the current commands")
        except Exception as e:
            print(f"❌ Error clearing commands: {e}")

        await client.close()

    await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(clear_commands())
