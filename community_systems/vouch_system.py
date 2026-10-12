"""
New Vouch System Module
Staff generates vouch codes for users to paste in vouch channel
"""
import json
import os
import random
import asyncio
from datetime import datetime, timezone
import discord
from discord import app_commands
from config import SUPPORT_ROLE_ID, VOUCH_CHANNEL_ID, get_data_dir
from utilities.embed_utils import create_embed


# Ticket messages storage - configurable from database
async def load_ticket_messages():
    """Load ticket messages from Firebase"""
    try:
        from firebase_client import get_document
        config = await get_document("config", "ticket_messages")
        if config:
            return config
    except Exception as e:
        print(f"Error loading ticket messages from Firebase: {e}")

    # Default ticket messages
    return {
        "ticket_creation": {
            "title": "🎫 Support Ticket Created",
            "description": "Thank you for creating a ticket! Our staff will be with you shortly.",
            "color": "#00FF00"
        },
        "purchase_creation": {
            "title": "🛒 Purchase Ticket Created",
            "description": "Thank you for your purchase request! Please complete the payment to proceed.",
            "color": "#00FFFF"
        },
        "payment_info": {
            "title": "💳 Payment Information",
            "description": "⚠️ **Payment Required Before Delivery**\n\nPlease complete your payment to proceed with your order. Once payment is confirmed, your item will be delivered automatically.",
            "color": "#FFC107",
            "fields": [
                {"name": "🇮🇳 INR (UPI)", "value": "Wallet: {INR_WALLET}", "inline": True},
                {"name": "₿ LTC (Litecoin)", "value": "Wallet: {LTC_WALLET}", "inline": True},
                {"name": "⏱️ Delivery Time", "value": "Usually within 1-24 hours after payment confirmation", "inline": True},
                {"name": "🛡️ Secure", "value": "All payments are processed securely", "inline": True},
                {"name": "📞 Support", "value": "Ping the support team if you need help", "inline": False},
                {"name": "📸 Important", "value": "Please send a screenshot of your payment after completion for verification", "inline": False}
            ]
        },
        "ticket_claimed": {
            "title": "✋ Ticket Claimed",
            "description": "This ticket has been claimed by {staff}",
            "color": "#00FF00"
        },
        "ticket_closed": {
            "title": "🔒 Ticket Closed",
            "description": "This ticket has been closed.",
            "color": "#FF0000"
        }
    }


async def save_ticket_messages(messages):
    """Save ticket messages to Firebase"""
    try:
        from firebase_client import set_document
        await set_document("config", "ticket_messages", messages)
    except Exception as e:
        print(f"Error saving ticket messages to Firebase: {e}")


# Vouch data storage - Now using Firebase
async def load_vouches():
    """Load vouches from Firebase"""
    try:
        from firebase_client import get_vouches
        return await get_vouches()
    except Exception as e:
        print(f"Error loading vouches from Firebase: {e}")
        return {}


async def save_vouches(vouches):
    """Save vouches to Firebase"""
    try:
        from firebase_client import set_vouch
        for user_id, data in vouches.items():
            await set_vouch(user_id, data)
    except Exception as e:
        print(f"Error saving vouches to Firebase: {e}")


def generate_vouch_code():
    """Generate a 12-digit random numeric vouch code"""
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])


