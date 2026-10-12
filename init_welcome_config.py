"""
Initialize welcome configuration in Firebase
"""
import asyncio
import sys
import os
from dotenv import load_dotenv
from firebase_client import set_welcome_config

# Load environment variables
load_dotenv()


async def init_welcome_config():
    """Initialize welcome configuration in Firebase"""
    config = {
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

    success = await set_welcome_config(config)
    if success:
        print("SUCCESS: Welcome configuration initialized in Firebase!")
        print(f"   - Welcome Message: {config['welcome_message'][:50]}...")
        print(f"   - Embed Title: {config['embed_title']}")
        print(f"   - Embed Color: {config['embed_color']}")
        print(f"   - Banner Image: {config['welcome_image'][:60]}...")
        print(f"   - Footer: {config['footer_text']}")
    else:
        print("ERROR: Failed to initialize welcome configuration in Firebase")


if __name__ == "__main__":
    # Set UTF-8 encoding for Windows
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    asyncio.run(init_welcome_config())
