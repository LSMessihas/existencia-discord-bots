import os
import re
import asyncio
import difflib
import unicodedata
import sqlite3
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from services.tibiadata import (
    get_character,
    get_guild,
    get_creatures_list,
    get_boostable_bosses,
    get_boosted_creature,
    get_boosted_boss,
    extract_boosted_boss_names
)

from services.tibiawiki import (
    get_wiki_creature,
    get_bosses_list,
    get_wiki_boss,
    get_items_list,
    get_wiki_item
)

from services.market import (
    get_market_price,
    format_gold,
    format_market_timestamp
)


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_NAME = "Existencia"


BASE_DIR = Path(__file__).resolve().parent
DELIVERY_DB_FILE = str(BASE_DIR / "delivery_cache.db")
TRACKING_DB_FILE = str(BASE_DIR / "guild_tracking.db")
TRACKING_POLL_SECONDS = int(os.getenv("TRACKING_POLL_SECONDS", "300"))
TRACKING_MAX_CONCURRENCY = int(os.getenv("TRACKING_MAX_CONCURRENCY", "8"))
DELIVERY_WORLD = os.getenv("DELIVERY_WORLD", "Celesta")
DELIVERY_CACHE_HOURS = int(os.getenv("DELIVERY_CACHE_HOURS", "12"))
TIBIA_MARKET_API = os.getenv(
    "TIBIA_MARKET_API",
    "https://api.tibiamarket.top"
).rstrip("/")

DELIVERY_ITEMS = [('Afflicted Strider Head', 900), ('Afflicted Strider Worms', 500), ('Alloy Legs', 11000), ('Amber Souvenir', 850), ('Ancient Belt Buckle', 260), ('Ancient Stone', 200), ('Angelic Axe', 5000), ('Apron', 1300), ('Badger Boots', 7500), ('Banana Sash', 55), ('Basalt Core', 5800), ('Basalt Crumbs', 3000), ('Basalt Fetish', 210), ('Basalt Figurine', 160), ('Bashmu Fang', 600), ('Bashmu Feather', 350), ('Bashmu Tongue', 400), ('Battle Shield', 95), ('Black Shield', 800), ('Blemished Spawn Abdomen', 550), ('Blemished Spawn Head', 800), ('Blemished Spawn Tail', 1000), ('Bloated Maggot', 5200), ('Blood Amulet', 1230), ('Blood Hood', 1550), ('Blood Preservation', 320), ('Blood Tincture In A Vial', 360), ('Blooded Worm', 4700), ('Bloodshot Giant Eye', 1820), ('Blue Goanna Scale', 230), ('Boar Man Hoof', 600), ('Boggy Dreads', 200), ('Bola', 35), ('Bone Club', 5), ('Bone Fetish', 150), ('Bone Fibula', 580), ('Bone Rattle', 790), ('Bone Shoulderplate', 150), ('Bone Toothpick', 150), ('Bonebreaker', 10000), ('Bonecarving Knife', 190), ('Bony Tail', 210), ('Book of Necromantic Rituals', 180), ('Book Page', 640), ('Book With A Dragon', 1800), ('Book With An Hourglass', 1450), ('Bowl of Terror Sweat', 500), ('Brigadeiro', 2640), ('Brinebrute Claw', 2600), ('Broadsword', 500), ('Broken Draken Mail', 340), ('Broken Gladiator Shield', 190), ('Broken Halberd', 100), ('Broken Mitmah Necklace', 210), ('Broken Slicer', 120), ('Broken Throwing Axe', 230), ('Broodrider Saddle', 2800), ('Buckle', 7000), ('Bulltaur Armor Scrap', 480), ('Bulltaur Hoof', 540), ('Bulltaur Horn', 385), ('Bundle of Cursed Straw', 800), ('Capricious Heart', 2100), ('Capricious Robe', 1200), ('Carnisylvan Bark', 230), ('Carnisylvan Finger', 250), ('Carnivostrich Feather', 630), ("Cat's Paw", 2000), ('Cave Chimera Head', 1200), ('Cave Chimera Leg', 650), ('Cave Devourer Eyes', 550), ('Cave Devourer Legs', 350), ('Cave Devourer Maw', 600), ('Centipede Leg', 28), ('Chain Leash', 970), ('Chaos Mace', 9000), ('Chasm Spawn Abdomen', 240), ('Chasm Spawn Head', 850), ('Chasm Spawn Tail', 120), ('Cheese Cutter', 50), ('Cheesy Figurine', 150), ('Cluster of Crystallized Death', 9000), ('Cobra Crest', 650), ('Colourful Feather', 110), ('Colourful Snail Shell', 250), ('Combat Knife', 1), ('Compound Eye', 150), ('Cookbook', 870), ('Coral Branch', 360), ('Cowbell', 210), ('Crab Man Claws', 550), ('Cracked Alabaster Vase', 180), ("Crawler's Essence", 3700), ('Crown', 2700), ('Cry-Stal', 3200), ('Crystal Bone', 250), ('Crystal Crossbow', 35000), ('Crystal Mace', 12000), ('Crystal of The Mitmah', 280), ('Crystal Sword', 600), ('Crystalline Armor', 16000), ('Crystalline Spikes', 440), ('Crystalline Sword', 0), ('Crystallized Death', 3000), ('Cuirass Plate', 1000), ('Curious Matter', 430), ('Cursed Shoulder Spikes', 320), ('Damaged Armor Plates', 280), ('Damselfly Eye', 25), ('Dandelion Seeds', 200), ('Dangerous Proto Matter', 300), ('Dark Obsidian Splinter', 4400), ('Dark Rosary', 48), ('Dark Shield', 400), ('Darklight Basalt Chunk', 3800), ('Darklight Core', 4100), ('Darklight Matter', 5500), ('Dead Weight', 450), ('Deadly Fangs', 5500), ('Decayed Finger Bone', 5100), ('Deepling Breaktime Snack', 90), ('Deepling Claw', 430), ('Deepling Guard Belt Buckle', 230), ('Deepling Ridge', 360), ('Deepling Scales', 80), ('Deeptags', 290), ('Deepworm Jaws', 500), ('Deepworm Spike Roots', 650), ('Deepworm Spikes', 800), ('Demon Root', 950), ('Demonic Matter', 0), ('Diamond Sceptre', 3000), ('Diremaw Brainpan', 350), ('Diremaw Legs', 270), ('Dirty Turban', 120), ('Distorted Heart', 2100), ('Distorted Robe', 1200), ('Double Axe', 260), ('Dowser', 35), ('Dragolisk Eye', 690), ('Dragolisk Poison Gland', 475), ('Dragon Hammer', 2000), ("Dragon Priest's Wandtip", 175), ('Dragon Slayer', 15000), ('Dragon Tongue', 550), ("Dragon's Tail", 100), ('Draken Wristbands', 430), ('Dream Essence Egg', 205), ('Dung Ball', 130), ('Earflap', 40), ('Elder Bonelord Tentacle', 150), ('Elven Astral Observer', 90), ('Emerald Tortoise Shell', 2150), ('Empty Honey Glass', 270), ('Encrypted Notes', 620), ('Energy Ball', 300), ('Ensouled Essence', 820), ('Essence of A Bad Dream', 360), ('Exalted Core', 0), ('Execowtioner Mask', 240), ('Eye of A Deepling', 150), ('Eye of A Weeper', 650), ('Eye of Corruption', 390), ('Eyeless Devourer Legs', 650), ('Eyeless Devourer Maw', 420), ('Eyeless Devourer Tongue', 900), ('Fafnar Symbol', 950), ('Falcon Crest', 650), ('Fig Leaf', 200), ('Fir Cone', 25), ('Fire Axe', 8000), ('Flask of Demonic Blood', 0), ('Flotsam', 330), ('Focus Cape', 6000), ('Fox Paw', 100), ('Frazzle Tongue', 700), ('Frozen Lightning', 270), ('Fur Armor', 5000), ('Gauze Bandage', 90), ('Ghastly Dragon Head', 700), ('Giant Pacifier', 170), ('Giant Tusk', 6000), ('Girlish Hair Decoration', 30), ('Girtablilu Warrior Carapace', 520), ('Glacier Mask', 2500), ('Glacier Robe', 11000), ('Glacier Shoes', 2500), ('Glob of Acid Slime', 25), ('Glob of Glooth', 125), ('Glob of Tar', 30), ('Glooth Axe', 1500), ('Glooth Blade', 1500), ('Glooth Cape', 7000), ('Glooth Club', 1500), ('Glooth Injection Tube', 350), ('Glorious Axe', 3000), ('Glowing Rune', 350), ('Goanna Claw', 260), ('Goanna Meat', 190), ('Gold Tooth', 120), ('Golden Legs', 30000), ('Golden Lotus Brooch', 270), ('Golden Sickle', 1000), ('Golden Sun Coin', 11000), ('Gore Horn', 2900), ('Gorerilla Mane', 2750), ('Gorerilla Tail', 2650), ('Gorger Antlers', 2250), ('Grappling Hook', 150), ('Green Bandage', 180), ('Guardian Shield', 2000), ('Halberd', 400), ('Half-Digested Stones', 40), ('Half-Eaten Brain', 85), ('Hand', 1450), ('Harpy Feathers', 730), ('Headpecker Beak', 2800), ('Headpecker Feather', 1300), ('Heart Amphora', 930), ('Heavy Machete', 90), ('Heavy Trident', 2000), ('Hellhound Slobber', 500), ('Hemp Rope', 350), ('Hibiscus Dress', 3000), ('Hideous Chunk', 510), ('High Guard Flag', 550), ('High Guard Shoulderplates', 130), ('Holy Ash', 160), ('Horoscope', 40), ('Human Teeth', 2000), ('Humongous Chunk', 540), ('Hydra Head', 600), ('Hydrophytes', 220), ('Ice Flower', 370), ('Idol of The Forge', 950), ('Infernal Heart', 2100), ('Infernal Robe', 1200), ('Infernoid Ember', 160), ('Inkwell', 720), ('Instable Proto Matter', 300), ('Ivory Carving', 300), ('Jaws', 3900), ('Key To The Drowned Library', 330), ('Knife', 1), ('Knight Axe', 2000), ('Knight Legs', 5000), ("Kongra's Shoulderpad", 100), ('Lamassu Hoof', 330), ('Lamassu Horn', 240), ('Lancer Beetle Shell', 80), ('Lancet', 90), ('Lavafungus Head', 900), ('Lavafungus Ring', 390), ('Lavaworm Jaws', 1100), ('Lavaworm Spike Roots', 600), ('Lavaworm Spikes', 750), ('Lightning Boots', 2500), ('Lightning Headband', 2500), ('Lightning Robe', 11000), ('Lime Tart', 1870), ('Liodile Fang', 480), ('Lion Cloak Patch', 190), ('Lion Crest', 270), ('Lizard Tail', 95), ("Lost Basher's Spike", 280), ('Lost Bracers', 140), ('Luminous Orb', 1000), ('Lump of Earth', 130), ('Mad Froth', 80), ('Magma Boots', 2500), ('Magma Clump', 570), ('Magma Coat', 11000), ('Magma Monocle', 2500), ('Makara Fin', 350), ('Makara Tongue', 320), ('Mammoth Tusk', 100), ('Mammoth Whopper', 300), ('Manticore Ear', 310), ('Manticore Tail', 220), ('Mantosaurus Jaw', 2800), ('Mega Dragon Heart', 1100), ('Mercenary Sword', 12000), ('Mercurial Wing', 2500), ('Metal Bat', 9000), ('Metal Jaw', 260), ('Metal Spats', 2000), ('Mino Lance', 7000), ('Mino Shield', 3000), ('Molten Dragon Essence', 840), ('Mould Heart', 2100), ('Mould Robe', 1200), ('Mouldy Powder', 200), ('Mummified Demon Finger', 800), ('Mutated Bat Ear', 420), ('Mutated Flesh', 50), ('Mutated Rat Tail', 150), ('Naga Archer Scales', 340), ('Naga Armring', 390), ('Naga Earring', 380), ('Naga Warrior Scales', 340), ('Necromantic Core', 10000), ('Necromantic Rust', 390), ('Night Harpy Feathers', 5000), ('Nighthunter Wing', 2000), ("Nimmersatt's Seal", 520), ('Odd Organ', 410), ('Ogre Ear Stud', 180), ('Old Girtablilu Carapace', 570), ('Orcish Axe', 350), ('Orcish Gear', 85), ('Orcish Toothbrush', 750), ('Ornate Crossbow', 12000), ('Pair of Hellflayer Horns', 1300), ('Paper Boat', 800), ('Paper Plane', 480), ('Piece of Draconian Steel', 3000), ('Piece of Frozen Night', 680), ('Piece of Hell Steel', 500), ('Piece of Warrior Armor', 50), ("Pirat's Tail", 180), ('Pirate Coin', 110), ('Plasma Pearls', 250), ('Plasmatic Lightning', 270), ('Plate Legs', 115), ('Poisoned Fang', 130), ('Pool of Chitinous Glue', 480), ('Pot of Orcish Warpaint', 1150), ('Prehemoth Claw', 2300), ('Prehemoth Horns', 3000), ('Pressed Flower', 570), ('Pulverized Ore', 400), ('Quara Bone', 500), ('Quara Eye', 350), ('Quara Pincers', 410), ('Quara Tentacle', 140), ('Ratana', 500), ('Raw Meat', 0), ('Red Goanna Scale', 270), ('Red Hair Dye', 40), ('Relic Sword', 25000), ('Resin Parasite', 1450), ('Resinous Fish Fin', 1250), ('Rhindeer Antlers', 680), ('Ripper Lance', 500), ('Ripptor Claw', 2600), ('Ripptor Scales', 1200), ('Ritual Bone Knife', 820), ('Ritual Tooth', 135), ('Rod', 2200), ('Roots', 1200), ('Rotten Feather', 120), ('Rotten Piece of Cloth', 30), ('Rotten Roots', 3800), ('Rotten Vermin Ichor', 4500), ('Rubber Cap', 11000), ('Sabretooth Fur', 2500), ('Sandcrawler Shell', 20), ('Scale of Corruption', 680), ('Scarab Pincers', 280), ('Scimitar', 150), ('Scorpion Charm', 620), ('Scroll of Heroic Deeds', 230), ('Scythe Leg', 450), ('Sealing Wax', 620), ('Shaggy Tail', 25), ('Shamanic Talisman', 200), ('Shark Fins', 250), ('Shimmering Beetles', 150), ('Shiny Stone', 500), ('Silencer Resonating Chamber', 600), ('Silken Bookmark', 1300), ('Silver Moon Coin', 11000), ('Silver Poniard', 2000), ('Sineater Wing', 2100), ('Single Human Eye', 1000), ('Skull Fetish', 250), ('Skullcracker Armor', 18000), ('Slimy Leaf Tentacle', 320), ('Sliver', 0), ('Small Flask of Eyedrops', 95), ('Small Notebook', 480), ('Small Treasure Chest', 500), ('Small Tropical Fish', 380), ('Spark Sphere', 350), ('Sparkion Claw', 290), ('Sparkion Legs', 310), ('Sparkion Stings', 280), ('Sparkion Tail', 300), ('Spellbook of Mind Control', 13000), ("Spellsinger's Seal", 280), ("Spellweaver's Robe", 12000), ('Sphinx Tiara', 360), ('Spiked Bracers', 1360), ('Spiked Gorget', 850), ('Spiked Iron Ball', 100), ('Spiky Club', 300), ('Spitter Nose', 340), ('Staff Piece', 560), ('Stag Parchment', 3000), ('Stalking Seeds', 1800), ('Stampor Talons', 150), ('Star Ink', 1250), ('Stone Wing', 120), ("Stonerefiner's Skull", 100), ('Strange Helmet', 500), ('Strange Substance', 810), ('Streaked Devourer Eyes', 500), ('Streaked Devourer Legs', 600), ('Streaked Devourer Maw', 400), ('Striped Fur', 50), ('Sulphider Shell', 2200), ('Sulphur Powder', 1900), ('Sulphurous Stone', 100), ('Swampling Club', 40), ('Swarmer Antenna', 130), ('Tail of Corruption', 240), ('Taurus Mace', 500), ('Telescope Eye', 1600), ('Terra Boots', 2500), ('Terra Hood', 2500), ('Terra Mantle', 11000), ('Terramite Legs', 60), ('Thorn', 100), ('Titan Axe', 4000), ('Toe Nails', 4500), ('Tooth File', 60), ('Torn Page', 340), ('Trapped Bad Dream Monster', 900), ('Tremendous Tyrant Head', 930), ('Tremendous Tyrant Shell', 740), ('Tunnel Tyrant Head', 500), ('Tunnel Tyrant Shell', 700), ('Two-Headed Turtle Heads', 460), ('Undertaker Fangs', 2700), ('Unholy Bone', 480), ("Vampire's Cape Chain", 150), ('Varnished Diremaw Brainpan', 750), ('Varnished Diremaw Legs', 670), ('Vein of Ore', 330), ('Venison', 55), ('Vibrant Heart', 2100), ('Vibrant Robe', 1200), ('Vile Axe', 30000), ('Volatile Proto Matter', 300), ('War Axe', 12000), ('Wardragon Claw', 550), ('Wardragon Tooth', 730), ('Waspoid Claw', 320), ("Weaver's Wandtip", 250), ('Werebadger Claws', 160), ('Werebadger Skull', 185), ('Werebear Fur', 185), ('Werebear Skull', 195), ('Wereboar Loincloth', 1500), ('Wereboar Tusks', 165), ('Werecrocodile Tongue', 570), ('Werefox Tail', 200), ('Werehyaena Nose', 220), ('Werehyaena Talisman', 350), ('Werepanther Claw', 280), ('Weretiger Tooth', 490), ('Werewolf Fur', 380), ("Widow's Mandibles", 110), ('Wild Flowers', 120), ('Wimp Tooth Chain', 120), ('Winged Tail', 800), ('Witch Broom', 60), ('Wood Cape', 5000), ('Wooden Spellbook', 12000), ('Worm Sponge', 4200), ('Yapunac Dagger', 240), ('Zaoan Armor', 14000), ('Zaoan Robe', 12000), ('Zaoan Shoes', 5000), ('Zaogun Flag', 600), ('Zaogun Shoulderplates', 150)]



