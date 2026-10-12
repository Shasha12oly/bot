"""
Role Analyzer & Setup Script - Two-Step Process
Step 1: Analyze and backup current roles
Step 2: Delete old roles and create new ones

This script safely analyzes your current roles, backs them up, and then creates
new roles optimized for the trading bot store system.
"""

import discord
from discord.ext import commands
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============ CONFIGURATION ============
GUILD_ID = int(os.getenv("SETUP_GUILD_ID", "0"))  # Your server ID

# Roles to keep (won't be deleted)
ROLES_TO_KEEP = ["@everyone", "Trading Vault Bot"]  # Add your bot's name here

# New role configuration for trading store
NEW_ROLE_CONFIG = {
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
# ========================================


class RoleAnalyzerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(f"✅ Bot logged in as {self.user}")

    async def on_ready(self):
        print(f"\n{'='*70}")
        print("🔍 ROLE ANALYZER & SETUP SCRIPT")
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

        # Step 1: Analyze current roles
        print(f"\n{'='*70}")
        print("STEP 1: ANALYZING CURRENT ROLES")
        print(f"{'='*70}\n")

        current_roles_data = []
        roles_to_delete = []

        for role in guild.roles:
            role_data = {
                "id": role.id,
                "name": role.name,
                "color": str(role.color),
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "position": role.position,
                "managed": role.managed,
                "members": len(role.members),
                "permissions": {
                    "administrator": role.permissions.administrator,
                    "manage_guild": role.permissions.manage_guild,
                    "manage_roles": role.permissions.manage_roles,
                    "manage_channels": role.permissions.manage_channels,
                    "manage_messages": role.permissions.manage_messages,
                    "kick_members": role.permissions.kick_members,
                    "ban_members": role.permissions.ban_members,
                    "moderate_members": role.permissions.moderate_members,
                    "read_messages": role.permissions.read_messages,
                    "send_messages": role.permissions.send_messages,
                    "connect": role.permissions.connect,
                    "speak": role.permissions.speak
                },
                "created_at": role.created_at.isoformat()
            }
            current_roles_data.append(role_data)

            if role.name not in ROLES_TO_KEEP and not role.managed:
                roles_to_delete.append(role)

        # Save backup
        backup_file = f"role_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w') as f:
            json.dump({
                "guild_id": guild.id,
                "guild_name": guild.name,
                "backup_date": datetime.now().isoformat(),
                "total_roles": len(guild.roles),
                "roles": current_roles_data
            }, f, indent=2)

        print(f"💾 Backup saved to: {backup_file}")
        print(f"📊 Total roles analyzed: {len(current_roles_data)}")
        print(f"🗑️  Roles to delete: {len(roles_to_delete)}")
        print(f"🛡️  Roles to keep: {len([r for r in guild.roles if r.name in ROLES_TO_KEEP or r.managed])}")

        # Display roles to delete
        if roles_to_delete:
            print(f"\n📋 Roles that will be DELETED:")
            for role in roles_to_delete:
                print(f"   • {role.name} (ID: {role.id}, Members: {len(role.members)})")
        else:
            print(f"\n✅ No roles to delete (all protected)")

        # Display roles to keep
        kept_roles = [r for r in guild.roles if r.name in ROLES_TO_KEEP or r.managed]
        if kept_roles:
            print(f"\n🛡️  Roles that will be KEPT:")
            for role in kept_roles:
                print(f"   • {role.name} (ID: {role.id}, Members: {len(role.members)})")

        # Display new roles to create
        print(f"\n✨ New roles that will be CREATED:")
        for role_name, role_config in NEW_ROLE_CONFIG.items():
            print(f"   • {role_name} - {role_config['description']}")

        # Ask for confirmation
        print(f"\n{'='*70}")
        print("⚠️  STEP 2: READY TO PROCEED?")
        print(f"{'='*70}")
        print(f"\n⏳ Waiting 15 seconds before starting deletion...")
        print(f"❌ Press Ctrl+C to cancel if you don't want to proceed!")
        print(f"💾 Your roles have been backed up to: {backup_file}\n")

        await asyncio.sleep(15)

        try:
            # Step 2: Delete old roles
            print(f"\n{'='*70}")
            print("STEP 2: DELETING OLD ROLES")
            print(f"{'='*70}\n")

            deleted_count = 0
            for role in roles_to_delete:
                try:
                    await role.delete()
                    print(f"   ✓ Deleted: {role.name}")
                    deleted_count += 1
                    await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"   ✗ Failed to delete {role.name}: {e}")

            print(f"\n✅ Deleted {deleted_count} roles")

            # Step 3: Create new roles
            print(f"\n{'='*70}")
            print("STEP 3: CREATING NEW ROLES")
            print(f"{'='*70}\n")

            created_roles = {}

            for role_name, role_config in NEW_ROLE_CONFIG.items():
                try:
                    role = await guild.create_role(
                        name=role_name,
                        color=role_config["color"],
                        hoist=role_config["hoist"],
                        mentionable=role_config["mentionable"],
                        permissions=role_config["permissions"],
                        reason="Role setup script for trading bot"
                    )
                    created_roles[role_name] = role.id
                    print(f"   ✓ Created: {role_name} (ID: {role.id})")
                    await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    print(f"   ✗ Failed to create {role_name}: {e}")

            # Step 4: Summary
            print(f"\n{'='*70}")
            print("✅ ROLE SETUP COMPLETE")
            print(f"{'='*70}")
            print(f"\n📊 Summary:")
            print(f"   • Roles deleted: {deleted_count}")
            print(f"   • Roles created: {len(created_roles)}")
            print(f"   • Backup file: {backup_file}")

            print(f"\n📝 New Role IDs (add these to your .env):")
            for role_name, role_id in created_roles.items():
                print(f"   {role_name}: {role_id}")

            if "Support Staff" in created_roles:
                print(f"\n⭐ IMPORTANT: Update your .env file with:")
                print(f"   SUPPORT_ROLE_ID={created_roles['Support Staff']}")

            print(f"\n💡 To restore old roles if needed:")
            print(f"   1. Use the backup file: {backup_file}")
            print(f"   2. Manually recreate roles using the data in the JSON file")

            print(f"\n{'='*70}\n")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print(f"💾 Your roles have been backed up to: {backup_file}")

        await self.close()


async def main():
    bot = RoleAnalyzerBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file")
        return

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
