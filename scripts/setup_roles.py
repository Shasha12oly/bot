"""
Role Management System - Temporary Setup Script
This script removes existing roles and creates new roles with permissions for the trading bot.

⚠️ WARNING: This script will DELETE all existing roles (except @everyone and the bot's role)
Make sure you have a backup or understand the consequences before running this.

Usage:
1. Update GUILD_ID and role names in the configuration section below
2. Run: python setup_roles.py
3. The bot will create roles with appropriate permissions
4. Update your .env file with the new SUPPORT_ROLE_ID
"""

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============ CONFIGURATION ============
# IMPORTANT: Update these values before running!

GUILD_ID = int(os.getenv("SETUP_GUILD_ID", "0"))  # Your server ID

# Role configuration
ROLE_CONFIG = {
    "Support Staff": {
        "color": discord.Color.from_rgb(0, 255, 127),  # Spring Green
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            manage_channels=True,
            manage_messages=True,
            manage_roles=True,
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
            read_message_history=True,
            manage_threads=True,
            create_public_threads=True,
            create_private_threads=True,
            send_messages_in_threads=True
        ),
        "description": "Support Staff - Can manage tickets and help users"
    },
    "Customer": {
        "color": discord.Color.from_rgb(0, 191, 255),  # Deep Sky Blue
        "hoist": True,
        "mentionable": False,
        "permissions": discord.Permissions(
            read_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            add_reactions=True,
            use_external_emojis=True,
            connect=True,
            speak=True,
            stream=True,
            read_message_history=True,
            create_public_threads=True,
            create_private_threads=True,
            send_messages_in_threads=True
        ),
        "description": "Customer - Has purchased from the store"
    },
    "VIP": {
        "color": discord.Color.from_rgb(255, 215, 0),  # Gold
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
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
            create_public_threads=True,
            create_private_threads=True,
            send_messages_in_threads=True
        ),
        "description": "VIP - Premium customer with special perks"
    },
    "Verified": {
        "color": discord.Color.from_rgb(114, 137, 218),  # Blurple
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions(
            read_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            add_reactions=True,
            use_external_emojis=True,
            connect=True,
            speak=True,
            read_message_history=True
        ),
        "description": "Verified member"
    },
    "Cape Owner": {
        "color": discord.Color.from_rgb(255, 105, 180),  # Hot Pink
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            read_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            add_reactions=True,
            use_external_emojis=True,
            connect=True,
            speak=True,
            read_message_history=True
        ),
        "description": "Owns a Minecraft Cape from our store"
    },
    "Nitro Subscriber": {
        "color": discord.Color.from_rgb(147, 112, 219),  # Medium Purple
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
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
            read_message_history=True
        ),
        "description": "Purchased Discord Nitro from our store"
    },
    "Muted": {
        "color": discord.Color.from_rgb(128, 128, 128),  # Gray
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions(
            read_messages=True,
            read_message_history=True
        ),
        "description": "User is muted - Cannot send messages"
    }
}

# Roles to keep (won't be deleted)
ROLES_TO_KEEP = ["@everyone", "Trading Vault Bot"]  # Add your bot's name here
# ========================================


class RoleSetupBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(f"✅ Bot logged in as {self.user}")

    async def on_ready(self):
        print(f"\n{'='*60}")
        print("⚠️  ROLE SETUP SCRIPT")
        print(f"{'='*60}")
        print(f"⚠️  WARNING: This will DELETE ALL EXISTING ROLES!")
        print(f"⚠️  Except: {', '.join(ROLES_TO_KEEP)}")
        print(f"{'='*60}\n")

        if GUILD_ID == 0:
            print("❌ ERROR: GUILD_ID not set in configuration!")
            print("Please update SETUP_GUILD_ID in your .env file or in the script.")
            await self.close()
            return

        guild = self.get_guild(GUILD_ID)
        if not guild:
            print(f"❌ ERROR: Bot is not in guild with ID {GUILD_ID}")
            await self.close()
            return

        print(f"📋 Guild: {guild.name} (ID: {guild.id})")
        print(f"📊 Current roles: {len(guild.roles)}")

        # Ask for confirmation
        print("\n⏳ Waiting 10 seconds before starting...")
        print("❌ Press Ctrl+C to cancel if you don't want to proceed!")
        await asyncio.sleep(10)

        try:
            # Step 1: Delete existing roles
            print("\n🗑️  Deleting existing roles...")
            deleted_count = 0
            for role in guild.roles:
                if role.name not in ROLES_TO_KEEP and not role.managed:
                    try:
                        await role.delete()
                        print(f"   ✓ Deleted: {role.name}")
                        deleted_count += 1
                        await asyncio.sleep(0.5)  # Rate limiting
                    except Exception as e:
                        print(f"   ✗ Failed to delete {role.name}: {e}")

            print(f"\n✅ Deleted {deleted_count} roles")

            # Step 2: Create new roles
            print("\n✨ Creating new roles...")
            created_roles = {}

            for role_name, role_config in ROLE_CONFIG.items():
                try:
                    role = await guild.create_role(
                        name=role_name,
                        color=role_config["color"],
                        hoist=role_config["hoist"],
                        mentionable=role_config["mentionable"],
                        permissions=role_config["permissions"],
                        reason="Role setup script"
                    )
                    created_roles[role_name] = role.id
                    print(f"   ✓ Created: {role_name} (ID: {role.id})")
                    await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"   ✗ Failed to create {role_name}: {e}")

            # Step 3: Display summary
            print(f"\n{'='*60}")
            print("✅ ROLE SETUP COMPLETE")
            print(f"{'='*60}")
            print(f"\n📊 Summary:")
            print(f"   • Roles deleted: {deleted_count}")
            print(f"   • Roles created: {len(created_roles)}")

            print(f"\n📝 Role IDs (add these to your .env):")
            for role_name, role_id in created_roles.items():
                print(f"   {role_name}: {role_id}")

            if "Support Staff" in created_roles:
                print(f"\n⭐ IMPORTANT: Update your .env file with:")
                print(f"   SUPPORT_ROLE_ID={created_roles['Support Staff']}")

            print(f"\n{'='*60}\n")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

        await self.close()


async def main():
    bot = RoleSetupBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file")
        return

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