# =========================================================
# CACHE
# =========================================================

CREATURES = []
BOSSES = []
ITEMS = []

BOOSTED_BOSS_NAMES = []


# =========================================================
# GENERAL FUNCTIONS
# =========================================================

def clean_number(value):
    if value is None:
        return "?"

    try:
        number = int(
            str(value)
            .replace(",", "")
            .replace(".", "")
            .replace(" ", "")
            .strip()
        )

        return f"{number:,}".replace(",", ".")

    except (ValueError, TypeError):
        return str(value)


def parse_tibia_number(value):
    if value is None:
        return 0

    text = str(value).strip()

    negative = text.startswith("-")

    digits = re.sub(
        r"[^\d]",
        "",
        text
    )

    if not digits:
        return 0

    number = int(digits)

    if negative:
        number *= -1

    return number


def format_gp(value):
    try:
        value = int(value)

    except (ValueError, TypeError):
        return "?"

    return (
        f"{value:,}"
        .replace(",", ".")
        + " gp"
    )


def format_short_gp(value):
    try:
        value = int(value)

    except (ValueError, TypeError):
        return "?"

    negative = value < 0
    number = abs(value)

    if number >= 1_000_000:
        text = f"{number / 1_000_000:.2f}kk"

    elif number >= 1_000:
        text = f"{number / 1_000:.0f}k"

    else:
        text = str(number)

    if negative:
        return f"-{text}"

    return text


def get_first(
    data: dict,
    *keys,
    default="?"
):
    if not isinstance(data, dict):
        return default

    for key in keys:
        value = data.get(key)

        if value not in (
            None,
            "",
            "unknown"
        ):
            return value

    return default


def clean_wiki_text(text):
    if text is None:
        return ""

    text = str(text)

    text = text.replace("[[", "")
    text = text.replace("]]", "")
    text = text.replace("<br>", "\n")
    text = text.replace("<br/>", "\n")
    text = text.replace("<br />", "\n")

    return text.strip()


def truncate_text(
    text,
    max_length=900
):
    text = str(text)

    if len(text) <= max_length:
        return text

    return (
        text[:max_length - 3]
        + "..."
    )


def chunk_lines(
    lines,
    max_chars=950
):
    chunks = []
    current = ""

    for line in lines:

        candidate = (
            f"{current}\n{line}"
            if current
            else line
        )

        if len(candidate) > max_chars:

            if current:
                chunks.append(current)

            current = line

        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks


# =========================================================
# SESSION / TIME
# =========================================================

def parse_session_hours(session):
    """
    Converts:
    02:41h

    en:
    2.6833 hours
    """

    if not session:
        return 0

    match = re.search(
        r"(\d+):(\d{2})h",
        str(session),
        re.IGNORECASE
    )

    if not match:
        return 0

    hours = int(
        match.group(1)
    )

    minutes = int(
        match.group(2)
    )

    return (
        hours
        + minutes / 60
    )


# =========================================================
# BESTIARY
# =========================================================

def get_charm_points(
    bestiary_level
):
    if not bestiary_level:
        return "?"

    level = (
        str(bestiary_level)
        .strip()
        .lower()
    )

    table = {
        "harmless": 1,
        "trivial": 5,
        "easy": 15,
        "medium": 25,
        "hard": 50,
        "challenging": 100
    }

    return table.get(
        level,
        "?"
    )


# =========================================================
# ELEMENTS
# =========================================================

def normalize_percentage_value(
    value
):
    if value in (
        None,
        "",
        "?"
    ):
        return None

    match = re.search(
        r"-?\d+",
        str(value)
    )

    if not match:
        return None

    try:
        return int(
            match.group(0)
        )

    except ValueError:
        return None


def format_percentage(value):
    numeric = normalize_percentage_value(
        value
    )

    if numeric is None:
        return "?"

    return f"{numeric}%"


def element_indicator(value):
    numeric = normalize_percentage_value(
        value
    )

    if numeric is None:
        return ""

    if numeric > 100:
        return " 🟢"

    if numeric == 100:
        return " ⚪"

    if numeric >= 75:
        return " 🟡"

    if numeric > 0:
        return " 🔴"

    return " ⛔"


def format_element(
    name,
    emoji,
    value
):
    return (
        f"{emoji} **{name}:** "
        f"{format_percentage(value)}"
        f"{element_indicator(value)}"
    )


# =========================================================
# DAMAGE
# =========================================================

def format_max_damage(value):
    if value in (
        None,
        "",
        "?"
    ):
        return "?"

    text = str(value)

    damage_types = {
        "physical": ("⚔️", "Physical"),
        "fire": ("🔥", "Fire"),
        "earth": ("🌱", "Earth"),
        "energy": ("⚡", "Energy"),
        "ice": ("❄️", "Ice"),
        "death": ("☠️", "Death"),
        "holy": ("✨", "Holy"),
        "lifedrain": ("🩸", "Life Drain"),
        "life": ("🩸", "Life Drain"),
        "manadrain": ("🔵", "Mana Drain"),
        "mana": ("🔵", "Mana Drain")
    }

    matches = re.findall(
        r"([a-zA-Z]+)=([0-9]+)",
        text
    )

    if matches:
        parsed = []
        total_damage = 0

        for damage_type, amount in matches:

            damage_type = (
                damage_type.lower()
            )

            if damage_type not in damage_types:
                continue

            amount = int(amount)

            if amount <= 0:
                continue

            total_damage += amount

            emoji, label = damage_types[
                damage_type
            ]

            parsed.append(
                (
                    amount,
                    emoji,
                    label
                )
            )

        parsed.sort(
            key=lambda entry: entry[0],
            reverse=True
        )

        if parsed:
            lines = []
            medals = [
                "🥇",
                "🥈",
                "🥉"
            ]

            for index, (
                amount,
                emoji,
                label
            ) in enumerate(parsed):

                position = (
                    medals[index]
                    if index < len(medals)
                    else f"{index + 1}."
                )

                lines.append(
                    f"{position} {emoji} "
                    f"**{label}:** "
                    f"**{clean_number(amount)}**"
                )

            if len(parsed) > 1:
                lines.append(
                    f"💥 **Maximum theoretical total: "
                    f"{clean_number(total_damage)}**"
                )

            return "\n".join(lines)

    plus_match = re.fullmatch(
        r"\s*([0-9]+)\+\s*",
        text
    )

    if plus_match:

        amount = int(
            plus_match.group(1)
        )

        return (
            f"**{clean_number(amount)}+**"
        )

    return clean_number(value)


def build_sorted_element_modifiers(
    data
):
    elements = [
        (
            "Physical",
            "⚔️",
            get_first(
                data,
                "physicalDmgMod"
            )
        ),
        (
            "Fire",
            "🔥",
            get_first(
                data,
                "fireDmgMod"
            )
        ),
        (
            "Earth",
            "🌱",
            get_first(
                data,
                "earthDmgMod"
            )
        ),
        (
            "Energy",
            "⚡",
            get_first(
                data,
                "energyDmgMod"
            )
        ),
        (
            "Ice",
            "❄️",
            get_first(
                data,
                "iceDmgMod"
            )
        ),
        (
            "Death",
            "☠️",
            get_first(
                data,
                "deathDmgMod"
            )
        ),
        (
            "Holy",
            "✨",
            get_first(
                data,
                "holyDmgMod"
            )
        )
    ]

    parsed = []

    for (
        label,
        emoji,
        value
    ) in elements:

        numeric = normalize_percentage_value(
            value
        )

        if numeric is None:
            continue

        parsed.append(
            (
                numeric,
                label,
                emoji,
                value
            )
        )

    parsed.sort(
        key=lambda entry: entry[0],
        reverse=True
    )

    if not parsed:
        return "No data available."

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    lines = []

    for index, (
        numeric,
        label,
        emoji,
        value
    ) in enumerate(parsed):

        position = (
            medals[index]
            if index < len(medals)
            else f"{index + 1}."
        )

        lines.append(
            f"{position} {emoji} "
            f"**{label}:** "
            f"{format_percentage(value)}"
            f"{element_indicator(value)}"
        )

    return "\n".join(lines)


# =========================================================
# HUNT ANALYZER / MULTIPLE CREATURES
# =========================================================

HUNT_ELEMENTS = [
    ("Physical", "⚔️", "physicalDmgMod"),
    ("Fire", "🔥", "fireDmgMod"),
    ("Earth", "🌱", "earthDmgMod"),
    ("Energy", "⚡", "energyDmgMod"),
    ("Ice", "❄️", "iceDmgMod"),
    ("Death", "☠️", "deathDmgMod"),
    ("Holy", "✨", "holyDmgMod")
]

HUNT_DAMAGE_TYPES = {
    "physical": ("Physical", "⚔️"),
    "fire": ("Fire", "🔥"),
    "earth": ("Earth", "🌱"),
    "energy": ("Energy", "⚡"),
    "ice": ("Ice", "❄️"),
    "death": ("Death", "☠️"),
    "holy": ("Holy", "✨"),
    "lifedrain": ("Life Drain", "🩸"),
    "life": ("Life Drain", "🩸"),
    "manadrain": ("Mana Drain", "🔵"),
    "mana": ("Mana Drain", "🔵")
}


