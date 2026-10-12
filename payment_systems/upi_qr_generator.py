"""
UPI QR Code Generator - Generate custom UPI QR codes with specific amounts
LTC QR Code Generator - Generate custom LTC QR codes with specific amounts
"""
import discord
from discord import app_commands
import qrcode
from io import BytesIO
import os
from config import SUPPORT_ROLE_ID, INR_WALLET_ADDRESS, LTC_WALLET_ADDRESS, get_data_dir
from utilities.embed_utils import create_embed
from utilities.logger import payment_logger


# UPI QR code storage
UPI_QR_DIR = os.path.join(get_data_dir(), "upi_qr_codes")

# LTC QR code storage
LTC_QR_DIR = os.path.join(get_data_dir(), "ltc_qr_codes")


def ensure_qr_directory():
    """Ensure the QR code directory exists"""
    if not os.path.exists(UPI_QR_DIR):
        os.makedirs(UPI_QR_DIR)
    if not os.path.exists(LTC_QR_DIR):
        os.makedirs(LTC_QR_DIR)


def generate_ltc_qr_code(ltc_address: str, amount: float = None, label: str = None, message: str = None):
    """
    Generate a LTC QR code
    
    Args:
        ltc_address: LTC wallet address
        amount: Amount in LTC (optional)
        label: Payee label (optional)
        message: Transaction message (optional)
    
    Returns:
        BytesIO object containing the QR code image
    """
    # Build LTC URL (Litecoin URI format)
    ltc_url = f"litecoin:{ltc_address}"
    
    params = []
    if amount:
        params.append(f"amount={amount}")
    if label:
        params.append(f"label={label}")
    if message:
        params.append(f"message={message}")
    
    if params:
        ltc_url += "?" + "&".join(params)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(ltc_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer


def save_ltc_qr_code(img_buffer: BytesIO, filename: str):
    """Save LTC QR code to file"""
    ensure_qr_directory()
    filepath = os.path.join(LTC_QR_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(img_buffer.getvalue())
    return filepath


def generate_upi_qr_code(upi_id: str, amount: float = None, name: str = None, note: str = None):
    """
    Generate a UPI QR code
    
    Args:
        upi_id: UPI ID (e.g., "example@upi")
        amount: Amount in INR (optional)
        name: Payee name (optional)
        note: Transaction note (optional)
    
    Returns:
        BytesIO object containing the QR code image
    """
    # Build UPI URL
    upi_url = f"upi://pay?pa={upi_id}"
    
    if amount:
        upi_url += f"&am={amount}"
    
    if name:
        upi_url += f"&pn={name}"
    
    if note:
        upi_url += f"&tn={note}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer


def save_qr_code(img_buffer: BytesIO, filename: str):
    """Save QR code to file"""
    ensure_qr_directory()
    filepath = os.path.join(UPI_QR_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(img_buffer.getvalue())
    return filepath


async def generate_custom_qr(interaction: discord.Interaction, amount: float, note: str = None):
    """Generate a custom UPI QR code with specific amount"""
    payment_logger.info(f"User {interaction.user.id} requested custom QR for ₹{amount}")

    if not INR_WALLET_ADDRESS:
        payment_logger.error("INR wallet address not configured")
        await interaction.response.send_message("INR wallet address not configured. Please set it using /setinrwallet.", ephemeral=True)
        return

    # Generate QR code
    img_buffer = generate_upi_qr_code(
        upi_id=INR_WALLET_ADDRESS,
        amount=amount,
        name="Trading Vault",
        note=note or "Payment"
    )

    payment_logger.debug(f"Generated custom QR code for ₹{amount}")

    # Save QR code
    filename = f"upi_{amount}_{interaction.user.id}.png"
    filepath = save_qr_code(img_buffer, filename)

    payment_logger.info(f"Saved custom QR code to {filename}")

    # Create embed
    embed = create_embed(
        title="💳 Custom UPI QR Code",
        description=f"**Amount:** ₹{amount}\n**UPI ID:** `{INR_WALLET_ADDRESS}`\n**Note:** {note or 'Payment'}",
        color=discord.Color.green(),
        message_type="payment_info",
        fields=[
            ("Instructions", "Scan this QR code with any UPI app to pay", False)
        ]
    )

    # Send QR code
    file = discord.File(filepath, filename=filename)
    embed.set_image(url=f"attachment://{filename}")

    await interaction.response.send_message(embed=embed, file=file)
    payment_logger.info(f"Sent custom QR to user {interaction.user.id}")


async def generate_qr_no_amount(interaction: discord.Interaction, note: str = None):
    """Generate a UPI QR code without specific amount (user can enter any amount)"""
    payment_logger.info(f"User {interaction.user.id} requested flexible amount QR")

    if not INR_WALLET_ADDRESS:
        payment_logger.error("INR wallet address not configured")
        await interaction.response.send_message("INR wallet address not configured. Please set it using /setinrwallet.", ephemeral=True)
        return

    # Generate QR code
    img_buffer = generate_upi_qr_code(
        upi_id=INR_WALLET_ADDRESS,
        amount=None,
        name="Trading Vault",
        note=note or "Payment"
    )

    payment_logger.debug("Generated flexible amount QR code")

    # Save QR code
    filename = f"upi_flexible_{interaction.user.id}.png"
    filepath = save_qr_code(img_buffer, filename)

    payment_logger.info(f"Saved flexible QR code to {filename}")

    # Create embed
    embed = create_embed(
        title="💳 UPI QR Code (Flexible Amount)",
        description=f"**UPI ID:** `{INR_WALLET_ADDRESS}`\n**Note:** {note or 'Payment'}\n\nUser can enter any amount when scanning.",
        color=discord.Color.blue(),
        message_type="payment_info",
        fields=[
            ("Instructions", "Scan this QR code with any UPI app and enter your desired amount", False)
        ]
    )

    # Send QR code
    file = discord.File(filepath, filename=filename)
    embed.set_image(url=f"attachment://{filename}")

    await interaction.response.send_message(embed=embed, file=file)
    payment_logger.info(f"Sent flexible QR to user {interaction.user.id}")


async def list_preset_amounts(interaction: discord.Interaction):
    """List preset QR code amounts"""
    # Check for existing QR codes
    ensure_qr_directory()
    
    if not os.path.exists(UPI_QR_DIR):
        await interaction.response.send_message("No preset QR codes found.", ephemeral=True)
        return
    
    qr_files = [f for f in os.listdir(UPI_QR_DIR) if f.endswith('.png')]
    
    if not qr_files:
        await interaction.response.send_message("No preset QR codes found.", ephemeral=True)
        return
    
    # Parse file names to get amounts
    amounts = set()
    for filename in qr_files:
        if filename.startswith("upi_") and not filename.startswith("upi_flexible"):
            try:
                # Extract amount from filename (format: upi_{amount}_{user_id}.png)
                parts = filename.replace("upi_", "").replace(".png", "").split("_")
                if parts[0].replace(".", "").isdigit():
                    amounts.add(float(parts[0]))
            except:
                pass
    
    if not amounts:
        await interaction.response.send_message("No preset QR codes found.", ephemeral=True)
        return
    
    # Create embed
    description = "**Available Preset Amounts:**\n\n"
    for amount in sorted(amounts):
        description += f"• ₹{amount}\n"
    
    embed = create_embed(
        title="💳 Preset UPI QR Codes",
        description=description,
        color=discord.Color.blue(),
        message_type="payment_info"
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def create_preset_qr(interaction: discord.Interaction, amount: float, note: str = None):
    """Create a preset QR code that can be reused"""
    payment_logger.info(f"Staff {interaction.user.id} requested preset QR for ₹{amount}")

    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        payment_logger.warning(f"Non-staff user {interaction.user.id} attempted to create preset QR")
        await interaction.response.send_message("Only staff can create preset QR codes.", ephemeral=True)
        return

    if not INR_WALLET_ADDRESS:
        payment_logger.error("INR wallet address not configured")
        await interaction.response.send_message("INR wallet address not configured. Please set it using /setinrwallet.", ephemeral=True)
        return

    # Generate QR code
    img_buffer = generate_upi_qr_code(
        upi_id=INR_WALLET_ADDRESS,
        amount=amount,
        name="Trading Vault",
        note=note or "Payment"
    )

    # Save QR code (without user ID for preset)
    filename = f"upi_{amount}.png"
    filepath = save_qr_code(img_buffer, filename)

    payment_logger.info(f"Created preset QR code for ₹{amount}")

    embed = create_embed(
        title="✅ Preset QR Code Created",
        description=f"**Amount:** ₹{amount}\n**Note:** {note or 'Payment'}\n\nThis QR code is now available as a preset.",
        color=discord.Color.green(),
        message_type="payment_info"
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


async def delete_preset_qr(interaction: discord.Interaction, amount: float):
    """Delete a preset QR code"""
    payment_logger.info(f"Staff {interaction.user.id} requested deletion of preset QR for ₹{amount}")

    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff:
        payment_logger.warning(f"Non-staff user {interaction.user.id} attempted to delete preset QR")
        await interaction.response.send_message("Only staff can delete preset QR codes.", ephemeral=True)
        return

    ensure_qr_directory()
    filename = f"upi_{amount}.png"
    filepath = os.path.join(UPI_QR_DIR, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        payment_logger.info(f"Deleted preset QR code for ₹{amount}")
        embed = create_embed(
            title="✅ Preset QR Code Deleted",
            description=f"QR code for ₹{amount} has been deleted.",
            color=discord.Color.green(),
            message_type="payment_info"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        payment_logger.warning(f"Preset QR code for ₹{amount} not found")
        await interaction.response.send_message(f"Preset QR code for ₹{amount} not found.", ephemeral=True)


async def send_preset_qr(interaction: discord.Interaction, amount: float):
    """Send a preset QR code to the channel"""
    payment_logger.info(f"User {interaction.user.id} requested preset QR for ₹{amount}")

    ensure_qr_directory()
    filename = f"upi_{amount}.png"
    filepath = os.path.join(UPI_QR_DIR, filename)

    if not os.path.exists(filepath):
        payment_logger.warning(f"Preset QR code for ₹{amount} not found")
        await interaction.response.send_message(f"Preset QR code for ₹{amount} not found. Create it first using /createpresetqr.", ephemeral=True)
        return

    # Create embed
    embed = create_embed(
        title="💳 Preset UPI QR Code",
        description=f"**Amount:** ₹{amount}\n**UPI ID:** `{INR_WALLET_ADDRESS}`",
        color=discord.Color.green(),
        message_type="payment_info",
        fields=[
            ("Instructions", "Scan this QR code with any UPI app to pay", False)
        ]
    )

    # Send QR code
    file = discord.File(filepath, filename=filename)
    embed.set_image(url=f"attachment://{filename}")

    await interaction.response.send_message(embed=embed, file=file)
    payment_logger.info(f"Sent preset QR to user {interaction.user.id}")


async def generate_custom_ltc_qr(interaction: discord.Interaction, amount: float, note: str = None):
    """Generate a custom LTC QR code with specific amount"""
    payment_logger.info(f"User {interaction.user.id} requested custom LTC QR for {amount} LTC")

    if not LTC_WALLET_ADDRESS:
        payment_logger.error("LTC wallet address not configured")
        await interaction.response.send_message("LTC wallet address not configured. Please set it using /setltcwallet.", ephemeral=True)
        return

    # Generate QR code
    img_buffer = generate_ltc_qr_code(
        ltc_address=LTC_WALLET_ADDRESS,
        amount=amount,
        label="Trading Vault",
        message=note or "Payment"
    )

    payment_logger.debug(f"Generated custom LTC QR code for {amount} LTC")

    # Save QR code
    filename = f"ltc_{amount}_{interaction.user.id}.png"
    filepath = save_ltc_qr_code(img_buffer, filename)

    payment_logger.info(f"Saved custom LTC QR code to {filename}")

    # Create embed
    embed = create_embed(
        title="₿ Custom LTC QR Code",
        description=f"**Amount:** {amount} LTC\n**LTC Address:** `{LTC_WALLET_ADDRESS}`\n**Note:** {note or 'Payment'}",
        color=discord.Color.from_rgb(53, 53, 53),  # Dark gray for LTC
        message_type="payment_info",
        fields=[
            ("Instructions", "Scan this QR code with any Litecoin wallet to pay", False)
        ]
    )

    # Send QR code
    file = discord.File(filepath, filename=filename)
    embed.set_image(url=f"attachment://{filename}")

    await interaction.response.send_message(embed=embed, file=file)
    payment_logger.info(f"Sent custom LTC QR to user {interaction.user.id}")


async def generate_ltc_qr_no_amount(interaction: discord.Interaction, note: str = None):
    """Generate a LTC QR code without specific amount (user can enter any amount)"""
    payment_logger.info(f"User {interaction.user.id} requested flexible amount LTC QR")

    if not LTC_WALLET_ADDRESS:
        payment_logger.error("LTC wallet address not configured")
        await interaction.response.send_message("LTC wallet address not configured. Please set it using /setltcwallet.", ephemeral=True)
        return

    # Generate QR code
    img_buffer = generate_ltc_qr_code(
        ltc_address=LTC_WALLET_ADDRESS,
        amount=None,
        label="Trading Vault",
        message=note or "Payment"
    )

    payment_logger.debug("Generated flexible amount LTC QR code")

    # Save QR code
    filename = f"ltc_flexible_{interaction.user.id}.png"
    filepath = save_ltc_qr_code(img_buffer, filename)

    payment_logger.info(f"Saved flexible LTC QR code to {filename}")

    # Create embed
    embed = create_embed(
        title="₿ LTC QR Code (Flexible Amount)",
        description=f"**LTC Address:** `{LTC_WALLET_ADDRESS}`\n**Note:** {note or 'Payment'}\n\nUser can enter any amount when scanning.",
        color=discord.Color.from_rgb(53, 53, 53),
        message_type="payment_info",
        fields=[
            ("Instructions", "Scan this QR code with any Litecoin wallet and enter your desired amount", False)
        ]
    )

    # Send QR code
    file = discord.File(filepath, filename=filename)
    embed.set_image(url=f"attachment://{filename}")

    await interaction.response.send_message(embed=embed, file=file)
    payment_logger.info(f"Sent flexible LTC QR to user {interaction.user.id}")
