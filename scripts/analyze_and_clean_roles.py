"""
Analyze and Clean Roles Script
Lists all roles, identifies duplicates, and keeps emoji versions while removing duplicates
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
ROLES_TO_KEEP = ["@everyone"]  # Add any role you want to keep regardless
# ========================================


class RoleCleanerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(f"✅ Bot logged in as {self.user}")

    async def on_ready(self):
        print(f"\n{'='*70}")
        print("🔍 ANALYZE AND CLEAN ROLES SCRIPT")
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
        print("STEP 1: ANALYZING ALL ROLES")
        print(f"{'='*70}\n")

        # Categorize roles
        managed_roles = []
        emoji_roles = []
        non_emoji_roles = []
        protected_roles = []

        for role in guild.roles:
            if role.name in ROLES_TO_KEEP:
                protected_roles.append(role)
            elif role.managed:
                managed_roles.append(role)
            elif self.has_emoji(role.name):
                emoji_roles.append(role)
            else:
                non_emoji_roles.append(role)

        print(f"📊 Role Categories:")
        print(f"   • Protected roles: {len(protected_roles)}")
        print(f"   • Managed roles (bot roles): {len(managed_roles)}")
        print(f"   • Emoji roles: {len(emoji_roles)}")
        print(f"   • Non-emoji roles: {len(non_emoji_roles)}")

        # Display emoji roles
        if emoji_roles:
            print(f"\n✨ Emoji Roles (will be kept):")
            for role in emoji_roles:
                print(f"   • {role.name} (ID: {role.id}, Members: {len(role.members)})")

        # Display non-emoji roles
        if non_emoji_roles:
            print(f"\n📋 Non-Emoji Roles (will be analyzed for duplicates):")
            for role in non_emoji_roles:
                print(f"   • {role.name} (ID: {role.id}, Members: {len(role.members)})")

        # Display managed roles
        if managed_roles:
            print(f"\n🤖 Managed Roles (bot roles - kept):")
            for role in managed_roles:
                print(f"   • {role.name} (ID: {role.id}, Members: {len(role.members)})")

        # Find potential duplicates
        print(f"\n{'='*70}")
        print("STEP 2: IDENTIFYING DUPLICATES")
        print(f"{'='*70}\n")

        duplicates = self.find_duplicates(non_emoji_roles, emoji_roles)

        if duplicates:
            print(f"🔄 Potential Duplicates Found:")
            for original, duplicate_list in duplicates.items():
                print(f"\n   Similar to: {original.name}")
                for dup in duplicate_list:
                    print(f"      → {dup.name} (ID: {dup.id}, Members: {len(dup.members)})")
        else:
            print(f"✅ No duplicates found!")

        # Roles to delete
        roles_to_delete = []
        for duplicate_list in duplicates.values():
            roles_to_delete.extend(duplicate_list)

        if not roles_to_delete:
            print(f"\n✅ No roles to delete. All good!")
            await self.close()
            return

        print(f"\n{'='*70}")
        print("STEP 3: READY TO DELETE DUPLICATES")
        print(f"{'='*70}\n")

        print(f"🗑️  Roles to delete: {len(roles_to_delete)}")
        for role in roles_to_delete:
            print(f"   • {role.name} (ID: {role.id}, Members: {len(role.members)})")

        print(f"\n⚠️  WARNING: This will delete {len(roles_to_delete)} duplicate roles")
        print(f"⏳ Waiting 15 seconds before starting...")
        print(f"❌ Press Ctrl+C to cancel if you don't want to proceed!\n")

        await asyncio.sleep(15)

        # Delete duplicates
        print(f"\n{'='*70}")
        print("STEP 4: DELETING DUPLICATE ROLES")
        print(f"{'='*70}\n")

        deleted_count = 0
        failed_count = 0

        for role in roles_to_delete:
            try:
                await role.delete()
                print(f"   ✓ Deleted: {role.name}")
                deleted_count += 1
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"   ✗ Failed to delete {role.name}: {e}")
                failed_count += 1

        # Summary
        print(f"\n{'='*70}")
        print("✅ ROLE CLEANUP COMPLETE")
        print(f"{'='*70}")
        print(f"\n📊 Summary:")
        print(f"   • Roles deleted: {deleted_count}")
        print(f"   • Failed: {failed_count}")
        print(f"   • Total processed: {len(roles_to_delete)}")

        print(f"\n💡 Kept Roles:")
        print(f"   • Emoji roles: {len(emoji_roles)}")
        print(f"   • Managed roles: {len(managed_roles)}")
        print(f"   • Protected roles: {len(protected_roles)}")

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

    def find_duplicates(self, non_emoji_roles, emoji_roles):
        """Find duplicates between non-emoji and emoji roles"""
        duplicates = {}

        # Create a normalized version of emoji role names for comparison
        emoji_normalized = {}
        for role in emoji_roles:
            # Remove emojis and normalize
            normalized = self.normalize_name(role.name)
            emoji_normalized[normalized] = role

        # Check non-emoji roles against emoji roles
        for role in non_emoji_roles:
            normalized = self.normalize_name(role.name)

            # Check if normalized name matches any emoji role
            for emoji_norm, emoji_role in emoji_normalized.items():
                # Check for exact match or similarity
                if normalized == emoji_norm or self.similar_names(normalized, emoji_norm):
                    if emoji_role not in duplicates:
                        duplicates[emoji_role] = []
                    duplicates[emoji_role].append(role)

        return duplicates

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

    def similar_names(self, name1, name2):
        """Check if two names are similar"""
        # Simple similarity check
        name1_words = set(name1.split())
        name2_words = set(name2.split())

        # If one is a subset of the other
        if name1_words.issubset(name2_words) or name2_words.issubset(name1_words):
            return True

        # If they share most words
        intersection = name1_words & name2_words
        if len(intersection) >= min(len(name1_words), len(name2_words)) - 1:
            return True

        return False


async def main():
    bot = RoleCleanerBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file")
        return

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
