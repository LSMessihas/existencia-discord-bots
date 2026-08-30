# Existencia Discord Bots

This repository contains two Discord bots developed for the Tibia guild **Existencia** on **Celesta**.

The project includes:

- **Exura** — A Tibia information and utility bot.
- **GH Existencia Bot** — A Guild House management, training dummy reservation and payment tracking bot.

The source code is publicly available so Discord server administrators and community staff can review exactly what the bots do before adding them to their servers.

---

# Exura

**Exura** is a Discord bot focused on providing useful Tibia information and tools directly inside Discord.

## Main Features

### Character Information

Retrieve information about Tibia characters using external Tibia data sources.

### Guild Information

Check guild information and currently online guild members, including information such as:

- Character name
- Level
- Vocation
- Guild rank
- Online status

### Creature / Bestiary Information

Search Tibia creatures and display useful information such as:

- Hit Points
- Experience
- Bestiary difficulty
- Charm Points
- Elemental weaknesses and resistances
- Maximum damage
- Damage types
- Locations
- Loot

Elemental weaknesses are automatically sorted so players can quickly identify which damage types are most effective against a creature.

Incoming damage types are also organized to help players understand which elemental protections they should prioritize.

---

## Hunt Analyzer

Exura includes a Hunt Analyzer capable of analyzing multiple creatures from the same hunting ground.

Instead of checking every creature individually, players can enter all the creatures they expect to encounter.

For example:

```text
Juggernaut
Demon Outcast
Dark Torturer
```

Exura combines their information and calculates:

- Best elemental damage to use
- Average elemental effectiveness
- Main incoming damage types
- Recommended elemental protections
- Secondary protection priorities

The purpose is to help players prepare their weapons, equipment, imbuments and elemental protection before starting a hunt.

---

## Boss Information

Exura can search Tibia bosses and display relevant information about them.

The bot also supports information related to:

- Boosted Creature
- Boosted Boss

This allows players to check useful daily information directly from Discord.

---

## Item Information

Players can search Tibia equipment and other items.

Depending on the available data, Exura can display:

- Item attributes
- Equipment slot
- Vocation requirements
- Elemental resistances
- Skill bonuses
- Other relevant properties

---

## Celesta Market Information

Exura integrates Tibia Market information.

Market data can include:

- Current sell offer
- Current buy offer
- Average sell price
- Average buy price
- Last market update

The default world currently used by the bot is **Celesta**.

---

## Weekly Delivery Items

Exura contains the complete list of **476 items that can appear in Tibia's Weekly Delivery Tasks**.

Using:

```text
/exura delivery
```

players can browse the Delivery Item database and compare:

**NPC sell price vs Celesta Market price**

### Why this feature exists

The main purpose is not simply to search the Market price of an individual item.

Tibia players accumulate hundreds or thousands of creature products in their **Stash** while hunting.

When players periodically sell their accumulated loot, many of these items may be sold automatically to NPCs even though some can be worth considerably more when sold to other players through the Market.

The Delivery tool helps identify these items.

Instead of manually checking hundreds of items one by one, players can quickly see:

> **Which items should I keep from my NPC sale and sell on the Market instead?**

The interface includes:

- All 476 eligible Delivery Items
- NPC sell prices
- Celesta Market prices
- Alphabetical sorting
- Letter filtering
- Pagination
- Market data caching

Market information is cached to avoid unnecessary API requests and reduce the risk of API rate limiting.

---

## Hunt Split Calculator

Exura can process **Hunt Analyzer data copied directly from Tibia**.

The bot analyzes:

- Total loot
- Total supplies
- Total profit or waste
- Session duration
- Individual player balances
- Damage
- Healing
- Equal profit per player
- Profit per hour

It then automatically calculates the transfers required to distribute the hunt profit equally between party members.

For example:

```text
Player A has to pay 850,000 gp to Player B
```

The bot can also generate the corresponding Tibia bank transfer command:

```text
transfer 850000 to Player B
```

This removes the need to calculate party hunt splits manually.

---

# GH Existencia Bot

The **GH Existencia Bot** was developed to automate the management of the Existencia Guild House.

Its main purpose is to manage training dummy reservations, Guild House payments and membership privileges directly through Discord.

---

## Training Dummy Reservations

Guild members can reserve training dummy time directly through Discord.

The reservation system supports:

- Date selection
- Starting time
- Ending time
- Reservation conflict detection
- Reservation cancellation
- Reservation limits based on membership status

The bot automatically prevents two players from reserving the same dummy during overlapping time periods.

---

## Reservation Limits

Different Guild House membership levels can have different reservation privileges.

For example, contributing Guild House members can receive longer reservation periods than regular members.

These limits are configured through environment variables and enforced automatically by the bot.

---

## Reservation Panel

The bot maintains a dedicated Discord panel showing current training dummy reservations.

The panel automatically updates whenever:

- A reservation is created
- A reservation is cancelled

This allows Guild House members to quickly see when the training dummy is available.

---

## Guild House Payments

The bot can register payments related to:

- Guild House rent
- Training dummy usage

Guild House rent can also be registered several months in advance.

For example, if a member pays three months of rent at once, the bot can register those months individually.

Administrators can also review payment information and remove incorrect payment records when necessary.

---

## Automatic Discord Role Management

The payment system is connected to Discord roles.

The bot can automatically assign Guild House membership roles depending on payment status.

