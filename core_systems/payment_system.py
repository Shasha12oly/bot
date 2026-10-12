"""
Payment system module
"""
import discord
from config import INR_QR_URL, LTC_QR_URL, INR_WALLET_ADDRESS, LTC_WALLET_ADDRESS
from utilities.embed_utils import create_embed
from utilities.logger import payment_logger


class PaymentMethodView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🇮🇳 INR (UPI)", emoji="💰", style=discord.ButtonStyle.green, custom_id="payment:inr", row=0)
    async def inr_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_payment_details(interaction, "inr")

    @discord.ui.button(label="₿ LTC (Litecoin)", emoji="🪙", style=discord.ButtonStyle.blurple, custom_id="payment:ltc", row=0)
    async def ltc_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await show_payment_details(interaction, "ltc")


async def show_payment_details(interaction: discord.Interaction, method: str):
    payment_logger.info(f"User {interaction.user.id} requested {method} payment details")

    if method == "inr":
        embed = create_embed(
            title="🇮🇳 INR (UPI) Payment Details",
            description="Scan the QR code or use the wallet address below to make your payment. Payment will be verified automatically.",
            color=discord.Color.from_rgb(0, 200, 83),  # Green
            message_type="payment_info",
            fields=[
                ("💰 Wallet Address", f"```{INR_WALLET_ADDRESS if INR_WALLET_ADDRESS else 'Contact staff for details'}```", False),
                ("📸 Important", "Please send a screenshot of your payment after completion for verification", False),
                ("⚡ Alternative", "Use `/upiqr` to generate a QR code with auto-tracking", False),
                ("⏱️ Verification", "Payment verification usually takes 1-5 minutes", False)
            ]
        )
        if INR_QR_URL:
            embed.set_image(url=INR_QR_URL)
    else:  # ltc
        embed = create_embed(
            title="₿ LTC (Litecoin) Payment Details",
            description="Scan the QR code or use the wallet address below to make your payment. Payment will be verified automatically.",
            color=discord.Color.from_rgb(114, 137, 218),  # Blurple
            message_type="payment_info",
            fields=[
                ("🪙 Wallet Address", f"```{LTC_WALLET_ADDRESS if LTC_WALLET_ADDRESS else 'Contact staff for details'}```", False),
                ("📸 Important", "Please send a screenshot of your payment after completion for verification", False),
                ("⏱️ Verification", "Payment verification usually takes 1-5 minutes", False)
            ]
        )
        if LTC_QR_URL:
            embed.set_image(url=LTC_QR_URL)

    # Send as a new message instead of editing
    await interaction.response.send_message(embed=embed, ephemeral=True)
    payment_logger.debug(f"Sent {method} payment details to user {interaction.user.id}")
