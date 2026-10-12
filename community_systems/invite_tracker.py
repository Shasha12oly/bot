"""
Invite tracker module - Track who invited whom with advanced features
"""
import discord
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime, timezone, timedelta
from config import SUPPORT_ROLE_ID, INVITE_ANNOUNCEMENT_CHANNEL_ID, get_data_dir
from utilities.embed_utils import create_embed

# Invite data storage - Now using Firebase
async def load_invites():
    """Load invites from Firebase"""
    try:
        from firebase_client import get_invites
        return await get_invites()
    except Exception as e:
        print(f"Error loading invites from Firebase: {e}")
        return {}


async def save_invites(invites):
    """Save invites to Firebase"""
    try:
        from firebase_client import set_invite
        for user_id, data in invites.items():
            await set_invite(user_id, data)
    except Exception as e:
        print(f"Error saving invites to Firebase: {e}")


async def load_invite_state():
    """Load the state of invite codes/uses from Firebase"""
    try:
        from firebase_client import get_invite_state
        return await get_invite_state()
    except Exception as e:
        print(f"Error loading invite state from Firebase: {e}")
        return {}


async def save_invite_state(state):
    """Save the state of invite codes/uses to Firebase"""
    try:
        from firebase_client import set_invite_state
        await set_invite_state(state)
    except Exception as e:
        print(f"Error saving invite state to Firebase: {e}")


# Track invites per server (in-memory, loaded from file)
SERVER_INVITES = {}
SERVER_DATA = {}

# Auto-updating leaderboard storage
LEADERBOARD_MESSAGES = {}  # {guild_id: {channel_id: message_id}}

# Invite milestones configuration
INVITE_MILESTONES = {
    5: {"role_id": None, "reward": "🥉 Bronze Inviter"},
    10: {"role_id": None, "reward": "🥈 Silver Inviter"},
    25: {"role_id": None, "reward": "🥇 Gold Inviter"},
    50: {"role_id": None, "reward": "💎 Diamond Inviter"},
    100: {"role_id": None, "reward": "👑 Legendary Inviter"}
}

# Fake invite detection settings
FAKE_INVITE_THRESHOLD_DAYS = 7  # If invited user leaves within 7 days, mark as potentially fake