These roles can then determine:

- Guild House membership
- Training dummy privileges
- Maximum reservation duration

This reduces the amount of manual administration required from guild leaders.

---

# Project Structure

```text
existencia-discord-bots/
│
├── Exura/
│   ├── bot.py
│   ├── data/
│   ├── services/
│   ├── requirements.txt
│   └── .env.example
│
├── GH Existencia Bot/
│   ├── bot.py
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
├── LICENSE
├── SECURITY.md
└── README.md
```

SQLite databases used for reservations, payments and cached data are generated locally when required and are intentionally excluded from the repository.

---

# External Data Sources

Exura retrieves public Tibia information from external services.

Current integrations include services related to:

- TibiaData
- TibiaWiki
- Tibia Market information

These API requests are used only to retrieve Tibia-related public information.

Market information is cached where appropriate to avoid unnecessary requests and API rate-limit issues.

---

# Configuration

Both bots use environment variables for configuration.

Real credentials are **not included in this repository**.

Each bot includes a `.env.example` file showing which environment variables are required.

## Exura configuration

```env
DISCORD_TOKEN=""
DELIVERY_WORLD="Celesta"
DELIVERY_CACHE_HOURS="12"
```

## GH Existencia Bot configuration

The Guild House bot requires additional configuration for the Discord server, channels, roles and reservation limits.

An example configuration is provided in:

```text
GH Existencia Bot/.env.example
```

The actual `.env` files containing real credentials must remain local and must never be committed to the repository.

---

# Discord Bot Setup

Before running either bot, create a Discord application and bot account through the **Discord Developer Portal**.

1. Create a new Discord application.
2. Open the **Bot** section and create/configure the bot user.
3. Generate or reset the bot token.
4. Copy the token into the local `.env` file:

```env
DISCORD_TOKEN="YOUR_BOT_TOKEN"
```

**Never commit the real bot token to GitHub.**

---

# Required Discord Permissions

## Exura

Exura does **not** require Administrator permission.

Recommended permissions:

- View Channels
- Send Messages
- Embed Links
- Use Application Commands

The bot uses standard Discord functionality required to respond to slash commands and display Tibia information.

## GH Existencia Bot

The Guild House bot requires:

- View Channels
- Send Messages
- Embed Links
- Use Application Commands
- Manage Roles

`Manage Roles` is required for automatic Guild House membership role management.

The bot's Discord role must be positioned **above the roles it needs to manage** in the Discord role hierarchy.

Administrator permission is not required.

---

# Finding Discord IDs

The Guild House bot requires several Discord IDs.

Enable **Developer Mode** in Discord:

```text
User Settings → Advanced → Developer Mode
```

You can then right-click the relevant server or channel and select **Copy ID**.

These values correspond to:

```env
GUILD_ID=""
COMMAND_CHANNEL_ID=""
SCHEDULE_CHANNEL_ID=""
RENT_CHANNEL_ID=""
```

The role names and reservation limits can also be configured through the `.env` file.

---

# Installation

## Requirements

- Python 3
- A Discord bot application
- Internet access for Tibia-related API requests

Clone the repository:

```bash
git clone https://github.com/LSMessihas/existencia-discord-bots.git
```

---

## Running Exura

Enter the Exura directory:

```bash
cd existencia-discord-bots/Exura
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`.

On Windows:

```bash
copy .env.example .env
```

On Linux/macOS:

```bash
cp .env.example .env
```

Edit `.env` and add your Discord bot token.

Then start Exura:

```bash
python bot.py
```

---

## Running GH Existencia Bot

Enter the Guild House bot directory.

On Windows:

```bash
cd "existencia-discord-bots\GH Existencia Bot"
```

On Linux/macOS:

```bash
cd "existencia-discord-bots/GH Existencia Bot"
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`.

On Windows:

```bash
copy .env.example .env
```

On Linux/macOS:

```bash
cp .env.example .env
```

Configure the required Discord server ID, channel IDs, roles and reservation limits in `.env`.

Then start the bot:

```bash
python bot.py
```

---

# Local Databases

The bots may create local SQLite databases for features such as:

- Guild House reservations
- Payment records
- Market caching

These databases are generated automatically when required.

They are intentionally excluded from Git using `.gitignore` because they may contain local operational data and are not required as part of the source code.

---

# Security

Discord bot tokens and other sensitive credentials are **not stored in the source code**.

Sensitive configuration is loaded through environment variables.

The repository's `.gitignore` excludes:

- `.env` files
- Local databases
- Python cache files
- Logs
- Temporary files
- Local development files

The repository also includes a `SECURITY.md` file describing how security vulnerabilities should be reported.

Security-related repository features such as dependency monitoring, secret protection and code scanning may also be enabled through GitHub.

---

# Transparency

These bots were originally developed for the **Existencia** guild on **Celesta**.

The source code is public so Tibia community members and Discord server administrators can inspect the implementation and verify exactly what the bots do before allowing them onto their servers.

The goal of this repository is to provide useful community tools while keeping their implementation transparent and auditable.

---

# License

This project is distributed under the **MIT License**.

See the `LICENSE` file for details.

---

# Disclaimer

This is an independent community project.

It is not affiliated with, endorsed by, sponsored by, or associated with **CipSoft GmbH** or **Tibia**.

Tibia and all Tibia-related content are trademarks of their respective owners.
