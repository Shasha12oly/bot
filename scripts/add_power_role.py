"""
Add Power Role Script
Creates a special "Power" role with cool styling
"""

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============ CONFIGURATION ============
GUILD_ID = int(os.getenv("SETUP_GUILD_ID", "0"))  # Your server ID
# ========================================


class PowerRoleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(f"✅ Bot logged in as {self.user}")

    async def on_ready(self):
        print(f"\n{'='*70}")
        print("⚡ ADD POWER ROLE SCRIPT")
        print(f"{'='*70}\n")

        if GUILD_ID == 0:
            print("❌ ERROR: GUILD_ID not set in configuration!")
            await self.close()
            return

        guild = self.get_guild(GUILD_ID)
        if not guild:
            print(f"❌ ERROR: Bot is not in guild with ID {GUILD_ID}")
            await self.close()
            return

        print(f"📋 Guild: {guild.name} (ID: {guild.id})")

        # Check if Power role already exists
        existing_role = discord.utils.get(guild.roles, name="⚡ Power")
        if existing_role:
            print(f"⚠️  Power role already exists (ID: {existing_role.id})")
            print(f"💡 If you want to recreate it, delete it first and run this script again")
            await self.close()
            return

        # Create Power role
        try:
            power_role = await guild.create_role(
                name="⚡ Power",
                color=discord.Color.from_rgb(255, 0, 255),  # Magenta
                hoist=True,
                mentionable=True,
                permissions=discord.Permissions(
                    administrator=True,
                    manage_guild=True,
                    manage_roles=True,
                    manage_channels=True,
                    manage_messages=True,
                    kick_members=True,
                    ban_members=True,
                    moderate_members=True,
                    view_audit_log=True,
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    add_reactions=True,
                    use_external_emojis=True,
                    connect=True,
                    speak=True,
                    stream=True,
                    priority_speaker=True,
                    read_message_history=True,
                    manage_threads=True,
                    create_public_threads=True,
                    create_private_threads=True,
                    send_messages_in_threads=True
                ),
                reason="Creating special Power role"
            )

            print(f"✅ Created: ⚡ Power (ID: {power_role.id})")
            print(f"\n💡 This role has:")
            print(f"   • Magenta color (RGB: 255, 0, 255)")
            print(f"   • Hoisted (displayed separately)")
            print(f"   • Mentionable")
            print(f"   • Full administrator permissions")
            print(f"   • Priority speaker in voice")

            print(f"\n⭐ Add this to your .env if you want to use it:")
            print(f"   POWER_ROLE_ID={power_role.id}")

        except Exception as e:
            print(f"❌ Error creating Power role: {e}")

        print(f"\n{'='*70}\n")
        await self.close()


async def main():
    bot = PowerRoleBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file")
        return

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
