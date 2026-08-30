import aiohttp
from urllib.parse import quote


BASE_URL = "https://api.tibiadata.com/v4"


# =========================================================
# PETICIÓN GENÉRICA
# =========================================================

async def _get_json(url: str):
    timeout = aiohttp.ClientTimeout(
        total=20
    )

    headers = {
        "User-Agent": "Exura Discord Bot"
    }

    try:
        async with aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        ) as session:

            async with session.get(
                url
            ) as response:

                if response.status == 404:
                    return None

                if response.status != 200:
                    print(
                        f"[TibiaData] Error HTTP "
                        f"{response.status}: {url}"
                    )
                    return None

                return await response.json()

    except aiohttp.ClientError as error:
        print(
            f"[TibiaData] Error de conexión: "
            f"{error}"
        )
        return None

    except TimeoutError:
        print(
            "[TibiaData] Timeout."
        )
        return None

    except Exception as error:
        print(
            f"[TibiaData] Error inesperado: "
            f"{error}"
        )
        return None


# =========================================================
# PERSONAJES
# =========================================================

async def get_character(
    name: str
):
    encoded_name = quote(
        name.strip()
    )

    url = (
        f"{BASE_URL}/character/"
        f"{encoded_name}"
    )

    return await _get_json(
        url
    )


# =========================================================
# GUILDS
# =========================================================

async def get_guild(
    name: str
):
    guild_name = (
        name.strip()
    )

    if not guild_name:
        return None

    encoded_name = quote(
        guild_name
    )

    url = (
        f"{BASE_URL}/guild/"
        f"{encoded_name}"
    )

    return await _get_json(
        url
    )


# =========================================================
# CRIATURAS
# =========================================================

async def get_creatures_data():
    url = (
        f"{BASE_URL}/creatures"
    )

    return await _get_json(
        url
    )


async def get_creatures_list():
    data = await get_creatures_data()

    if not data:
        return []

    try:
        return (
            data
            .get(
                "creatures",
                {}
            )
            .get(
                "creature_list",
                []
            )
        )

    except (
        AttributeError,
        TypeError
    ):
        return []


# =========================================================
# BOOSTED CREATURE
# =========================================================

async def get_boosted_creature():
    data = await get_creatures_data()

    if not isinstance(
        data,
        dict
    ):
        return None

    creatures = data.get(
        "creatures",
        {}
    )

    if not isinstance(
        creatures,
        dict
    ):
        return None

    boosted = creatures.get(
        "boosted"
    )

    if isinstance(
        boosted,
        dict
    ):
        return boosted

    return None


# =========================================================
# BOOSTABLE BOSSES
# =========================================================

async def get_boostable_bosses():
    url = (
        f"{BASE_URL}/boostablebosses"
    )

    return await _get_json(
        url
    )


async def get_boosted_boss():
    data = await get_boostable_bosses()

    if not isinstance(
        data,
        dict
    ):
        return None

    root = data.get(
        "boostable_bosses",
        {}
    )

    if not isinstance(
        root,
        dict
    ):
        return None

    boosted = root.get(
        "boosted"
    )

    if isinstance(
        boosted,
        dict
    ):
        return boosted

    return None


def extract_boosted_boss_names(
    data
):
    if not isinstance(
        data,
        dict
    ):
        return []

    root = data.get(
        "boostable_bosses",
        {}
    )

    if not isinstance(
        root,
        dict
    ):
        return []

    boosted = root.get(
        "boosted"
    )

    if not isinstance(
        boosted,
        dict
    ):
        return []

    name = boosted.get(
        "name"
    )

    if not name:
        return []

    return [
        str(name).strip()
    ]