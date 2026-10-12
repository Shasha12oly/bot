"""
Give Member Role to All Members Script
Assigns the Member role to all existing members who don't have it
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
MEMBER_ROLE_NAME = "👥 Member"  # The role to give to everyone
# ========================================


class MemberRoleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(f"✅ Bot logged in as {self.user}")

    async def on_ready(self):
        print(f"\n{'='*70}")
        print("👥 GIVE MEMBER ROLE TO ALL MEMBERS SCRIPT")
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
        print(f"👥 Total members: {guild.member_count}")

        # Find the Member role
        member_role = discord.utils.get(guild.roles, name=MEMBER_ROLE_NAME)
        if not member_role:
            print(f"❌ ERROR: Role '{MEMBER_ROLE_NAME}' not found!")
            print(f"💡 Make sure you've run create_improved_roles.py first")
            await self.close()
            return

        print(f"🎭 Role to assign: {member_role.name} (ID: {member_role.id})")

        # Count members without the role
        members_without_role = []
        for member in guild.members:
            if member_role not in member.roles and not member.bot:
                members_without_role.append(member)

        print(f"\n📊 Statistics:")
        print(f"   • Total members: {len(guild.members)}")
        print(f"   • Members with role: {len(guild.members) - len(members_without_role)}")
        print(f"   • Members without role: {len(members_without_role)}")

        if not members_without_role:
            print(f"\n✅ All members already have the role!")
            await self.close()
            return

        # Ask for confirmation
        print(f"\n⚠️  This will assign the role to {len(members_without_role)} members")
        print(f"⏳ Waiting 10 seconds before starting...")
        print(f"❌ Press Ctrl+C to cancel if you don't want to proceed!\n")

        await asyncio.sleep(10)

        print(f"\n{'='*70}")
        print("ASSIGNING ROLE TO MEMBERS")
        print(f"{'='*70}\n")

        success_count = 0
        failed_count = 0

        for member in members_without_role:
            try:
                await member.add_roles(member_role, reason="Bulk member role assignment")
                print(f"   ✓ Assigned to: {member.name}")
                success_count += 1
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"   ✗ Failed for {member.name}: {e}")
                failed_count += 1

        # Summary
        print(f"\n{'='*70}")
        print("✅ ROLE ASSIGNMENT COMPLETE")
        print(f"{'='*70}")
        print(f"\n📊 Summary:")
        print(f"   • Successfully assigned: {success_count}")
        print(f"   • Failed: {failed_count}")
        print(f"   • Total processed: {len(members_without_role)}")

        print(f"\n💡 To enable auto-role for new members:")
        print(f"   1. Find the Member role ID: {member_role.id}")
        print(f"   2. Add to your .env: AUTO_ROLE_ID={member_role.id}")
        print(f"   3. Restart your bot")

        print(f"\n{'='*70}\n")
        await self.close()


async def main():
    bot = MemberRoleBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file")
        return

    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