def extract_element_modifiers(data):
    result = {}

    for label, emoji, field in HUNT_ELEMENTS:
        value = get_first(
            data,
            field,
            default=None
        )

        numeric = normalize_percentage_value(
            value
        )

        if numeric is None:
            continue

        result[label] = {
            "value": numeric,
            "emoji": emoji
        }

    return result


def extract_max_damage_by_type(data):
    value = get_first(
        data,
        "maxdmg",
        "maxDamage",
        default=None
    )

    if value in (
        None,
        "",
        "?"
    ):
        return {}

    text = str(value)

    matches = re.findall(
        r"([a-zA-Z]+)=([0-9]+)",
        text
    )

    result = {}

    for raw_type, raw_amount in matches:
        damage_type = raw_type.lower()

        if damage_type not in HUNT_DAMAGE_TYPES:
            continue

        amount = int(raw_amount)

        if amount <= 0:
            continue

        label, emoji = HUNT_DAMAGE_TYPES[
            damage_type
        ]

        if label not in result:
            result[label] = {
                "amount": 0,
                "emoji": emoji
            }

        result[label]["amount"] += amount

    return result


def normalize_creature_search_name(value):
    """Normalize a name for comparison regardless of capitalization,
    accents, hyphens, apostrophes, or extra spaces.
    """
    if not value:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        str(value)
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()

    return text


def creature_name_variants(name):
    """Generate a few useful variants for Wiki pages that sometimes
    use the plural name even when TibiaData returns the singular form.
    """
    name = str(name).strip()

    if not name:
        return []

    variants = [name]
    lowered = name.lower()

    if lowered.endswith("y") and len(name) > 1:
        variants.append(name[:-1] + "ies")
    elif lowered.endswith(("s", "x", "z", "ch", "sh")):
        variants.append(name + "es")
    else:
        variants.append(name + "s")

    if lowered.endswith("ies") and len(name) > 3:
        variants.append(name[:-3] + "y")
    elif lowered.endswith("es") and len(name) > 2:
        variants.append(name[:-2])
    elif lowered.endswith("s") and len(name) > 1:
        variants.append(name[:-1])

    result = []
    seen = set()

    for variant in variants:
        key = normalize_creature_search_name(variant)
        if key and key not in seen:
            seen.add(key)
            result.append(variant)

    return result


def get_creature_name_candidates(user_name, max_candidates=5):
    """Find the most likely name in the real creature list.

    Priority:
    1. Exact match ignoring formatting.
    2. Match starting with the entered text.
    3. Match containing the entered text.
    4. Fuzzy matching for small spelling mistakes.
    """
    wanted = normalize_creature_search_name(user_name)

    if not wanted:
        return []

    canonical = []
    normalized_to_names = {}

    for creature in CREATURES:
        if not isinstance(creature, dict):
            continue

        name = creature.get("name")

        if not name:
            continue

        name = str(name).strip()
        normalized = normalize_creature_search_name(name)

        if not normalized:
            continue

        canonical.append((normalized, name))
        normalized_to_names.setdefault(
            normalized,
            []
        ).append(name)

    if wanted in normalized_to_names:
        return normalized_to_names[wanted][:max_candidates]

    starts = [
        name
        for normalized, name in canonical
        if normalized.startswith(wanted)
    ]

    if starts:
        return starts[:max_candidates]

    contains = [
        name
        for normalized, name in canonical
        if wanted in normalized
    ]

    if contains:
        return contains[:max_candidates]

    normalized_names = list(
        normalized_to_names.keys()
    )

    close = difflib.get_close_matches(
        wanted,
        normalized_names,
        n=max_candidates,
        cutoff=0.62
    )

    result = []

    for normalized in close:
        result.extend(
            normalized_to_names.get(
                normalized,
                []
            )
        )

    return result[:max_candidates]


async def resolve_hunt_creature(user_name):
    """Resolve user-entered text to a TibiaWiki creature.

    Returns:
        (data, interpreted_name)
    """
    candidates = get_creature_name_candidates(
        user_name,
        max_candidates=5
    )

    # If TibiaData finds nothing similar, still try the exact text
    # entered by the user.
    if not candidates:
        candidates = [str(user_name).strip()]

    lookup_names = []
    seen = set()

    for candidate in candidates:
        for variant in creature_name_variants(candidate):
            normalized = normalize_creature_search_name(
                variant
            )

            if not normalized or normalized in seen:
                continue

            seen.add(normalized)
            lookup_names.append(variant)

            # Avoid hammering the API if the name is badly misspelled.
            if len(lookup_names) >= 8:
                break

        if len(lookup_names) >= 8:
            break

    for lookup_name in lookup_names:
        result = await get_wiki_creature(
            lookup_name
        )

        if isinstance(result, dict):
            actual_name = get_first(
                result,
                "name",
                default=lookup_name
            )

            return result, str(actual_name)

    return None, None


def build_hunt_analysis(creatures_data):
    if not creatures_data:
        return None

    attack_totals = {}
    attack_counts = {}
    attack_emojis = {}

    defense_totals = {}
    defense_emojis = {}

    for creature_data in creatures_data:
        modifiers = extract_element_modifiers(
            creature_data
        )

        for element, info in modifiers.items():
            attack_totals[element] = (
                attack_totals.get(element, 0)
                + info["value"]
            )

            attack_counts[element] = (
                attack_counts.get(element, 0)
                + 1
            )

            attack_emojis[element] = info[
                "emoji"
            ]

        damage = extract_max_damage_by_type(
            creature_data
        )

        for damage_type, info in damage.items():
            defense_totals[damage_type] = (
                defense_totals.get(
                    damage_type,
                    0
                )
                + info["amount"]
            )

            defense_emojis[damage_type] = info[
                "emoji"
            ]

    attack_ranking = []

    for element, total in attack_totals.items():
        count = attack_counts.get(
            element,
            0
        )

        if count <= 0:
            continue

        average = total / count

        attack_ranking.append(
            {
                "element": element,
                "emoji": attack_emojis.get(
                    element,
                    ""
                ),
                "average": average,
                "count": count
            }
        )

    attack_ranking.sort(
        key=lambda entry: entry["average"],
        reverse=True
    )

    defense_total_all = sum(
        defense_totals.values()
    )

    defense_ranking = []

    for damage_type, amount in defense_totals.items():
        percentage = (
            amount / defense_total_all * 100
            if defense_total_all > 0
            else 0
        )

        defense_ranking.append(
            {
                "type": damage_type,
                "emoji": defense_emojis.get(
                    damage_type,
                    ""
                ),
                "amount": amount,
                "percentage": percentage
            }
        )

    defense_ranking.sort(
        key=lambda entry: entry["amount"],
        reverse=True
    )

    return {
        "attack": attack_ranking,
        "defense": defense_ranking
    }


def build_hunt_embed(
    requested_names,
    found_creatures,
    missing_names,
    interpreted_names=None
):
    analysis = build_hunt_analysis(
        found_creatures
    )

    if not analysis:
        return None

    embed = discord.Embed(
        title="🗺️ Hunt Analyzer",
        description=(
            f"Creatures analyzed: "
            f"**{len(found_creatures)}**\n"
            "Recommendations are calculated "
            "by combining the selected creatures."
        ),
        color=discord.Color.blue()
    )

    creature_lines = []

    for creature_data in found_creatures:
        creature_name = get_first(
            creature_data,
            "name",
            default="?"
        )

        creature_lines.append(
            f"• **{creature_name}**"
        )

    embed.add_field(
        name="👹 Creatures",
        value="\n".join(creature_lines),
        inline=False
    )

    if interpreted_names:
        interpreted_lines = []

        for original, interpreted in interpreted_names:
            if (
                normalize_creature_search_name(original)
                != normalize_creature_search_name(interpreted)
            ):
                interpreted_lines.append(
                    f"• `{original}` → **{interpreted}**"
                )

        if interpreted_lines:
            embed.add_field(
                name="🔎 Interpreted names",
                value=truncate_text(
                    "\n".join(interpreted_lines),
                    900
                ),
                inline=False
            )

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    attack_lines = []

    for index, entry in enumerate(
        analysis["attack"]
    ):
        position = (
            medals[index]
            if index < len(medals)
            else f"{index + 1}."
        )

        average = entry[
            "average"
        ]

        attack_lines.append(
            f"{position} {entry['emoji']} "
            f"**{entry['element']}** — "
            f"**{average:.1f}%** "
            "average effectiveness"
        )

    if attack_lines:
        embed.add_field(
            name="⚔️ Best damage to use",
            value="\n".join(
                attack_lines
            ),
            inline=False
        )

    defense_lines = []

    for index, entry in enumerate(
        analysis["defense"]
    ):
        position = (
            medals[index]
            if index < len(medals)
            else f"{index + 1}."
        )

        defense_lines.append(
            f"{position} {entry['emoji']} "
            f"**{entry['type']}** — "
            f"**{entry['percentage']:.1f}%** "
            f"of combined maximum damage "
            f"({clean_number(entry['amount'])})"
        )

    if defense_lines:
        embed.add_field(
            name="🛡️ Recommended protections",
            value="\n".join(
                defense_lines
            ),
            inline=False
        )

    attack_ranking = analysis[
        "attack"
    ]

    defense_ranking = analysis[
        "defense"
    ]

    recommendation_lines = []

    if attack_ranking:
        best_attack = attack_ranking[0]

        recommendation_lines.append(
            f"⚔️ **Recommended damage:** "
            f"{best_attack['emoji']} "
            f"**{best_attack['element']}** "
            f"({best_attack['average']:.1f}% medio)"
        )

    if defense_ranking:
        main_defenses = defense_ranking[:2]

        defense_text = " + ".join(
            f"{entry['emoji']} "
            f"**{entry['type']}**"
            for entry in main_defenses
        )

        recommendation_lines.append(
            f"🛡️ **Prioritize protection:** "
            f"{defense_text}"
        )

        if len(defense_ranking) >= 3:
            third = defense_ranking[2]

            recommendation_lines.append(
                f"📌 **Secondary protection:** "
                f"{third['emoji']} "
                f"**{third['type']}**"
            )

    if recommendation_lines:
        embed.add_field(
            name="✅ Quick recommendation",
            value="\n".join(
                recommendation_lines
            ),
            inline=False
        )

    if missing_names:
        missing_text = "\n".join(
            f"• {name}"
            for name in missing_names
        )

        embed.add_field(
            name="⚠️ Not found",
            value=truncate_text(
                missing_text,
                900
            ),
            inline=False
        )

    embed.add_field(
        name="ℹ️ How it is calculated",
        value=(
            "• **Attack:** average elemental effectiveness "
            "across all selected creatures.\n"
            "• **Defense:** sum of maximum damage "
            "by type recorded for the creatures "
            "and its share of the total.\n"
            "This is a guideline for choosing damage type "
            "and protections; it does not simulate the actual "
            "frequency of each attack."
        ),
        inline=False
    )

    embed.set_footer(
        text=(
            "Exura • Hunt Analyzer • TibiaWiki"
        )
    )

    return embed


class HuntCreaturesModal(
    discord.ui.Modal,
    title="Analizar Hunt"
):

    creatures = discord.ui.TextInput(
        label="Which creatures will you hunt?",
        placeholder=(
            "Enter one creature per line:\n"
            "Juggernaut\n"
            "Demon Outcast\n"
            "Dark Torturer"
        ),
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000
    )

    async def on_submit(
        self,
        interaction:
        discord.Interaction
    ):
        await interaction.response.defer()

        raw_text = str(
            self.creatures.value
        )

        raw_names = re.split(
            r"[\n,;]+",
            raw_text
        )

        requested_names = []
        seen = set()

        for raw_name in raw_names:
            name = raw_name.strip()

            if not name:
                continue

            normalized = name.lower()

            if normalized in seen:
                continue

            seen.add(normalized)
            requested_names.append(name)

        if not requested_names:
            await interaction.followup.send(
                "❌ You have not entered any creatures.",
                ephemeral=True
            )
            return

        if len(requested_names) > 15:
            await interaction.followup.send(
                "❌ You can analyze a maximum of "
                "**15 creatures** at a time.",
                ephemeral=True
            )
            return

        results = await asyncio.gather(
            *(
                resolve_hunt_creature(name)
                for name in requested_names
            )
        )

        found_creatures = []
        missing_names = []
        interpreted_names = []

        for requested_name, result in zip(
            requested_names,
            results
        ):
            creature_data, interpreted_name = result

            if isinstance(creature_data, dict):
                found_creatures.append(
                    creature_data
                )

                interpreted_names.append(
                    (
                        requested_name,
                        interpreted_name
                        or requested_name
                    )
                )
            else:
                missing_names.append(
                    requested_name
                )

        if not found_creatures:
            await interaction.followup.send(
                "❌ I could not find any "
                "of the specified creatures.",
                ephemeral=True
            )
            return

        embed = build_hunt_embed(
            requested_names,
            found_creatures,
            missing_names,
            interpreted_names
        )

        if not embed:
            await interaction.followup.send(
                "❌ I could not calculate the analysis "
                "for these creatures.",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            embed=embed
        )


# =========================================================
# LOOT
# =========================================================

def get_loot_name(item):
    if not isinstance(
        item,
        dict
    ):
        return None

    return (
        item.get("itemName")
        or item.get("name")
        or item.get("item")
    )


