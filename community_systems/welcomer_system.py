"""
Welcomer system module - Welcome messages for new members
"""
import discord
from discord import app_commands
import json
import os
import asyncio
from config import SUPPORT_ROLE_ID, get_data_dir
from utilities.embed_utils import create_embed


async def load_welcome_config():
    """Load welcome config from Firebase"""
    try:
        from firebase_client import get_welcome_config
        config = await get_welcome_config()
        if config:
            return config
    except Exception as e:
        print(f"Error loading welcome config from Firebase: {e}")

    # Default configuration with user's desired format
    return {
        "welcome_enabled": False,
        "welcome_channel_id": 0,
        "welcome_message": """🚀 Welcome {user} to Trading Vault ™ | Mcfa , Capes , Nitros! ⚡

📜 Head over to <#1552991912552824883> to make sure all transactions and chats stay safe and smooth.

🏷️ Visit <#1552991912552824883> to grab your ping roles for inventory restocks and deal alerts.

💬 Jump into <#1552991912552824883> to introduce yourself, or open a ticket when you're ready to buy, sell, or trade Minecraft accounts, capes, and gear""",
        "goodbye_enabled": False,
        "goodbye_channel_id": 0,
        "goodbye_message": "Goodbye {user}! We'll miss you.",
        "styled_welcome": True,
        "welcome_image": "https://media.discordapp.net/attachments/1556272868268965938/1558804707659747489/image.png?ex=6accc583&is=6acb7403&hm=d1d9d17a9a09d04e870f5ad93450e61560c59e9aabe958ec43292a278f1309f9&=&format=webp&quality=lossless&width=640&height=357",
        "thumbnail_image": "",
        "embed_title": "Trading Vault",
        "embed_color": "#9b59b6",
        "footer_text": "Made by Shashank Sharma"
    }


async def save_welcome_config(config):
    """Save welcome config to Firebase"""
    try:
        from firebase_client import set_welcome_config
        await set_welcome_config(config)
    except Exception as e:
        print(f"Error saving welcome config to Firebase: {e}")


async def send_welcome(member):
    """Send welcome message to new member"""
    config = await load_welcome_config()

    if not config.get("welcome_enabled", False):
        return

    welcome_channel_id = config.get("welcome_channel_id")
    if not welcome_channel_id:
        return

    welcome_channel = member.guild.get_channel(welcome_channel_id)
    if not welcome_channel:
        return

    # Get welcome message from database, with default template
    welcome_message = config.get("welcome_message", """🚀 Welcome {user} to Trading Vault ™ | Mcfa , Capes , Nitros! ⚡

📜 Head over to <#1552991912552824883> to make sure all transactions and chats stay safe and smooth.

🏷️ Visit <#1552991912552824883> to grab your ping roles for inventory restocks and deal alerts.

💬 Jump into <#1552991912552824883> to introduce yourself, or open a ticket when you're ready to buy, sell, or trade Minecraft accounts, capes, and gear""")

    # Replace placeholders
    welcome_message = welcome_message.replace("{user}", member.mention)
    welcome_message = welcome_message.replace("{server}", member.guild.name)
    welcome_message = welcome_message.replace("{count}", str(member.guild.member_count))
    welcome_message = welcome_message.replace("{username}", member.name)
    welcome_message = welcome_message.replace("{discriminator}", member.discriminator)

    # Get embed title from database or use default
    embed_title = config.get("embed_title", "Trading Vault")

    # Get embed color from database or use purple
    color_hex = config.get("embed_color", "#9b59b6")  # Purple hex code
    try:
        color = discord.Color.from_str(color_hex)
    except:
        color = discord.Color.purple()

    # Send welcome message
    if config.get("styled_welcome", False):
        # Styled welcome with image
        embed = discord.Embed(
            title=embed_title,
            description=welcome_message,
            color=color
        )

        # Add thumbnail - prefer custom thumbnail from database, otherwise use user's profile picture
        thumbnail_image = config.get("thumbnail_image")
        if thumbnail_image:
            embed.set_thumbnail(url=thumbnail_image)
        elif member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        # Add welcome banner image from database or use default
        welcome_image = config.get("welcome_image", "https://media.discordapp.net/attachments/1556272868268965938/1558804707659747489/image.png?ex=6accc583&is=6acb7403&hm=d1d9d17a9a09d04e870f5ad93450e61560c59e9aabe958ec43292a278f1309f9&=&format=webp&quality=lossless&width=640&height=357")
        if welcome_image:
            embed.set_image(url=welcome_image)

        # Add footer from database or use default
        footer_text = config.get("footer_text", "Made by Shashank Sharma")
        embed.set_footer(text=footer_text)

        await welcome_channel.send(embed=embed)
    else:
        # Standard welcome
        await welcome_channel.send(welcome_message)
        embed = create_embed(
            title="🎉 Welcome!",
            description=welcome_message,
            color=discord.Color.green(),
            message_type="general"
        )

        # Add user avatar if available
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        await welcome_channel.send(embed=embed)


