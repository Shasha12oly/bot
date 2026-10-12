"""
Utilities Module - General Info, Moderation, and Fun Commands
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import random
import json
import os
from config import SUPPORT_ROLE_ID
from .embed_utils import create_embed


# ============ GENERAL INFO COMMANDS ============

async def serverinfo(interaction: discord.Interaction, bot):
    """Display detailed server information"""
    guild = interaction.guild
    
    # Calculate member counts
    total_members = guild.member_count
    online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
    bot_count = sum(1 for m in guild.members if m.bot)
    human_count = total_members - bot_count
    
    # Get role count
    role_count = len(guild.roles) - 1  # Exclude @everyone
    
    # Get channel counts
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    total_channels = text_channels + voice_channels
    
    # Server age
    server_age = (datetime.now(timezone.utc) - guild.created_at).days
    
    embed = create_embed(
        title=f"📊 Server Information - {guild.name}",
        description=f"**Owner:** {guild.owner.mention}\n**Server ID:** `{guild.id}`\n**Created:** {guild.created_at.strftime('%B %d, %Y')} ({server_age} days ago)",
        color=discord.Color.blue(),
        message_type="general",
        fields=[
            ("Members", f"Total: {total_members}\nHumans: {human_count}\nBots: {bot_count}\nOnline: {online_members}", True),
            ("Channels", f"Text: {text_channels}\nVoice: {voice_channels}\nTotal: {total_channels}", True),
            ("Roles", str(role_count), True),
            ("Boost Level", f"Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts", True),
            ("Verification", str(guild.verification_level).replace("VerificationLevel.", " ").title(), True),
            ("Region", str(guild.region).replace("Region.", " ").title() if hasattr(guild, 'region') else "N/A", True)
        ]
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    if guild.banner:
        embed.set_image(url=guild.banner.url)
    
    await interaction.response.send_message(embed=embed)


async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    """Display detailed user information"""
    if member is None:
        member = interaction.user
    
    # Calculate account age
    account_age = (datetime.now(timezone.utc) - member.created_at).days
    
    # Calculate server join age
    join_age = (datetime.now(timezone.utc) - member.joined_at).days if member.joined_at else 0
    
    # Get top role
    top_role = member.top_role if member.top_role.name != "@everyone" else "None"
    
    # Get role list
    roles = [role.mention for role in member.roles if role.name != "@everyone"]
    roles_list = ", ".join(roles) if roles else "No roles"
    
    # Account status
    is_bot = "🤖 Bot" if member.bot else "👤 Human"
    
    embed = create_embed(
        title=f"👤 User Information - {member.name}",
        description=f"**Display Name:** {member.display_name}\n**User ID:** `{member.id}`\n**Type:** {is_bot}",
        color=member.color if member.color.value != 0 else discord.Color.blue(),
        message_type="general",
        fields=[
            ("Account Created", f"{member.created_at.strftime('%B %d, %Y')}\n({account_age} days ago)", True),
            ("Joined Server", f"{member.joined_at.strftime('%B %d, %Y') if member.joined_at else 'N/A'}\n({join_age} days ago)", True),
            ("Top Role", top_role.name if isinstance(top_role, discord.Role) else top_role, True),
            ("Roles", roles_list[:100] + "..." if len(roles_list) > 100 else roles_list, False)
        ]
    )
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    if member.banner:
        embed.set_image(url=member.banner.url)
    
    await interaction.response.send_message(embed=embed)


async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    """View a user's avatar"""
    if member is None:
        member = interaction.user
    
    if member.avatar:
        embed = create_embed(
            title=f"🖼️ {member.name}'s Avatar",
            color=discord.Color.blue(),
            message_type="general"
        )
        embed.set_image(url=member.avatar.url)
        await interaction.response.send_message(embed=embed)
    else:
        embed = create_embed(
            title="❌ No Avatar",
            description=f"{member.mention} doesn't have a custom avatar.",
            color=discord.Color.red(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)


async def banner(interaction: discord.Interaction, member: discord.Member = None):
    """View a user's banner"""
    if member is None:
        member = interaction.user
    
    if member.banner:
        embed = create_embed(
            title=f"🖼️ {member.name}'s Banner",
            color=discord.Color.blue(),
            message_type="general"
        )
        embed.set_image(url=member.banner.url)
        await interaction.response.send_message(embed=embed)
    else:
        embed = create_embed(
            title="❌ No Banner",
            description=f"{member.mention} doesn't have a custom banner.",
            color=discord.Color.red(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)


async def ping(interaction: discord.Interaction, bot):
    """Check bot latency"""
    # Measure websocket latency
    websocket_ping = round(bot.latency * 1000)
    
    # Measure round-trip latency
    start_time = datetime.now(timezone.utc)
    await interaction.response.defer()
    end_time = datetime.now(timezone.utc)
    roundtrip_ping = round((end_time - start_time).total_seconds() * 1000)
    
    embed = create_embed(
        title="🏓 Pong!",
        description=f"**WebSocket Latency:** {websocket_ping}ms\n**Round-trip Latency:** {roundtrip_ping}ms",
        color=discord.Color.green() if websocket_ping < 100 else discord.Color.orange() if websocket_ping < 200 else discord.Color.red(),
        message_type="general"
    )
    
    await interaction.followup.send(embed=embed)


async def botstats(interaction: discord.Interaction, bot):
    """View bot statistics"""
    # Calculate uptime
    uptime = datetime.now(timezone.utc) - bot.start_time if hasattr(bot, 'start_time') else timedelta(0)
    uptime_str = str(uptime).split('.')[0]
    
    # Server count
    server_count = len(bot.guilds)
    
    # Total members
    total_members = sum(guild.member_count for guild in bot.guilds)
    
    # Total channels
    total_channels = sum(len(guild.channels) for guild in bot.guilds)
    
    embed = create_embed(
        title="🤖 Bot Statistics",
        description=f"**Bot Name:** {bot.user.name}\n**Bot ID:** `{bot.user.id}`\n**Uptime:** {uptime_str}",
        color=discord.Color.blue(),
        message_type="general",
        fields=[
            ("Servers", str(server_count), True),
            ("Total Members", str(total_members), True),
            ("Total Channels", str(total_channels), True),
            ("Ping", f"{round(bot.latency * 1000)}ms", True),
            ("Python Version", "3.8+", True),
            ("Library", "discord.py 2.x", True)
        ]
    )
    
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    
    await interaction.response.send_message(embed=embed)


# ============ MODERATION COMMANDS ============

async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    """Kick a member from the server"""
    guild = interaction.guild
    
    # Check if user can kick this member
    if member.top_role >= interaction.user.top_role and member != interaction.user:
        await interaction.response.send_message("You cannot kick someone with a higher or equal role.", ephemeral=True)
        return
    
    if member == interaction.user:
        await interaction.response.send_message("You cannot kick yourself.", ephemeral=True)
        return
    
    if member == guild.owner:
        await interaction.response.send_message("You cannot kick the server owner.", ephemeral=True)
        return
    
    try:
        await member.kick(reason=reason)
        embed = create_embed(
            title="👢 Member Kicked",
            description=f"**User:** {member.mention}\n**Reason:** {reason or 'No reason provided'}\n**Moderator:** {interaction.user.mention}",
            color=discord.Color.orange(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to kick this member.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error kicking member: {str(e)}", ephemeral=True)


async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None, delete_message_days: int = 0):
    """Ban a member from the server"""
    guild = interaction.guild
    
    # Check if user can ban this member
    if member.top_role >= interaction.user.top_role and member != interaction.user:
        await interaction.response.send_message("You cannot ban someone with a higher or equal role.", ephemeral=True)
        return
    
    if member == interaction.user:
        await interaction.response.send_message("You cannot ban yourself.", ephemeral=True)
        return
    
    if member == guild.owner:
        await interaction.response.send_message("You cannot ban the server owner.", ephemeral=True)
        return
    
    try:
        await member.ban(reason=reason, delete_message_days=delete_message_days)
        embed = create_embed(
            title="🔨 Member Banned",
            description=f"**User:** {member.mention}\n**Reason:** {reason or 'No reason provided'}\n**Delete Messages:** {delete_message_days} days\n**Moderator:** {interaction.user.mention}",
            color=discord.Color.red(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to ban this member.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error banning member: {str(e)}", ephemeral=True)


async def unban(interaction: discord.Interaction, bot, user_id: str):
    """Unban a user from the server"""
    guild = interaction.guild
    
    try:
        user_id = int(user_id)
        user = await bot.fetch_user(user_id)
        
        await guild.unban(user)
        embed = create_embed(
            title="🔓 User Unbanned",
            description=f"**User:** {user.mention}\n**Moderator:** {interaction.user.mention}",
            color=discord.Color.green(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except ValueError:
        await interaction.response.send_message("Invalid user ID. Please provide a valid ID.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("This user is not banned.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to unban this user.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error unbanning user: {str(e)}", ephemeral=True)


async def purge(interaction: discord.Interaction, amount: int):
    """Delete multiple messages"""
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
        return
    
    try:
        deleted = await interaction.channel.purge(limit=amount)
        embed = create_embed(
            title="🗑️ Messages Deleted",
            description=f"Successfully deleted {len(deleted)} messages.",
            color=discord.Color.green(),
            message_type="general"
        )
        await interaction.channel.send(embed=embed, delete_after=5)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to delete messages.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error deleting messages: {str(e)}", ephemeral=True)


async def slowmode(interaction: discord.Interaction, seconds: int):
    """Set slowmode for the channel"""
    if seconds < 0 or seconds > 21600:
        await interaction.response.send_message("Slowmode must be between 0 and 21600 seconds (6 hours).", ephemeral=True)
        return
    
    try:
        await interaction.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            embed = create_embed(
                title="✅ Slowmode Disabled",
                description="Slowmode has been disabled for this channel.",
                color=discord.Color.green(),
                message_type="general"
            )
        else:
            embed = create_embed(
                title="✅ Slowmode Enabled",
                description=f"Slowmode has been set to {seconds} seconds for this channel.",
                color=discord.Color.green(),
                message_type="general"
            )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to edit this channel.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error setting slowmode: {str(e)}", ephemeral=True)


async def lock(interaction: discord.Interaction):
    """Lock the channel"""
    try:
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        embed = create_embed(
            title="🔒 Channel Locked",
            description="This channel has been locked.",
            color=discord.Color.orange(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to lock this channel.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error locking channel: {str(e)}", ephemeral=True)


async def unlock(interaction: discord.Interaction):
    """Unlock the channel"""
    try:
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=None)
        embed = create_embed(
            title="🔓 Channel Unlocked",
            description="This channel has been unlocked.",
            color=discord.Color.green(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to unlock this channel.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error unlocking channel: {str(e)}", ephemeral=True)


# ============ FUN & COMMUNITY COMMANDS ============

async def eightball(interaction: discord.Interaction, question: str):
    """Ask the magic 8-ball a question"""
    responses = [
        "Yes, definitely.",
        "It is certain.",
        "Without a doubt.",
        "Yes, absolutely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    
    response = random.choice(responses)
    
    embed = create_embed(
        title="🎱 Magic 8-Ball",
        description=f"**Question:** {question}\n\n**Answer:** {response}",
        color=discord.Color.purple(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def flip(interaction: discord.Interaction):
    """Flip a coin"""
    result = random.choice(["Heads", "Tails"])
    emoji = "🪙" if result == "Heads" else "🪙"
    
    embed = create_embed(
        title=f"{emoji} Coin Flip",
        description=f"The coin landed on **{result}**!",
        color=discord.Color.gold(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def roll(interaction: discord.Interaction, sides: int = 6):
    """Roll a dice"""
    if sides < 2 or sides > 100:
        await interaction.response.send_message("Sides must be between 2 and 100.", ephemeral=True)
        return
    
    result = random.randint(1, sides)
    
    embed = create_embed(
        title="🎲 Dice Roll",
        description=f"Rolled a {sides}-sided die and got **{result}**!",
        color=discord.Color.green(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def random_number(interaction: discord.Interaction, min_val: int, max_val: int):
    """Generate a random number"""
    if min_val >= max_val:
        await interaction.response.send_message("Min must be less than max.", ephemeral=True)
        return

    result = random.randint(min_val, max_val)

    embed = create_embed(
        title="🔢 Random Number",
        description=f"Random number between {min_val} and {max_val}: **{result}**",
        color=discord.Color.blue(),
        message_type="general"
    )

    await interaction.response.send_message(embed=embed)


async def choose(interaction: discord.Interaction, options: str):
    """Choose between options"""
    option_list = [opt.strip() for opt in options.split(",")]
    
    if len(option_list) < 2:
        await interaction.response.send_message("Please provide at least 2 options separated by commas.", ephemeral=True)
        return
    
    choice = random.choice(option_list)
    
    embed = create_embed(
        title="🎯 Random Choice",
        description=f"Options: {', '.join(option_list)}\n\n**I choose:** {choice}",
        color=discord.Color.purple(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def poll(interaction: discord.Interaction, question: str, options: str):
    """Create a poll"""
    option_list = [opt.strip() for opt in options.split(",")]
    
    if len(option_list) < 2 or len(option_list) > 10:
        await interaction.response.send_message("Please provide 2-10 options separated by commas.", ephemeral=True)
        return
    
    if len(option_list) > 4:
        await interaction.response.send_message("For polls with more than 4 options, please use /createpoll (coming soon). Currently limited to 4 for reaction-based polls.", ephemeral=True)
        option_list = option_list[:4]
    
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    
    poll_text = f"📊 **Poll:** {question}\n\n"
    for i, option in enumerate(option_list):
        poll_text += f"{emojis[i]} {option}\n"
    
    embed = create_embed(
        title="📊 New Poll",
        description=poll_text,
        color=discord.Color.blue(),
        message_type="general"
    )
    
    message = await interaction.channel.send(embed=embed)
    
    for i in range(len(option_list)):
        await message.add_reaction(emojis[i])
    
    await interaction.response.send_message("Poll created!", ephemeral=True)


async def suggest(interaction: discord.Interaction, suggestion: str):
    """Submit a suggestion"""
    # Check if suggestion channel is configured
    # You can add a SUGGESTION_CHANNEL_ID to config.py
    
    embed = create_embed(
        title="💡 New Suggestion",
        description=suggestion,
        color=discord.Color.green(),
        message_type="general",
        fields=[
            ("Author", interaction.user.mention, True),
            ("Status", "📝 Pending Review", True)
        ]
    )
    
    # Add to current channel (you can modify to send to a specific channel)
    message = await interaction.channel.send(embed=embed)
    
    # Add reactions for voting
    await message.add_reaction("👍")
    await message.add_reaction("👎")
    
    await interaction.response.send_message("Suggestion submitted!", ephemeral=True)


async def hug(interaction: discord.Interaction, member: discord.Member = None):
    """Hug someone"""
    if member is None:
        member = interaction.user
    
    hug_messages = [
        f"{interaction.user.mention} gives {member.mention} a warm hug! 🤗",
        f"{interaction.user.mention} hugs {member.mention} tightly! ❤️",
        f"{interaction.user.mention} gives {member.mention} a big bear hug! 🐻",
        f"{interaction.user.mention} wraps {member.mention} in a cozy hug! ✨"
    ]
    
    message = random.choice(hug_messages)
    
    embed = create_embed(
        title="🤗 Hug",
        description=message,
        color=discord.Color.pink(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def slap(interaction: discord.Interaction, member: discord.Member = None):
    """Slap someone"""
    if member is None:
        member = interaction.user
    
    slap_messages = [
        f"{interaction.user.mention} slaps {member.mention} with a trout! 🐟",
        f"{interaction.user.mention} slaps {member.mention} across the face! 👋",
        f"{interaction.user.mention} gives {member.mention} a gentle slap! 🤚",
        f"{interaction.user.mention} slaps {member.mention} with a wet noodle! 🍝"
    ]
    
    message = random.choice(slap_messages)
    
    embed = create_embed(
        title="👋 Slap",
        description=message,
        color=discord.Color.orange(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def pat(interaction: discord.Interaction, member: discord.Member = None):
    """Pat someone"""
    if member is None:
        member = interaction.user
    
    pat_messages = [
        f"{interaction.user.mention} pats {member.mention} on the head! 👋",
        f"{interaction.user.mention} gives {member.mention} a gentle pat! 🥰",
        f"{interaction.user.mention} pats {member.mention} affectionately! ✨",
        f"{interaction.user.mention} gives {member.mention} headpats! 🐱"
    ]
    
    message = random.choice(pat_messages)
    
    embed = create_embed(
        title="👋 Pat",
        description=message,
        color=discord.Color.blue(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)
async def serverinfo(interaction: discord.Interaction):
    """Display detailed server information"""
    guild = interaction.guild
    
    # Calculate member counts
    total_members = guild.member_count
    online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
    bot_count = sum(1 for m in guild.members if m.bot)
    human_count = total_members - bot_count
    
    # Get role count
    role_count = len(guild.roles) - 1  # Exclude @everyone
    
    # Get channel counts
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    total_channels = text_channels + voice_channels
    
    # Server age
    server_age = (datetime.now(timezone.utc) - guild.created_at).days
    
    embed = create_embed(
        title=f"📊 Server Information - {guild.name}",
        description=f"**Owner:** {guild.owner.mention}\n**Server ID:** `{guild.id}`\n**Created:** {guild.created_at.strftime('%B %d, %Y')} ({server_age} days ago)",
        color=discord.Color.blue(),
        message_type="general",
        fields=[
            ("Members", f"Total: {total_members}\nHumans: {human_count}\nBots: {bot_count}\nOnline: {online_members}", True),
            ("Channels", f"Text: {text_channels}\nVoice: {voice_channels}\nTotal: {total_channels}", True),
            ("Roles", str(role_count), True),
            ("Boost Level", f"Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts", True),
            ("Verification", str(guild.verification_level).replace("VerificationLevel.", " ").title(), True),
            ("Region", str(guild.region).replace("Region.", " ").title() if hasattr(guild, 'region') else "N/A", True)
        ]
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    if guild.banner:
        embed.set_image(url=guild.banner.url)
    
    await interaction.response.send_message(embed=embed)


async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    """Display detailed user information"""
    if member is None:
        member = interaction.user
    
    # Calculate account age
    account_age = (datetime.now(timezone.utc) - member.created_at).days
    
    # Calculate server join age
    join_age = (datetime.now(timezone.utc) - member.joined_at).days if member.joined_at else 0
    
    # Get top role
    top_role = member.top_role if member.top_role.name != "@everyone" else "None"
    
    # Get role list
    roles = [role.mention for role in member.roles if role.name != "@everyone"]
    roles_list = ", ".join(roles) if roles else "No roles"
    
    # Account status
    is_bot = "🤖 Bot" if member.bot else "👤 Human"
    
    embed = create_embed(
        title=f"👤 User Information - {member.name}",
        description=f"**Display Name:** {member.display_name}\n**User ID:** `{member.id}`\n**Type:** {is_bot}",
        color=member.color if member.color.value != 0 else discord.Color.blue(),
        message_type="general",
        fields=[
            ("Account Created", f"{member.created_at.strftime('%B %d, %Y')}\n({account_age} days ago)", True),
            ("Joined Server", f"{member.joined_at.strftime('%B %d, %Y') if member.joined_at else 'N/A'}\n({join_age} days ago)", True),
            ("Top Role", top_role.name if isinstance(top_role, discord.Role) else top_role, True),
            ("Roles", roles_list[:100] + "..." if len(roles_list) > 100 else roles_list, False)
        ]
    )
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    if member.banner:
        embed.set_image(url=member.banner.url)
    
    await interaction.response.send_message(embed=embed)


async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    """View a user's avatar"""
    if member is None:
        member = interaction.user
    
    if member.avatar:
        embed = create_embed(
            title=f"🖼️ {member.name}'s Avatar",
            color=discord.Color.blue(),
            message_type="general"
        )
        embed.set_image(url=member.avatar.url)
        await interaction.response.send_message(embed=embed)
    else:
        embed = create_embed(
            title="❌ No Avatar",
            description=f"{member.mention} doesn't have a custom avatar.",
            color=discord.Color.red(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)


async def banner(interaction: discord.Interaction, member: discord.Member = None):
    """View a user's banner"""
    if member is None:
        member = interaction.user
    
    if member.banner:
        embed = create_embed(
            title=f"🖼️ {member.name}'s Banner",
            color=discord.Color.blue(),
            message_type="general"
        )
        embed.set_image(url=member.banner.url)
        await interaction.response.send_message(embed=embed)
    else:
        embed = create_embed(
            title="❌ No Banner",
            description=f"{member.mention} doesn't have a custom banner.",
            color=discord.Color.red(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)


async def ping(interaction: discord.Interaction):
    """Check bot latency"""
    # Measure websocket latency
    websocket_ping = round(bot.latency * 1000)
    
    # Measure round-trip latency
    start_time = datetime.now(timezone.utc)
    await interaction.response.defer()
    end_time = datetime.now(timezone.utc)
    roundtrip_ping = round((end_time - start_time).total_seconds() * 1000)
    
    embed = create_embed(
        title="🏓 Pong!",
        description=f"**WebSocket Latency:** {websocket_ping}ms\n**Round-trip Latency:** {roundtrip_ping}ms",
        color=discord.Color.green() if websocket_ping < 100 else discord.Color.orange() if websocket_ping < 200 else discord.Color.red(),
        message_type="general"
    )
    
    await interaction.followup.send(embed=embed)


async def botstats(interaction: discord.Interaction):
    """View bot statistics"""
    # Calculate uptime
    uptime = datetime.now(timezone.utc) - bot.start_time if hasattr(bot, 'start_time') else timedelta(0)
    uptime_str = str(uptime).split('.')[0]
    
    # Server count
    server_count = len(bot.guilds)
    
    # Total members
    total_members = sum(guild.member_count for guild in bot.guilds)
    
    # Total channels
    total_channels = sum(len(guild.channels) for guild in bot.guilds)
    
    embed = create_embed(
        title="🤖 Bot Statistics",
        description=f"**Bot Name:** {bot.user.name}\n**Bot ID:** `{bot.user.id}`\n**Uptime:** {uptime_str}",
        color=discord.Color.blue(),
        message_type="general",
        fields=[
            ("Servers", str(server_count), True),
            ("Total Members", str(total_members), True),
            ("Total Channels", str(total_channels), True),
            ("Ping", f"{round(bot.latency * 1000)}ms", True),
            ("Python Version", "3.8+", True),
            ("Library", "discord.py 2.x", True)
        ]
    )
    
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    
    await interaction.response.send_message(embed=embed)


# ============ MODERATION COMMANDS ============

async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    """Kick a member from the server"""
    # Check if user can kick this member
    if member.top_role >= interaction.user.top_role and member != interaction.user:
        await interaction.response.send_message("You cannot kick someone with a higher or equal role.", ephemeral=True)
        return
    
    if member == interaction.user:
        await interaction.response.send_message("You cannot kick yourself.", ephemeral=True)
        return
    
    if member == guild.owner:
        await interaction.response.send_message("You cannot kick the server owner.", ephemeral=True)
        return
    
    try:
        await member.kick(reason=reason)
        embed = create_embed(
            title="👢 Member Kicked",
            description=f"**User:** {member.mention}\n**Reason:** {reason or 'No reason provided'}\n**Moderator:** {interaction.user.mention}",
            color=discord.Color.orange(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to kick this member.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error kicking member: {str(e)}", ephemeral=True)


async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None, delete_message_days: int = 0):
    """Ban a member from the server"""
    guild = interaction.guild
    
    # Check if user can ban this member
    if member.top_role >= interaction.user.top_role and member != interaction.user:
        await interaction.response.send_message("You cannot ban someone with a higher or equal role.", ephemeral=True)
        return
    
    if member == interaction.user:
        await interaction.response.send_message("You cannot ban yourself.", ephemeral=True)
        return
    
    if member == guild.owner:
        await interaction.response.send_message("You cannot ban the server owner.", ephemeral=True)
        return
    
    try:
        await member.ban(reason=reason, delete_message_days=delete_message_days)
        embed = create_embed(
            title="🔨 Member Banned",
            description=f"**User:** {member.mention}\n**Reason:** {reason or 'No reason provided'}\n**Delete Messages:** {delete_message_days} days\n**Moderator:** {interaction.user.mention}",
            color=discord.Color.red(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to ban this member.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error banning member: {str(e)}", ephemeral=True)


async def unban(interaction: discord.Interaction, user_id: str):
    """Unban a user from the server"""
    guild = interaction.guild
    
    try:
        user_id = int(user_id)
        user = await bot.fetch_user(user_id)
        
        await guild.unban(user)
        embed = create_embed(
            title="🔓 User Unbanned",
            description=f"**User:** {user.mention}\n**Moderator:** {interaction.user.mention}",
            color=discord.Color.green(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except ValueError:
        await interaction.response.send_message("Invalid user ID. Please provide a valid ID.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("This user is not banned.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to unban this user.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error unbanning user: {str(e)}", ephemeral=True)


async def purge(interaction: discord.Interaction, amount: int):
    """Delete multiple messages"""
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
        return
    
    try:
        deleted = await interaction.channel.purge(limit=amount)
        embed = create_embed(
            title="🗑️ Messages Deleted",
            description=f"Successfully deleted {len(deleted)} messages.",
            color=discord.Color.green(),
            message_type="general"
        )
        await interaction.channel.send(embed=embed, delete_after=5)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to delete messages.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error deleting messages: {str(e)}", ephemeral=True)


async def slowmode(interaction: discord.Interaction, seconds: int):
    """Set slowmode for the channel"""
    if seconds < 0 or seconds > 21600:
        await interaction.response.send_message("Slowmode must be between 0 and 21600 seconds (6 hours).", ephemeral=True)
        return
    
    try:
        await interaction.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            embed = create_embed(
                title="✅ Slowmode Disabled",
                description="Slowmode has been disabled for this channel.",
                color=discord.Color.green(),
                message_type="general"
            )
        else:
            embed = create_embed(
                title="✅ Slowmode Enabled",
                description=f"Slowmode has been set to {seconds} seconds for this channel.",
                color=discord.Color.green(),
                message_type="general"
            )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to edit this channel.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error setting slowmode: {str(e)}", ephemeral=True)


async def lock(interaction: discord.Interaction):
    """Lock the channel"""
    try:
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        embed = create_embed(
            title="🔒 Channel Locked",
            description="This channel has been locked.",
            color=discord.Color.orange(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to lock this channel.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error locking channel: {str(e)}", ephemeral=True)


async def unlock(interaction: discord.Interaction):
    """Unlock the channel"""
    try:
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=None)
        embed = create_embed(
            title="🔓 Channel Unlocked",
            description="This channel has been unlocked.",
            color=discord.Color.green(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission to unlock this channel.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error unlocking channel: {str(e)}", ephemeral=True)


# ============ FUN & COMMUNITY COMMANDS ============

async def eightball(interaction: discord.Interaction, question: str):
    """Ask the magic 8-ball a question"""
    responses = [
        "Yes, definitely.",
        "It is certain.",
        "Without a doubt.",
        "Yes, absolutely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    
    response = random.choice(responses)
    
    embed = create_embed(
        title="🎱 Magic 8-Ball",
        description=f"**Question:** {question}\n\n**Answer:** {response}",
        color=discord.Color.purple(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def flip(interaction: discord.Interaction):
    """Flip a coin"""
    result = random.choice(["Heads", "Tails"])
    emoji = "🪙" if result == "Heads" else "🪙"
    
    embed = create_embed(
        title=f"{emoji} Coin Flip",
        description=f"The coin landed on **{result}**!",
        color=discord.Color.gold(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def roll(interaction: discord.Interaction, sides: int = 6):
    """Roll a dice"""
    if sides < 2 or sides > 100:
        await interaction.response.send_message("Sides must be between 2 and 100.", ephemeral=True)
        return
    
    result = random.randint(1, sides)
    
    embed = create_embed(
        title="🎲 Dice Roll",
        description=f"Rolled a {sides}-sided die and got **{result}**!",
        color=discord.Color.green(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def random_number(interaction: discord.Interaction, min_val: int, max_val: int):
    """Generate a random number"""
    if min_val >= max_val:
        await interaction.response.send_message("Min must be less than max.", ephemeral=True)
        return

    result = random.randint(min_val, max_val)

    embed = create_embed(
        title="🔢 Random Number",
        description=f"Random number between {min_val} and {max_val}: **{result}**",
        color=discord.Color.blue(),
        message_type="general"
    )

    await interaction.response.send_message(embed=embed)


async def choose(interaction: discord.Interaction, options: str):
    """Choose between options"""
    option_list = [opt.strip() for opt in options.split(",")]
    
    if len(option_list) < 2:
        await interaction.response.send_message("Please provide at least 2 options separated by commas.", ephemeral=True)
        return
    
    choice = random.choice(option_list)
    
    embed = create_embed(
        title="🎯 Random Choice",
        description=f"Options: {', '.join(option_list)}\n\n**I choose:** {choice}",
        color=discord.Color.purple(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def poll(interaction: discord.Interaction, question: str, options: str):
    """Create a poll"""
    option_list = [opt.strip() for opt in options.split(",")]
    
    if len(option_list) < 2 or len(option_list) > 10:
        await interaction.response.send_message("Please provide 2-10 options separated by commas.", ephemeral=True)
        return
    
    if len(option_list) > 4:
        await interaction.response.send_message("For polls with more than 4 options, please use /createpoll (coming soon). Currently limited to 4 for reaction-based polls.", ephemeral=True)
        option_list = option_list[:4]
    
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    
    poll_text = f"📊 **Poll:** {question}\n\n"
    for i, option in enumerate(option_list):
        poll_text += f"{emojis[i]} {option}\n"
    
    embed = create_embed(
        title="📊 New Poll",
        description=poll_text,
        color=discord.Color.blue(),
        message_type="general"
    )
    
    message = await interaction.channel.send(embed=embed)
    
    for i in range(len(option_list)):
        await message.add_reaction(emojis[i])
    
    await interaction.response.send_message("Poll created!", ephemeral=True)


async def suggest(interaction: discord.Interaction, suggestion: str):
    """Submit a suggestion"""
    # Check if suggestion channel is configured
    # You can add a SUGGESTION_CHANNEL_ID to config.py
    
    embed = create_embed(
        title="💡 New Suggestion",
        description=suggestion,
        color=discord.Color.green(),
        message_type="general",
        fields=[
            ("Author", interaction.user.mention, True),
            ("Status", "📝 Pending Review", True)
        ]
    )
    
    # Add to current channel (you can modify to send to a specific channel)
    message = await interaction.channel.send(embed=embed)
    
    # Add reactions for voting
    await message.add_reaction("👍")
    await message.add_reaction("👎")
    
    await interaction.response.send_message("Suggestion submitted!", ephemeral=True)


async def hug(interaction: discord.Interaction, member: discord.Member = None):
    """Hug someone"""
    if member is None:
        member = interaction.user
    
    hug_messages = [
        f"{interaction.user.mention} gives {member.mention} a warm hug! 🤗",
        f"{interaction.user.mention} hugs {member.mention} tightly! ❤️",
        f"{interaction.user.mention} gives {member.mention} a big bear hug! 🐻",
        f"{interaction.user.mention} wraps {member.mention} in a cozy hug! ✨"
    ]
    
    message = random.choice(hug_messages)
    
    embed = create_embed(
        title="🤗 Hug",
        description=message,
        color=discord.Color.pink(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def slap(interaction: discord.Interaction, member: discord.Member = None):
    """Slap someone"""
    if member is None:
        member = interaction.user
    
    slap_messages = [
        f"{interaction.user.mention} slaps {member.mention} with a trout! 🐟",
        f"{interaction.user.mention} slaps {member.mention} across the face! 👋",
        f"{interaction.user.mention} gives {member.mention} a gentle slap! 🤚",
        f"{interaction.user.mention} slaps {member.mention} with a wet noodle! 🍝"
    ]
    
    message = random.choice(slap_messages)
    
    embed = create_embed(
        title="👋 Slap",
        description=message,
        color=discord.Color.orange(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)


async def pat(interaction: discord.Interaction, member: discord.Member = None):
    """Pat someone"""
    if member is None:
        member = interaction.user
    
    pat_messages = [
        f"{interaction.user.mention} pats {member.mention} on the head! 👋",
        f"{interaction.user.mention} gives {member.mention} a gentle pat! 🥰",
        f"{interaction.user.mention} pats {member.mention} affectionately! ✨",
        f"{interaction.user.mention} gives {member.mention} headpats! 🐱"
    ]
    
    message = random.choice(pat_messages)
    
    embed = create_embed(
        title="👋 Pat",
        description=message,
        color=discord.Color.blue(),
        message_type="general"
    )
    
    await interaction.response.send_message(embed=embed)
