"""
Create Improved Roles Script
Adds improved versions of your old roles with better styling, colors, and permissions
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

# Improved role configuration based on your old roles
IMPROVED_ROLE_CONFIG = {
    # Store/Trading Roles (from your old roles)
    "🛒 Customer": {
        "color": discord.Color.from_rgb(230, 126, 34),  # Orange (was Buyer)
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
            read_message_history=True
        ),
        "description": "Customer - Has purchased from the store"
    },
    "🎁 Giveaway Winner": {
        "color": discord.Color.from_rgb(46, 204, 113),  # Green (was Giveaway)
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
        "description": "Giveaway Winner - Won a server giveaway"
    },

    # Staff Roles (from your old roles)
    "👑 Administrator": {
        "color": discord.Color.from_rgb(52, 152, 219),  # Blue (was Administrator)
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
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
            read_message_history=True
        ),
        "description": "Administrator - Full server management"
    },
    "⚡ Head Moderator": {
        "color": discord.Color.from_rgb(231, 76, 60),  # Dark Red (was Head Moderator)
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
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
            read_message_history=True
        ),
        "description": "Head Moderator - Senior staff member"
    },
    "🛡️ Moderator": {
        "color": discord.Color.from_rgb(231, 76, 60),  # Red (was Moderator)
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            manage_messages=True,
            kick_members=True,
            ban_members=True,
            moderate_members=True,
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
        "description": "Moderator - Server moderation"
    },
    "🎫 Support Staff": {
        "color": discord.Color.from_rgb(52, 152, 219),  # Blue (was Support staff)
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            manage_channels=True,
            manage_messages=True,
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
        "description": "Support Staff - Helps with tickets and support"
    },
    "👥 Staff": {
        "color": discord.Color.from_rgb(149, 165, 166),  # Gray (was Staff)
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
            read_message_history=True
        ),
        "description": "Staff - Team member"
    },

    # Special Roles (from your old roles)
    "🏆 Champion": {
        "color": discord.Color.from_rgb(241, 196, 15),  # Gold (was 🏆 Champion)
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
            priority_speaker=True,
            read_message_history=True
        ),
        "description": "Champion - Top contributor or winner"
    },
    "🤖 Bot": {
        "color": discord.Color.from_rgb(96, 125, 139),  # Blue Gray (was Bot)
        "hoist": True,
        "mentionable": False,
        "permissions": discord.Permissions(
            administrator=True,
            manage_guild=True,
            manage_roles=True,
            manage_channels=True,
            manage_messages=True,
            read_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            add_reactions=True,
            use_external_emojis=True,
            connect=True,
            speak=True,
            stream=True,
            read_message_history=True
        ),
        "description": "Bot - For automated accounts"
    },
    "💎 VIP": {
        "color": discord.Color.from_rgb(155, 89, 182),  # Purple (was 👑 VIP)
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
        "description": "VIP - Premium member with special perks"
    },
    "💎 Premium VIP": {
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
            read_message_history=True
        ),
        "description": "Premium VIP - Highest tier VIP"
    },
    "👥 Member": {
        "color": discord.Color.from_rgb(127, 140, 141),  # Silver (was Members)
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
        "description": "Member - Regular server member"
    },
    "🤝 Friends": {
        "color": discord.Color.from_rgb(84, 110, 122),  # Blue Gray (was Friends)
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
            read_message_history=True
        ),
        "description": "Friends - Close friends of the owner"
    },
    "🌟 Verified": {
        "color": discord.Color.from_rgb(0, 191, 255),  # Deep Sky Blue
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
        "description": "Verified - Verified member"
    },

    # Trading Store Specific Roles
    "🦅 Cape Owner": {
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
        "description": "Cape Owner - Owns a Minecraft Cape"
    },
    "💎 Nitro Subscriber": {
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
        "description": "Nitro Subscriber - Purchased Discord Nitro"
    },
    "🔇 Muted": {
        "color": discord.Color.from_rgb(128, 128, 128),  # Gray
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions(
            read_messages=True,
            read_message_history=True
        ),
        "description": "Muted - Cannot send messages"
    }
}
# ========================================


class ImprovedRoleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(f"✅ Bot logged in as {self.user}")

    async def on_ready(self):
        print(f"\n{'='*70}")
        print("✨ CREATE IMPROVED ROLES SCRIPT")
        print(f"{'='*70}\n")

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
        print(f"👥 Members: {guild.member_count}")
        print(f"📊 Current roles: {len(guild.roles)}")

        print(f"\n{'='*70}")
        print("CREATING IMPROVED ROLES")
        print(f"{'='*70}\n")

        created_roles = {}
        skipped_roles = []

        for role_name, role_config in IMPROVED_ROLE_CONFIG.items():
            # Check if role already exists
            existing_role = discord.utils.get(guild.roles, name=role_name)
            if existing_role:
                print(f"   ⚠️  Role already exists: {role_name} (skipping)")
                skipped_roles.append(role_name)
                continue

            try:
                role = await guild.create_role(
                    name=role_name,
                    color=role_config["color"],
                    hoist=role_config["hoist"],
                    mentionable=role_config["mentionable"],
                    permissions=role_config["permissions"],
                    reason="Creating improved roles for trading bot"
                )
                created_roles[role_name] = role.id
                print(f"   ✓ Created: {role_name} (ID: {role.id})")
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"   ✗ Failed to create {role_name}: {e}")

        # Summary
        print(f"\n{'='*70}")
        print("✅ ROLE CREATION COMPLETE")
        print(f"{'='*70}")
        print(f"\n📊 Summary:")
        print(f"   • Roles created: {len(created_roles)}")
        print(f"   • Roles skipped (already exist): {len(skipped_roles)}")

        if created_roles:
            print(f"\n📝 Created Role IDs:")
            for role_name, role_id in created_roles.items():
                print(f"   {role_name}: {role_id}")

        if skipped_roles:
            print(f"\n⚠️  Skipped Roles (already exist):")
            for role_name in skipped_roles:
                print(f"   {role_name}")

        print(f"\n💡 Important:")
        print(f"   • Your old 'Administrator' and 'Infinity' roles still exist")
        print(f"   • You can manually delete them or keep them")
        print(f"   • New roles have better colors and permissions")
        print(f"   • Use /addrole command to assign roles to members")

        print(f"\n{'='*70}\n")

        await self.close()


async def main():
    bot = ImprovedRoleBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file")
        return

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
