import re
from difflib import SequenceMatcher
from urllib.parse import quote

import aiohttp

from data.hunts import (
    RESPAWN_NAMES,
    SPECIAL_RESPAWNS
)


BASE_URL = "https://tibiadata.bytewizards.de/api/v1"


# =========================================================
# HTTP
# =========================================================

async def _get_json(endpoint: str):
    url = f"{BASE_URL}{endpoint}"

    timeout = aiohttp.ClientTimeout(
        total=30
    )

    headers = {
        "User-Agent": "Exura Discord Bot"
    }

    try:
        async with aiohttp.ClientSession(
            headers=headers,
            timeout=timeout
        ) as session:

            async with session.get(
                url
            ) as response:

                if response.status == 404:
                    return None

                if response.status != 200:
                    print(
                        f"[Hunts] Error HTTP "
                        f"{response.status}: {url}"
                    )
                    return None

                return await response.json()

    except aiohttp.ClientError as error:
        print(
            f"[Hunts] Error de conexión: "
            f"{error}"
        )
        return None

    except TimeoutError:
        print(
            "[Hunts] Timeout."
        )
        return None

    except Exception as error:
        print(
            f"[Hunts] Error inesperado: "
            f"{error}"
        )
        return None


# =========================================================
# API HUNTING PLACES
# =========================================================

async def get_hunting_places_list():
    data = await _get_json(
        "/hunting-places/list"
    )

    if not isinstance(
        data,
        list
    ):
        return []

    return data


async def get_hunting_place(
    name: str
):
    if not name:
        return None

    encoded_name = quote(
        name.strip()
    )

    return await _get_json(
        f"/hunting-places/{encoded_name}"
    )


# =========================================================
# CATÁLOGO DE RESPAWNS
# =========================================================

def get_respawn_names():
    """
    Devuelve la lista de nombres populares
    que usamos dentro de /exura hunt.
    """

    return RESPAWN_NAMES.copy()


# =========================================================
# NORMALIZACIÓN
# =========================================================