def get_loot_rarity(item):
    if not isinstance(
        item,
        dict
    ):
        return "unknown"

    value = (
        item.get("rarity")
        or item.get("dropRate")
        or item.get("dropchance")
        or "unknown"
    )

    return (
        str(value)
        .strip()
        .lower()
    )


def get_loot_sort_score(item):
    rarity = get_loot_rarity(item)

    rarity_order = {
        "extremely rare": 110,
        "very rare": 100,
        "rare": 90,
        "semi-rare": 80,
        "semi rare": 80,
        "uncommon": 70,
        "common": 60,
        "always": 50,
        "unknown": 0
    }

    return rarity_order.get(
        rarity,
        10
    )


def format_rarity(rarity):
    rarity = str(rarity).strip()

    if not rarity:
        return "Unknown"

    return rarity.title()


def get_highlight_loot(
    loot,
    amount=7
):
    if not isinstance(
        loot,
        list
    ):
        return "No data available."

    valid_items = []

    for item in loot:

        if not isinstance(
            item,
            dict
        ):
            continue

        name = get_loot_name(item)

        if not name:
            continue

        rarity = get_loot_rarity(item)

        valid_items.append(
            (
                get_loot_sort_score(item),
                name,
                rarity
            )
        )

    valid_items.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if not valid_items:
        return "No data available."

    lines = []

    for (
        _,
        name,
        rarity
    ) in valid_items[:amount]:

        lines.append(
            f"• **{name}** "
            f"— {format_rarity(rarity)}"
        )

    return "\n".join(lines)


def build_full_loot_fields(
    loot,
    max_chars=950
):
    if not isinstance(
        loot,
        list
    ):
        return []

    valid_items = []

    for index, item in enumerate(
        loot
    ):

        if not isinstance(
            item,
            dict
        ):
            continue

        name = get_loot_name(item)

        if not name:
            continue

        valid_items.append(
            {
                "name": str(name),
                "rarity": get_loot_rarity(item),
                "score": get_loot_sort_score(item),
                "index": index
            }
        )

    valid_items.sort(
        key=lambda item: (
            -item["score"],
            item["index"]
        )
    )

    lines = []

    for item in valid_items:

        lines.append(
            f"• **{item['name']}** "
            f"— "
            f"{format_rarity(item['rarity'])}"
        )

    return chunk_lines(
        lines,
        max_chars
    )


# =========================================================
# LOCALIZACIONES
# =========================================================

def get_locations_text(
    locations
):
    if not locations:
        return "No data available."

    if isinstance(
        locations,
        list
    ):
        result = []

        for location in locations[:8]:

            result.append(
                f"• "
                f"{clean_wiki_text(location)}"
            )

        return "\n".join(result)

    return truncate_text(
        clean_wiki_text(locations),
        850
    )


# =========================================================
# ITEMS
# =========================================================

def get_item_name(item):
    if isinstance(
        item,
        str
    ):
        return item

    if not isinstance(
        item,
        dict
    ):
        return None

    return (
        item.get("name")
        or item.get("itemName")
        or item.get("title")
    )


def get_item_id(
    item_data
):
    value = get_first(
        item_data,
        "itemid",
        "itemId",
        "item_id",
        default=None
    )

    if value is None:
        return None

    if isinstance(
        value,
        list
    ):

        if not value:
            return None

        value = value[0]

    try:
        return int(
            str(value).strip()
        )

    except (
        ValueError,
        TypeError
    ):
        return None


def format_vocation(value):
    if not value:
        return "?"

    text = str(value).strip()

    mapping = {
        "knights": "Knight",
        "knight": "Knight",
        "paladins": "Paladin",
        "paladin": "Paladin",
        "druids": "Druid",
        "druid": "Druid",
        "sorcerers": "Sorcerer",
        "sorcerer": "Sorcerer",
        "monks": "Monk",
        "monk": "Monk"
    }

    return mapping.get(
        text.lower(),
        text.title()
    )


def format_slot(value):
    if not value:
        return None

    mapping = {
        "body": "Armor",
        "head": "Helmet",
        "legs": "Legs",
        "feet": "Boots",
        "left-hand": "Left Hand",
        "right-hand": "Right Hand",
        "two-handed": "Two-Handed",
        "both hands": "Both Hands",
        "shield hand": "Shield Hand",
        "necklace": "Amulet",
        "ring": "Ring",
        "backpack": "Backpack"
    }

    text = str(value).strip()

    return mapping.get(
        text.lower(),
        text
    )


def format_item_resistances(value):
    if not value:
        return None

    text = clean_wiki_text(value)

    emoji_map = {
        "physical": "⚔️",
        "fire": "🔥",
        "earth": "🌱",
        "energy": "⚡",
        "ice": "❄️",
        "death": "☠️",
        "holy": "✨"
    }

    lines = []

    for part in text.split(","):

        part = part.strip()

        if not part:
            continue

        emoji = "🛡️"

        for (
            element,
            icon
        ) in emoji_map.items():

            if element in part.lower():
                emoji = icon
                break

        lines.append(
            f"{emoji} "
            f"**{part.title()}**"
        )

    return "\n".join(lines)


def format_item_attributes(value):
    if not value:
        return None

    text = clean_wiki_text(value)

    lines = []

    for part in text.split(","):

        part = part.strip()

        if not part:
            continue

        lowered = part.lower()

        if "sword fighting" in lowered:
            emoji = "⚔️"

        elif "axe fighting" in lowered:
            emoji = "🪓"

        elif "club fighting" in lowered:
            emoji = "🔨"

        elif "distance fighting" in lowered:
            emoji = "🏹"

        elif "magic level" in lowered:
            emoji = "🪄"

        elif "shielding" in lowered:
            emoji = "🛡️"

        elif "damage reflection" in lowered:
            emoji = "💥"

        elif "capacity" in lowered:
            emoji = "🎒"

        elif "speed" in lowered:
            emoji = "🏃"

        elif "mana" in lowered:
            emoji = "🔵"

        elif "hit points" in lowered:
            emoji = "❤️"

        else:
            emoji = "✨"

        lines.append(
            f"{emoji} "
            f"**{part.title()}**"
        )

    return "\n".join(lines)


# =========================================================
# MARKET
# =========================================================

async def build_market_text(
    item_id,
    world="Celesta"
):
    current = await get_market_price(
        item_id=item_id,
        world=world
    )

    if not current:

        return (
            f"No recent data "
            f"for **{world}**."
        )

    if current.get("rate_limited"):

        return (
            "⏳ Market API "
            "is temporarily rate-limited."
        )

    lines = [
        f"🌍 **World:** {world}",
        "",
        f"📈 **Current sell:** "
        f"{format_gold(current.get('sell_offer'))}",
        f"📉 **Current buy:** "
        f"{format_gold(current.get('buy_offer'))}"
    ]

    avg_sell = current.get(
        "avg_sell_price"
    )

    avg_buy = current.get(
        "avg_buy_price"
    )

    if avg_sell:

        lines.append(
            f"📊 **Average sell:** "
            f"{format_gold(avg_sell)}"
        )

    if avg_buy:

        lines.append(
            f"📊 **Average buy:** "
            f"{format_gold(avg_buy)}"
        )

    timestamp = current.get(
        "time"
    )

    if timestamp:

        lines.append(
            f"🕒 **Updated:** "
            f"{format_market_timestamp(timestamp)}"
        )

    return "\n".join(lines)



# =========================================================
# GUILD TRACKING — LEVEL UPS AND DEATHS
# =========================================================

def connect_tracking_db():
    return sqlite3.connect(TRACKING_DB_FILE)


def crear_tracking_db():
    conn = connect_tracking_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_tracking_config (
            discord_guild_id INTEGER PRIMARY KEY,
            tibia_guild_name TEXT NOT NULL,
            tibia_world TEXT,
            channel_id INTEGER NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_tracking_characters (
            discord_guild_id INTEGER NOT NULL,
            character_name TEXT NOT NULL,
            level INTEGER,
            last_death_key TEXT,
            updated_at REAL NOT NULL,
            PRIMARY KEY (discord_guild_id, character_name)
        )
    """)

    conn.commit()
    conn.close()


def get_tracking_configs():
    conn = connect_tracking_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT discord_guild_id, tibia_guild_name, tibia_world, channel_id
        FROM guild_tracking_config
        WHERE enabled = 1
        ORDER BY discord_guild_id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_tracking_config(discord_guild_id):
    conn = connect_tracking_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT discord_guild_id, tibia_guild_name, tibia_world, channel_id, enabled
        FROM guild_tracking_config
        WHERE discord_guild_id = ?
    """, (int(discord_guild_id),))
    row = cursor.fetchone()
    conn.close()
    return row


def save_tracking_config(discord_guild_id, tibia_guild_name, tibia_world, channel_id):
    now = time.time()
    conn = connect_tracking_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guild_tracking_config (
            discord_guild_id, tibia_guild_name, tibia_world, channel_id,
            enabled, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(discord_guild_id) DO UPDATE SET
            tibia_guild_name = excluded.tibia_guild_name,
            tibia_world = excluded.tibia_world,
            channel_id = excluded.channel_id,
            enabled = 1,
            updated_at = excluded.updated_at
    """, (
        int(discord_guild_id),
        str(tibia_guild_name),
        str(tibia_world or ""),
        int(channel_id),
        now,
        now
    ))
    conn.commit()
    conn.close()


def delete_tracking_config(discord_guild_id):
    conn = connect_tracking_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM guild_tracking_config WHERE discord_guild_id = ?",
        (int(discord_guild_id),)
    )
    cursor.execute(
        "DELETE FROM guild_tracking_characters WHERE discord_guild_id = ?",
        (int(discord_guild_id),)
    )
    conn.commit()
    conn.close()


def get_tracking_character(discord_guild_id, character_name):
    conn = connect_tracking_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT level, last_death_key
        FROM guild_tracking_characters
        WHERE discord_guild_id = ? AND character_name = ? COLLATE NOCASE
    """, (int(discord_guild_id), str(character_name)))
    row = cursor.fetchone()
    conn.close()
    return row


def save_tracking_character(
    discord_guild_id,
    character_name,
    level=None,
    last_death_key=None,
    preserve_death_key=False
):
    existing = get_tracking_character(
        discord_guild_id,
        character_name
    )

    if existing:
        old_level, old_death_key = existing
        if level is None:
            level = old_level
        if preserve_death_key:
            last_death_key = old_death_key

    conn = connect_tracking_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guild_tracking_characters (
            discord_guild_id, character_name, level, last_death_key, updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(discord_guild_id, character_name) DO UPDATE SET
            level = excluded.level,
            last_death_key = excluded.last_death_key,
            updated_at = excluded.updated_at
    """, (
        int(discord_guild_id),
        str(character_name),
        int(level) if level is not None else None,
        last_death_key,
        time.time()
    ))
    conn.commit()
    conn.close()


def limpiar_tracking_members(discord_guild_id, active_names):
    active = {str(name).casefold() for name in active_names}
    conn = connect_tracking_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT character_name
        FROM guild_tracking_characters
        WHERE discord_guild_id = ?
    """, (int(discord_guild_id),))

    for (name,) in cursor.fetchall():
        if str(name).casefold() not in active:
            cursor.execute("""
                DELETE FROM guild_tracking_characters
                WHERE discord_guild_id = ? AND character_name = ?
            """, (int(discord_guild_id), str(name)))

    conn.commit()
    conn.close()


def extract_character_data_and_deaths(data):
    if not isinstance(data, dict):
        return None, []

    root = data.get("character")
    if not isinstance(root, dict):
        return None, []

    character = root.get("character")
    if not isinstance(character, dict):
        character = None

    deaths = root.get("deaths", [])
    if not isinstance(deaths, list):
        deaths = []

    return character, deaths


def death_killer_names(death):
    if not isinstance(death, dict):
        return []

    killers = death.get("killers", [])
    if not isinstance(killers, list):
        killers = []

    names = []
    for killer in killers:
        if isinstance(killer, dict):
            name = killer.get("name")
            if name:
                names.append(str(name))
        elif killer:
            names.append(str(killer))

    return names