class VouchModal(discord.ui.Modal, title="Generate Vouch Code"):
    """Modal for staff to enter item and price for vouch"""
    item = discord.ui.TextInput(
        label="Item",
        placeholder="What was purchased?",
        max_length=100,
        required=True
    )

    price = discord.ui.TextInput(
        label="Price",
        placeholder="e.g., ₹500 or $5",
        max_length=50,
        required=True
    )

    def __init__(self, user_id: int, channel_id: int):
        super().__init__()
        self.user_id = user_id
        self.channel_id = channel_id

    async def on_submit(self, interaction: discord.Interaction):
        """Generate vouch code and send to user"""
        is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
        if not is_staff:
            await interaction.response.send_message("Only staff can generate vouch codes.", ephemeral=True)
            return

        # Generate vouch code
        vouch_code = generate_vouch_code()

        # Format: +Legit | code | item | price
        # Display "Giveaway" if price is 0
        display_price = "Giveaway" if self.price.value.strip() == "0" else self.price.value
        vouch_message = f"+Legit | {vouch_code} | {self.item.value} | {display_price}"

        # Save vouch data
        vouches = await load_vouches()
        vouches[vouch_code] = {
            "user_id": self.user_id,
            "staff_id": interaction.user.id,
            "item": self.item.value,
            "price": self.price.value,  # Store original price
            "display_price": display_price,  # Store display price for showing
            "channel_id": self.channel_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "used": False
        }
        await save_vouches(vouches)

        # Get ticket owner for ping
        ticket_owner = interaction.guild.get_member(self.user_id)
        owner_mention = ticket_owner.mention if ticket_owner else f"<@{self.user_id}>"

        # Send embed visible to everyone in the ticket (not ephemeral)
        embed = create_embed(
            title="✅ Vouch Code Generated",
            description=f"Vouch code generated for {owner_mention}. Please copy the message below and paste it in the vouch channel.",
            color=discord.Color.green(),
            message_type="general",
            fields=[
                ("👤 Customer", owner_mention, True),
                ("📝 Item", self.item.value, True),
                ("💰 Price", display_price, True),
                ("🔢 Vouch Code", f"```{vouch_message}```", False)
            ]
        )

        embed.add_field(
            name="📋 Instructions",
            value=f"1. Copy the code above\n2. Go to <#{VOUCH_CHANNEL_ID}>\n3. Paste the code\n4. Bot will react with ✅ if valid\n\nFormat: `+Legit | code | item | price`",
            inline=False
        )

        # Send publicly (not ephemeral) and ping the ticket owner
        await interaction.response.send_message(content=owner_mention, embed=embed)