async def track_invites(guild):
    """Track all invites in a server"""
    try:
        invites = {}
        invites_list = await guild.invites()
        for invite in invites_list:
            invites[invite.code] = {
                "uses": invite.uses,
                "inviter_id": str(invite.inviter.id) if invite.inviter else None,
                "url": invite.url
            }
        SERVER_INVITES[str(guild.id)] = invites
        # Save state to file for persistence
        await save_invite_state(SERVER_INVITES)
        print(f"Tracked {len(invites)} invites for {guild.name}")
        return invites
    except discord.Forbidden:
        print(f"⚠️ Missing permissions to track invites for {guild.name}")
        print(f"   Bot needs 'Manage Server' permission to track invites")
        return {}
    except Exception as e:
        print(f"⚠️ Error tracking invites for {guild.name}: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return {}


async def check_invite_join(member):
    """Check who invited a new member"""
    guild = member.guild

    # Get old invites first (before fetching current)
    old_invites = SERVER_INVITES.get(str(guild.id), {})

    # Small delay to ensure Discord has updated the invite uses
    import asyncio
    await asyncio.sleep(1)

    # Get current invites
    current_invites = await track_invites(guild)

    # Find which invite was used
    invite_code = None
    inviter_id = None

    for code, data in current_invites.items():
        if code in old_invites:
            if data["uses"] > old_invites[code]["uses"]:
                invite_code = code
                inviter_id = data["inviter_id"]
                break
        else:
            # New invite created - check if it has any uses
            if data["uses"] > 0:
                invite_code = code
                inviter_id = data["inviter_id"]
                break

    # Additional check: if no invite found, try to find the most recently used invite
    if not invite_code and current_invites:
        # Find the invite with the highest uses that wasn't tracked before
        for code, data in current_invites.items():
            if code not in old_invites and data["uses"] > 0:
                invite_code = code
                inviter_id = data["inviter_id"]
                break

        # If still not found, find the invite with the most recent activity
        if not invite_code:
            for code, data in current_invites.items():
                if data["uses"] > 0:
                    invite_code = code
                    inviter_id = data["inviter_id"]
                    break

    # Store the invite data
    server_data = await load_invites()
    if str(guild.id) not in server_data:
        server_data[str(guild.id)] = {"invites": {}, "members": {}}

    server_data[str(guild.id)]["members"][str(member.id)] = {
        "inviter_id": inviter_id,
        "invite_code": invite_code,
        "joined_at": datetime.now(timezone.utc).isoformat()
    }

    # Update inviter stats
    if inviter_id:
        if str(inviter_id) not in server_data[str(guild.id)]["invites"]:
            server_data[str(guild.id)]["invites"][str(inviter_id)] = {
                "total_invites": 0,
                "valid_invites": 0,
                "invalid_invites": 0
            }
        server_data[str(guild.id)]["invites"][str(inviter_id)]["total_invites"] += 1
        server_data[str(guild.id)]["invites"][str(inviter_id)]["valid_invites"] += 1
        print(f"User {member.name} invited by {inviter_id} using code {invite_code}")

        # Send announcement to invite channel if configured
        if INVITE_ANNOUNCEMENT_CHANNEL_ID:
            try:
                invite_channel = guild.get_channel(INVITE_ANNOUNCEMENT_CHANNEL_ID)
                if invite_channel:
                    inviter = guild.get_member(inviter_id)
                    inviter_name = inviter.name if inviter else f"User {inviter_id}"
                    inviter_mention = inviter.mention if inviter else f"<@{inviter_id}>"

                    total_invites = server_data[str(guild.id)]["invites"][str(inviter_id)]["total_invites"]

                    announcement_message = f"{member.mention} has been invited by {inviter_mention} and has now {total_invites} invites."
                    await invite_channel.send(announcement_message)
            except Exception as e:
                print(f"Error sending invite announcement: {e}")
    else:
        print(f"User {member.name} joined without tracking (no invite code found)")
        print(f"   This can happen if: they joined via direct link, vanity URL, or before bot was ready")

    await save_invites(server_data)

    return inviter_id, invite_code


async def check_invite_leave(member):
    """Handle member leaving - track for fake invite detection"""
    server_data = await load_invites()
    guild_id = str(member.guild.id)

    if guild_id in server_data and str(member.id) in server_data[guild_id]["members"]:
        member_data = server_data[guild_id]["members"][str(member.id)]
        inviter_id = member_data["inviter_id"]
        joined_at = datetime.fromisoformat(member_data["joined_at"])
        left_at = datetime.now(timezone.utc)
        days_active = (left_at - joined_at).days

        # Mark as left
        member_data["status"] = "left"
        member_data["left_at"] = left_at.isoformat()
        member_data["days_active"] = days_active

        # Check if potentially fake (left within threshold days)
        is_fake = days_active <= FAKE_INVITE_THRESHOLD_DAYS

        if inviter_id:
            if str(inviter_id) in server_data[guild_id]["invites"]:
                inviter_stats = server_data[guild_id]["invites"][str(inviter_id)]
                
                if is_fake:
                    inviter_stats["fake_invites"] += 1
                    inviter_stats["valid_invites"] = max(0, inviter_stats["valid_invites"] - 1)
                else:
                    inviter_stats["invalid_invites"] += 1

                # Update history
                for history_entry in inviter_stats.get("history", []):
                    if history_entry["user_id"] == str(member.id):
                        history_entry["status"] = "left"
                        history_entry["left_at"] = left_at.isoformat()
                        history_entry["days_active"] = days_active
                        history_entry["is_fake"] = is_fake
                        break

        del server_data[guild_id]["members"][str(member.id)]
        await save_invites(server_data)
        
        print(f"User {member.name} left after {days_active} days (Fake: {is_fake})")


async def check_milestone_rewards(guild, inviter_id, valid_invites):
    """Check and award milestone rewards"""
    for milestone, config in INVITE_MILESTONES.items():
        if valid_invites >= milestone:
            # Award milestone reward
            member = guild.get_member(inviter_id)
            if member:
                try:
                    # Add milestone role if configured
                    if config["role_id"]:
                        role = guild.get_role(config["role_id"])
                        if role:
                            await member.add_roles(role)
                            print(f"Awarded milestone role to {member.name}: {config['reward']}")
                    
                    # Send milestone announcement
                    announcements_channel = guild.get_channel(INVITE_ANNOUNCEMENT_CHANNEL_ID)
                    if announcements_channel:
                        embed = create_embed(
                            title="🎉 Milestone Reached!",
                            description=f"{member.mention} has reached {valid_invites} invites!",
                            color=discord.Color.gold(),
                            message_type="general",
                            fields=[
                                ("🏆 Milestone", config["reward"], True),
                                ("📊 Total Invites", str(valid_invites), True)
                            ]
                        )
                        await announcements_channel.send(embed=embed)
                except Exception as e:
                    print(f"Error awarding milestone reward: {e}")


async def get_invite_stats(interaction: discord.Interaction, member: discord.Member = None):
    """Get enhanced invite statistics for a member"""
    if member is None:
        member = interaction.user

    server_data = await load_invites()
    guild_id = str(interaction.guild.id)

    if guild_id not in server_data or str(member.id) not in server_data[guild_id]["invites"]:
        embed = create_embed(
            title="📊 Invite Statistics",
            description=f"{member.mention} has no invite data yet.",
            color=discord.Color.blue(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    stats = server_data[guild_id]["invites"][str(member.id)]
    
    # Calculate fake invite percentage
    fake_percentage = 0
    if stats["total_invites"] > 0:
        fake_percentage = round((stats["fake_invites"] / stats["total_invites"]) * 100, 1)

    embed = create_embed(
        title="📊 Invite Statistics",
        description=f"**User:** {member.mention}",
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="general",
        fields=[
            ("📊 Total Invites", str(stats["total_invites"]), True),
            ("✅ Valid Invites", str(stats["valid_invites"]), True),
            ("❌ Left Members", str(stats["invalid_invites"]), True),
            ("🚫 Fake Invites", str(stats["fake_invites"]), True),
            ("📈 Fake Rate", f"{fake_percentage}%", True)
        ]
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def get_invite_leaderboard(interaction: discord.Interaction):
    """Get enhanced invite leaderboard with fake detection"""
    server_data = await load_invites()
    guild_id = str(interaction.guild.id)

    if guild_id not in server_data or not server_data[guild_id]["invites"]:
        await interaction.response.send_message("No invite data available yet.", ephemeral=True)
        return

    # Calculate leaderboard
    leaderboard = []
    for user_id_str, stats in server_data[guild_id]["invites"].items():
        leaderboard.append({
            "user_id": int(user_id_str),
            "total_invites": stats["total_invites"],
            "valid_invites": stats["valid_invites"],
            "fake_invites": stats.get("fake_invites", 0),
            "invalid_invites": stats["invalid_invites"]
        })

    # Sort by valid invites
    leaderboard.sort(key=lambda x: x["valid_invites"], reverse=True)
    top_10 = leaderboard[:10]

    description = ""
    for i, entry in enumerate(top_10, 1):
        member = interaction.guild.get_member(entry["user_id"])
        member_name = member.name if member else f"User {entry['user_id']}"
        fake_rate = round((entry["fake_invites"] / entry["total_invites"]) * 100, 1) if entry["total_invites"] > 0 else 0
        description += f"**{i}.** {member_name}\n   📊 {entry['valid_invites']} valid ({entry['total_invites']} total) | 🚫 {fake_rate}% fake\n\n"

    embed = create_embed(
        title="🏆 Invite Leaderboard",
        description=description or "No invites yet.",
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="general"
    )
    await interaction.response.send_message(embed=embed)


async def get_invite_history(interaction: discord.Interaction, member: discord.Member = None):
    """Get detailed invite history for a member"""
    if member is None:
        member = interaction.user

    server_data = await load_invites()
    guild_id = str(interaction.guild.id)

    if guild_id not in server_data or str(member.id) not in server_data[guild_id]["invites"]:
        await interaction.response.send_message("No invite data available yet.", ephemeral=True)
        return

    stats = server_data[guild_id]["invites"][str(member.id)]
    history = stats.get("history", [])

    if not history:
        await interaction.response.send_message("No invite history available.", ephemeral=True)
        return

    description = f"**Recent Invite History for {member.mention}:**\n\n"
    for entry in history[-10:]:  # Show last 10 invites
        status_emoji = "✅" if entry["status"] == "active" else "❌"
        fake_warning = " ⚠️ POTENTIALLY FAKE" if entry.get("is_fake") else ""
        description += f"{status_emoji} <@{entry['user_id']}> - {entry.get('days_active', 'N/A')} days{fake_warning}\n"
        description += f"   Joined: {entry['joined_at'][:10]}\n"

    embed = create_embed(
        title="📜 Invite History",
        description=description,
        color=discord.Color.from_rgb(0, 255, 255),
        message_type="general"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def get_inviter_info(interaction: discord.Interaction, member: discord.Member = None):
    """Get who invited a member"""
    if member is None:
        member = interaction.user

    server_data = await load_invites()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in server_data or str(member.id) not in server_data[guild_id]["members"]:
        embed = create_embed(
            title="🔍 Inviter Information",
            description=f"Could not find inviter information for {member.mention}.",
            color=discord.Color.red(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    member_data = server_data[guild_id]["members"][str(member.id)]
    inviter_id = member_data["inviter_id"]
    
    if inviter_id:
        inviter = interaction.guild.get_member(inviter_id)
        inviter_name = inviter.name if inviter else f"User {inviter_id}"
        
        embed = create_embed(
            title="🔍 Inviter Information",
            description=f"**Member:** {member.mention}\n**Invited by:** {inviter.mention if inviter else inviter_name}\n**Invite Code:** {member_data['invite_code'] or 'Unknown'}\n**Joined:** {member_data['joined_at']}",
            color=discord.Color.green(),
            message_type="general"
        )
    else:
        embed = create_embed(
            title="🔍 Inviter Information",
            description=f"**Member:** {member.mention}\n**Invited by:** Unknown (joined via direct link or vanity URL)",
            color=discord.Color.orange(),
            message_type="general"
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# Command wrappers
async def invitestats_command(interaction: discord.Interaction, member: discord.Member = None):
    """Get invite statistics for a member"""
    await get_invite_stats(interaction, member)


async def inviteleaderboard_command(interaction: discord.Interaction):
    """Get invite leaderboard"""
    await get_invite_leaderboard(interaction)


async def whoinvited_command(interaction: discord.Interaction, member: discord.Member = None):
    """Get who invited a member"""
    await get_inviter_info(interaction, member)


async def invitehistory_command(interaction: discord.Interaction, member: discord.Member = None):
    """Get invite history for a member"""
    await get_invite_history(interaction, member)


async def setinvitemilestone_command(interaction: discord.Interaction, milestone: int, role: discord.Role = None, reward: str = None):
    """Set milestone reward configuration"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set milestone rewards.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    from firebase_client import get_document, set_document

    # Get current milestones
    config = await get_document("config", "invite_milestones")
    if not config:
        config = {}

    config[str(milestone)] = {
        "role_id": str(role.id) if role else None,
        "reward": reward or f"{milestone} Invites"
    }

    await set_document("config", "invite_milestones", config)

    # Update global config
    INVITE_MILESTONES[str(milestone)] = config[str(milestone)]

    embed = create_embed(
        title="✅ Milestone Configured",
        description=f"Milestone reward set for {milestone} invites!",
        color=discord.Color.green(),
        message_type="general",
        fields=[
            ("🎯 Milestone", str(milestone), True),
            ("🏆 Reward", config[str(milestone)]["reward"], True),
            ("🎭 Role", role.mention if role else "None", True)
        ]
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def post_leaderboard_command(interaction: discord.Interaction, channel: discord.TextChannel, refresh_seconds: int = 30):
    """Post an auto-updating invite leaderboard"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can post auto-updating leaderboards.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild_id = str(interaction.guild.id)
    channel_id = str(channel.id)

    # Generate initial leaderboard
    embed = await generate_leaderboard_embed(interaction.guild)

    # Post the leaderboard message
    message = await channel.send(embed=embed)

    # Store the message info for auto-updates
    if guild_id not in LEADERBOARD_MESSAGES:
        LEADERBOARD_MESSAGES[guild_id] = {}
    LEADERBOARD_MESSAGES[guild_id][channel_id] = {
        "message_id": message.id,
        "refresh_seconds": refresh_seconds,
        "last_update": datetime.now(timezone.utc)
    }

    # Save to Firebase
    from firebase_client import set_document
    await set_document("config", "leaderboard_messages", LEADERBOARD_MESSAGES)

    response_embed = create_embed(
        title="✅ Leaderboard Posted",
        description=f"Auto-updating leaderboard posted to {channel.mention}!\nRefreshes every {refresh_seconds} seconds.",
        color=discord.Color.green(),
        message_type="general"
    )
    await interaction.followup.send(embed=response_embed, ephemeral=True)


async def generate_leaderboard_embed(guild):
    """Generate the leaderboard embed"""
    server_data = await load_invites()
    guild_id = str(guild.id)

    if guild_id not in server_data or not server_data[guild_id]["invites"]:
        return create_embed(
            title="🏆 Invite Leaderboard",
            description="No invite data available yet.",
            color=discord.Color.from_rgb(0, 255, 255),
            message_type="general"
        )

    # Calculate leaderboard
    leaderboard = []
    for user_id_str, stats in server_data[guild_id]["invites"].items():
        leaderboard.append({
            "user_id": int(user_id_str),
            "total_invites": stats["total_invites"],
            "valid_invites": stats["valid_invites"],
            "fake_invites": stats.get("fake_invites", 0),
            "invalid_invites": stats["invalid_invites"]
        })

    # Sort by valid invites
    leaderboard.sort(key=lambda x: x["valid_invites"], reverse=True)
    top_10 = leaderboard[:10]

    description = ""
    for i, entry in enumerate(top_10, 1):
        member = guild.get_member(entry["user_id"])
        member_name = member.name if member else f"User {entry['user_id']}"
        fake_rate = round((entry["fake_invites"] / entry["total_invites"]) * 100, 1) if entry["total_invites"] > 0 else 0
        description += f"**{i}.** {member_name}\n   📊 {entry['valid_invites']} valid ({entry['total_invites']} total) | 🚫 {fake_rate}% fake\n\n"

    embed = create_embed(
        title="🏆 Invite Leaderboard",
        description=description or "No invites yet.",
        color=discord.Color.from_rgb(0, 255, 255),
        message_type="general"
    )
    embed.set_footer(text="Auto-updating leaderboard | Last updated")
    embed.timestamp = datetime.now(timezone.utc)

    return embed


async def update_leaderboards(guild):
    """Update all auto-updating leaderboards in a guild"""
    guild_id = str(guild.id)

    if guild_id not in LEADERBOARD_MESSAGES:
        return

    for channel_id, leaderboard_info in LEADERBOARD_MESSAGES[guild_id].items():
        try:
            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue

            # Check if it's time to update
            time_since_update = (datetime.now(timezone.utc) - leaderboard_info["last_update"]).total_seconds()
            if time_since_update < leaderboard_info["refresh_seconds"]:
                continue

            # Generate new embed
            new_embed = await generate_leaderboard_embed(guild)

            # Update the message
            message = await channel.fetch_message(leaderboard_info["message_id"])
            await message.edit(embed=new_embed)

            # Update last update time
            leaderboard_info["last_update"] = datetime.now(timezone.utc)

        except Exception as e:
            print(f"Error updating leaderboard in channel {channel_id}: {e}")


async def setinvitechannel_command(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the invite announcement channel"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set invite announcement channels.", ephemeral=True)
        return
    
    from config import update_env_var
    update_env_var("INVITE_ANNOUNCEMENT_CHANNEL_ID", str(channel.id))
    
    embed = create_embed(
        title="✅ Invite Announcement Channel Set",
        description=f"Invite announcements will now be sent to {channel.mention}",
        color=discord.Color.green(),
        message_type="general"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