def make_death_key(death):
    if not isinstance(death, dict):
        return None

    payload = {
        "time": death.get("time"),
        "level": death.get("level"),
        "killers": death_killer_names(death),
        "reason": death.get("reason")
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def death_description(death):
    if not isinstance(death, dict):
        return "Unknown cause."

    level = death.get("level", "?")
    killers = death_killer_names(death)
    killer_text = ", ".join(killers) if killers else "unknown cause"
    death_time = death.get("time")

    lines = [
        f"Died at level **{level}** to **{killer_text}**."
    ]

    if death_time:
        lines.append(f"🕒 {death_time}")

    return "\n".join(lines)


def build_level_embed(character_name, old_level, new_level, tibia_guild_name, world):
    gained = max(1, int(new_level) - int(old_level))
    embed = discord.Embed(
        title=f"🆙 {character_name} leveled up",
        description=(
            f"**{old_level} → {new_level}**"
            + (f"  (+{gained})" if gained > 1 else "")
        ),
        color=discord.Color.green()
    )
    embed.add_field(name="🏰 Guild", value=str(tibia_guild_name), inline=True)
    embed.add_field(name="🌍 World", value=str(world or "?"), inline=True)
    embed.set_footer(text="Exura • Guild Tracker • TibiaData")
    return embed


def build_death_embed(character_name, death, tibia_guild_name, world):
    embed = discord.Embed(
        title=f"☠️ {character_name} died",
        description=death_description(death),
        color=discord.Color.red()
    )
    embed.add_field(name="🏰 Guild", value=str(tibia_guild_name), inline=True)
    embed.add_field(name="🌍 World", value=str(world or "?"), inline=True)
    embed.set_footer(text="Exura • Guild Tracker • TibiaData")
    return embed


async def tracking_send(channel_id, embed):
    channel = bot.get_channel(int(channel_id))
    if channel is None:
        try:
            channel = await bot.fetch_channel(int(channel_id))
        except Exception:
            return False

    try:
        await channel.send(embed=embed)
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False


async def tracking_scan_character(
    discord_guild_id,
    channel_id,
    tibia_guild_name,
    world,
    member,
    semaphore
):
    name = get_first(member, "name", default=None)
    if not name:
        return

    try:
        current_level = int(get_first(member, "level", default=0))
    except (TypeError, ValueError):
        current_level = 0

    state = get_tracking_character(discord_guild_id, name)

    # First time: create a baseline and never announce old history.
    if state is None:
        save_tracking_character(
            discord_guild_id,
            name,
            level=current_level or None,
            last_death_key=None
        )
        previous_level = None
        previous_death_key = None
    else:
        previous_level, previous_death_key = state

    if (
        previous_level is not None
        and current_level > int(previous_level)
    ):
        await tracking_send(
            channel_id,
            build_level_embed(
                name,
                int(previous_level),
                current_level,
                tibia_guild_name,
                world
            )
        )

    # Store the level now so level losses can also be detected without announcing them.
    save_tracking_character(
        discord_guild_id,
        name,
        level=current_level or previous_level,
        last_death_key=previous_death_key
    )

    async with semaphore:
        data = await get_character(name)

    _character, deaths = extract_character_data_and_deaths(data)
    if not deaths:
        return

    newest_key = make_death_key(deaths[0])
    if not newest_key:
        return

    # First death lookup: establish the baseline without spamming old deaths.
    if not previous_death_key:
        save_tracking_character(
            discord_guild_id,
            name,
            level=current_level or previous_level,
            last_death_key=newest_key
        )
        return

    new_deaths = []
    found_previous = False

    for death in deaths:
        key = make_death_key(death)
        if key == previous_death_key:
            found_previous = True
            break
        new_deaths.append(death)

    # If the previous death has fallen out of the list (e.g. due to truncation), avoid
    # posting a whole block of history; announce at most the most recent one.
    if not found_previous and new_deaths:
        new_deaths = new_deaths[:1]

    for death in reversed(new_deaths):
        await tracking_send(
            channel_id,
            build_death_embed(
                name,
                death,
                tibia_guild_name,
                world
            )
        )

    save_tracking_character(
        discord_guild_id,
        name,
        level=current_level or previous_level,
        last_death_key=newest_key
    )


async def tracking_scan_config(config):
    discord_guild_id, tibia_guild_name, stored_world, channel_id = config

    data = await get_guild(tibia_guild_name)
    if not data:
        return

    guild_info, members = extract_guild_data(data)
    if not guild_info or not members:
        return

    canonical_name = get_first(guild_info, "name", default=tibia_guild_name)
    world = get_first(guild_info, "world", default=stored_world or "?")

    # If Tibia returns the canonical spelling or world, keep the configuration updated.
    save_tracking_config(
        discord_guild_id,
        canonical_name,
        world,
        channel_id
    )

    active_names = [
        get_first(member, "name", default="")
        for member in members
        if get_first(member, "name", default=None)
    ]
    limpiar_tracking_members(discord_guild_id, active_names)

    semaphore = asyncio.Semaphore(max(1, TRACKING_MAX_CONCURRENCY))
    await asyncio.gather(*(
        tracking_scan_character(
            discord_guild_id,
            channel_id,
            canonical_name,
            world,
            member,
            semaphore
        )
        for member in members
    ))


async def guild_tracking_loop():
    await bot.wait_until_ready()

    # Small startup delay to avoid competing with the bot's initial loading.
    await asyncio.sleep(10)

    while not bot.is_closed():
        started = time.time()

        for config in get_tracking_configs():
            try:
                await tracking_scan_config(config)
            except Exception as exc:
                print(f"[Guild Tracker] Error: {exc}")

        elapsed = time.time() - started
        wait_for = max(30, TRACKING_POLL_SECONDS - elapsed)
        await asyncio.sleep(wait_for)


# =========================================================
# WEEKLY DELIVERY TASKS
# =========================================================

def connect_delivery_db():
    return sqlite3.connect(DELIVERY_DB_FILE)


def crear_delivery_db():
    conn = connect_delivery_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_items (
            name TEXT PRIMARY KEY,
            npc_price INTEGER NOT NULL,
            item_id INTEGER,
            market_price INTEGER,
            market_updated_at REAL
        )
    """)
    cursor.executemany("""
        INSERT INTO delivery_items (name, npc_price)
        VALUES (?, ?)
        ON CONFLICT(name)
        DO UPDATE SET npc_price = excluded.npc_price
    """, DELIVERY_ITEMS)
    conn.commit()
    conn.close()


def normalize_delivery_name(name_value):
    return " ".join(
        str(name_value or "")
        .replace("’", "'")
        .replace("`", "'")
        .strip()
        .casefold()
        .split()
    )


def formatear_delivery_gp(valor):
    if valor is None:
        return "—"
    try:
        valor = int(valor)
    except (TypeError, ValueError):
        return "—"
    if valor < 0:
        return "—"
    return f"{valor:,}".replace(",", ".") + " gp"


def get_delivery_items():
    conn = connect_delivery_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, npc_price, market_price, market_updated_at
        FROM delivery_items
        ORDER BY name COLLATE NOCASE ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def delivery_cache_timestamp():
    conn = connect_delivery_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(market_updated_at)
        FROM delivery_items
        WHERE market_updated_at IS NOT NULL
    """)
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row and row[0] else None


def delivery_cache_desactualizada():
    timestamp = delivery_cache_timestamp()
    if timestamp is None:
        return True
    return (time.time() - timestamp) >= (DELIVERY_CACHE_HOURS * 3600)


def ids_delivery_faltantes():
    conn = connect_delivery_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM delivery_items WHERE item_id IS NULL")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def save_delivery_ids(mapa_ids):
    conn = connect_delivery_db()
    cursor = conn.cursor()
    for name_value, item_id in mapa_ids.items():
        cursor.execute(
            "UPDATE delivery_items SET item_id = ? WHERE name = ?",
            (item_id, name_value)
        )
    conn.commit()
    conn.close()


def save_delivery_prices(prices, timestamp):
    conn = connect_delivery_db()
    cursor = conn.cursor()
    for item_id, price in prices.items():
        cursor.execute("""
            UPDATE delivery_items
            SET market_price = ?, market_updated_at = ?
            WHERE item_id = ?
        """, (price, timestamp, item_id))
    conn.commit()
    conn.close()


