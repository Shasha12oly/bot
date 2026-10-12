"""
Purchase ticket system module
"""
import discord
from config import CATEGORY_ID, SUPPORT_ROLE_ID, INR_QR_URL, LTC_QR_URL, INR_WALLET_ADDRESS, LTC_WALLET_ADDRESS
from utilities.embed_utils import create_embed
from .ticket_utils import owner_tag


class PurchaseSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Capes",
                description="Click to Buy...",
                emoji="🦅",
                value="capes"
            ),
            discord.SelectOption(
                label="Minecraft Accounts",
                description="Click to Buy...",
                emoji="⛏️",
                value="minecraft"
            ),
            discord.SelectOption(
                label="Discord Nitro",
                description="Click to Buy...",
                emoji="💎",
                value="nitro"
            ),
            discord.SelectOption(
                label="Boosts",
                description="Click to Buy...",
                emoji="🚀",
                value="boosts"
            ),
            discord.SelectOption(
                label="Discord Decoration",
                description="Click to Buy...",
                emoji="🎨",
                value="decoration"
            ),
        ]
        super().__init__(
            placeholder="Select What you want to buy",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="purchase:select"
        )

    async def callback(self, interaction: discord.Interaction):
        item = self.values[0]
        await create_purchase_ticket(interaction, item)


class PurchaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PurchaseSelect())


