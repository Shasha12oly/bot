"""
Role Restoration Script
Restores roles from a backup file created by role_analyzer.py

Usage:
1. Have a backup file from role_analyzer.py (e.g., role_backup_20240105_123456.json)
2. Run: python restore_roles.py <backup_file>
3. The script will restore all roles from the backup
"""

import discord
from discord.ext import commands
import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============ CONFIGURATION ============
GUILD_ID = int(os.getenv("SETUP_GUILD_ID", "0"))  # Your server ID
# ========================================


class RoleRestoreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(f"✅ Bot logged in as {self.user}")

    async def on_ready(self):
        print(f"\n{'='*70}")
        print("🔄 ROLE RESTORATION SCRIPT")
        print(f"{'='*70}\n")

        # Check for backup file argument
        if len(sys.argv) < 2:
            print("❌ ERROR: No backup file specified")
            print("Usage: python restore_roles.py <backup_file.json>")
            print("\nAvailable backup files:")
            for file in os.listdir('.'):
                if file.startswith('role_backup_') and file.endswith('.json'):
                    print(f"  • {file}")
            await self.close()
            return

        backup_file = sys.argv[1]
        if not os.path.exists(backup_file):
            print(f"❌ ERROR: Backup file not found: {backup_file}")
            await self.close()
            return

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
        print(f"💾 Backup file: {backup_file}")

        # Load backup
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
        except Exception as e:
            print(f"❌ ERROR: Failed to load backup file: {e}")
            await self.close()
            return

        print(f"📊 Backup from: {backup_data['backup_date']}")
        print(f"👥 Original guild: {backup_data['guild_name']}")
        print(f"📋 Roles in backup: {len(backup_data['roles'])}")

        # Confirm
        print(f"\n⚠️  WARNING: This will recreate all roles from the backup")
        print(f"⏳ Waiting 10 seconds before starting...")
        print(f"❌ Press Ctrl+C to cancel if you don't want to proceed!\n")

        await asyncio.sleep(10)

        try:
            print(f"\n{'='*70}")
            print("RESTORING ROLES")
            print(f"{'='*70}\n")

            restored_count = 0
            failed_count = 0

            for role_data in backup_data['roles']:
                if role_data['name'] == '@everyone':
                    print(f"   ⊘ Skipping @everyone")
                    continue

                # Check if role already exists
                existing_role = discord.utils.get(guild.roles, name=role_data['name'])
                if existing_role:
                    print(f"   ⚠️  Role already exists: {role_data['name']} (skipping)")
                    continue

                try:
                    # Parse color
                    color = discord.Color.from_rgb(0, 0, 0)  # Default black
                    if role_data['color'] and role_data['color'] != '#000000':
                        # Remove # if present
                        color_str = role_data['color'].lstrip('#')
                        if len(color_str) == 6:
                            r = int(color_str[0:2], 16)
                            g = int(color_str[2:4], 16)
                            b = int(color_str[4:6], 16)
                            color = discord.Color.from_rgb(r, g, b)

                    # Parse permissions
                    perms_data = role_data['permissions']
                    permissions = discord.Permissions(
                        administrator=perms_data.get('administrator', False),
                        manage_guild=perms_data.get('manage_guild', False),
                        manage_roles=perms_data.get('manage_roles', False),
                        manage_channels=perms_data.get('manage_channels', False),
                        manage_messages=perms_data.get('manage_messages', False),
                        kick_members=perms_data.get('kick_members', False),
                        ban_members=perms_data.get('ban_members', False),
                        moderate_members=perms_data.get('moderate_members', False),
                        read_messages=perms_data.get('read_messages', True),
                        send_messages=perms_data.get('send_messages', True),
                        connect=perms_data.get('connect', False),
                        speak=perms_data.get('speak', False)
                    )

                    # Create role
                    role = await guild.create_role(
                        name=role_data['name'],
                        color=color,
                        hoist=role_data['hoist'],
                        mentionable=role_data['mentionable'],
                        permissions=permissions,
                        reason=f"Restored from backup {backup_file}"
                    )

                    print(f"   ✓ Restored: {role_data['name']} (ID: {role.id})")
                    restored_count += 1
                    await asyncio.sleep(0.5)  # Rate limiting

                except Exception as e:
                    print(f"   ✗ Failed to restore {role_data['name']}: {e}")
                    failed_count += 1

            print(f"\n{'='*70}")
            print("✅ RESTORATION COMPLETE")
            print(f"{'='*70}")
            print(f"\n📊 Summary:")
            print(f"   • Roles restored: {restored_count}")
            print(f"   • Roles failed: {failed_count}")
            print(f"   • Total in backup: {len(backup_data['roles'])}")

            print(f"\n⚠️  Note: Role assignments to members were not restored")
            print(f"💡 You'll need to manually reassign roles to members if needed")

            print(f"\n{'='*70}\n")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

        await self.close()


async def main():
    bot = RoleRestoreBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file")
        return

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
