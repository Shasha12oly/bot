"""
Clean Duplicate Roles Script (Safe Version)
Safely removes duplicate roles, keeping emoji versions
"""

import discord
from discord.ext import commands
import asyncio
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============ CONFIGURATION ============
GUILD_ID = int(os.getenv("SETUP_GUILD_ID", "0"))  # Your server ID

# Roles to always keep (won't be deleted)
ROLES_TO_KEEP = ["@everyone", "Administrator", "Infinity"]  # Add any role you want to keep
# ========================================


class SafeRoleCleanerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(f"✅ Bot logged in as {self.user}")

    async def on_ready(self):
        print(f"\n{'='*70}")
        print("🧹 CLEAN DUPLICATE ROLES (SAFE VERSION)")
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
        print(f"👥 Members: {guild.member_count}")
        print(f"📊 Current roles: {len(guild.roles)}")

        print(f"\n{'='*70}")
        print("STEP 1: ANALYZING ROLES")
        print(f"{'='*70}\n")

        # Get all roles and categorize
        roles_by_name = {}  # Key: normalized name, Value: list of roles with that name
        emoji_roles = []
        managed_roles = []
        protected_roles = []

        for role in guild.roles:
            if role.name in ROLES_TO_KEEP:
                protected_roles.append(role)
            elif role.managed:
                managed_roles.append(role)
            elif self.has_emoji(role.name):
                emoji_roles.append(role)
            else:
                # Group by normalized name
                normalized = self.normalize_name(role.name)
                if normalized not in roles_by_name:
                    roles_by_name[normalized] = []
                roles_by_name[normalized].append(role)

        print(f"📊 Statistics:")
        print(f"   • Protected roles: {len(protected_roles)}")
        print(f"   • Managed roles (bot): {len(managed_roles)}")
        print(f"   • Emoji roles: {len(emoji_roles)}")
        print(f"   • Non-emoji roles: {sum(len(v) for v in roles_by_name.values())}")

        # Find duplicates (roles with same normalized name)
        duplicates = []
        for normalized_name, role_list in roles_by_name.items():
            if len(role_list) > 1:
                # Keep the one with most members, delete others
                role_list.sort(key=lambda r: len(r.members), reverse=True)
                keep = role_list[0]
                delete = role_list[1:]
                duplicates.append((keep, delete))

        print(f"\n🔄 Duplicates Found: {len(duplicates)} groups")

        if duplicates:
            print(f"\n📋 Duplicate Groups:")
            for keep_role, delete_roles in duplicates:
                print(f"\n   Keep: {keep_role.name} (ID: {keep_role.id}, Members: {len(keep_role.members)})")
                for role in delete_roles:
                    print(f"      Delete: {role.name} (ID: {role.id}, Members: {len(role.members)})")
        else:
            print(f"\n✅ No duplicates found!")
            await self.close()
            return

        # Flatten to single list of roles to delete
        roles_to_delete = []
        for keep_role, delete_roles in duplicates:
            roles_to_delete.extend(delete_roles)

        # Remove duplicates from the delete list (in case of any issues)
        unique_delete = []
        seen_ids = set()
        for role in roles_to_delete:
            if role.id not in seen_ids:
                unique_delete.append(role)
                seen_ids.add(role.id)

        roles_to_delete = unique_delete

        print(f"\n{'='*70}")
        print("STEP 2: READY TO DELETE")
        print(f"{'='*70}\n")

        print(f"🗑️  Unique roles to delete: {len(roles_to_delete)}")
        for role in roles_to_delete:
            print(f"   • {role.name} (ID: {role.id})")

        print(f"\n⚠️  WARNING: This will delete {len(roles_to_delete)} duplicate roles")
        print(f"⏳ Waiting 15 seconds before starting...")
        print(f"❌ Press Ctrl+C to cancel if you don't want to proceed!\n")

        await asyncio.sleep(15)

        print(f"\n{'='*70}")
        print("STEP 3: DELETING ROLES")
        print(f"{'='*70}\n")

        deleted_count = 0
        failed_count = 0
        not_found_count = 0
        permission_denied_count = 0

        for role in roles_to_delete:
            try:
                await role.delete()
                print(f"   ✓ Deleted: {role.name}")
                deleted_count += 1
                await asyncio.sleep(0.5)  # Rate limiting
            except discord.NotFound:
                print(f"   ⊘ Not found (already deleted): {role.name}")
                not_found_count += 1
            except discord.Forbidden:
                print(f"   ✗ Permission denied: {role.name}")
                permission_denied_count += 1
            except Exception as e:
                print(f"   ✗ Failed: {role.name} - {e}")
                failed_count += 1

        # Summary
        print(f"\n{'='*70}")
        print("✅ CLEANUP COMPLETE")
        print(f"{'='*70}")
        print(f"\n📊 Summary:")
        print(f"   • Successfully deleted: {deleted_count}")
        print(f"   • Not found (already deleted): {not_found_count}")
        print(f"   • Permission denied: {permission_denied_count}")
        print(f"   • Other errors: {failed_count}")
        print(f"   • Total processed: {len(roles_to_delete)}")

        print(f"\n💡 Remaining roles:")
        print(f"   • Emoji roles: {len(emoji_roles)}")
        print(f"   • Managed roles: {len(managed_roles)}")
        print(f"   • Protected roles: {len(protected_roles)}")

        if permission_denied_count > 0:
            print(f"\n⚠️  Some roles couldn't be deleted due to permissions")
            print(f"💡 You may need to delete them manually in Discord server settings")

        print(f"\n{'='*70}\n")
        await self.close()

    def has_emoji(self, text):
        """Check if text contains emojis"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return bool(emoji_pattern.search(text))

    def normalize_name(self, name):
        """Normalize role name for comparison"""
        # Remove emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        name = emoji_pattern.sub('', name)

        # Remove special characters and lowercase
        name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        name = name.lower().strip()

        return name


async def main():
    bot = SafeRoleCleanerBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file")
        return

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
