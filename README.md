# Existencia Discord Bots

This repository contains two Discord bots developed for the Tibia guild **Existencia**.

The project currently includes:

- **Exura Bot** — Tibia information and utility bot.
- **Guild House Bot** — Guild House management, dummy reservations and payment tracking.

The source code is public so server administrators and community staff can review exactly what the bots do before adding them to their Discord servers.

---

# Exura Bot

Exura is a Discord bot focused on providing useful Tibia information and tools directly inside Discord.

## Main Features

### Character Information
Retrieve information about Tibia characters using external Tibia data sources.

### Guild Information
Check guild information and currently online guild members.

### Creature / Bestiary Information
Search creatures and display information such as:

- Hit Points
- Experience
- Bestiary difficulty
- Charm Points
- Elemental weaknesses and resistances
- Maximum damage
- Damage types
- Locations
- Loot

Elemental weaknesses and damage types are automatically sorted so players can quickly identify the best offensive element and the most important protections.

### Hunt Analyzer

Players can enter multiple creatures from a hunting ground and Exura combines their statistics.

The bot calculates:

- Best elemental damage to use
- Average elemental effectiveness
- Main incoming damage types
- Recommended elemental protections
- Secondary protection priorities

This is intended to help players prepare their equipment before hunting.

### Boss Information

Search Tibia bosses and retrieve relevant information.

The bot also supports information related to:

- Boosted Creature
- Boosted Boss

### Item Information

Search Tibia equipment and other items.

Depending on the available data, Exura can display:

- Item attributes
- Equipment slot
- Vocation requirements
- Elemental resistances
- Skills
- Other relevant properties

### Market Information

Exura integrates Tibia market information.

Market data can include:

- Current sell offer
- Current buy offer
- Average sell price
- Average buy price
- Last market update

The default world currently used by the bot is **Celesta**.

### Weekly Delivery Items

The bot contains the complete list of **476 items that can appear in Tibia Weekly Delivery Tasks**.

Using:

`/exura delivery`

players can compare:

**NPC sell price vs Celesta Market price**

The main purpose of this feature is to help players identify items stored in their Stash that may be worth significantly more when sold to other players instead of selling them directly to an NPC.

The Delivery interface includes:

- Alphabetical sorting
- Letter filtering
- Pagination
- NPC prices
- Celesta Market prices
- Cached market information to avoid unnecessary API requests

### Hunt Split Calculator

Exura can process Hunt Analyzer data copied directly from Tibia.

It calculates:

- Total loot
- Total supplies
- Total profit or waste
- Session duration
- Individual player balances
- Equal profit share
- Profit per hour
- Required transfers between party members

It can also generate the corresponding Tibia bank transfer commands.

---

# Guild House Bot

The Guild House bot was developed to automate the management of the **Existencia Guild House**.

## Dummy Reservations

Guild members can reserve training dummy time directly through Discord.

The system supports:

- Date selection
- Start and end time
- Reservation conflict detection
- Reservation cancellation
- Reservation limits depending on membership status

The bot prevents overlapping reservations automatically.

## Reservation Panel

The bot maintains a Discord panel showing current dummy reservations.

The panel updates automatically whenever reservations are created or cancelled.

## Guild House Payments

The bot can register payments related to:

- Guild House rent
- Training dummy usage

Guild House rent can also be paid several months in advance.

Administrators can review or remove payment records when necessary.

## Discord Role Management

The payment system is connected to Discord roles.

The bot can automatically assign membership roles depending on Guild House payment status.

These roles can also determine reservation privileges.

---

# Project Structure

```text
existencia-discord-bots/
│
├── exura/
│   ├── bot.py
│   ├── services/
│   ├── requirements.txt
│   └── .env.example
│
├── gh-bot/
│   ├── bot.py
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
└── README.md