async def send_goodbye(member):
    """Send goodbye message when member leaves"""
    config = await load_welcome_config()

    if not config.get("goodbye_enabled", False):
        return

    goodbye_channel_id = config.get("goodbye_channel_id")
    if not goodbye_channel_id:
        return

    goodbye_channel = member.guild.get_channel(goodbye_channel_id)
    if not goodbye_channel:
        return

    # Get goodbye message
    goodbye_message = config.get("goodbye_message", "Goodbye {user}!")

    # Replace placeholders
    goodbye_message = goodbye_message.replace("{user}", member.mention)
    goodbye_message = goodbye_message.replace("{server}", member.guild.name)

    # Send goodbye message
    embed = create_embed(
        title="👋 Goodbye!",
        description=goodbye_message,
        color=discord.Color.red(),
        message_type="general"
    )
    await goodbye_channel.send(embed=embed)


# Configuration commands
async def setwelcomemessage_command(interaction: discord.Interaction, message: str):
    """Set the welcome message"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set welcome messages.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    config["welcome_message"] = message
    config["welcome_enabled"] = True
    await save_welcome_config(config)

    embed = create_embed(
        title="✅ Welcome Message Set",
        description=f"Welcome message has been set to:\n\n{message}\n\nAvailable placeholders: {{user}}, {{server}}, {{count}}, {{username}}, {{discriminator}}",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def setwelcomerchannel_command(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the welcome channel"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set welcome channels.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    config["welcome_channel_id"] = channel.id
    config["welcome_enabled"] = True
    await save_welcome_config(config)

    embed = create_embed(
        title="✅ Welcome Channel Set",
        description=f"Welcome channel has been set to {channel.mention}",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def togglewelcome_command(interaction: discord.Interaction):
    """Toggle welcome messages on/off"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can toggle welcome messages.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    current_state = config.get("welcome_enabled", False)
    config["welcome_enabled"] = not current_state
    await save_welcome_config(config)

    status = "enabled" if config["welcome_enabled"] else "disabled"
    embed = create_embed(
        title="✅ Welcome Messages Toggled",
        description=f"Welcome messages are now **{status}**",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def setgoodbyemessage_command(interaction: discord.Interaction, message: str):
    """Set the goodbye message"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set goodbye messages.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    config["goodbye_message"] = message
    config["goodbye_enabled"] = True
    await save_welcome_config(config)

    embed = create_embed(
        title="✅ Goodbye Message Set",
        description=f"Goodbye message has been set to:\n\n{message}",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def setgoodbyechannel_command(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the goodbye channel"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set goodbye channels.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    config["goodbye_channel_id"] = channel.id
    config["goodbye_enabled"] = True
    await save_welcome_config(config)

    embed = create_embed(
        title="✅ Goodbye Channel Set",
        description=f"Goodbye channel has been set to {channel.mention}",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def togglegoodbye_command(interaction: discord.Interaction):
    """Toggle goodbye messages on/off"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can toggle goodbye messages.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    current_state = config.get("goodbye_enabled", False)
    config["goodbye_enabled"] = not current_state
    await save_welcome_config(config)

    status = "enabled" if config["goodbye_enabled"] else "disabled"
    embed = create_embed(
        title="✅ Goodbye Messages Toggled",
        description=f"Goodbye messages are now **{status}**",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def welcomeconfig_command(interaction: discord.Interaction):
    """Show current welcome configuration"""
    config = await load_welcome_config()

    embed = create_embed(
        title="⚙️ Welcome Configuration",
        description="Current welcome system settings:",
        color=discord.Color.blue(),
        fields=[
            ("Welcome Enabled", "✅ Yes" if config.get("welcome_enabled", False) else "❌ No", True),
            ("Welcome Channel", f"<#{config.get('welcome_channel_id')}>" if config.get("welcome_channel_id") else "Not set", True),
            ("Styled Welcome", "✅ Yes" if config.get("styled_welcome", False) else "❌ No", True),
            ("Banner Image", "✅ Set" if config.get("welcome_image") else "❌ Not set", True),
            ("Thumbnail Image", "✅ Set" if config.get("thumbnail_image") else "❌ Not set", True),
            ("Goodbye Enabled", "✅ Yes" if config.get("goodbye_enabled", False) else "❌ No", True),
            ("Goodbye Channel", f"<#{config.get('goodbye_channel_id')}>" if config.get("goodbye_channel_id") else "Not set", True),
            ("Welcome Message", config.get("welcome_message", "Not set")[:100] + "..." if len(config.get("welcome_message", "")) > 100 else config.get("welcome_message", "Not set"), False),
            ("Goodbye Message", config.get("goodbye_message", "Not set")[:100] + "..." if len(config.get("goodbye_message", "")) > 100 else config.get("goodbye_message", "Not set"), False)
        ]
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def togglestyledwelcome_command(interaction: discord.Interaction):
    """Toggle styled welcome messages on/off"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can toggle styled welcome messages.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    current_state = config.get("styled_welcome", False)
    config["styled_welcome"] = not current_state
    await save_welcome_config(config)

    status = "enabled" if config["styled_welcome"] else "disabled"
    embed = create_embed(
        title="✅ Styled Welcome Toggled",
        description=f"Styled welcome messages are now **{status}**",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def setwelcomeimage_command(interaction: discord.Interaction, image_url: str):
    """Set the welcome image URL"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set welcome images.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    config["welcome_image"] = image_url
    await save_welcome_config(config)

    embed = create_embed(
        title="✅ Welcome Banner Image Set",
        description=f"Welcome banner image has been set to:\n{image_url}",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def setthumbnailimage_command(interaction: discord.Interaction, image_url: str):
    """Set the thumbnail image URL"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set thumbnail images.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    config["thumbnail_image"] = image_url
    await save_welcome_config(config)

    embed = create_embed(
        title="✅ Thumbnail Image Set",
        description=f"Thumbnail image has been set to:\n{image_url}\n\nNote: This overrides the user's profile picture if set.",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def setwelcometitle_command(interaction: discord.Interaction, title: str):
    """Set the welcome embed title"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set welcome title.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    config["embed_title"] = title
    await save_welcome_config(config)

    embed = create_embed(
        title="✅ Welcome Title Set",
        description=f"Welcome embed title has been set to:\n{title}",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def setwelcomecolor_command(interaction: discord.Interaction, color_hex: str):
    """Set the welcome embed color"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set welcome color.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    config["embed_color"] = color_hex
    await save_welcome_config(config)

    embed = create_embed(
        title="✅ Welcome Color Set",
        description=f"Welcome embed color has been set to:\n{color_hex}\n\nExample: #9b59b6 for purple",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def setwelcomefooter_command(interaction: discord.Interaction, footer_text: str):
    """Set the welcome embed footer"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can set welcome footer.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    config = await load_welcome_config()
    config["footer_text"] = footer_text
    await save_welcome_config(config)

    embed = create_embed(
        title="✅ Welcome Footer Set",
        description=f"Welcome embed footer has been set to:\n{footer_text}",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
