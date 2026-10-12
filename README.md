# Trading Vault Discord Bot

A comprehensive Discord bot for managing a trading marketplace for Minecraft capes, accounts, Discord Nitro, and more.

## Features

- **Ticket System**
  - Support tickets (General Support, Account Issues, Giveaway Claims, Enquiry)
  - Purchase tickets for items
  - Priority levels (Low, Medium, High)
  - Close confirmation dialogs with transcript logging
  - Reopen closed tickets

- **Store System**
  - Capes store (Builder, Home, Copper, Menace, Purple Heart, Moonlight, Experience, Followers)
  - Minecraft accounts marketplace
  - Discord Nitro subscriptions
  - Server boosts
  - Avatar decorations
  - Dynamic pricing with INR/USD conversion

- **Payment System**
  - Multiple payment methods (INR UPI, LTC crypto)
  - QR code support for payments
  - Payment timeout handling
  - **UPI QR Generator** - Custom QR codes with specific amounts
  - **Firebase Firestore Database** - Persistent cloud database

- **Community Systems**
  - Giveaway system with multiple winners
  - Invite tracker with leaderboard
  - Welcomer system with custom messages
  - 5-star rating system with reviews
  - Vouch system for trust building

## Requirements

- Python 3.8+
- Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
DISCORD_TOKEN=your_bot_token_here
SUPPORT_ROLE_ID=123456789012345678
TICKET_CATEGORY_ID=123456789012345678
LOG_CHANNEL_ID=123456789012345678
RATING_CHANNEL_ID=123456789012345678
VOUCH_CHANNEL_ID=123456789012345678
INVITE_ANNOUNCEMENT_CHANNEL_ID=123456789012345678
SYNC_GUILD_ID=0
THUMBNAIL_URL=https://example.com/thumbnail.png
BANNER_URL=https://example.com/banner.png
INR_QR_URL=https://example.com/inr_qr.png
LTC_QR_URL=https://example.com/ltc_qr.png
INR_WALLET_ADDRESS=your_inr_wallet_address
LTC_WALLET_ADDRESS=your_ltc_wallet_address
FLASK_SECRET_KEY=your_secret_key_here
WEB_USERNAME=admin
WEB_PASSWORD=admin123
GIVEAWAY_CLAIM_CATEGORY_ID=123456789012345678
FIREBASE_PROJECT_ID=trading-vault-9e015
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key_with_newlines
FIREBASE_CLIENT_EMAIL=your_service_account_email
FIREBASE_CLIENT_ID=your_client_id
```

### 3. Run the Bot

```bash
python ticket_bot.py
```

### 4. Setup Commands

In your Discord server, run:
- `/ticketpanel` - Post the support ticket panel
- `/purchasepanel` - Post the purchase ticket panel
- `/sync` - Sync bot commands (admin only)

## Required Environment Variables

- `DISCORD_TOKEN` - Your Discord bot token (required)
- `SUPPORT_ROLE_ID` - Support/Staff role ID (required)
- `TICKET_CATEGORY_ID` - Category where tickets are created (required)
- `FIREBASE_PROJECT_ID` - Firebase project ID (required for database)
- `FIREBASE_PRIVATE_KEY_ID` - Firebase private key ID (required for database)
- `FIREBASE_PRIVATE_KEY` - Firebase private key (required for database)
- `FIREBASE_CLIENT_EMAIL` - Firebase client email (required for database)
- `FIREBASE_CLIENT_ID` - Firebase client ID (required for database)

## Optional Environment Variables

- `LOG_CHANNEL_ID` - Channel for ticket transcripts
- `RATING_CHANNEL_ID` - Channel for ratings
- `VOUCH_CHANNEL_ID` - Channel for vouches
- `INVITE_ANNOUNCEMENT_CHANNEL_ID` - Channel for invite announcements
- `SYNC_GUILD_ID` - Guild ID for faster command syncing
- `THUMBNAIL_URL` - Thumbnail image for embeds
- `BANNER_URL` - Banner image for embeds
- `INR_QR_URL` - INR QR code URL
- `LTC_QR_URL` - LTC QR code URL
- `INR_WALLET_ADDRESS` - INR wallet address
- `LTC_WALLET_ADDRESS` - LTC wallet address
- `FLASK_SECRET_KEY` - Secret key for web interface
- `WEB_USERNAME` - Web interface username
- `WEB_PASSWORD` - Web interface password
- `GIVEAWAY_CLAIM_CATEGORY_ID` - Category for giveaway claim tickets

## Commands

### Admin Commands
- `/ticketpanel` - Post support ticket panel
- `/purchasepanel` - Post purchase ticket panel
- `/sync` - Sync bot commands
- `/clearglobal` - Clear global commands
- `/config` - View bot configuration
- `/setcategory` - Set ticket category ID
- `/setrole` - Set support role ID
- `/setlogchannel` - Set log channel ID
- `/setthumbnail` - Set thumbnail URL
- `/setbanner` - Set banner image URL
- `/togglebanner` - Toggle banner visibility for specific message types
- `/bannersettings` - View current banner settings
- `/setinrqr` - Set INR QR code URL
- `/setltcqr` - Set LTC QR code URL
- `/setinrwallet` - Set INR wallet address
- `/setltcwallet` - Set LTC wallet address

### Giveaway Commands
- `/giveaway` - Create a giveaway
- `/endgiveaway` - End a giveaway
- `/reroll` - Reroll giveaway winners
- `/listgiveaways` - List active giveaways

### Invite Commands
- `/invitestats` - View your invite stats
- `/inviteleaderboard` - View invite leaderboard
- `/whoinvited` - Check who invited a user
- `/setinvitechannel` - Set invite announcement channel

### Welcomer Commands
- `/setwelcomemessage` - Set welcome message
- `/setwelcomerchannel` - Set welcome channel
- `/togglewelcome` - Toggle welcome messages on/off
- `/setgoodbyemessage` - Set goodbye message
- `/setgoodbyechannel` - Set goodbye channel
- `/togglegoodbye` - Toggle goodbye messages on/off
- `/welcomeconfig` - View welcome configuration
- `/togglestyledwelcome` - Toggle styled welcome messages
- `/setwelcomeimage` - Set welcome banner image URL
- `/setthumbnailimage` - Set welcome thumbnail image URL

### Store Commands
- `/postpricelist` - Post price list
- `/setstorechannel` - Set store channel
- `/updatepricelist` - Update price list
- `/storeinfo` - View store information
- `/postcapecards` - Post cape cards
- `/setcapeimage` - Set cape image
- `/reloadstoreconfig` - Reload store config
- `/setstorebanner` - Set store banner
- `/getstorebanner` - Get store banner

### Payment Commands
- `/generateqr` - Generate UPI QR code with specific amount
- `/generateqrflex` - Generate UPI QR code (flexible amount)
- `/listpresets` - List preset UPI QR codes
- `/createpresetqr` - Create a preset UPI QR code (staff only)
- `/deletepresetqr` - Delete a preset UPI QR code (staff only)
- `/sendpresetqr` - Send a preset UPI QR code

### Utility Commands
- `/serverinfo` - View server information
- `/userinfo` - View user information
- `/avatar` - View a user's avatar
- `/banner` - View a user's banner
- `/ping` - Check bot latency
- `/botstats` - View bot statistics
- `/kick` - Kick a member from the server
- `/ban` - Ban a member from the server
- `/unban` - Unban a user from the server
- `/purge` - Delete multiple messages
- `/slowmode` - Set slowmode for the channel
- `/lock` - Lock the channel
- `/unlock` - Unlock the channel
- `/8ball` - Ask the magic 8-ball a question
- `/flip` - Flip a coin
- `/roll` - Roll a dice
- `/random` - Generate a random number
- `/poll` - Create a poll
- `/suggest` - Submit a suggestion
- `/hug` - Hug someone
- `/slap` - Slap someone
- `/pat` - Pat someone

### Role Management Commands
- `/addrole` - Add a role to a member (staff only)
- `/removerole` - Remove a role from a member (staff only)
- `/listroles` - List all roles in the server
- `/roleinfo` - View detailed information about a role
- `/mute` - Mute a member (staff only)
- `/unmute` - Unmute a member (staff only)

## File Structure

```
trading/
├── ticket_bot.py              # Main bot entry point
├── config.py                  # Configuration module
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Your secrets (not in git)
├── railway.json                  # Railway deployment config
├── nixpacks.toml                 # Nixpacks configuration
├── Procfile                      # Railway start command
├── README.md                     # This file
│
├── core_systems/                 # Core ticket and store systems
│   ├── support_system.py      # Support ticket creation
│   ├── purchase_system.py     # Purchase ticket creation
│   ├── payment_system.py      # Payment method selection
│   ├── store_system.py        # Store and price list management
│   ├── ticket_management.py   # Ticket creation logic
│   ├── ticket_controls.py     # Ticket control buttons
│   ├── ticket_close.py        # Ticket closing logic
│   └── ticket_utils.py        # Ticket utilities
│
├── community_systems/            # Community engagement systems
│   ├── giveaway_system.py     # Giveaway hosting
│   ├── invite_tracker.py      # Invite tracking & leaderboard
│   ├── welcomer_system.py     # Welcome/goodbye messages
│   ├── rating_system.py       # 5-star rating system
│   └── vouch_system.py        # Vouch system for trust
│
├── payment_systems/           # Payment processing systems
│   └── upi_qr_generator.py    # UPI QR code generation
│
├── utilities/                 # Utility modules
│   ├── utilities.py           # General commands (info, moderation, fun)
│   ├── embed_utils.py         # Embed creation utilities
│   ├── logger.py              # Logging system
│   └── role_management.py     # Role management commands
│
├── web_interface/            # Web embed builder (local only)
│   ├── web_embed_builder.py   # Flask web app
│   ├── run_web_builder.bat     # Windows launcher
│   └── run_web_builder.sh      # Linux/Mac launcher
│
├── data_files/               # Data storage (JSON files)
│   ├── store_config.json      # Store configuration
│   ├── store_data.json        # Store data
│   ├── giveaways.json         # Giveaway data
│   ├── invites.json           # Invite tracking data
│   ├── invite_state.json     # Invite state tracking
│   ├── vouches.json          # Vouch data
│   ├── welcome_config.json    # Welcome configuration
│   ├── banner_config.json     # Banner settings
│   └── upi_qr_codes/         # Generated UPI QR codes
│
└── firebase_client.py          # Firebase Firestore client
```

## Web Interface (Local Only)

The web embed builder (`web_embed_builder.py`) runs **locally on your machine**, not on Railway.

### Running the Web Interface

**Windows:**
```bash
web_interface\run_web_builder.bat
```

**Linux/Mac:**
```bash
chmod +x web_interface/run_web_builder.sh
./web_interface/run_web_builder.sh
```

**Or manually:**
```bash
python web_interface/web_embed_builder.py
```

### Accessing the Web Interface

1. After starting, open your browser to: `http://localhost:5000`
2. Login with credentials from your `.env`:
   - Username: `WEB_USERNAME` (default: admin)
   - Password: `WEB_PASSWORD` (default: admin123)
3. Select a Discord channel
4. Build your embed with:
   - Title and description
   - Color picker
   - Thumbnail and banner images
   - Footer text
   - Multiple fields
5. Preview and post to Discord

### Important Notes

- The web interface uses the same `DISCORD_TOKEN` as your bot
- Make sure the bot is invited to your server
- The bot needs permissions to send messages in target channels
- **Do not run the web interface and the bot simultaneously** with the same token (causes conflicts)
- When using Railway deployment, run the web interface locally only when needed

## Support

For issues or questions, please check the documentation:
- [README.md](README.md) - Main documentation

## License

This project is part of Trading Vault.
