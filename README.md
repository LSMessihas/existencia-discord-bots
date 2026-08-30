# Existencia Discord Bots

Discord bots developed for the **Existencia** guild on **Celesta**.

The project currently includes two bots:

- **Exura** — Tibia information, hunt analysis, market utilities and party hunt tools.
- **GH Existencia Bot** — Guild House management, training dummy reservations and payment tracking.

Both bots are available in **Spanish and English**.

---

# Language Versions

The project provides separate Spanish and English versions instead of using automatic runtime translation.

This allows the Discord messages and terminology to be reviewed manually while preserving common Tibia terminology such as **hunt**, **loot**, **waste**, **split**, **charm**, **boosted creature**, **Market**, and other game-specific terms.

## Exura

- `bot_es.py` — Spanish version
- `bot_en.py` — English version

Both versions provide the same features and use the same external services.

Only the Discord-facing interface, command descriptions, messages and responses are translated.

## GH Existencia Bot

- `bot.py` — Original Spanish version
- `bot_en.py` — English version

Both versions provide the same Guild House management functionality.

> Only one language version of each bot should be running with the same Discord bot token at a time.

---

# Exura

Exura is a Discord assistant designed to provide Tibia information and useful tools directly inside Discord.

## Features

### Character Information

Look up Tibia characters and display useful information about them.

### Guild Information

Retrieve information about the **Existencia** guild and its online members.

### Creature & Bestiary Information

Search Tibia creatures and display information such as:

- Hit Points
- Experience
- Bestiary difficulty
- Charm Points
- Elemental weaknesses and resistances
- Maximum damage
- Locations
- Loot

### Hunt Analyzer

Analyze multiple creatures from the same hunting ground.

Exura combines their information to provide:

- Recommended attack elements
- Average elemental effectiveness
- Main incoming damage types
- Recommended elemental protections
- Quick equipment guidance

This makes it easier to prepare equipment for hunts containing several different creatures.

### Boss Information

Search Tibia bosses and display available information about them.

### Boosted Creature & Boss

Check the current:

- Boosted Creature
- Boosted Boss

### Item Information

Search Tibia items and display information such as:

- Equipment slot
- Vocations
- Attributes
- Elemental protections
- Other relevant item properties

### Celesta Market

Exura can retrieve Market information for items on **Celesta**.

Available information may include:

- Current sell offers
- Current buy offers
- Market timestamps

### Weekly Delivery Items

Exura includes the complete list of possible Weekly Delivery items.

The tool compares:

- NPC value
- Current Celesta Market value

This is particularly useful when clearing accumulated loot from the stash.

Instead of automatically selling everything to NPCs, players can quickly identify items that may be worth significantly more on the player Market.

Market information is cached locally to reduce unnecessary API requests.

### Party Hunt Split

Exura can parse Tibia Hunt Analyzer session data and automatically calculate the party split.

The system processes information such as:

- Loot
- Supplies
- Balance
- Damage
- Healing
- Session duration

It can then calculate:

- Total party profit
- Equal share
- Profit per hour
- Transfers between players
- Tibia bank transfer commands

---

# GH Existencia Bot

The GH Existencia Bot is designed to manage the Existencia Guild House.

## Features

### Training Dummy Reservations

Members can reserve Guild House training dummies using Discord slash commands.

The bot manages:

- Reservation dates
- Start and end times
- Reservation conflicts
- Maximum booking duration
- Automatic booking IDs

### Reservation Limits

Reservation limits can be configured depending on the Discord role.

Example configuration:

- GH Member — 4 hours
- GH Renter — 8 hours

These limits can be changed through environment variables.

### Reservation Panel

The bot maintains an automatically updated Discord embed containing the current dummy reservation schedule.

### Payment Tracking

Guild House payments can be registered directly through Discord.

The system supports:

- Guild House rent payments
- Training Dummy payments
- Monthly payment tracking
- Payment removal
- Payment summaries

### Automatic Roles

The bot can automatically assign or remove Discord roles depending on registered Guild House payments.

For this feature, the bot requires the **Manage Roles** permission.

The bot's Discord role must also be positioned above the roles it needs to manage.

---

# Project Structure

```text
existencia-discord-bots/
│
├── Exura/
│   ├── bot_es.py
│   ├── bot_en.py
│   ├── data/
│   ├── services/
│   ├── requirements.txt
│   └── .env.example
│
├── GH Existencia Bot/
│   ├── bot.py
│   ├── bot_en.py
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
├── README.md
├── SECURITY.md
└── LICENSE
```

---

# External Data Sources

Exura uses public Tibia-related APIs to retrieve game and Market information.

Current services include:

- TibiaData
- TibiaWiki
- TibiaMarket

No Tibia account credentials are required.

---

# Requirements

Python 3 is required to run the bots.

The required Python packages are listed in the corresponding `requirements.txt` files.

---

# Discord Bot Setup

Before running either bot, create a Discord application.

1. Open the Discord Developer Portal.
2. Create a new application.
3. Open the **Bot** section.
4. Create a bot user.
5. Generate or copy the bot token.
6. Store the token inside the bot's `.env` file.
7. Invite the bot to your Discord server with the required permissions.

