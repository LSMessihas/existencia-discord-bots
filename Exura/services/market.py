import aiohttp
import statistics
from datetime import datetime


BASE_URL = "https://api.tibiamarket.top"

DEFAULT_WORLD = "Celesta"


async def _get_json(
    endpoint: str,
    params: dict | None = None
):
    url = f"{BASE_URL}{endpoint}"

    timeout = aiohttp.ClientTimeout(
        total=15
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
                url,
                params=params
            ) as response:

                if response.status == 404:
                    return None

                if response.status == 429:
                    print(
                        "[Market] Rate limit alcanzado."
                    )
                    return {
                        "rate_limited": True
                    }

                if response.status != 200:
                    print(
                        f"[Market] Error HTTP "
                        f"{response.status}: "
                        f"{await response.text()}"
                    )

                    return None

                return await response.json()

    except aiohttp.ClientError as error:

        print(
            f"[Market] Error de conexión: "
            f"{error}"
        )

        return None

    except TimeoutError:

        print(
            "[Market] Timeout consultando "
            "TibiaMarket."
        )

        return None

    except Exception as error:

        print(
            f"[Market] Error inesperado: "
            f"{error}"
        )

        return None


# =========================================================
# PRECIO ACTUAL
# =========================================================

async def get_market_price(
    item_id: int,
    world: str = DEFAULT_WORLD
):
    """
    Obtiene el precio actual de un item
    para un mundo concreto.
    """

    data = await _get_json(
        "/market_values",
        params={
            "server": world,
            "item_ids": str(item_id),
            "limit": 1
        }
    )

    if not data:
        return None

    if isinstance(
        data,
        dict
    ) and data.get(
        "rate_limited"
    ):

        return {
            "rate_limited": True
        }

    if not isinstance(
        data,
        list
    ):

        return None

    if not data:
        return None

    value = data[0]

    return {
        "world": world,

        "item_id": value.get(
            "id",
            item_id
        ),

        "sell_offer": value.get(
            "sell_offer"
        ),

        "buy_offer": value.get(
            "buy_offer"
        ),

        "avg_sell_price": value.get(
            "avg_sell_price"
        ),

        "avg_buy_price": value.get(
            "avg_buy_price"
        ),

        "sold": value.get(
            "sold"
        ),

        "bought": value.get(
            "bought"
        ),

        "active_traders": value.get(
            "active_traders"
        ),

        "time": value.get(
            "time"
        )
    }


# =========================================================
# HISTORIAL
# =========================================================

async def get_market_history(
    item_id: int,
    world: str = DEFAULT_WORLD,
    days: int = 30
):
    data = await _get_json(
        "/item_history",
        params={
            "server": world,
            "item_id": item_id,
            "start_days_ago": days
        }
    )

    if not isinstance(
        data,
        list
    ):

        return []

    return data


# =========================================================
# PRECIO MEDIO RECIENTE
# =========================================================

async def get_recent_average(
    item_id: int,
    world: str = DEFAULT_WORLD,
    days: int = 30
):
    """
    Calcula una mediana reciente utilizando
    el historial disponible del mundo.

    Se usa mediana en vez de media para evitar
    que ofertas absurdas distorsionen el precio.
    """

    history = await get_market_history(
        item_id=item_id,
        world=world,
        days=days
    )

    if not history:
        return None

    sell_prices = []
    buy_prices = []

    for entry in history:

        sell = entry.get(
            "sell_offer"
        )

        buy = entry.get(
            "buy_offer"
        )

        if isinstance(
            sell,
            (int, float)
        ) and sell > 0:

            sell_prices.append(
                sell
            )

        if isinstance(
            buy,
            (int, float)
        ) and buy > 0:

            buy_prices.append(
                buy
            )

    result = {
        "world": world,
        "days": days,
        "samples": len(
            history
        ),
        "median_sell": None,
        "median_buy": None
    }

    if sell_prices:

        result[
            "median_sell"
        ] = int(
            statistics.median(
                sell_prices
            )
        )

    if buy_prices:

        result[
            "median_buy"
        ] = int(
            statistics.median(
                buy_prices
            )
        )

    return result


# =========================================================
# WORLD DATA
# =========================================================

async def get_world_data(
    world: str
):
    data = await _get_json(
        "/world_data",
        params={
            "servers": world
        }
    )

    if (
        not isinstance(
            data,
            list
        )
        or not data
    ):

        return None

    return data[0]


# =========================================================
# FORMATEO
# =========================================================

def format_gold(
    value
):
    if value in (
        None,
        0,
        "0"
    ):

        return "Sin datos"

    try:

        value = int(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return str(
            value
        )

    if value >= 1_000_000_000:

        return (
            f"{value / 1_000_000_000:.2f}kkk"
        )

    if value >= 1_000_000:

        return (
            f"{value / 1_000_000:.2f}kk"
        )

    if value >= 1_000:

        return (
            f"{value / 1_000:.1f}k"
        )

    return f"{value:,} gp"


def format_market_timestamp(
    timestamp
):
    if not timestamp:
        return "?"

    try:

        date = datetime.fromtimestamp(
            float(timestamp)
        )

        return date.strftime(
            "%d/%m/%Y %H:%M"
        )

    except (
        ValueError,
        TypeError,
        OSError
    ):

        return str(
            timestamp
        )