class PurchaseModal(discord.ui.Modal, title="Purchase Details"):
    def __init__(self, item: str):
        super().__init__()
        self.item = item

    quantity = discord.ui.TextInput(
        label="Quantity",
        placeholder="How many would you like to purchase?",
        max_length=10,
        required=True
    )

    payment_method = discord.ui.TextInput(
        label="Payment Method",
        placeholder="e.g., PayPal, Crypto, etc.",
        max_length=50,
        required=True
    )

    additional_info = discord.ui.TextInput(
        label="Additional Information",
        style=discord.TextStyle.long,
        placeholder="Any specific requirements or details...",
        max_length=1000,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await process_purchase(
            interaction,
            self.item,
            self.quantity.value,
            self.payment_method.value,
            self.additional_info.value,
            from_modal=True
        )


async def create_purchase_ticket(interaction: discord.Interaction, item: str):
    modal = PurchaseModal(item)
    await interaction.response.send_modal(modal)


async def process_purchase(interaction: discord.Interaction, item: str, quantity: str, payment_method: str, additional_info: str, from_modal: bool = False):
    """Process a purchase ticket"""
    guild = interaction.guild
    category_channel = guild.get_channel(CATEGORY_ID)
    support_role = guild.get_role(SUPPORT_ROLE_ID)

    if not category_channel:
        if from_modal:
            await interaction.followup.send(
                "Ticket category not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Ticket category not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        return

    if not support_role:
        if from_modal:
            await interaction.followup.send(
                "Support role not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Support role not found. Please contact an administrator to configure the bot.",
                ephemeral=True
            )
        return

    # Check for existing tickets
    for ch in category_channel.text_channels:
        if ch.topic and owner_tag(interaction.user.id) in ch.topic:
            if from_modal:
                await interaction.followup.send(
                    f"You already have an open ticket: {ch.mention}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"You already have an open ticket: {ch.mention}",
                    ephemeral=True
                )
            return

    # Load configurable ticket messages from database
    try:
        from community_systems.vouch_system import load_ticket_messages
        ticket_messages = await load_ticket_messages()
        purchase_msg = ticket_messages.get("purchase_creation", {})
        payment_msg = ticket_messages.get("payment_info", {})
    except:
        purchase_msg = {}
        payment_msg = {}

    member_perms = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        attach_files=True,
        embed_links=True
    )
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: member_perms,
        support_role: member_perms,
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            read_message_history=True
        ),
    }

    # Create channel
    channel_name = f"purchase-{item}-{interaction.user.name}"[:90]
    topic = f"{owner_tag(interaction.user.id)} | category:purchase | item:{item} | quantity:{quantity}"
    
    channel = await guild.create_text_channel(
        name=channel_name,
        category=category_channel,
        topic=topic,
        overwrites=overwrites,
    )

    # Create purchase embed
    item_names = {
        "capes": "Capes",
        "minecraft": "Minecraft Accounts",
        "nitro": "Discord Nitro",
        "boosts": "Boosts",
        "decoration": "Discord Decoration"
    }

    item_emojis = {
        "capes": "🦅",
        "minecraft": "⛏️",
        "nitro": "💎",
        "boosts": "🚀",
        "decoration": "🎨"
    }

    embed = create_embed(
        title=f"🛒 Purchase Ticket - {item_emojis.get(item, '📦')} {item_names.get(item, item)}",
        description=f"Thank you for your purchase request! Please complete the payment to proceed.\n\n**Item:** {item_names.get(item, item)}\n**Quantity:** {quantity}\n**Payment Method:** {payment_method}",
        color=discord.Color.from_rgb(0, 255, 255),  # Aqua #00FFFF
        message_type="purchase_creation",
        fields=[
            ("📦 Item", f"{item_emojis.get(item, '📦')} {item_names.get(item, item)}", True),
            ("🔢 Quantity", quantity, True),
            ("💳 Payment Method", payment_method, True),
            ("📊 Status", "⏳ Pending Payment", True),
            ("👤 Customer", interaction.user.mention, True)
        ]
    )

    if additional_info:
        embed.add_field(name="📝 Additional Info", value=additional_info, inline=False)

    # Import here to avoid circular dependency
    from .ticket_controls import PurchaseTicketControlView
    from .payment_system import PaymentMethodView

    # Send welcome message with payment info
    payment_info = create_embed(
        title="💳 Payment Information",
        description="⚠️ **Payment Required Before Delivery**\n\nPlease complete your payment to proceed with your order. Once payment is confirmed, your item will be delivered automatically.",
        color=discord.Color.from_rgb(255, 193, 7),  # Gold/Orange
        message_type="payment_info",
        fields=[
            ("🇮🇳 INR (UPI)", f"Wallet: `{INR_WALLET_ADDRESS if INR_WALLET_ADDRESS else 'Contact staff'}`", True),
            ("₿ LTC (Litecoin)", f"Wallet: `{LTC_WALLET_ADDRESS if LTC_WALLET_ADDRESS else 'Contact staff'}`", True),
            ("⏱️ Delivery Time", "Usually within 1-24 hours after payment confirmation", True),
            ("🛡️ Secure", "All payments are processed securely", True),
            ("📞 Support", "Ping the support team if you need help", False),
            ("� Important", "Please send a screenshot of your payment after completion for verification", False)
        ]
    )

    if INR_QR_URL:
        payment_info.add_field(name="🇮🇳 INR QR Code", value=f"[View QR Code]({INR_QR_URL})", inline=False)
    if LTC_QR_URL:
        payment_info.add_field(name="₿ LTC QR Code", value=f"[View QR Code]({LTC_QR_URL})", inline=False)

    await channel.send(
        content=f"{interaction.user.mention} {support_role.mention}",
        embed=embed,
        view=PurchaseTicketControlView()
    )
    await channel.send(embed=payment_info)

    # DM the user
    try:
        dm_embed = create_embed(
            title="Purchase Ticket Created",
            description=f"Your purchase ticket has been created successfully!\n\n**Channel:** {channel.mention}\n**Item:** {item_names.get(item, item)}\n**Quantity:** {quantity}\n\nPlease proceed to the channel to complete your payment.",
            color=discord.Color.from_rgb(0, 255, 255)  # Aqua #00FFFF
        )
        await interaction.user.send(embed=dm_embed)
    except discord.Forbidden:
        pass

    if from_modal:
        await interaction.followup.send(
            f"Your purchase ticket has been created: {channel.mention}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"Your purchase ticket has been created: {channel.mention}",
            ephemeral=True
        )