Never place a real Discord bot token directly inside the source code.

Never commit your `.env` file to GitHub.

---

# Required Discord Permissions

## Exura

Exura requires standard permissions for slash commands and embeds.

Recommended permissions:

- View Channels
- Send Messages
- Embed Links
- Use Application Commands

Exura does **not** require Administrator permission.

## GH Existencia Bot

Recommended permissions:

- View Channels
- Send Messages
- Embed Links
- Use Application Commands
- Manage Roles

`Manage Roles` is required because the GH bot can automatically assign and remove Guild House roles.

The bot's role must be above the roles it manages in the Discord role hierarchy.

Administrator permission is **not required**.

---

# Finding Discord IDs

The GH bot requires several Discord IDs.

To obtain them:

1. Open Discord.
2. Go to **User Settings → Advanced**.
3. Enable **Developer Mode**.
4. Right-click the server or channel you need.
5. Select **Copy ID**.

These values can then be placed inside the `.env` configuration.

---

# Configuration

Each bot uses environment variables stored in a local `.env` file.

Example files are included in the repository as `.env.example`.

Copy the corresponding example file:

```bash
cp .env.example .env
```

On Windows, you can also simply duplicate `.env.example` and rename the copy to:

```text
.env
```

Then configure the required values.

---

# Exura Configuration

Example:

```env
DISCORD_TOKEN=""
DELIVERY_WORLD="Celesta"
DELIVERY_CACHE_HOURS="12"
```

`DELIVERY_WORLD` determines which Tibia world is used for Weekly Delivery Market comparisons.

---

# GH Existencia Bot Configuration

Example:

```env
DISCORD_TOKEN=""

GUILD_ID=""
COMMAND_CHANNEL_ID=""
SCHEDULE_CHANNEL_ID=""
RENT_CHANNEL_ID=""

MEMBER_ROLE=Miembro GH
RENTER_ROLE=Socio GH
ADMIN_ROLE=Gestor GH

MAX_MEMBER_HOURS=4
MAX_RENTER_HOURS=8
DEFAULT_DUMMY_PRICE=25
```

The role names can be changed to match the roles used by your Discord server.

For example, an English server could use:

```env
MEMBER_ROLE=GH Member
RENTER_ROLE=GH Renter
ADMIN_ROLE=GH Manager
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/LSMessihas/existencia-discord-bots.git
```

Enter the repository:

```bash
cd existencia-discord-bots
```

---

# Running Exura

Enter the Exura directory:

```bash
cd Exura
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create and configure your `.env` file.

## Spanish Version

```bash
python bot_es.py
```

## English Version

```bash
python bot_en.py
```

Run only the language version you want to use.

---

# Running GH Existencia Bot

Enter the GH bot directory.

From the repository root:

```bash
cd "GH Existencia Bot"
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create and configure your `.env` file.

## Spanish Version

```bash
python bot.py
```

## English Version

```bash
python bot_en.py
```

Run only the language version you want to use.

---

# Local Databases

Both bots may generate local SQLite databases while running.

Examples include:

```text
bookings.db
delivery_cache.db
```

These databases are generated locally and are excluded from Git through `.gitignore`.

They should not be committed to the repository.

The GH database may contain operational information such as:

- Discord user IDs
- Display names
- Reservations
- Payment records

For this reason, local database files should remain private.

---

# Security

The project is designed so that credentials are not stored directly in the source code.

Sensitive configuration is loaded through environment variables.

The repository excludes:

```text
.env
*.db
*.sqlite
*.sqlite3
*.log
```

Example environment files contain placeholders only.

Additional vulnerability reporting information is available in:

```text
SECURITY.md
```

If you discover a security issue, please follow the instructions in `SECURITY.md` instead of publicly disclosing sensitive details.

---

# GitHub Security

The repository uses GitHub security features to help identify potential vulnerabilities and exposed credentials.

These may include:

- Dependency graph
- Dependabot alerts
- Dependabot security updates
- Secret scanning
- Push protection
- Code scanning with CodeQL

These tools complement manual code review and do not replace normal security practices.

---

# Data & Privacy

The bots do not require Tibia account credentials.

Exura communicates with public Tibia-related services to retrieve game and Market information.

The GH bot stores reservation and payment information locally in SQLite.

Discord bot credentials are loaded from environment variables and should never be committed to the repository.

---

# Transparency

The complete source code is publicly available so Discord server administrators and community members can review:

- Bot permissions
- External API connections
- Stored data
- Discord interactions
- Database usage
- Security practices

The bots do not require Discord Administrator permission.

---

# Contributing

Suggestions, bug reports and improvements are welcome.

When reporting a bug, please include enough information to reproduce the issue while avoiding the publication of:

- Discord bot tokens
- API credentials
- Private database contents
- Other sensitive information

Security vulnerabilities should be reported according to `SECURITY.md`.

---

# License

This project is released under the **MIT License**.

See:

```text
LICENSE
```

for the complete license text.

---

# Disclaimer

This is an independent community project developed for the **Existencia** guild.

It is not affiliated with, endorsed by, or officially connected to **CipSoft GmbH**, **Tibia**, Discord, or the external API providers used by the project.

Tibia and related trademarks belong to their respective owners.
