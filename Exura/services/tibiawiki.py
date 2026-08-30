import aiohttp
from urllib.parse import quote


BASE_URL = "https://tibiawiki.dev/api"


# =========================================================
# PETICIÓN GENÉRICA
# =========================================================

async def _request_json(
    session: aiohttp.ClientSession,
    url: str
):
    async with session.get(url) as response:

        if response.status == 404:
            return None

        if response.status != 200:
            print(
                f"[TibiaWiki] Error HTTP "
                f"{response.status}: {url}"
            )
            return None

        return await response.json()


# =========================================================
# SESSION
# =========================================================

def _headers():
    return {
        "User-Agent": "Exura Discord Bot"
    }


def _timeout():
    return aiohttp.ClientTimeout(
        total=30
    )


# =========================================================
# CRIATURA INDIVIDUAL
# =========================================================

async def _request_creature(
    session: aiohttp.ClientSession,
    creature_name: str
):
    encoded_name = quote(
        creature_name.strip()
    )

    url = (
        f"{BASE_URL}/creatures/"
        f"{encoded_name}"
    )

    data = await _request_json(
        session,
        url
    )

    if not data:
        return None

    if isinstance(
        data,
        dict
    ):

        if (
            "creature" in data
            and isinstance(
                data["creature"],
                dict
            )
        ):
            return data["creature"]

        if (
            "data" in data
            and isinstance(
                data["data"],
                dict
            )
        ):
            return data["data"]

    return data


async def get_wiki_creature(
    name: str
):
    creature_name = name.strip()

    if not creature_name:
        return None

    try:
        async with aiohttp.ClientSession(
            headers=_headers(),
            timeout=_timeout()
        ) as session:

            # Nombre exacto
            data = await _request_creature(
                session,
                creature_name
            )

            if data:
                return data

            # TibiaData usa algunos plurales:
            # Grim Reapers -> Grim Reaper
            if (
                creature_name
                .lower()
                .endswith("s")
            ):

                singular_name = (
                    creature_name[:-1]
                )

                data = await _request_creature(
                    session,
                    singular_name
                )

                if data:
                    return data

            return None

    except aiohttp.ClientError as error:
        print(
            f"[TibiaWiki] Error buscando "
            f"{creature_name}: {error}"
        )
        return None

    except TimeoutError:
        print(
            f"[TibiaWiki] Timeout buscando "
            f"{creature_name}"
        )
        return None

    except Exception as error:
        print(
            f"[TibiaWiki] Error inesperado: "
            f"{error}"
        )
        return None


# =========================================================
# LISTA COMPLETA DE BOSSES
# =========================================================

async def get_bosses_list():
    """
    Descarga las criaturas completas y conserva
    únicamente las marcadas como boss.
    """

    url = (
        f"{BASE_URL}/creatures"
        f"?expand=true"
    )

    try:
        async with aiohttp.ClientSession(
            headers=_headers(),
            timeout=aiohttp.ClientTimeout(
                total=60
            )
        ) as session:

            data = await _request_json(
                session,
                url
            )

            if not data:
                return []

            if isinstance(
                data,
                dict
            ):
                for key in (
                    "creatures",
                    "data"
                ):
                    possible = data.get(
                        key
                    )

                    if isinstance(
                        possible,
                        list
                    ):
                        data = possible
                        break

            if not isinstance(
                data,
                list
            ):
                return []

            bosses = []

            for creature in data:

                if not isinstance(
                    creature,
                    dict
                ):
                    continue

                is_boss = creature.get(
                    "isboss"
                )

                if is_boss is None:
                    is_boss = creature.get(
                        "isBoss"
                    )

                normalized = str(
                    is_boss
                ).strip().lower()

                if normalized in (
                    "yes",
                    "true",
                    "1"
                ):
                    bosses.append(
                        creature
                    )

            bosses.sort(
                key=lambda boss: str(
                    boss.get(
                        "name",
                        ""
                    )
                ).lower()
            )

            return bosses

    except Exception as error:
        print(
            "[TibiaWiki] Error cargando "
            f"lista de bosses: {error}"
        )
        return []


# =========================================================
# BOSS INDIVIDUAL
# =========================================================

async def get_wiki_boss(
    name: str
):
    data = await get_wiki_creature(
        name
    )

    if not isinstance(
        data,
        dict
    ):
        return None

    is_boss = data.get(
        "isboss"
    )

    if is_boss is None:
        is_boss = data.get(
            "isBoss"
        )

    normalized = str(
        is_boss
    ).strip().lower()

    # Permitimos también bosses antiguos cuyo
    # campo no venga informado correctamente.
    if normalized in (
        "no",
        "false",
        "0"
    ):
        return None

    return data


# =========================================================
# ITEMS
# =========================================================

async def get_items_list():
    url = f"{BASE_URL}/items"

    try:
        async with aiohttp.ClientSession(
            headers=_headers(),
            timeout=_timeout()
        ) as session:

            data = await _request_json(
                session,
                url
            )

            if not data:
                return []

            if isinstance(
                data,
                list
            ):
                return data

            if isinstance(
                data,
                dict
            ):

                for key in (
                    "items",
                    "item_list",
                    "data"
                ):
                    value = data.get(
                        key
                    )

                    if isinstance(
                        value,
                        list
                    ):
                        return value

            return []

    except Exception as error:
        print(
            f"[TibiaWiki] Error cargando "
            f"items: {error}"
        )

        return []


async def _request_item(
    session: aiohttp.ClientSession,
    item_name: str
):
    encoded_name = quote(
        item_name.strip()
    )

    url = (
        f"{BASE_URL}/items/"
        f"{encoded_name}"
    )

    data = await _request_json(
        session,
        url
    )

    if not data:
        return None

    if isinstance(
        data,
        dict
    ):

        if (
            "item" in data
            and isinstance(
                data["item"],
                dict
            )
        ):
            return data["item"]

        if (
            "data" in data
            and isinstance(
                data["data"],
                dict
            )
        ):
            return data["data"]

    return data


async def get_wiki_item(
    name: str
):
    item_name = name.strip()

    if not item_name:
        return None

    try:
        async with aiohttp.ClientSession(
            headers=_headers(),
            timeout=_timeout()
        ) as session:

            return await _request_item(
                session,
                item_name
            )

    except aiohttp.ClientError as error:
        print(
            f"[TibiaWiki] Error buscando "
            f"{item_name}: {error}"
        )
        return None

    except TimeoutError:
        print(
            f"[TibiaWiki] Timeout buscando "
            f"{item_name}"
        )
        return None

    except Exception as error:
        print(
            f"[TibiaWiki] Error inesperado "
            f"buscando {item_name}: {error}"
        )
        return None