async def process_vouch_message(message: discord.Message):
    """Process vouch messages in the vouch channel"""
    # Check if message is in vouch channel
    if message.channel.id != VOUCH_CHANNEL_ID:
        return
    
    # Validate vouch format: +Legit | code | item | price (with spaces) or +Legit|code|item|price (without spaces)
    content = message.content.strip()
    
    # Try format with spaces first
    if content.startswith("+Legit |"):
        parts = [part.strip() for part in content.split("|")]
        if len(parts) != 4:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, invalid vouch format. Please use the format: +Legit | code | item | price", delete_after=10)
            return
    # Try format without spaces (backward compatibility)
    elif content.startswith("+Legit|"):
        parts = content.split("|")
        if len(parts) != 4:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, invalid vouch format. Please use the format: +Legit | code | item | price", delete_after=10)
            return
    else:
        await message.delete()
        await message.channel.send(f"❌ {message.author.mention}, invalid vouch format. Please use the format: +Legit | code | item | price", delete_after=10)
        return
    
    try:
        vouch_code = parts[1]
        item = parts[2]
        price = parts[3]
        
        # Check if vouch code exists and is unused
        vouches = await load_vouches()
        if vouch_code not in vouches:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, invalid vouch code. Please use a valid code generated by staff.", delete_after=10)
            return

        vouch_data = vouches[vouch_code]

        # Check if vouch is already used
        if vouch_data["used"]:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, this vouch code has already been used.", delete_after=10)
            return

        # Check if the user is the intended recipient
        if vouch_data["user_id"] != message.author.id:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, this vouch code is not for you.", delete_after=10)
            return

        # Mark vouch as used
        vouches[vouch_code]["used"] = True
        vouches[vouch_code]["used_at"] = datetime.now(timezone.utc).isoformat()
        vouches[vouch_code]["used_by"] = message.author.id
        await save_vouches(vouches)

        # React with checkmark
        await message.add_reaction("✅")

        # Add to user's vouch count
        user_id_str = str(message.author.id)
        if user_id_str not in vouches:
            vouches[user_id_str] = {"total_vouches": 0, "vouch_history": []}

        vouches[user_id_str]["total_vouches"] += 1
        # Display "Giveaway" if price is 0
        display_price = "Giveaway" if price.strip() == "0" else price
        vouches[user_id_str]["vouch_history"].append({
            "item": item,
            "price": price,  # Store original price
            "display_price": display_price,  # Store display price
            "code": vouch_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        await save_vouches(vouches)
        
    except Exception as e:
        print(f"Error processing vouch: {e}")
        await message.delete()
        await message.channel.send(f"❌ Error processing vouch: {str(e)}", delete_after=10)


async def handle_vouch_channel_message(message: discord.Message):
    """Handle messages in vouch channel - only allow vouch codes"""
    if message.channel.id != VOUCH_CHANNEL_ID:
        return
    
    # Allow bot messages
    if message.author.bot:
        return
    
    # Process the vouch message
    await process_vouch_message(message)


async def get_vouch_info(interaction: discord.Interaction, member: discord.Member = None):
    """Get vouch information for a user"""
    if member is None:
        member = interaction.user

    vouches = await load_vouches()
    user_id_str = str(member.id)
    
    if user_id_str not in vouches or vouches[user_id_str].get("total_vouches", 0) == 0:
        embed = create_embed(
            title="📊 Vouch Information",
            description=f"{member.mention} has no vouches yet.",
            color=discord.Color.blue(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    user_data = vouches[user_id_str]
    total_vouches = user_data.get("total_vouches", 0)
    vouch_history = user_data.get("vouch_history", [])
    
    # Display "Giveaway" if price is 0, otherwise use display_price or price
    recent_vouches = "\n".join([
        f"✅ {v['item']} - {v.get('display_price', 'Giveaway' if v['price'].strip() == '0' else v['price'])}" 
        for v in vouch_history[-5:]
    ])
    
    embed = create_embed(
        title="📊 Vouch Information",
        description=f"**User:** {member.mention}\n**Total Vouches:** {total_vouches}",
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="general",
        fields=[
            ("Recent Vouches", recent_vouches or "No recent vouches", False)
        ]
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def get_leaderboard(interaction: discord.Interaction):
    """Get vouch leaderboard"""
    vouches = await load_vouches()
    
    if not vouches:
        await interaction.response.send_message("No vouch data available yet.", ephemeral=True)
        return
    
    # Calculate leaderboard
    leaderboard = []
    for user_id_str, data in vouches.items():
        if user_id_str.isdigit():  # Skip vouch code entries
            total_vouches = data.get("total_vouches", 0)
            if total_vouches > 0:
                leaderboard.append({
                    "user_id": int(user_id_str),
                    "total_vouches": total_vouches
                })
    
    # Sort by total vouches
    leaderboard.sort(key=lambda x: x["total_vouches"], reverse=True)
    top_10 = leaderboard[:10]
    
    if not top_10:
        await interaction.response.send_message("No vouches yet.", ephemeral=True)
        return
    
    description = ""
    for i, entry in enumerate(top_10, 1):
        member = interaction.guild.get_member(entry["user_id"])
        member_name = member.name if member else f"User {entry['user_id']}"
        description += f"**{i}.** {member_name}\n   📊 {entry['total_vouches']} vouches\n\n"
    
    embed = create_embed(
        title="🏆 Vouch Leaderboard",
        description=description,
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="general"
    )
    await interaction.response.send_message(embed=embed)


async def vouch_button_handler(interaction: discord.Interaction):
    """Handle vouch button click - show modal for staff"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can generate vouch codes.", ephemeral=True)
        return

    # Check if in a ticket channel
    channel = interaction.channel
    from core_systems.ticket_utils import get_ticket_info
    info = get_ticket_info(channel)

    if not info.get("owner_id"):
        await interaction.response.send_message("This is not a valid ticket channel.", ephemeral=True)
        return

    # Show modal
    modal = VouchModal(info["owner_id"], channel.id)
    await interaction.response.send_modal(modal)


async def setticketmessage_command(interaction: discord.Interaction, message_type: str, title: str = None, description: str = None, color: str = None):
    """Set ticket message configuration"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can configure ticket messages.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    messages = await load_ticket_messages()

    if message_type not in messages:
        await interaction.followup.send(f"Invalid message type. Valid types: {', '.join(messages.keys())}", ephemeral=True)
        return

    if title:
        messages[message_type]["title"] = title
    if description:
        messages[message_type]["description"] = description
    if color:
        messages[message_type]["color"] = color

    await save_ticket_messages(messages)

    embed = create_embed(
        title="✅ Ticket Message Updated",
        description=f"Message type '{message_type}' has been updated.",
        color=discord.Color.green(),
        message_type="general",
        fields=[
            ("📝 Type", message_type, True),
            ("📌 Title", messages[message_type]["title"], True),
            ("🎨 Color", messages[message_type]["color"], True)
        ]
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def viewticketmessages_command(interaction: discord.Interaction):
    """View current ticket message configuration"""
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        await interaction.response.send_message("Only staff can view ticket message configuration.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    messages = await load_ticket_messages()

    description = ""
    for msg_type, config in messages.items():
        description += f"**{msg_type}**\n"
        description += f"Title: {config['title']}\n"
        description += f"Color: {config['color']}\n\n"

    embed = create_embed(
        title="📋 Ticket Message Configuration",
        description=description,
        color=discord.Color.blue(),
        message_type="general"
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
