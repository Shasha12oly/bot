"""
Professional Discord Bot (discord.py 2.x)

Features:
- Support Ticket System (General Support, Account Issue)
- Purchase Ticket System (Capes, Minecraft Accounts, Discord Nitro, Boosts, Discord Decoration)
- Giveaway System (Host giveaways with multiple winners)
- Invite Tracker (Track who invited whom)
- Welcomer System (Welcome/goodbye messages)
- Priority system (Low, Medium, High)
- Close confirmation dialog
- Reopen closed tickets
- User DM notifications
- Professional embed styling
- Transcript logging
- UPI QR Code Generator
- LTC Payment System
- Firebase Firestore Database

Setup:
  pip install -U discord.py python-dotenv firebase-admin
  Copy .env.example to .env and fill in your values
  Run: python ticket_bot.py
  Then, in your server, run /ticketpanel for support or /purchasepanel for purchases.
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timezone
import io
import asyncio
import sys
import os
from utilities.logger import bot_logger

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure data directory exists (for Railway deployment)
# Import startup before config to avoid circular dependency
from startup import ensure_data_directory
ensure_data_directory()

# Initialize Firebase
try:
    from firebase_client import initialize_firebase
    initialize_firebase()
    bot_logger.info("Firebase initialized successfully")
except Exception as e:
    bot_logger.warning(f"Firebase initialization failed: {e}")
    bot_logger.warning("Bot will continue without Firebase (some features may not work)")

# Import configuration
from config import (
    TOKEN, SUPPORT_ROLE_ID, CATEGORY_ID, LOG_CHANNEL_ID, SYNC_GUILD_ID,
    RATING_CHANNEL_ID, VOUCH_CHANNEL_ID, THUMBNAIL_URL, BANNER_URL,
    INR_QR_URL, LTC_QR_URL, INR_WALLET_ADDRESS, LTC_WALLET_ADDRESS,
    BANNER_SETTINGS, update_env_var, ENABLE_GIVEAWAYS, ENABLE_INVITE_TRACKER, ENABLE_WELCOMER,
    INVITE_ANNOUNCEMENT_CHANNEL_ID, AUTO_ROLE_ID, get_data_dir,
    load_banner_config
)

# Import utilities
from utilities.embed_utils import create_embed
from core_systems.ticket_utils import owner_tag, get_ticket_info

# Import core systems
from core_systems.support_system import OpenTicketView
from core_systems.purchase_system import PurchaseView
from core_systems.ticket_controls import SupportTicketControlView, PurchaseTicketControlView, ConfirmCloseView
from core_systems.payment_system import PaymentMethodView
from core_systems.ticket_close import close_ticket_final
from core_systems.ticket_management import create_ticket
from core_systems.store_system import post_price_list, setstorechannel_command, updatepricelist_command, storeinfo_command, post_cape_cards, setcapeimage_command, reloadstoreconfig_command, setstorebanner_command, getstorebanner_command, NITRO_STORE_DATA, DECORATION_STORE_DATA, BOOSTS_STORE_DATA

# Import community systems
from community_systems.rating_system import RatingView
from community_systems.vouch_system import load_vouches, save_vouches, handle_vouch_channel_message, get_vouch_info, get_leaderboard, setticketmessage_command, viewticketmessages_command
from community_systems.giveaway_system import giveaway_command, endgiveaway_command, reroll_command, check_giveaways, listgiveaways_command
from community_systems.invite_tracker import track_invites, check_invite_join, check_invite_leave, invitestats_command, inviteleaderboard_command, whoinvited_command, setinvitechannel_command, invitehistory_command, setinvitemilestone_command, post_leaderboard_command, update_leaderboards
from community_systems.welcomer_system import send_welcome, send_goodbye, setwelcomemessage_command, setwelcomerchannel_command, togglewelcome_command, setgoodbyemessage_command, setgoodbyechannel_command, togglegoodbye_command, welcomeconfig_command, togglestyledwelcome_command, setwelcomeimage_command, setthumbnailimage_command, setwelcometitle_command, setwelcomecolor_command, setwelcomefooter_command

# Import utilities
from utilities.utilities import (
    serverinfo, userinfo, avatar, banner, ping, botstats,
    kick, ban, unban, purge, slowmode, lock, unlock,
    eightball, flip, roll, random_number, choose, poll, suggest,
    hug, slap, pat
)
from utilities.role_management import (
    add_role_command, remove_role_command, list_roles_command,
    role_info_command, mute_command, unmute_command
)

# Import payment systems
from payment_systems.upi_qr_generator import generate_custom_qr, generate_qr_no_amount, list_preset_amounts, create_preset_qr, delete_preset_qr, send_preset_qr, generate_custom_ltc_qr, generate_ltc_qr_no_amount

intents = discord.Intents.default()
intents.message_content = True  # Required for ! commands
intents.members = True
intents.invites = True  # Required for invite tracking


class TicketBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.start_time = datetime.now(timezone.utc)

    async def setup_hook(self):
        bot_logger.info("Setting up bot...")

        self.add_view(OpenTicketView())
        self.add_view(PurchaseView())
        self.add_view(ConfirmCloseView())
        self.add_view(PaymentMethodView())
        self.add_view(RatingView())
        self.add_view(SupportTicketControlView())
        self.add_view(PurchaseTicketControlView())

        bot_logger.info("Added all persistent views")

        # Start giveaway checker task if enabled
        if ENABLE_GIVEAWAYS:
            self.giveaway_checker.start()
            bot_logger.info("Started giveaway checker task")

        # Start leaderboard updater task
        if ENABLE_INVITE_TRACKER:
            self.leaderboard_updater.start()
            bot_logger.info("Started leaderboard updater task")

        # Sync commands globally or to specific guild for faster updates
        # Due to command limit (100), we use global sync only
        bot_logger.info("Syncing commands globally")
        await self.tree.sync()

        bot_logger.info("Bot setup complete")

    # Giveaway checker task
    @tasks.loop(minutes=1)
    async def giveaway_checker(self):
        """Check for ended giveaways every minute"""
        await check_giveaways(self)

    @giveaway_checker.before_loop
    async def before_giveaway_checker(self):
        """Wait for bot to be ready before starting task"""
        await self.wait_until_ready()
        bot_logger.info("Giveaway checker ready")

    # Leaderboard updater task
    @tasks.loop(seconds=10)
    async def leaderboard_updater(self):
        """Update auto-updating leaderboards every 10 seconds"""
        for guild in self.guilds:
            try:
                await update_leaderboards(guild)
            except Exception as e:
                bot_logger.error(f"Error updating leaderboard for guild {guild.id}: {e}")

    @leaderboard_updater.before_loop
    async def before_leaderboard_updater(self):
        """Wait for bot to be ready before starting task"""
        await self.wait_until_ready()
        bot_logger.info("Leaderboard updater ready")


bot = TicketBot()


# ============ BOT COMMANDS ============

@bot.tree.command(name="ticketpanel", description="Post the support ticket panel in this channel")
@app_commands.default_permissions(administrator=True)
async def ticketpanel(interaction: discord.Interaction):
    embed = create_embed(
        title="🎫 Support Ticket System",
        description="Welcome to our support system! Please select a category below to open a ticket.\n\nOur team will respond as soon as possible.",
        color=discord.Color.from_rgb(88, 101, 242),
        message_type="panel",
        fields=[
            ("Available Categories", "• 📧 General Support\n• 🎁 Claim Giveaway\n• 📖 Enquiry", False),
            ("Response Time", "Staff typically respond within 24 hours", False)
        ]
    )

    # Set banner image from config
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)

    await interaction.channel.send(embed=embed, view=OpenTicketView())
    await interaction.response.send_message("Support ticket panel posted successfully.", ephemeral=True)


@bot.tree.command(name="purchasepanel", description="Post the purchase ticket panel in this channel")
@app_commands.default_permissions(administrator=True)
async def purchasepanel(interaction: discord.Interaction):
    embed = create_embed(
        title="🛒 Purchase Ticket System",
        description="**How to Purchase:**\n1. Select the item you want to buy from the dropdown\n2. Fill in the purchase details\n3. Complete payment in the ticket channel\n4. Receive your item after payment confirmation\n\n**Payment & Delivery:**\n• Multiple payment methods accepted\n• Fast delivery within 1-24 hours\n• Secure and reliable service",
        color=discord.Color.from_rgb(114, 114, 255),  # #7272ff
        message_type="panel",
        fields=[
            ("Available Items", "• Capes\n• Minecraft Accounts\n• Discord Nitro\n• Boosts\n• Discord Decoration", False),
            ("Support", "Contact staff if you have any questions", False)
        ]
    )

    # Set banner image from config
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)

    await interaction.channel.send(embed=embed, view=PurchaseView())
    await interaction.response.send_message("Purchase panel posted successfully.", ephemeral=True)


@bot.tree.command(name="sync", description="Sync bot commands with Discord (admin only)")
@app_commands.default_permissions(administrator=True)
async def sync(interaction: discord.Interaction):
    """Force sync bot commands"""
    # Defer the response since sync can take time
    await interaction.response.defer(ephemeral=True)
    
    try:
        if SYNC_GUILD_ID:
            synced = await bot.tree.sync(guild=discord.Object(SYNC_GUILD_ID))
        else:
            synced = await bot.tree.sync()
        embed = create_embed(
            title="✅ Commands Synced",
            description=f"Successfully synced {len(synced)} commands",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        try:
            embed = create_embed(
                title="❌ Sync Failed",
                description=f"Error syncing commands: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send(f"Sync failed: {str(e)}", ephemeral=True)


@bot.tree.command(name="clearglobal", description="Clear all global commands to fix duplicates (admin only)")
@app_commands.default_permissions(administrator=True)
async def clearglobal(interaction: discord.Interaction):
    """Clear all global commands"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Clear all global commands
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        
        embed = create_embed(
            title="✅ Global Commands Cleared",
            description="All global commands have been cleared. Please restart the bot and use /sync to sync guild commands only.",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        try:
            embed = create_embed(
                title="❌ Clear Failed",
                description=f"Error clearing global commands: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send(f"Clear failed: {str(e)}", ephemeral=True)


@bot.tree.command(name="config", description="Configure bot settings (admin only)")
@app_commands.default_permissions(administrator=True)
async def config(interaction: discord.Interaction):
    """Show current configuration"""
    try:
        embed = create_embed(
            title="⚙️ Bot Configuration",
            description="Current bot settings:",
            color=discord.Color.blue(),
            message_type="config",
            fields=[
                ("Support Role ID", str(SUPPORT_ROLE_ID), True),
                ("Ticket Category ID", str(CATEGORY_ID), True),
                ("Log Channel ID", str(LOG_CHANNEL_ID), True),
                ("Rating Channel ID", str(RATING_CHANNEL_ID), True),
                ("Vouch Channel ID", str(VOUCH_CHANNEL_ID), True),
                ("Thumbnail URL", THUMBNAIL_URL if THUMBNAIL_URL else "Not set", False),
                ("Banner URL", BANNER_URL if BANNER_URL else "Not set", False),
                ("INR QR URL", INR_QR_URL if INR_QR_URL else "Not set", False),
                ("LTC QR URL", LTC_QR_URL if LTC_QR_URL else "Not set", False),
                ("INR Wallet", INR_WALLET_ADDRESS if INR_WALLET_ADDRESS else "Not set", False),
                ("LTC Wallet", LTC_WALLET_ADDRESS if LTC_WALLET_ADDRESS else "Not set", False)
            ]
        )
        
        # Add banner settings as a separate field
        banner_settings_text = "\n".join([
            f"• Ticket Creation: {'✅' if BANNER_SETTINGS['ticket_creation'] else '❌'}",
            f"• Purchase Creation: {'✅' if BANNER_SETTINGS['purchase_creation'] else '❌'}",
            f"• Ticket Controls: {'✅' if BANNER_SETTINGS['ticket_controls'] else '❌'}",
            f"• Payment Info: {'✅' if BANNER_SETTINGS['payment_info'] else '❌'}",
            f"• Rating: {'✅' if BANNER_SETTINGS['rating'] else '❌'}",
            f"• Vouch: {'✅' if BANNER_SETTINGS['vouch'] else '❌'}",
            f"• Panels: {'✅' if BANNER_SETTINGS['panel'] else '❌'}",
            f"• General: {'✅' if BANNER_SETTINGS['general'] else '❌'}",
        ])
        embed.add_field(name="Banner Settings", value=banner_settings_text, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.InteractionResponded:
        # If already responded, try to follow up
        try:
            await interaction.followup.send("Configuration already sent.", ephemeral=True)
        except:
            pass
    except Exception as e:
        try:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
        except:
            pass


@bot.tree.command(name="setcategory", description="Set the ticket category ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setcategory(interaction: discord.Interaction, category_id: str):
    """Set the category where tickets are created"""
    global CATEGORY_ID
    try:
        CATEGORY_ID = int(category_id)
        # Update .env file
        update_env_var("TICKET_CATEGORY_ID", category_id)
        
        embed = create_embed(
            title="✅ Category Updated",
            description=f"Ticket category ID has been set to `{category_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid category ID. Please provide a valid number.", ephemeral=True)


@bot.tree.command(name="setrole", description="Set the support role ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setrole(interaction: discord.Interaction, role_id: str):
    """Set the support/staff role"""
    global SUPPORT_ROLE_ID
    try:
        SUPPORT_ROLE_ID = int(role_id)
        # Update .env file
        update_env_var("SUPPORT_ROLE_ID", role_id)
        
        embed = create_embed(
            title="✅ Support Role Updated",
            description=f"Support role ID has been set to `{role_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid role ID. Please provide a valid number.", ephemeral=True)


@bot.tree.command(name="setlogchannel", description="Set the log channel ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setlogchannel(interaction: discord.Interaction, channel_id: str):
    """Set the channel for ticket transcripts"""
    global LOG_CHANNEL_ID
    try:
        LOG_CHANNEL_ID = int(channel_id)
        # Update .env file
        update_env_var("LOG_CHANNEL_ID", channel_id)
        
        embed = create_embed(
            title="✅ Log Channel Updated",
            description=f"Log channel ID has been set to `{channel_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid channel ID. Please provide a valid number.", ephemeral=True)


@bot.tree.command(name="setthumbnail", description="Set the thumbnail image URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setthumbnail(interaction: discord.Interaction, url: str):
    """Set the thumbnail image for embeds"""
    global THUMBNAIL_URL
    THUMBNAIL_URL = url
    # Update .env file
    update_env_var("THUMBNAIL_URL", url)
    
    embed = create_embed(
        title="✅ Thumbnail Updated",
        description=f"Thumbnail image has been set to the provided URL",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setbanner", description="Set the banner image URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setbanner(interaction: discord.Interaction, url: str):
    """Set the banner image for embeds"""
    global BANNER_URL
    BANNER_URL = url
    # Update .env file
    update_env_var("BANNER_URL", url)
    
    embed = create_embed(
        title="✅ Banner Updated",
        description=f"Banner image has been set to the provided URL",
        color=discord.Color.green()
    )
    embed.set_image(url=url)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="togglebanner", description="Toggle banner visibility for specific message types (admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(
    message_type=[
        app_commands.Choice(name="Ticket Creation", value="ticket_creation"),
        app_commands.Choice(name="Purchase Creation", value="purchase_creation"),
        app_commands.Choice(name="Ticket Controls", value="ticket_controls"),
        app_commands.Choice(name="Payment Info", value="payment_info"),
        app_commands.Choice(name="Rating", value="rating"),
        app_commands.Choice(name="Vouch", value="vouch"),
        app_commands.Choice(name="Panel", value="panel"),
        app_commands.Choice(name="General", value="general"),
        app_commands.Choice(name="All", value="all"),
    ]
)
async def togglebanner(interaction: discord.Interaction, message_type: str):
    """Toggle banner visibility for specific message types
    
    Args:
        message_type: Type of message (ticket_creation, purchase_creation, ticket_controls, payment_info, rating, vouch, panel, general, all)
    """
    from config import BANNER_SETTINGS as current_settings
    
    message_type = message_type.lower()
    
    if message_type == "all":
        # Toggle all settings
        new_state = not current_settings["general"]
        for key in current_settings:
            await set_banner_setting(key, new_state)

        status = "enabled" if new_state else "disabled"
        embed = create_embed(
            title="✅ All Banner Settings Toggled",
            description=f"Banners are now **{status}** for all message types.",
            color=discord.Color.green()
        )
    elif message_type in current_settings:
        # Toggle specific setting
        new_state = await toggle_banner_setting(message_type)
        
        status = "enabled" if new_state else "disabled"
        embed = create_embed(
            title="✅ Banner Setting Toggled",
            description=f"Banners for **{message_type}** messages are now **{status}**.",
            color=discord.Color.green()
        )
    else:
        # Show available options
        available_types = ", ".join(current_settings.keys()) + ", all"
        embed = create_embed(
            title="❌ Invalid Message Type",
            description=f"Available message types: {available_types}",
            color=discord.Color.red()
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="bannersettings", description="View current banner settings")
async def bannersettings(interaction: discord.Interaction):
    """View current banner settings"""
    from config import BANNER_SETTINGS as current_settings
    
    settings_text = ""
    for setting, enabled in current_settings.items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        settings_text += f"**{setting}:** {status}\n"
    
    embed = create_embed(
        title="🎨 Banner Settings",
        description=settings_text,
        color=discord.Color.blue(),
        message_type="general"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setinrqr", description="Set INR QR code URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setinrqr(interaction: discord.Interaction, url: str):
    """Set the INR QR code URL"""
    global INR_QR_URL
    INR_QR_URL = url
    update_env_var("INR_QR_URL", url)
    
    embed = create_embed(
        title="✅ INR QR Code Updated",
        description=f"INR QR code has been set to the provided URL",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setltcqr", description="Set LTC QR code URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setltcqr(interaction: discord.Interaction, url: str):
    """Set the LTC QR code URL"""
    global LTC_QR_URL
    LTC_QR_URL = url
    update_env_var("LTC_QR_URL", url)
    
    embed = create_embed(
        title="✅ LTC QR Code Updated",
        description=f"LTC QR code has been set to the provided URL",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setinrwallet", description="Set INR wallet address (admin only)")
@app_commands.default_permissions(administrator=True)
async def setinrwallet(interaction: discord.Interaction, address: str):
    """Set the INR wallet address"""
    global INR_WALLET_ADDRESS
    INR_WALLET_ADDRESS = address
    update_env_var("INR_WALLET_ADDRESS", address)
    
    embed = create_embed(
        title="✅ INR Wallet Updated",
        description=f"INR wallet address has been set",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setltcwallet", description="Set LTC wallet address (admin only)")
@app_commands.default_permissions(administrator=True)
async def setltcwallet(interaction: discord.Interaction, address: str):
    """Set the LTC wallet address"""
    global LTC_WALLET_ADDRESS
    LTC_WALLET_ADDRESS = address
    update_env_var("LTC_WALLET_ADDRESS", address)
    
    embed = create_embed(
        title="✅ LTC Wallet Updated",
        description=f"LTC wallet address has been set",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setratingchannel", description="Set rating channel ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setratingchannel(interaction: discord.Interaction, channel_id: str):
    """Set the channel for ratings"""
    global RATING_CHANNEL_ID
    try:
        RATING_CHANNEL_ID = int(channel_id)
        update_env_var("RATING_CHANNEL_ID", channel_id)
        
        embed = create_embed(
            title="✅ Rating Channel Updated",
            description=f"Rating channel ID has been set to `{channel_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid channel ID. Please provide a valid number.", ephemeral=True)


@bot.tree.command(name="setvouchchannel", description="Set vouch channel ID (admin only)")
@app_commands.default_permissions(administrator=True)
async def setvouchchannel(interaction: discord.Interaction, channel_id: str):
    """Set the channel for vouches"""
    global VOUCH_CHANNEL_ID
    try:
        VOUCH_CHANNEL_ID = int(channel_id)
        update_env_var("VOUCH_CHANNEL_ID", channel_id)
        
        embed = create_embed(
            title="✅ Vouch Channel Updated",
            description=f"Vouch channel ID has been set to `{channel_id}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Invalid channel ID. Please provide a valid number.", ephemeral=True)





@bot.tree.command(name="vouch", description="View vouch information for a user")
async def vouch_command(interaction: discord.Interaction, member: discord.Member = None):
    """View vouch information for a user"""
    await get_vouch_info(interaction, member)


@bot.tree.command(name="leaderboard", description="Show top vouched users")
async def leaderboard_command(interaction: discord.Interaction):
    """Show top vouched users"""
    await get_leaderboard(interaction)


@bot.tree.command(name="myvouches", description="View your own vouches")
async def myvouches_slash_command(interaction: discord.Interaction):
    """View your own vouches"""
    await get_vouch_info(interaction, interaction.user)


@bot.tree.command(name="setticketmessage", description="Configure ticket messages (admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(
    message_type=[
        app_commands.Choice(name="Ticket Creation", value="ticket_creation"),
        app_commands.Choice(name="Purchase Creation", value="purchase_creation"),
        app_commands.Choice(name="Payment Info", value="payment_info"),
        app_commands.Choice(name="Ticket Claimed", value="ticket_claimed"),
        app_commands.Choice(name="Ticket Closed", value="ticket_closed"),
    ]
)
async def setticketmessage(interaction: discord.Interaction, message_type: str, title: str = None, description: str = None, color: str = None):
    """Configure ticket messages"""
    await setticketmessage_command(interaction, message_type, title, description, color)


@bot.tree.command(name="viewticketmessages", description="View ticket message configuration (admin only)")
@app_commands.default_permissions(administrator=True)
async def viewticketmessages(interaction: discord.Interaction):
    """View ticket message configuration"""
    await viewticketmessages_command(interaction)


@bot.tree.command(name="claimed", description="View all claimed tickets (staff only)")
@app_commands.default_permissions(administrator=True)
async def claimed(interaction: discord.Interaction):
    """View all currently claimed tickets"""
    guild = interaction.guild
    category = guild.get_channel(CATEGORY_ID)
    
    if not category:
        await interaction.response.send_message("Ticket category not found.", ephemeral=True)
        return
    
    claimed_tickets = []
    
    for channel in category.text_channels:
        info = get_ticket_info(channel)
        if info.get("claimed_by"):
            claimed_member = guild.get_member(info["claimed_by"])
            owner = guild.get_member(info["owner_id"])
            
            claimed_tickets.append({
                "channel": channel,
                "claimed_by": claimed_member,
                "owner": owner,
                "category": info["category"],
                "priority": info.get("priority", "N/A"),
                "item": info.get("item", "N/A")
            })
    
    if not claimed_tickets:
        embed = create_embed(
            title="📋 Claimed Tickets",
            description="No tickets are currently claimed.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Create description with claimed tickets
    description = f"**Total Claimed: {len(claimed_tickets)}**\n\n"
    for i, ticket in enumerate(claimed_tickets, 1):
        claimed_name = ticket["claimed_by"].name if ticket["claimed_by"] else "Unknown"
        owner_name = ticket["owner"].name if ticket["owner"] else "Unknown"
        
        if ticket["category"] == "purchase":
            item_info = f"Item: {ticket['item']}"
        else:
            item_info = f"Priority: {ticket['priority']}"
        
        description += f"**{i}.** {ticket['channel'].mention}\n"
        description += f"   👤 Owner: {owner_name}\n"
        description += f"   ✋ Claimed by: {claimed_name}\n"
        description += f"   📂 {item_info}\n\n"
    
    embed = create_embed(
        title="📋 Claimed Tickets",
        description=description,
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="reopen", description="Reopen a closed ticket (staff only)")
@app_commands.default_permissions(administrator=True)
async def reopen(interaction: discord.Interaction, channel: discord.TextChannel):
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can reopen tickets.", ephemeral=True)
        return

    # Check if channel exists and is a ticket
    if not channel.topic or "ticket-owner:" not in channel.topic:
        await interaction.response.send_message("This is not a valid ticket channel.", ephemeral=True)
        return

    info = get_ticket_info(channel)
    owner = interaction.guild.get_member(info["owner_id"])
    
    # Restore permissions
    support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
    member_perms = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        attach_files=True,
        embed_links=True
    )
    
    await channel.set_permissions(interaction.guild.default_role, view_channel=False)
    await channel.set_permissions(owner, overwrite=member_perms)
    await channel.set_permissions(support_role, overwrite=member_perms)
    
    embed = create_embed(
        title="🔓 Ticket Reopened",
        description=f"This ticket has been reopened by {interaction.user.mention}",
        color=discord.Color.green()
    )
    
    await channel.send(content=f"{owner.mention if owner else ''} {support_role.mention}", embed=embed)
    
    # DM the owner
    if owner:
        try:
            dm_embed = create_embed(
                title="Ticket Reopened",
                description=f"Your ticket **{channel.name}** has been reopened.",
                color=discord.Color.green()
            )
            await owner.send(embed=dm_embed)
        except discord.Forbidden:
            pass
    
    await interaction.response.send_message(f"Ticket {channel.mention} has been reopened.", ephemeral=True)


@bot.tree.command(name="closeallticket", description="Close all tickets (admin only)")
@app_commands.default_permissions(administrator=True)
async def closeallticket(interaction: discord.Interaction):
    """Close all tickets in the ticket category"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can close all tickets.", ephemeral=True)
        return

    guild = interaction.guild
    category = guild.get_channel(CATEGORY_ID)
    
    if not category:
        await interaction.response.send_message("Ticket category not found.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    closed_count = 0
    failed_count = 0
    
    for channel in category.text_channels:
        if channel.topic and "ticket-owner:" in channel.topic:
            try:
                info = get_ticket_info(channel)
                owner = guild.get_member(info["owner_id"])
                
                # Build transcript
                lines = []
                lines.append("=" * 50)
                lines.append(f"Ticket: {channel.name}")
                lines.append(f"Category: {info['category']}")
                if info['category'] == 'purchase':
                    lines.append(f"Item: {info.get('item', 'Unknown')}")
                    lines.append(f"Quantity: {info.get('quantity', 'Unknown')}")
                elif info.get('priority'):
                    lines.append(f"Priority: {info['priority']}")
                if info['claimed_by']:
                    claimed_member = guild.get_member(info['claimed_by'])
                    lines.append(f"Claimed by: {claimed_member.name if claimed_member else 'Unknown'} ({info['claimed_by']})")
                lines.append(f"Owner: {owner.name if owner else 'Unknown'} ({info['owner_id']})")
                lines.append(f"Closed by: {interaction.user}")
                lines.append(f"Closed at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
                lines.append("=" * 50)
                lines.append("")
                
                async for m in channel.history(limit=None, oldest_first=True):
                    ts = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    text = m.content or ""
                    if m.attachments:
                        text += " " + " ".join(f"[Attachment: {a.filename}]({a.url})" for a in m.attachments)
                    lines.append(f"[{ts}] {m.author}: {text}")
                
                transcript = io.BytesIO("\n".join(lines).encode("utf-8"))

                # Send to log channel
                if LOG_CHANNEL_ID:
                    log = guild.get_channel(LOG_CHANNEL_ID)
                    if log:
                        log_embed = create_embed(
                            title="🔒 Ticket Closed (Bulk)",
                            description=f"**Ticket:** {channel.name}\n**Closed by:** {interaction.user.mention}",
                            color=discord.Color.red()
                        )
                        await log.send(embed=log_embed, file=discord.File(transcript, filename=f"{channel.name}-transcript.txt"))

                # DM the owner
                if owner:
                    try:
                        if info['category'] == 'purchase':
                            dm_embed = create_embed(
                                title="Purchase Ticket Closed",
                                description=f"Your purchase ticket **{channel.name}** has been closed by {interaction.user.mention}.\n\nIf you need to make another purchase, please open a new ticket.",
                                color=discord.Color.from_rgb(114, 114, 255)  # #7272ff
                            )
                        else:
                            dm_embed = create_embed(
                                title="Ticket Closed",
                                description=f"Your ticket **{channel.name}** has been closed by {interaction.user.mention}.\n\nIf you need further assistance, please open a new ticket.",
                                color=discord.Color.red()
                            )
                        await owner.send(embed=dm_embed)
                    except discord.Forbidden:
                        pass

                await channel.delete(reason=f"Bulk closed by {interaction.user}")
                closed_count += 1
            except Exception as e:
                print(f"Error closing ticket {channel.name}: {e}")
                failed_count += 1
    
    embed = create_embed(
        title="✅ Bulk Close Complete",
        description=f"Successfully closed {closed_count} ticket(s)",
        color=discord.Color.green()
    )
    if failed_count > 0:
        embed.add_field(name="Failed", value=f"{failed_count} ticket(s) could not be closed", inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)


# ============ PREFIX COMMANDS ============

@bot.command(name="payment")
async def payment_command(ctx):
    """Show payment options"""
    # Check if user is in a ticket channel
    info = get_ticket_info(ctx.channel)
    if not info.get("owner_id"):
        await ctx.send("This command can only be used in ticket channels.")
        return
    
    try:
        embed = create_embed(
            title="💳 Select Payment Method",
            description="Choose your preferred payment method to see the QR code and wallet details.",
            color=discord.Color.from_rgb(114, 114, 255),  # #7272ff
            message_type="payment_info"
        )
        await ctx.send(embed=embed, view=PaymentMethodView())
    except Exception as e:
        await ctx.send(f"Error showing payment options: {str(e)}")


@bot.command(name="order")
async def order_command(ctx, action: str = None):
    """Order management commands"""
    if action is None:
        await ctx.send("Usage: `!order done` - Mark order as complete and request rating")
        return
    
    if action.lower() == "done":
        # Check if user is staff
        is_staff = any(r.id == SUPPORT_ROLE_ID for r in ctx.author.roles)
        if not is_staff:
            await ctx.send("Only staff can mark orders as done.")
            return
        
        # Check if in a ticket channel
        info = get_ticket_info(ctx.channel)
        if not info.get("owner_id"):
            await ctx.send("This command can only be used in ticket channels.")
            return
        
        owner = ctx.guild.get_member(info["owner_id"])
        if not owner:
            await ctx.send("Ticket owner not found.")
            return
        
        # Create professional rating request embed
        rating_request = discord.Embed(
            title="🎉 Order Completed Successfully!",
            description="Your order has been completed and delivered. We'd love to hear about your experience!",
            color=discord.Color.from_rgb(114, 114, 255),  # #7272ff
            timestamp=datetime.now(timezone.utc)
        )
        
        rating_request.add_field(
            name="⭐ Rate Your Experience",
            value="Please take a moment to rate our service. Your feedback helps us improve!",
            inline=False
        )
        
        rating_request.add_field(
            name="📝 Leave a Review",
            value="You can also share your detailed experience in the review (optional).",
            inline=False
        )
        
        rating_request.add_field(
            name="💬 Questions?",
            value="If you have any questions or concerns, feel free to ask in this ticket.",
            inline=False
        )
        
        rating_request.set_footer(text="Trading Vault • Professional Service")
        rating_request.set_thumbnail(url=owner.avatar.url if owner.avatar else None)
        
        await ctx.send(f"{owner.mention}", embed=rating_request, view=RatingView())
    else:
        await ctx.send("Unknown action. Usage: `!order done`")


@bot.command(name="vouch")
async def vouch_prefix_command(ctx, member: discord.Member = None):
    """Prefix command for vouch (alias)"""
    if member is None:
        member = ctx.author
    
    vouches = load_vouches()
    user_id_str = str(member.id)
    
    if user_id_str not in vouches or not vouches[user_id_str].get("vouches"):
        embed = create_embed(
            title="📊 Vouch Information",
            description=f"{member.mention} has no vouches yet.",
            color=discord.Color.blue(),
            message_type="vouch"
        )
        await ctx.send(embed=embed)
        return
    
    user_vouches = vouches[user_id_str]
    vouch_list = user_vouches["vouches"]
    
    embed = create_embed(
        title="📊 Vouch Information",
        description=f"**User:** {member.mention}\n**Total Vouches:** {len(vouch_list)}",
        color=discord.Color.from_rgb(114, 114, 255),  # #7272ff
        message_type="vouch",
        fields=[
            ("Recent Vouches", "\n".join([f"✅ {v['item']} - {v['price']}" for v in vouch_list[-5:]]), False)
        ]
    )
    await ctx.send(embed=embed)


@bot.command(name="myvouches")
async def myvouches_command(ctx):
    """View your own vouches"""
    vouches = load_vouches()
    user_id_str = str(ctx.author.id)
    
    if user_id_str not in vouches or not vouches[user_id_str].get("vouches"):
        embed = create_embed(
            title="📊 My Vouches",
            description="You have no vouches yet.",
            color=discord.Color.blue(),
            message_type="vouch"
        )
        await ctx.send(embed=embed)
        return
    
    user_vouches = vouches[user_id_str]
    vouch_list = user_vouches["vouches"]
    
    embed = create_embed(
        title="📊 My Vouches",
        description=f"**Total Vouches:** {len(vouch_list)}",
        color=discord.Color.from_rgb(114, 114, 255),  # #7272ff
        message_type="vouch",
        fields=[
            ("My Vouches", "\n".join([f"✅ {v['item']} - {v['price']}" for v in vouch_list]), False)
        ]
    )
    await ctx.send(embed=embed)


@bot.command(name="leaderboard")
async def leaderboard_prefix_command(ctx):
    """Prefix command for leaderboard (alias)"""
    vouches = load_vouches()
    
    if not vouches:
        await ctx.send("No vouch data available yet.")
        return
    
    # Calculate leaderboard
    leaderboard = []
    for user_id_str, data in vouches.items():
        if data.get("vouches"):
            leaderboard.append({
                "user_id": int(user_id_str),
                "total_vouches": len(data["vouches"])
            })
    
    # Sort by total vouches
    leaderboard.sort(key=lambda x: x["total_vouches"], reverse=True)
    top_10 = leaderboard[:10]
    
    description = ""
    for i, entry in enumerate(top_10, 1):
        member = ctx.guild.get_member(entry["user_id"])
        member_name = member.name if member else f"User {entry['user_id']}"
        description += f"**{i}.** {member_name}\n   📊 {entry['total_vouches']} vouches\n\n"
    
    embed = create_embed(
        title="🏆 Vouch Leaderboard",
        description=description or "No vouches yet.",
        color=discord.Color.from_rgb(114, 114, 255),  # #7272ff
        message_type="vouch"
    )
    await ctx.send(embed=embed)





# ============ GIVEAWAY COMMANDS ============

@bot.tree.command(name="giveaway", description="Create a new giveaway (admin only)")
@app_commands.default_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction):
    """Create a new giveaway"""
    if not ENABLE_GIVEAWAYS:
        await interaction.response.send_message("Giveaway system is disabled.", ephemeral=True)
        return
    await giveaway_command(interaction)


@bot.tree.command(name="endgiveaway", description="End a giveaway manually (admin only)")
@app_commands.default_permissions(administrator=True)
async def endgiveaway(interaction: discord.Interaction, giveaway_id: str):
    """End a giveaway manually"""
    if not ENABLE_GIVEAWAYS:
        await interaction.response.send_message("Giveaway system is disabled.", ephemeral=True)
        return
    await endgiveaway_command(interaction, giveaway_id)


@bot.tree.command(name="reroll", description="Reroll a giveaway winner (admin only)")
@app_commands.default_permissions(administrator=True)
async def reroll(interaction: discord.Interaction, giveaway_id: str):
    """Reroll a giveaway winner"""
    if not ENABLE_GIVEAWAYS:
        await interaction.response.send_message("Giveaway system is disabled.", ephemeral=True)
        return
    await reroll_command(interaction, giveaway_id)


@bot.tree.command(name="listgiveaways", description="List all giveaways")
async def listgiveaways(interaction: discord.Interaction):
    """List all giveaways"""
    if not ENABLE_GIVEAWAYS:
        await interaction.response.send_message("Giveaway system is disabled.", ephemeral=True)
        return
    await listgiveaways_command(interaction)


# ============ INVITE TRACKER COMMANDS ============

@bot.tree.command(name="invitestats", description="View invite statistics for a user")
async def invitestats(interaction: discord.Interaction, member: discord.Member = None):
    """View invite statistics for a user"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await invitestats_command(interaction, member)


@bot.tree.command(name="inviteleaderboard", description="View invite leaderboard")
async def inviteleaderboard(interaction: discord.Interaction):
    """View invite leaderboard"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await inviteleaderboard_command(interaction)


@bot.tree.command(name="whoinvited", description="Check who invited a user")
async def whoinvited(interaction: discord.Interaction, member: discord.Member = None):
    """Check who invited a user"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await whoinvited_command(interaction, member)


@bot.tree.command(name="setinvitechannel", description="Set the invite announcement channel (admin only)")
@app_commands.default_permissions(administrator=True)
async def setinvitechannel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the invite announcement channel"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await setinvitechannel_command(interaction, channel)


@bot.tree.command(name="invitehistory", description="View invite history for a user")
async def invitehistory(interaction: discord.Interaction, member: discord.Member = None):
    """View invite history for a user"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await invitehistory_command(interaction, member)


@bot.tree.command(name="setinvitemilestone", description="Set milestone reward (admin only)")
@app_commands.default_permissions(administrator=True)
async def setinvitemilestone(interaction: discord.Interaction, milestone: int, role: discord.Role = None, reward: str = None):
    """Set milestone reward"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await setinvitemilestone_command(interaction, milestone, role, reward)


@bot.tree.command(name="giveeveryonememberrole", description="Give everyone in the server the member role (admin only)")
@app_commands.default_permissions(administrator=True)
async def giveeveryonememberrole(interaction: discord.Interaction):
    """Give everyone in the server the member role"""
    if AUTO_ROLE_ID == 0:
        await interaction.response.send_message("AUTO_ROLE_ID is not configured in .env file", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    member_role = interaction.guild.get_role(AUTO_ROLE_ID)
    if not member_role:
        await interaction.followup.send("Member role not found! Check AUTO_ROLE_ID in .env", ephemeral=True)
        return

    count = 0
    errors = 0
    error_users = []

    for member in interaction.guild.members:
        if not member.bot:
            try:
                await member.add_roles(member_role, reason="Mass role assignment by admin")
                count += 1
            except Exception as e:
                errors += 1
                error_users.append(f"{member.name}: {str(e)}")

    embed = create_embed(
        title="✅ Role Assignment Complete",
        description=f"Member role {member_role.mention} has been assigned to all members.",
        color=discord.Color.green(),
        message_type="general",
        fields=[
            ("✅ Successfully Assigned", str(count), True),
            ("❌ Errors", str(errors), True)
        ]
    )

    if errors > 0:
        embed.add_field(name="⚠️ Error Details", value=f"First {min(5, len(error_users))} errors:\n" + "\n".join(error_users[:5]), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="postinviteleaderboard", description="Post auto-updating invite leaderboard (admin only)")
@app_commands.default_permissions(administrator=True)
async def postinviteleaderboard(interaction: discord.Interaction, channel: discord.TextChannel, refresh_seconds: int = 30):
    """Post auto-updating invite leaderboard"""
    if not ENABLE_INVITE_TRACKER:
        await interaction.response.send_message("Invite tracker is disabled.", ephemeral=True)
        return
    await post_leaderboard_command(interaction, channel, refresh_seconds)


# ============ WELCOMER COMMANDS ============

@bot.tree.command(name="setwelcomemessage", description="Set the welcome message (admin only)")
@app_commands.default_permissions(administrator=True)
async def setwelcomemessage(interaction: discord.Interaction, message: str):
    """Set the welcome message"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setwelcomemessage_command(interaction, message)


@bot.tree.command(name="setwelcomerchannel", description="Set the welcome channel (admin only)")
@app_commands.default_permissions(administrator=True)
async def setwelcomerchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the welcome channel"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setwelcomerchannel_command(interaction, channel)


@bot.tree.command(name="togglewelcome", description="Toggle welcome messages on/off (admin only)")
@app_commands.default_permissions(administrator=True)
async def togglewelcome(interaction: discord.Interaction):
    """Toggle welcome messages on/off"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await togglewelcome_command(interaction)


@bot.tree.command(name="setgoodbyemessage", description="Set the goodbye message (admin only)")
@app_commands.default_permissions(administrator=True)
async def setgoodbyemessage(interaction: discord.Interaction, message: str):
    """Set the goodbye message"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setgoodbyemessage_command(interaction, message)


@bot.tree.command(name="setgoodbyechannel", description="Set the goodbye channel (admin only)")
@app_commands.default_permissions(administrator=True)
async def setgoodbyechannel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the goodbye channel"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setgoodbyechannel_command(interaction, channel)


@bot.tree.command(name="togglegoodbye", description="Toggle goodbye messages on/off (admin only)")
@app_commands.default_permissions(administrator=True)
async def togglegoodbye(interaction: discord.Interaction):
    """Toggle goodbye messages on/off"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await togglegoodbye_command(interaction)


@bot.tree.command(name="welcomeconfig", description="View welcome configuration (admin only)")
@app_commands.default_permissions(administrator=True)
async def welcomeconfig(interaction: discord.Interaction):
    """View welcome configuration"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await welcomeconfig_command(interaction)


@bot.tree.command(name="togglestyledwelcome", description="Toggle styled welcome messages (admin only)")
@app_commands.default_permissions(administrator=True)
async def togglestyledwelcome(interaction: discord.Interaction):
    """Toggle styled welcome messages"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await togglestyledwelcome_command(interaction)


@bot.tree.command(name="setwelcomeimage", description="Set the welcome banner image URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setwelcomeimage(interaction: discord.Interaction, image_url: str):
    """Set the welcome banner image URL"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setwelcomeimage_command(interaction, image_url)


@bot.tree.command(name="setthumbnailimage", description="Set the welcome thumbnail image URL (admin only)")
@app_commands.default_permissions(administrator=True)
async def setthumbnailimage(interaction: discord.Interaction, image_url: str):
    """Set the welcome thumbnail image URL"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setthumbnailimage_command(interaction, image_url)


@bot.tree.command(name="setwelcometitle", description="Set the welcome embed title (admin only)")
@app_commands.default_permissions(administrator=True)
async def setwelcometitle(interaction: discord.Interaction, title: str):
    """Set the welcome embed title"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setwelcometitle_command(interaction, title)


@bot.tree.command(name="setwelcomecolor", description="Set the welcome embed color (admin only)")
@app_commands.default_permissions(administrator=True)
async def setwelcomecolor(interaction: discord.Interaction, color_hex: str):
    """Set the welcome embed color"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setwelcomecolor_command(interaction, color_hex)


@bot.tree.command(name="setwelcomefooter", description="Set the welcome embed footer (admin only)")
@app_commands.default_permissions(administrator=True)
async def setwelcomefooter(interaction: discord.Interaction, footer_text: str):
    """Set the welcome embed footer"""
    if not ENABLE_WELCOMER:
        await interaction.response.send_message("Welcomer system is disabled.", ephemeral=True)
        return
    await setwelcomefooter_command(interaction, footer_text)


# ============ STORE SYSTEM COMMANDS ============

@bot.tree.command(name="setstorechannel", description="Set a store channel for a specific store type (admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(
    store_type=[
        app_commands.Choice(name="Capes", value="capes"),
        app_commands.Choice(name="Decoration", value="decoration"),
        app_commands.Choice(name="Boosts", value="boosts"),
        app_commands.Choice(name="Nitro", value="nitro"),
        app_commands.Choice(name="Minecraft", value="minecraft"),
    ]
)
async def setstorechannel(interaction: discord.Interaction, channel: discord.TextChannel, store_type: str):
    """Set a store channel for a specific store type"""
    await setstorechannel_command(interaction, channel, store_type)


@bot.tree.command(name="postpricelist", description="Post price list to a channel (admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(
    store_type=[
        app_commands.Choice(name="Capes", value="capes"),
        app_commands.Choice(name="Decoration", value="decoration"),
        app_commands.Choice(name="Boosts", value="boosts"),
        app_commands.Choice(name="Nitro", value="nitro"),
        app_commands.Choice(name="Minecraft", value="minecraft"),
    ]
)
async def postpricelist(interaction: discord.Interaction, channel: discord.TextChannel, store_type: str = "capes"):
    """Post price list to a store channel"""
    await post_price_list(interaction, channel, store_type)


@bot.tree.command(name="updatepricelist", description="Update price list in configured store channel (admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(
    store_type=[
        app_commands.Choice(name="Capes", value="capes"),
        app_commands.Choice(name="Decoration", value="decoration"),
        app_commands.Choice(name="Boosts", value="boosts"),
        app_commands.Choice(name="Nitro", value="nitro"),
        app_commands.Choice(name="Minecraft", value="minecraft"),
    ]
)
async def updatepricelist(interaction: discord.Interaction, store_type: str = "capes"):
    """Update and repost price list to the configured store channel"""
    await updatepricelist_command(interaction, store_type)


@bot.tree.command(name="postnitromessage", description="Post nitro shop embed in the exact format (admin only)")
@app_commands.default_permissions(administrator=True)
async def postnitromessage(interaction: discord.Interaction, channel: discord.TextChannel):
    """Post nitro shop embed in the exact format requested"""
    from core_systems.store_system import create_nitro_embed, NITRO_STORE_DATA, load_store_config
    
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can post nitro embeds.", ephemeral=True)
        return
    
    try:
        # Load current nitro data
        config = await load_store_config()
        store_data = config.get("nitro", NITRO_STORE_DATA)
        banner_config = config.get("banner_configs", {}).get("nitro_style_1")
        banner_url = store_data.get("banner_url")
        
        # Create the nitro embed
        nitro_embed = await create_nitro_embed(store_data, banner_config, banner_url)
        
        # Send the embed
        await channel.send(embed=nitro_embed)
        
        embed = create_embed(
            title="✅ Nitro Embed Posted",
            description=f"Nitro shop embed has been posted to {channel.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error posting nitro embed: {str(e)}", ephemeral=True)


@bot.tree.command(name="postdecorationmessage", description="Post decoration shop embed in the exact format (admin only)")
@app_commands.default_permissions(administrator=True)
async def postdecorationmessage(interaction: discord.Interaction, channel: discord.TextChannel):
    """Post decoration shop embed in the exact format requested"""
    from core_systems.store_system import create_decoration_embed, DECORATION_STORE_DATA, load_store_config
    
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can post decoration embeds.", ephemeral=True)
        return
    
    try:
        # Load current decoration data
        config = await load_store_config()
        store_data = config.get("decoration", DECORATION_STORE_DATA)
        banner_config = config.get("banner_configs", {}).get("decoration_style_1")
        banner_url = store_data.get("banner_url")

        # Create the decoration embed
        decoration_embed = await create_decoration_embed(store_data, banner_config, banner_url)
        
        # Send the embed
        await channel.send(embed=decoration_embed)
        
        embed = create_embed(
            title="✅ Decoration Embed Posted",
            description=f"Decoration shop embed has been posted to {channel.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error posting decoration embed: {str(e)}", ephemeral=True)


@bot.tree.command(name="postboostsmessage", description="Post boosts shop embed in the exact format (admin only)")
@app_commands.default_permissions(administrator=True)
async def postboostsmessage(interaction: discord.Interaction, channel: discord.TextChannel):
    """Post boosts shop embed in the exact format requested"""
    from core_systems.store_system import create_boosts_embed, BOOSTS_STORE_DATA, load_store_config
    
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can post boosts embeds.", ephemeral=True)
        return
    
    try:
        # Load current boosts data
        config = await load_store_config()
        store_data = config.get("boosts", BOOSTS_STORE_DATA)
        banner_config = config.get("banner_configs", {}).get("boosts_style_1")
        banner_url = store_data.get("banner_url")

        # Create the boosts embed
        boosts_embed = await create_boosts_embed(store_data, banner_config, banner_url)
        
        # Send the embed
        await channel.send(embed=boosts_embed)
        
        embed = create_embed(
            title="✅ Boosts Embed Posted",
            description=f"Boosts shop embed has been posted to {channel.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error posting boosts embed: {str(e)}", ephemeral=True)


@bot.tree.command(name="storeinfo", description="View store configuration (admin only)")
@app_commands.default_permissions(administrator=True)
async def storeinfo(interaction: discord.Interaction):
    """Show store configuration information"""
    await storeinfo_command(interaction)


@bot.tree.command(name="postcapecards", description="Post individual cape cards with images (admin only)")
@app_commands.default_permissions(administrator=True)
async def postcapecards(interaction: discord.Interaction, channel: discord.TextChannel):
    """Post individual cape cards with images to a channel"""
    await post_cape_cards(interaction, channel)


@bot.tree.command(name="reloadstoreconfig", description="Reload store configuration from file (admin only)")
@app_commands.default_permissions(administrator=True)
async def reloadstoreconfig(interaction: discord.Interaction):
    """Reload store configuration from file"""
    await reloadstoreconfig_command(interaction)


@bot.tree.command(name="setstorebannerimage", description="Set banner image URL for a specific store (admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(
    store_type=[
        app_commands.Choice(name="Capes", value="capes"),
        app_commands.Choice(name="Decoration", value="decoration"),
        app_commands.Choice(name="Boosts", value="boosts"),
        app_commands.Choice(name="Nitro", value="nitro"),
        app_commands.Choice(name="Minecraft", value="minecraft"),
    ]
)
async def setstorebannerimage(interaction: discord.Interaction, store_type: str, banner_url: str):
    """Set banner image URL for a specific store type"""
    await setstorebanner_command(interaction, store_type, banner_url)


@bot.tree.command(name="getstorebanner", description="View current banner settings for stores (admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(
    store_type=[
        app_commands.Choice(name="Capes", value="capes"),
        app_commands.Choice(name="Decoration", value="decoration"),
        app_commands.Choice(name="Boosts", value="boosts"),
        app_commands.Choice(name="Nitro", value="nitro"),
        app_commands.Choice(name="Minecraft", value="minecraft"),
        app_commands.Choice(name="All Stores", value="all"),
    ]
)
async def getstorebanner(interaction: discord.Interaction, store_type: str = "all"):
    """View current banner settings for stores"""
    if store_type == "all":
        await getstorebanner_command(interaction, None)
    else:
        await getstorebanner_command(interaction, store_type)


@bot.tree.command(name="setstorebanner", description="Configure banner settings for store price lists (admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(
    store_type=[
        app_commands.Choice(name="Capes", value="capes"),
        app_commands.Choice(name="Decoration", value="decoration"),
        app_commands.Choice(name="Boosts", value="boosts"),
        app_commands.Choice(name="Nitro", value="nitro"),
        app_commands.Choice(name="Minecraft", value="minecraft"),
    ],
    banner_enabled=[
        app_commands.Choice(name="Enabled", value="true"),
        app_commands.Choice(name="Disabled", value="false"),
    ]
)
async def setstorebanner(interaction: discord.Interaction, store_type: str, banner_enabled: str, show_why_choose: bool = True, show_conversion_rate: bool = True):
    """Configure banner settings for store price lists"""
    from core_systems.store_system import load_store_config, save_store_config
    
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can configure store banners.", ephemeral=True)
        return
    
    config = load_store_config()
    
    # Get the appropriate banner config key
    banner_config_key = f"{store_type}_style_1"
    
    if "banner_configs" not in config:
        config["banner_configs"] = {}
    
    if banner_config_key not in config["banner_configs"]:
        config["banner_configs"][banner_config_key] = {}
    
    # Update banner settings
    config["banner_configs"][banner_config_key]["banner_enabled"] = banner_enabled == "true"
    config["banner_configs"][banner_config_key]["show_why_choose"] = show_why_choose
    config["banner_configs"][banner_config_key]["show_conversion_rate"] = show_conversion_rate
    
    # Save the updated config
    save_store_config(config)
    
    status = "enabled" if banner_enabled == "true" else "disabled"
    embed = create_embed(
        title="✅ Store Banner Configured",
        description=f"Banner for {store_type.capitalize()} store has been {status}.",
        color=discord.Color.green(),
        fields=[
            ("Store Type", store_type.capitalize(), True),
            ("Banner Status", status.capitalize(), True),
            ("Show Why Choose", "Yes" if show_why_choose else "No", True),
            ("Show Conversion Rate", "Yes" if show_conversion_rate else "No", True)
        ]
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ============ UTILITY COMMANDS ============

@bot.tree.command(name="serverinfo", description="View server information")
async def serverinfo_cmd(interaction: discord.Interaction):
    await serverinfo(interaction, bot)


@bot.tree.command(name="userinfo", description="View user information")
async def userinfo_cmd(interaction: discord.Interaction, member: discord.Member = None):
    await userinfo(interaction, member)


@bot.tree.command(name="avatar", description="View a user's avatar")
async def avatar_cmd(interaction: discord.Interaction, member: discord.Member = None):
    await avatar(interaction, member)


@bot.tree.command(name="banner", description="View a user's banner")
async def banner_cmd(interaction: discord.Interaction, member: discord.Member = None):
    await banner(interaction, member)


@bot.tree.command(name="ping", description="Check bot latency")
async def ping_cmd(interaction: discord.Interaction):
    await ping(interaction, bot)


@bot.tree.command(name="botstats", description="View bot statistics")
async def botstats_cmd(interaction: discord.Interaction):
    await botstats(interaction, bot)


@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.default_permissions(kick_members=True)
async def kick_cmd(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await kick(interaction, member, reason)


@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.default_permissions(ban_members=True)
async def ban_cmd(interaction: discord.Interaction, member: discord.Member, reason: str = None, delete_message_days: int = 0):
    await ban(interaction, member, reason, delete_message_days)


@bot.tree.command(name="unban", description="Unban a user from the server")
@app_commands.default_permissions(ban_members=True)
async def unban_cmd(interaction: discord.Interaction, user_id: str):
    await unban(interaction, bot, user_id)


@bot.tree.command(name="purge", description="Delete multiple messages")
@app_commands.default_permissions(manage_messages=True)
async def purge_cmd(interaction: discord.Interaction, amount: int):
    await purge(interaction, amount)


@bot.tree.command(name="slowmode", description="Set slowmode for the channel")
@app_commands.default_permissions(manage_channels=True)
async def slowmode_cmd(interaction: discord.Interaction, seconds: int):
    await slowmode(interaction, seconds)


@bot.tree.command(name="lock", description="Lock the channel")
@app_commands.default_permissions(manage_channels=True)
async def lock_cmd(interaction: discord.Interaction):
    await lock(interaction)


@bot.tree.command(name="unlock", description="Unlock the channel")
@app_commands.default_permissions(manage_channels=True)
async def unlock_cmd(interaction: discord.Interaction):
    await unlock(interaction)


@bot.tree.command(name="8ball", description="Ask the magic 8-ball a question")
async def eightball_cmd(interaction: discord.Interaction, question: str):
    await eightball(interaction, question)


@bot.tree.command(name="flip", description="Flip a coin")
async def flip_cmd(interaction: discord.Interaction):
    await flip(interaction)


@bot.tree.command(name="roll", description="Roll a dice")
async def roll_cmd(interaction: discord.Interaction, sides: int = 6):
    await roll(interaction, sides)


@bot.tree.command(name="random", description="Generate a random number")
async def random_cmd(interaction: discord.Interaction, min_val: int, max_val: int):
    await random_number(interaction, min_val, max_val)


@bot.tree.command(name="poll", description="Create a poll")
async def poll_cmd(interaction: discord.Interaction, question: str, options: str):
    await poll(interaction, question, options)


@bot.tree.command(name="suggest", description="Submit a suggestion")
async def suggest_cmd(interaction: discord.Interaction, suggestion: str):
    await suggest(interaction, suggestion)


@bot.tree.command(name="hug", description="Hug someone")
async def hug_cmd(interaction: discord.Interaction, member: discord.Member = None):
    await hug(interaction, member)


@bot.tree.command(name="slap", description="Slap someone")
async def slap_cmd(interaction: discord.Interaction, member: discord.Member = None):
    await slap(interaction, member)


@bot.tree.command(name="pat", description="Pat someone")
async def pat_cmd(interaction: discord.Interaction, member: discord.Member = None):
    await pat(interaction, member)


# ============ ROLE MANAGEMENT COMMANDS ============

@bot.tree.command(name="addrole", description="Add a role to a member (staff only)")
@app_commands.default_permissions(manage_roles=True)
async def addrole_cmd(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await add_role_command(interaction, member, role)


@bot.tree.command(name="removerole", description="Remove a role from a member (staff only)")
@app_commands.default_permissions(manage_roles=True)
async def removerole_cmd(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await remove_role_command(interaction, member, role)


@bot.tree.command(name="listroles", description="List all roles in the server")
async def listroles_cmd(interaction: discord.Interaction):
    await list_roles_command(interaction)


@bot.tree.command(name="roleinfo", description="View detailed information about a role")
async def roleinfo_cmd(interaction: discord.Interaction, role: discord.Role):
    await role_info_command(interaction, role)


@bot.tree.command(name="mute", description="Mute a member (staff only)")
@app_commands.default_permissions(moderate_members=True)
async def mute_cmd(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await mute_command(interaction, member, reason)


@bot.tree.command(name="unmute", description="Unmute a member (staff only)")
@app_commands.default_permissions(moderate_members=True)
async def unmute_cmd(interaction: discord.Interaction, member: discord.Member):
    await unmute_command(interaction, member)


# ============ UPI QR CODE COMMANDS ============

@bot.tree.command(name="generateqr", description="Generate a UPI QR code with specific amount")
async def generateqr_cmd(interaction: discord.Interaction, amount: float, note: str = None):
    await generate_custom_qr(interaction, amount, note)


@bot.tree.command(name="generateqrflex", description="Generate a UPI QR code (flexible amount)")
async def generateqrflex_cmd(interaction: discord.Interaction, note: str = None):
    await generate_qr_no_amount(interaction, note)


@bot.tree.command(name="listpresets", description="List preset UPI QR codes")
async def listpresets_cmd(interaction: discord.Interaction):
    await list_preset_amounts(interaction)


@bot.tree.command(name="createpresetqr", description="Create a preset UPI QR code (staff only)")
@app_commands.default_permissions(administrator=True)
async def createpresetqr_cmd(interaction: discord.Interaction, amount: float, note: str = None):
    await create_preset_qr(interaction, amount, note)


@bot.tree.command(name="deletepresetqr", description="Delete a preset UPI QR code (staff only)")
@app_commands.default_permissions(administrator=True)
async def deletepresetqr_cmd(interaction: discord.Interaction, amount: float):
    await delete_preset_qr(interaction, amount)


@bot.tree.command(name="sendpresetqr", description="Send a preset UPI QR code")
async def sendpresetqr_cmd(interaction: discord.Interaction, amount: float):
    await send_preset_qr(interaction, amount)


@bot.tree.command(name="generateltcqr", description="Generate a LTC QR code with specific amount")
async def generateltcqr_cmd(interaction: discord.Interaction, amount: float, note: str = None):
    await generate_custom_ltc_qr(interaction, amount, note)


@bot.tree.command(name="generateltcqrflex", description="Generate a LTC QR code (flexible amount)")
async def generateltcqrflex_cmd(interaction: discord.Interaction, note: str = None):
    await generate_ltc_qr_no_amount(interaction, note)


# ============ INTEGRATED UPI PAYMENT SYSTEM ============

# Note: Auto-tracking and payment verification removed. Only QR generation is available.


# ============ BOT EVENTS ============

@bot.event
async def on_ready():
    bot_logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    bot_logger.info(f"Support Role ID: {SUPPORT_ROLE_ID}")
    bot_logger.info(f"Category ID: {CATEGORY_ID}")
    bot_logger.info(f"Log Channel ID: {LOG_CHANNEL_ID}")
    bot_logger.info(f"Rating Channel ID: {RATING_CHANNEL_ID}")
    bot_logger.info(f"Connected to {len(bot.guilds)} guild(s)")
    bot_logger.info("------")

    # Set bot status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Made by Shashank Sharma"))
    bot_logger.info("Set bot status")

    # Load invite state from Firebase before tracking
    if ENABLE_INVITE_TRACKER:
        from community_systems.invite_tracker import load_invite_state, SERVER_INVITES
        SERVER_INVITES.update(await load_invite_state())
        bot_logger.info("Loaded invite state from Firebase")

    # Load giveaways from Firebase
    if ENABLE_GIVEAWAYS:
        from community_systems.giveaway_system import load_giveaways, GIVEAWAYS
        GIVEAWAYS.update(await load_giveaways())
        bot_logger.info("Loaded giveaways from Firebase")

    # Load store config from Firebase
    from core_systems.store_system import load_store_config, STORE_CONFIG, CAPE_STORE_DATA, DECORATION_STORE_DATA, BOOSTS_STORE_DATA, NITRO_STORE_DATA, MINECRAFT_STORE_DATA
    STORE_CONFIG.update(await load_store_config())
    bot_logger.info("Loaded store config from Firebase")

    # Load banner config from Firebase
    from config import load_banner_config
    BANNER_SETTINGS.update(await load_banner_config())
    bot_logger.info("Loaded banner config from Firebase")

    # Track invites for all servers
    for guild in bot.guilds:
        await track_invites(guild)
        bot_logger.debug(f"Tracking invites for guild: {guild.name} (ID: {guild.id})")


@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return

    # Process commands
    await bot.process_commands(message)

    # Check for vouch messages using new system
    if message.channel.id == VOUCH_CHANNEL_ID and VOUCH_CHANNEL_ID != 0:
        from community_systems.vouch_system import handle_vouch_channel_message
        await handle_vouch_channel_message(message)


@bot.event
async def on_member_join(member):
    # Handle invite tracking if enabled
    if ENABLE_INVITE_TRACKER:
        await check_invite_join(member)

    # Handle welcome message if enabled
    if ENABLE_WELCOMER:
        await send_welcome(member)

    # Auto-role: Give auto role to new members
    if AUTO_ROLE_ID != 0:
        try:
            auto_role = member.guild.get_role(AUTO_ROLE_ID)
            if auto_role:
                await member.add_roles(auto_role, reason="Auto-role on join")
                bot_logger.info(f"Given auto role {auto_role.name} to {member.name}")
        except Exception as e:
            bot_logger.error(f"Failed to give auto role to {member.name}: {e}")


@bot.event
async def on_member_remove(member):
    # Handle invite tracking if enabled
    if ENABLE_INVITE_TRACKER:
        await check_invite_leave(member)
    
    # Handle goodbye message if enabled
    if ENABLE_WELCOMER:
        await send_goodbye(member)


@bot.event
async def on_guild_join(guild):
    # Track invites when bot joins a new server if enabled
    if ENABLE_INVITE_TRACKER:
        await track_invites(guild)


if __name__ == "__main__":
    bot.run(TOKEN)