def http_json_delivery(url, intentos=3):
    headers = {
        "User-Agent": "Exura-Discord-Bot/1.0 (Weekly Delivery price list)",
        "Accept": "application/json"
    }
    last_error = None
    for intento in range(intentos):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code == 429:
                time.sleep(6 * (intento + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            time.sleep(2 * (intento + 1))
    raise RuntimeError(f"Could not query Tibia Market API: {last_error}")


def descargar_metadata_delivery():
    metadata = http_json_delivery(f"{TIBIA_MARKET_API}/item_metadata")
    if isinstance(metadata, dict):
        for key in ("items", "data", "results"):
            if isinstance(metadata.get(key), list):
                metadata = metadata[key]
                break
    if not isinstance(metadata, list):
        raise RuntimeError("Unexpected format in /item_metadata")

    conn = connect_delivery_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM delivery_items")
    names = {normalize_delivery_name(n): n for (n,) in cursor.fetchall()}
    conn.close()

    encontrados = {}
    for entry in metadata:
        if not isinstance(entry, dict):
            continue
        name_value = entry.get("name") or entry.get("item_name") or entry.get("itemName")
        item_id = entry.get("id") or entry.get("item_id") or entry.get("itemId")
        if not name_value or item_id is None:
            continue
        norm = normalize_delivery_name(name_value)
        if norm in names:
            try:
                encontrados[names[norm]] = int(item_id)
            except (TypeError, ValueError):
                pass

    save_delivery_ids(encontrados)
    return len(encontrados)


def descargar_market_delivery():
    params = urllib.parse.urlencode({
        "server": DELIVERY_WORLD,
        "limit": 10000
    })
    data = http_json_delivery(f"{TIBIA_MARKET_API}/market_values?{params}")
    if isinstance(data, dict):
        for key in ("items", "data", "results", "market_values"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        raise RuntimeError("Unexpected format in /market_values")

    conn = connect_delivery_db()
    cursor = conn.cursor()
    cursor.execute("SELECT item_id FROM delivery_items WHERE item_id IS NOT NULL")
    wanted_ids = {int(row[0]) for row in cursor.fetchall()}
    conn.close()

    prices = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        item_id = entry.get("item_id") or entry.get("itemId") or entry.get("id")
        sell = entry.get("sell_offer")
        if sell is None:
            sell = entry.get("sellOffer")
        if sell is None:
            sell = entry.get("sell")
        try:
            item_id = int(item_id)
        except (TypeError, ValueError):
            continue
        if item_id not in wanted_ids:
            continue
        try:
            sell = int(sell) if sell is not None else None
        except (TypeError, ValueError):
            sell = None
        if sell is not None and sell >= 0:
            prices[item_id] = sell

    timestamp = time.time()
    save_delivery_prices(prices, timestamp)
    return len(prices)


_delivery_update_lock = asyncio.Lock()


async def actualizar_delivery_market(forzar=False):
    async with _delivery_update_lock:
        if not forzar and not delivery_cache_desactualizada():
            return True, "fresh cache"
        try:
            if ids_delivery_faltantes() > 0:
                encontrados = await asyncio.to_thread(descargar_metadata_delivery)
                print(f"Delivery: {encontrados}/{len(DELIVERY_ITEMS)} IDs identificados.")
                await asyncio.sleep(5.5)
            updated_count = await asyncio.to_thread(descargar_market_delivery)
            print(
                f"Delivery: {updated_count}/{len(DELIVERY_ITEMS)} prices "
                f"updated for {DELIVERY_WORLD}."
            )
            return True, f"{updated_count} prices updated_count"
        except Exception as error:
            print(f"ERROR updating Delivery Market: {error}")
            return False, str(error)


def texto_antiguedad_delivery():
    timestamp = delivery_cache_timestamp()
    if timestamp is None:
        return "no data"
    seconds = max(0, int(time.time() - timestamp))
    if seconds < 3600:
        return f"{max(1, seconds // 60)} min ago"
    hours = seconds // 3600
    if hours < 48:
        return f"{hours} h ago"
    return f"{hours // 24} d ago"


class DeliveryLetterSelect(discord.ui.Select):
    def __init__(self, available_letters):
        opciones = [
            discord.SelectOption(label=f"Letter {letter}", value=letter, emoji="🔤")
            for letter in available_letters
        ]
        super().__init__(
            placeholder="🔎 Jump directly to a letter...",
            min_values=1,
            max_values=1,
            options=opciones,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not isinstance(view, DeliveryView):
            return
        view.letter_filter = self.values[0]
        view.page = 0
        view.actualizar_botones()
        view.actualizar_selector()
        await interaction.response.edit_message(
            content=view.build_content(),
            embed=None,
            view=view
        )


class DeliveryView(discord.ui.View):
    def __init__(self, items, page=0, author_id=None):
        super().__init__(timeout=300)
        self.todos_items = items
        self.page = page
        self.author_id = author_id
        self.por_pagina = 20
        self.letter_filter = None
        self.available_letters = sorted({
            str(item[0])[0].upper()
            for item in self.todos_items
            if item and item[0]
        })
        self.selector_letras = DeliveryLetterSelect(self.available_letters)
        self.add_item(self.selector_letras)
        self.actualizar_botones()
        self.actualizar_selector()

    @property
    def items(self):
        if self.letter_filter is None:
            return self.todos_items
        return [
            item for item in self.todos_items
            if str(item[0]).upper().startswith(self.letter_filter)
        ]

    @property
    def total_pages(self):
        return max(1, (len(self.items) + self.por_pagina - 1) // self.por_pagina)

    def actualizar_selector(self):
        self.selector_letras.placeholder = (
            f"🔎 Current letter: {self.letter_filter}"
            if self.letter_filter
            else "🔎 Jump directly to a letter..."
        )
        for opcion in self.selector_letras.options:
            opcion.default = opcion.value == self.letter_filter

    def actualizar_botones(self):
        self.previous.disabled = self.page <= 0
        self.next_page.disabled = self.page >= self.total_pages - 1
        self.show_all.disabled = self.letter_filter is None

    def build_content(self):
        inicio = self.page * self.por_pagina
        page_items = self.items[inicio:inicio + self.por_pagina]

        encabezado = (
            "📦 **WEEKLY DELIVERY ITEMS**\n"
            f"🌍 **{DELIVERY_WORLD}**  •  "
            f"🕒 Market **{texto_antiguedad_delivery()}**  •  "
            f"📚 **{len(self.todos_items)} items**"
        )
        if self.letter_filter:
            encabezado += (
                f"  •  🔤 **Letter {self.letter_filter}** "
                f"({len(self.items)} items)"
            )

        lineas = [
            f"{'ITEM':<30} {'NPC':>12} {'MARKET':>12}",
            f"{'─' * 30} {'─' * 12} {'─' * 12}"
        ]
        for name_value, npc_price, market_price, _market_updated_at in page_items:
            short_name = name_value if len(name_value) <= 30 else name_value[:27] + "..."
            lineas.append(
                f"{short_name:<30} "
                f"{formatear_delivery_gp(npc_price):>12} "
                f"{formatear_delivery_gp(market_price):>12}"
            )

        tabla = "\n".join(lineas)
        pie = (
            f"**Page {self.page + 1}/{self.total_pages}**"
            "  •  Market = lowest sell offer"
        )
        return f"{encabezado}\n\n```text\n{tabla}\n```\n{pie}"

    async def interaction_check(self, interaction):
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Usa tu propio `/exura delivery`.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary, row=1)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self.actualizar_botones()
        await interaction.response.edit_message(
            content=self.build_content(), embed=None, view=self
        )

    @discord.ui.button(label="Show all", emoji="📚", style=discord.ButtonStyle.primary, row=1)
    async def show_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.letter_filter = None
        self.page = 0
        self.actualizar_botones()
        self.actualizar_selector()
        await interaction.response.edit_message(
            content=self.build_content(), embed=None, view=self
        )

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, row=1)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self.actualizar_botones()
        await interaction.response.edit_message(
            content=self.build_content(), embed=None, view=self
        )


# =========================================================
# AUTOCOMPLETE
# =========================================================

def make_choices(
    names,
    current
):
    current = (
        current
        .lower()
        .strip()
    )

    starts = []
    contains = []
    seen = set()

    for name in names:

        if not name:
            continue

        name = str(name)

        normalized = (
            name
            .lower()
            .strip()
        )

        if normalized in seen:
            continue

        seen.add(normalized)

        choice = app_commands.Choice(
            name=name,
            value=name
        )

        if (
            not current
            or normalized.startswith(
                current
            )
        ):
            starts.append(choice)

        elif current in normalized:
            contains.append(choice)

    return (
        starts
        + contains
    )[:25]


# =========================================================
# GUILD ONLINE
# =========================================================

def extract_guild_data(
    data
):
    if not isinstance(
        data,
        dict
    ):
        return None, []

    guild_root = data.get(
        "guild"
    )

    if not isinstance(
        guild_root,
        dict
    ):
        return None, []

    guild_info = guild_root.get(
        "guild"
    )

    if not isinstance(
        guild_info,
        dict
    ):
        guild_info = guild_root

    members = guild_root.get(
        "members"
    )

    if not isinstance(
        members,
        list
    ):
        members = guild_info.get(
            "members",
            []
        )

    if not isinstance(
        members,
        list
    ):
        members = []

    return guild_info, members


def guild_member_is_online(
    member
):
    if not isinstance(
        member,
        dict
    ):
        return False

    online_value = member.get(
        "online"
    )

    if isinstance(
        online_value,
        bool
    ):
        return online_value

    status = member.get(
        "status"
    )

    if status is not None:

        return (
            str(status)
            .strip()
            .lower()
            == "online"
        )

    return False


def get_vocation_short(
    vocation
):
    if not vocation:
        return "?"

    text = (
        str(vocation)
        .strip()
        .lower()
    )

    mapping = {
        "elite knight": "EK",
        "knight": "K",
        "royal paladin": "RP",
        "paladin": "P",
        "elder druid": "ED",
        "druid": "D",
        "master sorcerer": "MS",
        "sorcerer": "S",
        "exalted monk": "EM",
        "monk": "M"
    }

    return mapping.get(
        text,
        str(vocation)
    )


def build_online_chunks(
    members,
    max_chars=950
):
    lines = []

    for member in members:

        name = get_first(
            member,
            "name",
            default="?"
        )

        level = get_first(
            member,
            "level",
            default="?"
        )

        vocation = get_vocation_short(
            get_first(
                member,
                "vocation",
                default="?"
            )
        )

        rank = get_first(
            member,
            "rank",
            default=None
        )

        line = (
            f"🟢 **{name}** "
            f"— Lv. **{level}** "
            f"• **{vocation}**"
        )

        if rank:
            line += f" • {rank}"

        lines.append(line)

    return chunk_lines(
        lines,
        max_chars
    )


# =========================================================
# HUNT ANALYZER
# =========================================================

def parse_hunt_analyzer(
    text
):
    if not text:
        return None

    text = (
        str(text)
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )

    session_match = re.search(
        r"\bSession:\s*([0-9]{1,3}:[0-9]{2}h)",
        text,
        re.IGNORECASE
    )

    session = (
        session_match.group(1)
        if session_match
        else "?"
    )

    total_loot_match = re.search(
        r"(?:^|\n)\s*Loot:\s*(-?[\d.,]+)",
        text,
        re.IGNORECASE
    )

    total_supplies_match = re.search(
        r"(?:^|\n)\s*Supplies:\s*(-?[\d.,]+)",
        text,
        re.IGNORECASE
    )

    total_balance_match = re.search(
        r"(?:^|\n)\s*Balance:\s*(-?[\d.,]+)",
        text,
        re.IGNORECASE
    )

    if not (
        total_loot_match
        and total_supplies_match
        and total_balance_match
    ):
        return None

    total_loot = parse_tibia_number(
        total_loot_match.group(1)
    )

    total_supplies = parse_tibia_number(
        total_supplies_match.group(1)
    )

    total_balance = parse_tibia_number(
        total_balance_match.group(1)
    )

    player_pattern = re.compile(
        r"""
        ^\s*
        (?P<name>[^\n]+?)
        \s*\n
        \s*Loot:\s*
        (?P<loot>-?[\d.,]+)
        \s*\n
        \s*Supplies:\s*
        (?P<supplies>-?[\d.,]+)
        \s*\n
        \s*Balance:\s*
        (?P<balance>-?[\d.,]+)
        \s*\n
        \s*Damage:\s*
        (?P<damage>-?[\d.,]+)
        \s*\n
        \s*Healing:\s*
        (?P<healing>-?[\d.,]+)
        """,
        re.IGNORECASE
        | re.MULTILINE
        | re.VERBOSE
    )

    players = []

    for match in player_pattern.finditer(
        text
    ):

        raw_name = (
            match.group("name")
            .strip()
        )

        is_leader = bool(
            re.search(
                r"\(Leader\)\s*$",
                raw_name,
                re.IGNORECASE
            )
        )

        name = re.sub(
            r"\s*\(Leader\)\s*$",
            "",
            raw_name,
            flags=re.IGNORECASE
        ).strip()

        players.append(
            {
                "name": name,
                "leader": is_leader,
                "loot": parse_tibia_number(
                    match.group("loot")
                ),
                "supplies": parse_tibia_number(
                    match.group("supplies")
                ),
                "balance": parse_tibia_number(
                    match.group("balance")
                ),
                "damage": parse_tibia_number(
                    match.group("damage")
                ),
                "healing": parse_tibia_number(
                    match.group("healing")
                )
            }
        )

    if not players:
        return None

    return {
        "session": session,
        "loot": total_loot,
        "supplies": total_supplies,
        "balance": total_balance,
        "players": players
    }


# =========================================================
# SPLIT CALCULATION
# =========================================================

def calculate_split(
    hunt
):
    players = hunt["players"]

    total_balance = hunt[
        "balance"
    ]

    player_count = len(players)

    if player_count <= 0:
        return None

    base_share = (
        total_balance
        // player_count
    )

    remainder = (
        total_balance
        - (
            base_share
            * player_count
        )
    )

    for index, player in enumerate(
        players
    ):

        target = base_share

        if remainder > 0:

            if index < remainder:
                target += 1

        elif remainder < 0:

            if index < abs(remainder):
                target -= 1

        player[
            "target_balance"
        ] = target

        player[
            "adjustment"
        ] = (
            target
            - player["balance"]
        )

    payers = []
    receivers = []

    for player in players:

        adjustment = player[
            "adjustment"
        ]

        if adjustment < 0:

            payers.append(
                {
                    "name": player["name"],
                    "amount": abs(
                        adjustment
                    )
                }
            )

        elif adjustment > 0:

            receivers.append(
                {
                    "name": player["name"],
                    "amount": adjustment
                }
            )

    transactions = []

    payer_index = 0
    receiver_index = 0

    while (
        payer_index < len(payers)
        and receiver_index < len(receivers)
    ):

        payer = payers[
            payer_index
        ]

        receiver = receivers[
            receiver_index
        ]

        amount = min(
            payer["amount"],
            receiver["amount"]
        )

        if amount > 0:

            transactions.append(
                {
                    "from": payer["name"],
                    "to": receiver["name"],
                    "amount": amount
                }
            )

        payer["amount"] -= amount
        receiver["amount"] -= amount

        if payer["amount"] == 0:
            payer_index += 1

        if receiver["amount"] == 0:
            receiver_index += 1

    return {
        "share": (
            total_balance
            / player_count
        ),
        "base_share": base_share,
        "remainder": remainder,
        "transactions": transactions
    }


# =========================================================
# SPLIT EMBED
# =========================================================

def build_split_embed(
    hunt,
    split_data
):
    players = hunt[
        "players"
    ]

    total_damage = sum(
        player["damage"]
        for player in players
    )

    total_healing = sum(
        player["healing"]
        for player in players
    )

    balance = hunt[
        "balance"
    ]

    session_hours = parse_session_hours(
        hunt["session"]
    )

    share = split_data[
        "share"
    ]

    profit_per_hour = 0

    if session_hours > 0:

        profit_per_hour = (
            share
            / session_hours
        )

    color = (
        discord.Color.green()
        if balance >= 0
        else discord.Color.red()
    )

    embed = discord.Embed(
        title="💰 Hunt Split",
        description=(
            f"⏱️ Session: **{hunt['session']}**\n"
            f"👥 Players: **{len(players)}**"
        ),
        color=color
    )

    # =====================================================
    # WHAT YOU NEED TO DO
    # =====================================================

    transactions = split_data[
        "transactions"
    ]

    if transactions:

        action_lines = []

        for transaction in transactions:

            payer = transaction[
                "from"
            ]

            receiver = transaction[
                "to"
            ]

            amount = transaction[
                "amount"
            ]

            action_lines.append(
                f"🔴 **{payer}** needs to pay "
                f"**{format_gp(amount)}** "
                f"to **{receiver}**\n"
                f"🏦 `transfer {amount} to {receiver}`"
            )

        action_chunks = chunk_lines(
            action_lines,
            950
        )

        for index, chunk in enumerate(
            action_chunks
        ):

            title = (
                "💸 What you need to do"
                if index == 0
                else
                f"💸 What you need to do "
                f"({index + 1})"
            )

            embed.add_field(
                name=title,
                value=chunk,
                inline=False
            )

    else:

        embed.add_field(
            name="💸 What you need to do",
            value=(
                "✅ No transfers are needed. "
                ""
            ),
            inline=False
        )

    # =====================================================
    # FINANCIAL SUMMARY
    # =====================================================

    embed.add_field(
        name="📦 Loot",
        value=(
            f"**{format_gp(hunt['loot'])}**\n"
            f"`{format_short_gp(hunt['loot'])}`"
        ),
        inline=True
    )

    embed.add_field(
        name="🧪 Supplies",
        value=(
            f"**{format_gp(hunt['supplies'])}**\n"
            f"`{format_short_gp(hunt['supplies'])}`"
        ),
        inline=True
    )

    embed.add_field(
        name=(
            "💰 Profit total"
            if balance >= 0
            else "📉 Waste total"
        ),
        value=(
            f"**{format_gp(balance)}**\n"
            f"`{format_short_gp(balance)}`"
        ),
        inline=True
    )

    embed.add_field(
        name="👤 Profit per player",
        value=(
            f"**{format_gp(round(share))}**"
        ),
        inline=True
    )

    if session_hours > 0:

        embed.add_field(
            name="📈 Profit per player/h",
            value=(
                f"**~{format_short_gp(round(profit_per_hour))}/h**"
            ),
            inline=True
        )

    embed.add_field(
        name="⏱️ Duration",
        value=(
            f"**{hunt['session']}**"
        ),
        inline=True
    )

    # =====================================================
    # DAMAGE SUMMARY
    # =====================================================

    damage_sorted = sorted(
        players,
        key=lambda player:
            player["damage"],
        reverse=True
    )

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    damage_summary = []

    for index, player in enumerate(
        damage_sorted
    ):

        if total_damage > 0:

            percentage = (
                player["damage"]
                / total_damage
                * 100
            )

        else:

            percentage = 0

        medal = (
            medals[index]
            if index < len(medals)
            else "•"
        )

        damage_summary.append(
            f"{medal} **{player['name']}** "
            f"— **{percentage:.1f}%**"
        )

    embed.add_field(
        name="⚔️ Damage Split",
        value="\n".join(
            damage_summary
        ),
        inline=False
    )

    # =====================================================
    # SPLIT DETAILS
    # =====================================================

    split_lines = []

    for player in players:

        adjustment = player[
            "adjustment"
        ]

        leader_text = (
            " 👑"
            if player["leader"]
            else ""
        )

        if adjustment > 0:

            action = (
                f"🟢 receives "
                f"**{format_gp(adjustment)}**"
            )

        elif adjustment < 0:

            action = (
                f"🔴 pays "
                f"**{format_gp(abs(adjustment))}**"
            )

        else:

            action = (
                "⚪ does not need to pay "
                "or receive"
            )

        split_lines.append(
            f"**{player['name']}**"
            f"{leader_text}\n"
            f"Current balance: "
            f"{format_gp(player['balance'])}\n"
            f"{action}"
        )

    split_chunks = chunk_lines(
        split_lines,
        950
    )

    for index, chunk in enumerate(
        split_chunks
    ):

        title = (
            "👥 Split details"
            if index == 0
            else
            f"👥 Split details "
            f"({index + 1})"
        )

        embed.add_field(
            name=title,
            value=chunk,
            inline=False
        )

    # =====================================================
    # FULL DAMAGE
    # =====================================================

    damage_lines = []

    for index, player in enumerate(
        damage_sorted
    ):

        if total_damage > 0:

            percentage = (
                player["damage"]
                / total_damage
                * 100
            )

        else:

            percentage = 0

        medal = (
            medals[index]
            if index < len(medals)
            else "•"
        )

        damage_lines.append(
            f"{medal} **{player['name']}** "
            f"— {clean_number(player['damage'])} "
            f"({percentage:.1f}%)"
        )

    embed.add_field(
        name="⚔️ Damage",
        value="\n".join(
            damage_lines
        ),
        inline=False
    )

    # =====================================================
    # HEALING
    # =====================================================

    healing_sorted = sorted(
        players,
        key=lambda player:
            player["healing"],
        reverse=True
    )

    healing_lines = []

    for index, player in enumerate(
        healing_sorted
    ):

        if total_healing > 0:

            percentage = (
                player["healing"]
                / total_healing
                * 100
            )

        else:

            percentage = 0

        medal = (
            medals[index]
            if index < len(medals)
            else "•"
        )

        healing_lines.append(
            f"{medal} **{player['name']}** "
            f"— {clean_number(player['healing'])} "
            f"({percentage:.1f}%)"
        )

    embed.add_field(
        name="❤️ Healing",
        value="\n".join(
            healing_lines
        ),
        inline=False
    )

    # =====================================================
    # VALIDATION
    # =====================================================

    individual_balance = sum(
        player["balance"]
        for player in players
    )

    difference = (
        hunt["balance"]
        - individual_balance
    )

    if difference != 0:

        embed.add_field(
            name="⚠️ Diferencia detectada",
            value=(
                "The sum of individual balances "
                "does not match "
                "the total balance.\n"
                f"Diferencia: "
                f"**{format_gp(difference)}**"
            ),
            inline=False
        )

    embed.set_footer(
        text=(
            "Exura • Hunt Analyzer Split"
        )
    )

    return embed


# =========================================================
# MODAL SPLIT
# =========================================================

class HuntSplitModal(
    discord.ui.Modal,
    title="Hunt Split"
):

    analyzer = discord.ui.TextInput(
        label="Paste the Hunt Analyzer here",
        placeholder=(
            "Session data: From...\n"
            "Session: 02:41h\n"
            "Loot: 6,120,001\n"
            "Supplies: 1,532,490\n"
            "..."
        ),
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )

    async def on_submit(
        self,
        interaction:
        discord.Interaction
    ):

        await interaction.response.defer()

        hunt = parse_hunt_analyzer(
            str(self.analyzer.value)
        )

        if not hunt:

            await interaction.followup.send(
                "❌ I could not read the Hunt Analyzer.\n\n"
                "Copy it directly from Tibia "
                "including each player block.",
                ephemeral=True
            )

            return

        split_data = calculate_split(
            hunt
        )

        if not split_data:

            await interaction.followup.send(
                "❌ I could not calculate "
                "the split.",
                ephemeral=True
            )

            return

        embed = build_split_embed(
            hunt,
            split_data
        )

        await interaction.followup.send(
            embed=embed
        )


# =========================================================
# BOT
# =========================================================

class Exura(
    commands.Bot
):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=discord.Intents.default()
        )

    async def setup_hook(self):

        global CREATURES
        global BOSSES
        global ITEMS
        global BOOSTED_BOSS_NAMES

        crear_delivery_db()
        crear_tracking_db()

        print(
            "===================================="
        )

        print(
            "Exura starting..."
        )

        print(
            "===================================="
        )

        print(
            "Loading creatures..."
        )

        CREATURES = (
            await get_creatures_list()
        )

        print(
            f"{len(CREATURES)} "
            "creatures loaded."
        )

        print(
            "Loading bosses..."
        )

        BOSSES = (
            await get_bosses_list()
        )

        print(
            f"{len(BOSSES)} "
            "bosses loaded."
        )

        print(
            "Fetching boostable boss..."
        )

        boost_data = (
            await get_boostable_bosses()
        )

        BOOSTED_BOSS_NAMES = (
            extract_boosted_boss_names(
                boost_data
            )
        )

        print(
            "Loading items..."
        )

        ITEMS = (
            await get_items_list()
        )

        print(
            f"{len(ITEMS)} "
            "items loaded."
        )

        print(
            "Syncing commands..."
        )

        await self.tree.sync()

        print(
            "Comandos sincronizados."
        )

        asyncio.create_task(actualizar_delivery_market())
        asyncio.create_task(guild_tracking_loop())


bot = Exura()


# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():

    print(
        "===================================="
    )

    print(
        f"Exura connected as "
        f"{bot.user}"
    )

    print(
        f"Ping: "
        f"{round(bot.latency * 1000)} ms"
    )

    print(
        "===================================="
    )


# =========================================================
# PING
# =========================================================

@bot.tree.command(
    name="ping",
    description="Comprueba si Exura funciona."
)
async def ping(
    interaction:
    discord.Interaction
):

    await interaction.response.send_message(
        f"🏓 Pong! "
        f"{round(bot.latency * 1000)} ms"
    )


# =========================================================
# /EXURA
# =========================================================

exura = app_commands.Group(
    name="exura",
    description=(
        "Tibia tools and data."
    )
)


# =========================================================
# /EXURA SPLIT
# =========================================================

@exura.command(
    name="split",
    description=(
        "Paste a Hunt Analyzer "
        "and calculate the split."
    )
)
async def split(
    interaction:
    discord.Interaction
):

    await interaction.response.send_modal(
        HuntSplitModal()
    )


# =========================================================
# /EXURA BOOSTED
# =========================================================

@exura.command(
    name="boosted",
    description=(
        "Shows the boosted creature and "
        "boosted boss of the day."
    )
)
async def boosted(
    interaction:
    discord.Interaction
):

    await interaction.response.defer()

    boosted_creature_data, boosted_boss_data = (
        await asyncio.gather(
            get_boosted_creature(),
            get_boosted_boss()
        )
    )

    creature_name = None
    boss_name = None

    if isinstance(
        boosted_creature_data,
        dict
    ):

        creature_name = get_first(
            boosted_creature_data,
            "name",
            "race",
            default=None
        )

    if isinstance(
        boosted_boss_data,
        dict
    ):

        boss_name = get_first(
            boosted_boss_data,
            "name",
            default=None
        )

    embed = discord.Embed(
        title="🔥 Daily Boosted",
        color=discord.Color.orange()
    )

    if creature_name:

        creature_details = (
            await get_wiki_creature(
                creature_name
            )
        )

        text = (
            f"**{creature_name}**"
        )

        if isinstance(
            creature_details,
            dict
        ):

            hp = get_first(
                creature_details,
                "hitpoints",
                "hp",
                default=None
            )

            exp = get_first(
                creature_details,
                "exp",
                "experience",
                default=None
            )

            if hp:

                text += (
                    f"\n❤️ HP: "
                    f"**{clean_number(hp)}**"
                )

            if exp:

                text += (
                    f"\n⭐ XP: "
                    f"**{clean_number(exp)}**"
                )

        embed.add_field(
            name="👹 Boosted Creature",
            value=text,
            inline=True
        )

    else:

        embed.add_field(
            name="👹 Boosted Creature",
            value="Not available.",
            inline=True
        )

    if boss_name:

        boss_details = (
            await get_wiki_boss(
                boss_name
            )
        )

        text = (
            f"**{boss_name}**"
        )

        if isinstance(
            boss_details,
            dict
        ):

            hp = get_first(
                boss_details,
                "hitpoints",
                "hp",
                default=None
            )

            exp = get_first(
                boss_details,
                "exp",
                "experience",
                default=None
            )

            if hp:

                text += (
                    f"\n❤️ HP: "
                    f"**{clean_number(hp)}**"
                )

            if exp:

                text += (
                    f"\n⭐ XP: "
                    f"**{clean_number(exp)}**"
                )

        embed.add_field(
            name="🏆 Boosted Boss",
            value=text,
            inline=True
        )

    else:

        embed.add_field(
            name="🏆 Boosted Boss",
            value="Not available.",
            inline=True
        )

    embed.set_footer(
        text=(
            "Exura • TibiaData"
        )
    )

    await interaction.followup.send(
        embed=embed
    )


# =========================================================
# /EXURA ONLINE
# =========================================================

@exura.command(
    name="online",
    description=(
        "Shows online members "
        "of Existencia."
    )
)
async def online(
    interaction:
    discord.Interaction
):

    await interaction.response.defer()

    data = await get_guild(
        GUILD_NAME
    )

    if not data:

        await interaction.followup.send(
            "❌ I could not query "
            f"the guild **{GUILD_NAME}**."
        )

        return

    guild_info, members = (
        extract_guild_data(data)
    )

    online_members = [
        member
        for member in members
        if guild_member_is_online(
            member
        )
    ]

    def member_level(member):

        try:
            return int(
                member.get(
                    "level",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):
            return 0

    online_members.sort(
        key=member_level,
        reverse=True
    )

    guild_name = get_first(
        guild_info,
        "name",
        default=GUILD_NAME
    )

    world = get_first(
        guild_info,
        "world",
        default="Celesta"
    )

    embed = discord.Embed(
        title=(
            f"🟢 {guild_name} — Online"
        ),
        description=(
            f"**{len(online_members)}** "
            f"out of **{len(members)}** members "
            "online."
        ),
        color=(
            discord.Color.green()
            if online_members
            else discord.Color.red()
        )
    )

    embed.add_field(
        name="🌍 World",
        value=str(world),
        inline=True
    )

    embed.add_field(
        name="🟢 Online",
        value=str(
            len(online_members)
        ),
        inline=True
    )

    embed.add_field(
        name="👥 Members",
        value=str(
            len(members)
        ),
        inline=True
    )

    if online_members:

        chunks = build_online_chunks(
            online_members
        )

        for index, chunk in enumerate(
            chunks
        ):

            embed.add_field(
                name=(
                    "⚔️ Online members"
                    if index == 0
                    else
                    f"⚔️ Online members "
                    f"({index + 1})"
                ),
                value=chunk,
                inline=False
            )

    else:

        embed.add_field(
            name="🔴 Estado",
            value=(
                "There are no online members "
                "ahora mismo."
            ),
            inline=False
        )

    embed.set_footer(
        text=(
            "Exura • Existencia • TibiaData"
        )
    )

    await interaction.followup.send(
        embed=embed
    )


# =========================================================
# /EXURA CHAR
# =========================================================

@exura.command(
    name="char",
    description=(
        "Searches for information "
        "about a Tibia character."
    )
)
async def char(
    interaction:
    discord.Interaction,
    name: str
):

    await interaction.response.defer()

    data = await get_character(
        name
    )

    if not data:

        await interaction.followup.send(
            f"❌ I could not find "
            f"**{name}**."
        )

        return

    try:

        character = (
            data[
                "character"
            ][
                "character"
            ]
        )

    except Exception:

        await interaction.followup.send(
            f"❌ I could not find "
            f"**{name}**."
        )

        return

    guild = character.get(
        "guild"
    )

    if guild:

        guild_text = guild.get(
            "name",
            "?"
        )

        rank = guild.get(
            "rank"
        )

        if rank:
            guild_text += (
                f"\n{rank}"
            )

    else:

        guild_text = "No guild"

    embed = discord.Embed(
        title=(
            f"⚔️ "
            f"{character.get('name', name)}"
        ),
        color=discord.Color.purple()
    )

    embed.add_field(
        name="⭐ Level",
        value=str(
            character.get(
                "level",
                "?"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="⚔️ Vocation",
        value=str(
            character.get(
                "vocation",
                "?"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="🌍 World",
        value=str(
            character.get(
                "world",
                "?"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="🏠 Residencia",
        value=str(
            character.get(
                "residence",
                "?"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="🏰 Guild",
        value=guild_text,
        inline=True
    )

    embed.add_field(
        name="👤 Sexo",
        value=str(
            character.get(
                "sex",
                "?"
            )
        ),
        inline=True
    )

    embed.set_footer(
        text="Exura • TibiaData"
    )

    await interaction.followup.send(
        embed=embed
    )


# =========================================================
# CREATURE
# =========================================================

async def creature_autocomplete(
    interaction:
    discord.Interaction,
    current: str
):

    names = [
        creature.get("name")
        for creature in CREATURES
        if isinstance(
            creature,
            dict
        )
    ]

    return make_choices(
        names,
        current
    )


@exura.command(
    name="creature",
    description=(
        "Looks up a Tibia creature."
    )
)
@app_commands.autocomplete(
    name=creature_autocomplete
)
async def creature(
    interaction:
    discord.Interaction,
    name: str
):

    await interaction.response.defer()

    data = await get_wiki_creature(
        name
    )

    if not isinstance(
        data,
        dict
    ):

        await interaction.followup.send(
            f"❌ I could not find "
            f"**{name}**."
        )

        return

    bestiary = get_first(
        data,
        "bestiaryLevel",
        "bestiarylevel",
        default="?"
    )

    embed = discord.Embed(
        title=(
            "👹 "
            + str(
                get_first(
                    data,
                    "name",
                    default=name
                )
            )
        ),
        color=discord.Color.dark_purple()
    )

    embed.add_field(
        name="❤️ HP",
        value=clean_number(
            get_first(
                data,
                "hitpoints",
                "hp"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="⭐ Experiencia",
        value=clean_number(
            get_first(
                data,
                "exp",
                "experience"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="📖 Bestiary",
        value=str(bestiary),
        inline=True
    )

    embed.add_field(
        name="💎 Charm Points",
        value=str(
            get_charm_points(
                bestiary
            )
        ),
        inline=True
    )

    embed.add_field(
        name="🛡️ Armor",
        value=str(
            get_first(
                data,
                "armor"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="🏃 Velocidad",
        value=str(
            get_first(
                data,
                "speed"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="🛡️ Damage dealt / Protection",
        value=format_max_damage(
            get_first(
                data,
                "maxdmg",
                "maxDamage",
                default="?"
            )
        ),
        inline=False
    )

    elements = build_sorted_element_modifiers(
        data
    )

    embed.add_field(
        name="🎯 Best damage against the creature",
        value=elements,
        inline=False
    )

    embed.add_field(
        name="📦 Loot destacado",
        value=get_highlight_loot(
            data.get(
                "loot",
                []
            )
        ),
        inline=False
    )

    embed.add_field(
        name="📍 Localizaciones",
        value=get_locations_text(
            get_first(
                data,
                "location",
                "locations",
                default=None
            )
        ),
        inline=False
    )

    await interaction.followup.send(
        embed=embed
    )


# =========================================================
# /EXURA HUNT
# =========================================================

@exura.command(
    name="hunt",
    description=(
        "Analyzes multiple creatures and recommends "
        "damage types and protections."
    )
)
async def hunt(
    interaction:
    discord.Interaction
):
    await interaction.response.send_modal(
        HuntCreaturesModal()
    )


# =========================================================
# BOSS
# =========================================================

async def boss_autocomplete(
    interaction:
    discord.Interaction,
    current: str
):

    names = [
        boss.get("name")
        for boss in BOSSES
        if isinstance(
            boss,
            dict
        )
    ]

    return make_choices(
        names,
        current
    )


@exura.command(
    name="boss",
    description=(
        "Looks up boss information."
    )
)
@app_commands.autocomplete(
    name=boss_autocomplete
)
async def boss(
    interaction:
    discord.Interaction,
    name: str
):

    await interaction.response.defer()

    data = await get_wiki_boss(
        name
    )

    if not isinstance(
        data,
        dict
    ):

        await interaction.followup.send(
            f"❌ I could not find "
            f"el boss **{name}**."
        )

        return

    boss_name = get_first(
        data,
        "name",
        default=name
    )

    embed = discord.Embed(
        title=f"🏆 {boss_name}",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="❤️ HP",
        value=clean_number(
            get_first(
                data,
                "hitpoints",
                "hp"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="⭐ Experiencia",
        value=clean_number(
            get_first(
                data,
                "exp",
                "experience"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="👑 Tipo",
        value=str(
            get_first(
                data,
                "bosstype",
                "bossType",
                "creatureclass",
                default="Boss"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="🛡️ Armor",
        value=str(
            get_first(
                data,
                "armor"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="🏃 Velocidad",
        value=str(
            get_first(
                data,
                "speed"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="💥 Maximum damage",
        value=format_max_damage(
            get_first(
                data,
                "maxdmg",
                "maxDamage",
                default="?"
            )
        ),
        inline=True
    )

    elements = "\n".join(
        [
            format_element(
                "Physical",
                "⚔️",
                get_first(
                    data,
                    "physicalDmgMod"
                )
            ),
            format_element(
                "Fire",
                "🔥",
                get_first(
                    data,
                    "fireDmgMod"
                )
            ),
            format_element(
                "Earth",
                "🌱",
                get_first(
                    data,
                    "earthDmgMod"
                )
            ),
            format_element(
                "Energy",
                "⚡",
                get_first(
                    data,
                    "energyDmgMod"
                )
            ),
            format_element(
                "Ice",
                "❄️",
                get_first(
                    data,
                    "iceDmgMod"
                )
            ),
            format_element(
                "Death",
                "☠️",
                get_first(
                    data,
                    "deathDmgMod"
                )
            ),
            format_element(
                "Holy",
                "✨",
                get_first(
                    data,
                    "holyDmgMod"
                )
            )
        ]
    )

    embed.add_field(
        name="🧪 Damage modifiers",
        value=elements,
        inline=False
    )

    loot = data.get(
        "loot",
        []
    )

    loot_chunks = build_full_loot_fields(
        loot
    )

    for index, chunk in enumerate(
        loot_chunks
    ):

        embed.add_field(
            name=(
                f"🎁 Loot completo ({len(loot)} items)"
                if index == 0
                else
                f"🎁 Loot completo "
                f"(continued {index + 1})"
            ),
            value=chunk,
            inline=False
        )

    embed.add_field(
        name="📍 Location",
        value=get_locations_text(
            get_first(
                data,
                "location",
                "locations",
                default=None
            )
        ),
        inline=False
    )

    await interaction.followup.send(
        embed=embed
    )


# =========================================================
# ITEM
# =========================================================

async def item_autocomplete(
    interaction:
    discord.Interaction,
    current: str
):

    names = [
        get_item_name(item)
        for item in ITEMS
    ]

    return make_choices(
        names,
        current
    )


@exura.command(
    name="item",
    description=(
        "Looks up stats "
        "and item price."
    )
)
@app_commands.autocomplete(
    name=item_autocomplete
)
async def item(
    interaction:
    discord.Interaction,
    name: str
):

    await interaction.response.defer()

    data = await get_wiki_item(
        name
    )

    if not isinstance(
        data,
        dict
    ):

        await interaction.followup.send(
            f"❌ I could not find "
            f"**{name}**."
        )

        return

    item_name = get_first(
        data,
        "name",
        default=name
    )

    embed = discord.Embed(
        title=f"🎒 {item_name}",
        color=discord.Color.dark_purple()
    )

    embed.add_field(
        name="🏷️ Tipo",
        value=str(
            get_first(
                data,
                "primarytype"
            )
        ),
        inline=True
    )

    slot = get_first(
        data,
        "slot",
        default=None
    )

    if slot:

        embed.add_field(
            name="🎽 Slot",
            value=format_slot(slot),
            inline=True
        )

    embed.add_field(
        name="⭐ Level",
        value=str(
            get_first(
                data,
                "levelrequired"
            )
        ),
        inline=True
    )

    embed.add_field(
        name="⚔️ Vocation",
        value=format_vocation(
            get_first(
                data,
                "vocrequired"
            )
        ),
        inline=True
    )

    weight = get_first(
        data,
        "weight",
        default="?"
    )

    embed.add_field(
        name="⚖️ Weight",
        value=(
            f"{weight} oz"
            if weight != "?"
            else "?"
        ),
        inline=True
    )

    imbues = get_first(
        data,
        "imbueslots",
        default=None
    )

    if imbues:

        embed.add_field(
            name="💎 Imbuement Slots",
            value=str(imbues),
            inline=True
        )

    for (
        key,
        title,
        emoji
    ) in (
        (
            "attack",
            "Attack",
            "🗡️"
        ),
        (
            "defense",
            "Defense",
            "🛡️"
        ),
        (
            "armor",
            "Armor",
            "🛡️"
        )
    ):

        value = get_first(
            data,
            key,
            default=None
        )

        if value:

            embed.add_field(
                name=f"{emoji} {title}",
                value=str(value),
                inline=True
            )

    resistances = (
        format_item_resistances(
            get_first(
                data,
                "resist",
                default=None
            )
        )
    )

    if resistances:

        embed.add_field(
            name="🧪 Resistances",
            value=resistances,
            inline=False
        )

    attributes = (
        format_item_attributes(
            get_first(
                data,
                "attrib",
                default=None
            )
        )
    )

    if attributes:

        embed.add_field(
            name="✨ Bonuses",
            value=attributes,
            inline=False
        )

    item_id = get_item_id(
        data
    )

    if item_id:

        market = await build_market_text(
            item_id,
            "Celesta"
        )

        embed.add_field(
            name="💰 Market",
            value=market,
            inline=False
        )

    await interaction.followup.send(
        embed=embed
    )



# =========================================================
# /EXURA DELIVERY
# =========================================================

@exura.command(
    name="delivery",
    description="Weekly Delivery list: NPC and Celesta Market prices."
)
async def delivery(
    interaction: discord.Interaction
):
    await interaction.response.defer(thinking=True)

    updated, _detail = await actualizar_delivery_market()
    items = get_delivery_items()

    if not items:
        await interaction.followup.send(
            "❌ No Delivery Items are loaded.",
            ephemeral=True
        )
        return

    view = DeliveryView(
        items=items,
        page=0,
        author_id=interaction.user.id
    )

    notice = None
    if not updated and delivery_cache_timestamp() is None:
        notice = (
            "⚠️ The Market API is not responding right now. "
            "Showing NPC prices; Market prices will appear once "
            "the first update is available."
        )
    elif not updated:
        notice = (
            "⚠️ The Market could not be refreshed. "
            "Showing the latest saved prices."
        )

    content = view.build_content()
    if notice:
        content = f"{notice}\n\n{content}"

    await interaction.followup.send(
        content=content,
        view=view
    )


# =========================================================
# /EXURA TRACKING
# =========================================================

tracking = app_commands.Group(
    name="tracking",
    description="Configure automatic guild announcements."
)


@tracking.command(
    name="setup",
    description="Track a guild and announce level ups and deaths in a channel."
)
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(
    guild_name="Exact name of the Tibia guild.",
    channel="Channel where Exura will post level ups and deaths."
)
async def tracking_setup(
    interaction: discord.Interaction,
    guild_name: str,
    channel: discord.TextChannel
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used inside a server.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    data = await get_guild(guild_name.strip())
    if not data:
        await interaction.followup.send(
            f"❌ I could not find the guild **{guild_name}** in Tibia.",
            ephemeral=True
        )
        return

    guild_info, members = extract_guild_data(data)
    if not guild_info:
        await interaction.followup.send(
            f"❌ I could not read information for **{guild_name}**.",
            ephemeral=True
        )
        return

    canonical_name = get_first(guild_info, "name", default=guild_name.strip())
    world = get_first(guild_info, "world", default="?")

    save_tracking_config(
        interaction.guild.id,
        canonical_name,
        world,
        channel.id
    )

    # Level baseline: prevents old level-ups from being announced when the tracker is enabled.
    for member in members:
        name = get_first(member, "name", default=None)
        if not name:
            continue
        try:
            level = int(get_first(member, "level", default=0))
        except (TypeError, ValueError):
            level = 0
        save_tracking_character(
            interaction.guild.id,
            name,
            level=level or None,
            last_death_key=None
        )

    await interaction.followup.send(
        "✅ **Guild Tracker enabled**\n"
        f"🏰 Guild: **{canonical_name}**\n"
        f"🌍 World: **{world}**\n"
        f"📢 Channel: {channel.mention}\n"
        f"👥 Members detected: **{len(members)}**\n\n"
        "Exura will automatically announce **level ups** and **new deaths**. "
        "The first death check only creates a baseline and does not publish old history.",
        ephemeral=True
    )


@tracking.command(
    name="status",
    description="Show the guild and channel tracked by this server."
)
async def tracking_status(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used inside a server.",
            ephemeral=True
        )
        return

    config = get_tracking_config(interaction.guild.id)
    if not config or not config[4]:
        await interaction.response.send_message(
            "ℹ️ This server does not have a Guild Tracker configured.",
            ephemeral=True
        )
        return

    _gid, guild_name, world, channel_id, _enabled = config
    channel = interaction.guild.get_channel(int(channel_id))
    channel_text = channel.mention if channel else f"`{channel_id}` (channel not found)"

    await interaction.response.send_message(
        "📡 **Guild Tracker**\n"
        f"🏰 Guild: **{guild_name}**\n"
        f"🌍 World: **{world or '?'}**\n"
        f"📢 Channel: {channel_text}\n"
        f"⏱️ Check interval: every **{max(1, TRACKING_POLL_SECONDS // 60)} min**",
        ephemeral=True
    )


@tracking.command(
    name="disable",
    description="Disable automatic guild tracking on this server."
)
@app_commands.checks.has_permissions(manage_guild=True)
async def tracking_disable(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used inside a server.",
            ephemeral=True
        )
        return

    config = get_tracking_config(interaction.guild.id)
    if not config:
        await interaction.response.send_message(
            "ℹ️ No Guild Tracker was configured.",
            ephemeral=True
        )
        return

    delete_tracking_config(interaction.guild.id)
    await interaction.response.send_message(
        "✅ Guild Tracker disabled on this server.",
        ephemeral=True
    )


@tracking.command(
    name="test",
    description="Send a test message to the configured channel."
)
@app_commands.checks.has_permissions(manage_guild=True)
async def tracking_test(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used inside a server.",
            ephemeral=True
        )
        return

    config = get_tracking_config(interaction.guild.id)
    if not config or not config[4]:
        await interaction.response.send_message(
            "❌ Configure `/exura tracking setup` first.",
            ephemeral=True
        )
        return

    _gid, guild_name, world, channel_id, _enabled = config
    embed = discord.Embed(
        title="✅ Guild Tracker working",
        description=(
            f"Exura is ready to announce **level ups** and **deaths** "
            f"for **{guild_name}**."
        ),
        color=discord.Color.blue()
    )
    embed.add_field(name="🌍 World", value=str(world or "?"), inline=True)
    embed.set_footer(text="Exura • Guild Tracker • Test")

    sent = await tracking_send(channel_id, embed)
    await interaction.response.send_message(
        "✅ Test message sent." if sent else
        "❌ I could not write to the configured channel. Check my permissions.",
        ephemeral=True
    )


exura.add_command(tracking)


# =========================================================
# REGISTER /EXURA
# =========================================================

bot.tree.add_command(
    exura
)


# =========================================================
# ARRANQUE
# =========================================================

if not TOKEN:

    raise RuntimeError(
        "Could not find "
        "DISCORD_TOKEN in .env"
    )


bot.run(
    TOKEN
)