def normalize_name(value):
    if not value:
        return ""

    value = (
        str(value)
        .lower()
        .strip()
    )

    value = (
        value
        .replace("'", "")
        .replace("’", "")
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def remove_spawn_qualifiers(value):
    """
    Ejemplos:

    Roshamuul Prison -3
        -> Roshamuul Prison

    Gnomprona Crystal Enigma (NORTH)
        -> Gnomprona Crystal Enigma
    """

    value = str(
        value
    ).strip()

    value = re.sub(
        r"\([^)]*\)",
        "",
        value
    )

    value = re.sub(
        r"\s[-+]\d+"
        r"(?:\s*&\s*[-+]?\d+)?"
        r"\s*$",
        "",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# =========================================================
# HINTS DEL NOMBRE POPULAR
# =========================================================

def extract_spawn_hints(
    respawn_name
):
    hints = []

    name = str(
        respawn_name
    )

    # Plantas como -1, -2, -3...
    floors = re.findall(
        r"(?<!\w)([-+]\d+)",
        name
    )

    for floor in floors:
        hints.append(
            floor
        )

    # Texto entre paréntesis
    parentheses = re.findall(
        r"\(([^)]+)\)",
        name
    )

    ignored = {
        "poh",
        "thais",
        "carlin",
        "edron",
        "ab",
        "hideout"
    }

    for text in parentheses:

        for token in re.split(
            r"[+/,& ]+",
            text
        ):
            token = token.strip()

            if (
                len(token) >= 3
                and token.lower()
                not in ignored
            ):
                hints.append(
                    token
                )

    # Direcciones
    for direction in (
        "north",
        "south",
        "east",
        "west",
        "left",
        "right",
        "surface"
    ):
        if direction in name.lower():
            hints.append(
                direction
            )

    result = []
    seen = set()

    for hint in hints:
        normalized = (
            hint
            .lower()
            .strip()
        )

        if normalized not in seen:
            seen.add(
                normalized
            )

            result.append(
                hint
            )

    return result


# =========================================================
# RESOLVER NOMBRE POPULAR -> HUNT WIKI
# =========================================================

def resolve_respawn(
    respawn_name,
    available_hunts
):
    config = {
        "display_name": respawn_name,
        "wiki_hunt": None,
        "section_keywords": []
    }

    # =====================================================
    # MAPEADO MANUAL
    # =====================================================

    special = SPECIAL_RESPAWNS.get(
        respawn_name
    )

    if special:
        config.update(
            special
        )

        return config

    # =====================================================
    # LISTADO DE NOMBRES DE LA API
    # =====================================================

    api_names = []

    for hunt in available_hunts:

        if isinstance(
            hunt,
            dict
        ):
            name = hunt.get(
                "name"
            )

        else:
            name = str(
                hunt
            )

        if name:
            api_names.append(
                name
            )

    wanted = normalize_name(
        respawn_name
    )

    # =====================================================
    # MATCH EXACTO
    # =====================================================

    for api_name in api_names:

        if (
            normalize_name(
                api_name
            )
            == wanted
        ):
            config[
                "wiki_hunt"
            ] = api_name

            config[
                "section_keywords"
            ] = extract_spawn_hints(
                respawn_name
            )

            return config

    # =====================================================
    # ELIMINAR PLANTA / PARÉNTESIS
    # =====================================================

    base = remove_spawn_qualifiers(
        respawn_name
    )

    normalized_base = normalize_name(
        base
    )

    for api_name in api_names:

        if (
            normalize_name(
                api_name
            )
            == normalized_base
        ):
            config[
                "wiki_hunt"
            ] = api_name

            config[
                "section_keywords"
            ] = extract_spawn_hints(
                respawn_name
            )

            return config

    # =====================================================
    # CONTENCIÓN
    # =====================================================

    containment_matches = []

    for api_name in api_names:

        normalized_api = normalize_name(
            api_name
        )

        if not normalized_api:
            continue

        if (
            normalized_api
            in normalized_base
            or normalized_base
            in normalized_api
        ):
            difference = abs(
                len(normalized_api)
                -
                len(normalized_base)
            )

            containment_matches.append(
                (
                    difference,
                    api_name
                )
            )

    if containment_matches:
        containment_matches.sort(
            key=lambda item: item[0]
        )

        config[
            "wiki_hunt"
        ] = containment_matches[0][1]

        config[
            "section_keywords"
        ] = extract_spawn_hints(
            respawn_name
        )

        return config

    # =====================================================
    # FUZZY MATCH
    # =====================================================

    best_name = None
    best_score = 0

    for api_name in api_names:

        score = SequenceMatcher(
            None,
            normalized_base,
            normalize_name(
                api_name
            )
        ).ratio()

        if score > best_score:
            best_score = score
            best_name = api_name

    if (
        best_name
        and best_score >= 0.58
    ):
        config[
            "wiki_hunt"
        ] = best_name

    config[
        "section_keywords"
    ] = extract_spawn_hints(
        respawn_name
    )

    return config


# =========================================================
# PARSEAR SECCIONES DEL WIKI
# =========================================================

def parse_wiki_sections(
    raw_text
):
    if not raw_text:
        return []

    heading_pattern = re.compile(
        r"^(={2,6})\s*"
        r"(.*?)"
        r"\s*\1\s*$",
        re.MULTILINE
    )

    matches = list(
        heading_pattern.finditer(
            raw_text
        )
    )

    sections = []

    for index, match in enumerate(
        matches
    ):
        level = len(
            match.group(1)
        )

        title = (
            match.group(2)
            .strip()
        )

        start = match.end()
        end = len(
            raw_text
        )

        for next_match in matches[
            index + 1:
        ]:
            next_level = len(
                next_match.group(1)
            )

            if next_level <= level:
                end = next_match.start()
                break

        body = raw_text[
            start:end
        ]

        sections.append(
            {
                "title": title,
                "level": level,
                "body": body
            }
        )

    return sections


# =========================================================
# CREATURE LIST
# =========================================================

def parse_creature_lists(
    text
):
    if not text:
        return []

    blocks = re.findall(
        r"\{\{CreatureList"
        r"(.*?)"
        r"\}\}",
        text,
        flags=re.DOTALL
    )

    creatures = []

    ignored_keys = {
        "type",
        "caption",
        "style",
        "image",
        "sort",
        "collapsed"
    }

    for block in blocks:

        lines = block.splitlines()

        for line in lines:

            line = line.strip()

            if not line.startswith(
                "|"
            ):
                continue

            value = (
                line[1:]
                .strip()
            )

            if not value:
                continue

            if "=" in value:

                key = (
                    value
                    .split(
                        "=",
                        1
                    )[0]
                    .strip()
                    .lower()
                )

                if key in ignored_keys:
                    continue

            value = (
                value
                .replace(
                    "[[",
                    ""
                )
                .replace(
                    "]]",
                    ""
                )
                .strip()
            )

            if "|" in value:
                value = (
                    value
                    .split(
                        "|"
                    )[0]
                    .strip()
                )

            if value:
                creatures.append(
                    value
                )

    result = []
    seen = set()

    for creature in creatures:

        normalized = normalize_name(
            creature
        )

        if (
            normalized
            and normalized
            not in seen
        ):
            seen.add(
                normalized
            )

            result.append(
                creature
            )

    return result


# =========================================================
# SCORE DE SECCIÓN
# =========================================================

def score_section(
    title,
    keywords
):
    if not keywords:
        return 0

    normalized_title = normalize_name(
        title
    )

    score = 0

    for keyword in keywords:

        normalized_keyword = normalize_name(
            keyword
        )

        if not normalized_keyword:
            continue

        if (
            normalized_keyword
            in normalized_title
        ):
            score += 10

        else:

            ratio = SequenceMatcher(
                None,
                normalized_keyword,
                normalized_title
            ).ratio()

            if ratio >= 0.70:
                score += 3

    return score


# =========================================================
# CRIATURAS DE UN RESPAWN
# =========================================================

def extract_respawn_creatures(
    hunt_data,
    respawn_config
):
    if not isinstance(
        hunt_data,
        dict
    ):
        return []

    # =====================================================
    # OVERRIDE MANUAL
    # =====================================================

    manual = respawn_config.get(
        "creatures"
    )

    if manual:
        return manual

    keywords = respawn_config.get(
        "section_keywords",
        []
    )

    raw = hunt_data.get(
        "rawWikiText"
    )

    # =====================================================
    # BUSCAR SECCIÓN ESPECÍFICA
    # =====================================================

    if raw and keywords:

        sections = parse_wiki_sections(
            raw
        )

        scored = []

        for section in sections:

            score = score_section(
                section[
                    "title"
                ],
                keywords
            )

            if score <= 0:
                continue

            creatures = parse_creature_lists(
                section[
                    "body"
                ]
            )

            if creatures:

                scored.append(
                    (
                        score,
                        creatures,
                        section[
                            "title"
                        ]
                    )
                )

        if scored:

            scored.sort(
                key=lambda item: item[0],
                reverse=True
            )

            return scored[0][1]

    # =====================================================
    # AREA CREATURE SUMMARIES
    # =====================================================

    structured = hunt_data.get(
        "structuredData",
        {}
    )

    if isinstance(
        structured,
        dict
    ):
        summaries = structured.get(
            "areaCreatureSummaries",
            []
        )

    else:
        summaries = []

    hunt_name = normalize_name(
        hunt_data.get(
            "name",
            ""
        )
    )

    creatures = []
    seen = set()

    if isinstance(
        summaries,
        list
    ):

        for summary in summaries:

            if not isinstance(
                summary,
                dict
            ):
                continue

            area_name = normalize_name(
                summary.get(
                    "areaName",
                    ""
                )
            )

            if (
                "boss" in area_name
                or "raid" in area_name
            ):
                continue

            if (
                hunt_name
                and area_name
                and area_name != hunt_name
            ):
                continue

            for creature in summary.get(
                "creatures",
                []
            ):

                if not isinstance(
                    creature,
                    dict
                ):
                    continue

                name = creature.get(
                    "name"
                )

                if not name:
                    continue

                normalized = normalize_name(
                    name
                )

                if normalized not in seen:
                    seen.add(
                        normalized
                    )

                    creatures.append(
                        name
                    )

    if creatures:
        return creatures

    # =====================================================
    # FALLBACK FINAL
    # =====================================================

    for creature in hunt_data.get(
        "creatures",
        []
    ):

        if not isinstance(
            creature,
            dict
        ):
            continue

        name = creature.get(
            "name"
        )

        if not name:
            continue

        normalized = normalize_name(
            name
        )

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        creatures.append(
            name
        )

    return creatures


# =========================================================
# NIVEL RECOMENDADO
# =========================================================

def get_recommended_level(
    data,
    vocation
):
    if not isinstance(
        data,
        dict
    ):
        return None

    vocation = (
        vocation
        .lower()
        .strip()
    )

    if vocation == "knight":

        keys = [
            "levelKnights",
            "lvlknights"
        ]

    elif vocation == "paladin":

        keys = [
            "levelPaladins",
            "lvlpaladins"
        ]

    elif vocation in (
        "druid",
        "sorcerer"
    ):

        keys = [
            "levelMages",
            "lvlmages"
        ]

    elif vocation == "monk":

        keys = [
            "levelMonks",
            "lvlmonks"
        ]

    else:
        keys = []

    structured = data.get(
        "structuredData",
        {}
    )

    if isinstance(
        structured,
        dict
    ):
        infobox = structured.get(
            "infobox",
            {}
        )

    else:
        infobox = {}

    for source in (
        data,
        infobox
    ):

        if not isinstance(
            source,
            dict
        ):
            continue

        for key in keys:

            value = source.get(
                key
            )

            if value not in (
                None,
                "",
                "?"
            ):
                return value

    return None


# =========================================================
# APLANAR DATOS A TEXTO
# =========================================================

def flatten_to_text(
    value
):
    if value is None:
        return ""

    if isinstance(
        value,
        str
    ):
        return value

    if isinstance(
        value,
        list
    ):
        return " ".join(
            flatten_to_text(
                item
            )
            for item in value
        )

    if isinstance(
        value,
        dict
    ):
        return " ".join(
            f"{key} "
            f"{flatten_to_text(item)}"
            for key, item
            in value.items()
        )

    return str(
        value
    )


# =========================================================
# PROTECCIONES
# =========================================================

ELEMENTS = {
    "physical": "Physical",
    "fire": "Fire",
    "earth": "Earth",
    "energy": "Energy",
    "ice": "Ice",
    "death": "Death",
    "holy": "Holy"
}


def get_creature_damage_profile(
    creature
):
    scores = {
        element: 0.0
        for element in ELEMENTS
    }

    if not isinstance(
        creature,
        dict
    ):
        return scores

    attack_text = flatten_to_text(
        {
            "attacks":
            creature.get(
                "attacks"
            ),

            "attack":
            creature.get(
                "attack"
            ),

            "spells":
            creature.get(
                "spells"
            ),

            "abilities":
            creature.get(
                "abilities"
            ),

            "maxdmg":
            creature.get(
                "maxdmg"
            ),

            "maxDamage":
            creature.get(
                "maxDamage"
            )
        }
    ).lower()

    keywords = {
        "physical": [
            "physical",
            "melee"
        ],

        "fire": [
            "fire"
        ],

        "earth": [
            "earth",
            "poison"
        ],

        "energy": [
            "energy"
        ],

        "ice": [
            "ice"
        ],

        "death": [
            "death"
        ],

        "holy": [
            "holy"
        ]
    }

    for element, words in (
        keywords.items()
    ):

        for word in words:

            count = attack_text.count(
                word
            )

            scores[
                element
            ] += (
                count * 1.4
            )

    # =====================================================
    # DAÑO MÁXIMO DOCUMENTADO
    # =====================================================

    max_damage = (
        creature.get(
            "maxdmg"
        )
        or creature.get(
            "maxDamage"
        )
    )

    if max_damage:

        matches = re.findall(
            r"(physical|fire|earth|energy|ice|death|holy)"
            r"\s*=\s*([0-9]+)",
            str(
                max_damage
            ).lower()
        )

        for (
            element,
            amount
        ) in matches:

            try:
                amount = int(
                    amount
                )

                scores[
                    element
                ] += (
                    amount / 350
                )

            except ValueError:
                pass

    if "melee" in attack_text:
        scores[
            "physical"
        ] += 2.0

    return scores


def calculate_protection_priorities(
    creatures
):
    totals = {
        element: 0.0
        for element in ELEMENTS
    }

    for creature in creatures:

        profile = get_creature_damage_profile(
            creature
        )

        for (
            element,
            score
        ) in profile.items():

            totals[
                element
            ] += score

    ranked = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True
    )

    ranked = [
        item
        for item in ranked
        if item[1] > 0
    ]

    if not ranked:
        return []

    maximum = ranked[0][1]

    result = []

    for (
        element,
        score
    ) in ranked:

        ratio = (
            score / maximum
            if maximum
            else 0
        )

        if ratio >= 0.80:
            priority = (
                "Prioridad máxima"
            )

        elif ratio >= 0.55:
            priority = "Muy alta"

        elif ratio >= 0.32:
            priority = "Alta"

        elif ratio >= 0.15:
            priority = "Secundaria"

        else:
            priority = "Baja"

        result.append(
            {
                "element":
                element,

                "score":
                score,

                "priority":
                priority
            }
        )

    return result


# =========================================================
# CHARMS
# =========================================================

CHARM_BY_ELEMENT = {
    "physical":
    "Wound",

    "fire":
    "Enflame",

    "earth":
    "Poison",

    "energy":
    "Zap",

    "ice":
    "Freeze",

    "death":
    "Curse",

    "holy":
    "Divine Wrath"
}


ELEMENT_MODIFIER_KEYS = {
    "physical":
    "physicalDmgMod",

    "fire":
    "fireDmgMod",

    "earth":
    "earthDmgMod",

    "energy":
    "energyDmgMod",

    "ice":
    "iceDmgMod",

    "death":
    "deathDmgMod",

    "holy":
    "holyDmgMod"
}


def parse_modifier(
    value
):
    if value in (
        None,
        "",
        "?"
    ):
        return 0

    try:
        return int(
            str(value)
            .replace(
                "%",
                ""
            )
            .strip()
        )

    except (
        ValueError,
        TypeError
    ):
        return 0


def get_hp(
    creature
):
    if not isinstance(
        creature,
        dict
    ):
        return 0

    value = (
        creature.get(
            "hitpoints"
        )
        or creature.get(
            "hp"
        )
    )

    try:
        return int(
            str(value)
            .replace(
                ",",
                ""
            )
            .strip()
        )

    except (
        ValueError,
        TypeError
    ):
        return 0


# =========================================================
# TOP CHARMS POR CRIATURA
# =========================================================

def calculate_charm_rankings(
    creatures,
    top_n=3
):
    result = {}

    for creature in creatures:

        if not isinstance(
            creature,
            dict
        ):
            continue

        name = creature.get(
            "name"
        )

        if not name:
            continue

        hp = get_hp(
            creature
        )

        options = []

        for (
            element,
            key
        ) in (
            ELEMENT_MODIFIER_KEYS
            .items()
        ):

            modifier = parse_modifier(
                creature.get(
                    key
                )
            )

            if modifier <= 0:
                continue

            score = (
                hp
                * modifier
                / 100
            )

            options.append(
                {
                    "charm":
                    CHARM_BY_ELEMENT[
                        element
                    ],

                    "element":
                    element,

                    "modifier":
                    modifier,

                    "score":
                    score
                }
            )

        options.sort(
            key=lambda entry:
            entry["score"],
            reverse=True
        )

        good_options = [
            option
            for option in options
            if option[
                "modifier"
            ] >= 75
        ]

        if not good_options:
            good_options = options

        result[
            name
        ] = good_options[
            :top_n
        ]

    return result


# =========================================================
# MEJOR ASIGNACIÓN SIN REPETIR CHARMS
# =========================================================

def calculate_best_charm_assignment(
    creatures
):
    charms = list(
        CHARM_BY_ELEMENT.values()
    )

    charm_indexes = {
        charm: index
        for index, charm
        in enumerate(
            charms
        )
    }

    valid_creatures = []

    for creature in creatures:

        if not isinstance(
            creature,
            dict
        ):
            continue

        name = creature.get(
            "name"
        )

        if not name:
            continue

        hp = get_hp(
            creature
        )

        options = []

        for (
            element,
            key
        ) in (
            ELEMENT_MODIFIER_KEYS
            .items()
        ):

            modifier = parse_modifier(
                creature.get(
                    key
                )
            )

            # No usamos elementos demasiado malos
            # en la asignación final.
            if modifier < 60:
                continue

            charm = (
                CHARM_BY_ELEMENT[
                    element
                ]
            )

            score = (
                hp
                * modifier
                / 100
            )

            options.append(
                {
                    "charm":
                    charm,

                    "element":
                    element,

                    "modifier":
                    modifier,

                    "score":
                    score
                }
            )

        valid_creatures.append(
            {
                "name": name,
                "options": options
            }
        )

    # =====================================================
    # PROGRAMACIÓN DINÁMICA
    # =====================================================

    dp = {
        0: (
            0,
            []
        )
    }

    for creature in (
        valid_creatures
    ):

        new_dp = dict(
            dp
        )

        for (
            mask,
            (
                total_score,
                assignments
            )
        ) in dp.items():

            for option in (
                creature[
                    "options"
                ]
            ):

                index = charm_indexes[
                    option[
                        "charm"
                    ]
                ]

                bit = (
                    1 << index
                )

                if mask & bit:
                    continue

                new_mask = (
                    mask | bit
                )

                new_score = (
                    total_score
                    + option[
                        "score"
                    ]
                )

                assignment = {
                    "creature":
                    creature[
                        "name"
                    ],

                    **option
                }

                new_assignments = (
                    assignments
                    + [
                        assignment
                    ]
                )

                old = new_dp.get(
                    new_mask
                )

                if (
                    old is None
                    or new_score
                    > old[0]
                ):
                    new_dp[
                        new_mask
                    ] = (
                        new_score,
                        new_assignments
                    )

        dp = new_dp

    if not dp:
        return []

    best = max(
        dp.values(),
        key=lambda entry:
        entry[0]
    )

    return best[1]