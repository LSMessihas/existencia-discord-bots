import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = int(os.getenv("GUILD_ID", "0"))

COMMAND_CHANNEL_ID = int(
    os.getenv("COMMAND_CHANNEL_ID", "0")
)

SCHEDULE_CHANNEL_ID = int(
    os.getenv("SCHEDULE_CHANNEL_ID", "0")
)

RENT_CHANNEL_ID = int(
    os.getenv("RENT_CHANNEL_ID", "0")
)

MEMBER_ROLE = os.getenv(
    "MEMBER_ROLE",
    "GH Member"
)

RENTER_ROLE = os.getenv(
    "RENTER_ROLE",
    "GH Renter"
)

ADMIN_ROLE = os.getenv(
    "ADMIN_ROLE",
    "GH Manager"
)

MAX_MEMBER_HOURS = int(
    os.getenv("MAX_MEMBER_HOURS", "4")
)

MAX_RENTER_HOURS = int(
    os.getenv("MAX_RENTER_HOURS", "8")
)

DEFAULT_DUMMY_PRICE = int(
    os.getenv("DEFAULT_DUMMY_PRICE", "25")
)

DATABASE_FILE = "bookings.db"

TIMEZONE = ZoneInfo("Europe/Madrid")

GUILD_OBJECT = discord.Object(id=GUILD_ID)


# =========================================================
# DISCORD
# =========================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

comandos_sincronizados = False


# =========================================================
# DATE / TIME
# =========================================================

def ahora():
    return datetime.now(TIMEZONE)


MESES = {
    1: "JANUARY",
    2: "FEBRUARY",
    3: "MARCH",
    4: "APRIL",
    5: "MAY",
    6: "JUNE",
    7: "JULY",
    8: "AUGUST",
    9: "SEPTEMBER",
    10: "OCTOBER",
    11: "NOVEMBER",
    12: "DECEMBER"
}


def mes_actual_db():
    fecha = ahora()

    return fecha.strftime("%Y-%m")


def mes_actual_visible():
    fecha = ahora()

    return f"{MESES[fecha.month]} {fecha.year}"


# =========================================================
# DATABASE
# =========================================================

def conectar_db():
    return sqlite3.connect(
        DATABASE_FILE
    )


def crear_db():

    conn = conectar_db()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # BOOKINGS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            dummy TEXT NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # CONFIGURATION / MENSAJES FIJOS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # -----------------------------------------------------
    # PAYMENTS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            user_name TEXT NOT NULL,

            payment_type TEXT NOT NULL,

            amount INTEGER NOT NULL DEFAULT 0,

            month TEXT NOT NULL,

            registered_by INTEGER NOT NULL,

            registered_at TEXT NOT NULL,

            UNIQUE (
                user_id,
                payment_type,
                month
            )
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# SETTINGS
# =========================================================

def obtener_setting(key):

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT value
        FROM settings
        WHERE key = ?
    """, (
        key,
    ))

    resultado = cursor.fetchone()

    conn.close()

    if resultado:
        return resultado[0]

    return None


def guardar_setting(
    key,
    value
):

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO settings (
            key,
            value
        )
        VALUES (?, ?)
    """, (
        key,
        str(value)
    ))

    conn.commit()
    conn.close()


# =========================================================
# ROLEES
# =========================================================

def nombres_roles(member):

    return [
        role.name
        for role in member.roles
    ]


def obtener_tipo_usuario(
    interaction
):

    if not isinstance(
        interaction.user,
        discord.Member
    ):
        return None

    roles = nombres_roles(
        interaction.user
    )

    # Renter takes priority if the user has both roles
    if RENTER_ROLE in roles:
        return "renter"

    if MEMBER_ROLE in roles:
        return "member"

    return None


def es_gestor(
    interaction
):

    if not isinstance(
        interaction.user,
        discord.Member
    ):
        return False

    return ADMIN_ROLE in nombres_roles(
        interaction.user
    )


def obtener_limite_horas(
    tipo
):

    if tipo == "renter":
        return MAX_RENTER_HOURS

    if tipo == "member":
        return MAX_MEMBER_HOURS

    return 0


def nombre_tipo_usuario(
    tipo
):

    if tipo == "renter":
        return "GH Renter"

    if tipo == "member":
        return "GH Member"

    return "No Access"


async def dar_rol(
    member,
    nombre_rol
):

    guild = member.guild

    rol = discord.utils.get(
        guild.roles,
        name=nombre_rol
    )

    if rol is None:
        return False, (
            f"I cannot find the role "
            f"`{nombre_rol}`."
        )

    if rol in member.roles:
        return True, "The user already had the role."

    try:

        await member.add_roles(
            rol,
            reason="Automatic GH management"
        )

        return True, "Role added."

    except discord.Forbidden:

        return False, (
            "The bot does not have permission to "
            f"assign `{nombre_rol}`.\n"
            "Check the role hierarchy."
        )


async def quitar_rol(
    member,
    nombre_rol
):

    guild = member.guild

    rol = discord.utils.get(
        guild.roles,
        name=nombre_rol
    )

    if rol is None:
        return False, (
            f"I cannot find the role "
            f"`{nombre_rol}`."
        )

    if rol not in member.roles:
        return True, "The user did not have the role."

    try:

        await member.remove_roles(
            rol,
            reason="Automatic GH management"
        )

        return True, "Role removed."

    except discord.Forbidden:

        return False, (
            "The bot does not have permission to "
            f"remove `{nombre_rol}`."
        )


# =========================================================
# CHANNELS
# =========================================================

def canal_reservas_correcto(
    interaction
):

    return (
        interaction.channel_id
        == COMMAND_CHANNEL_ID
    )


def canal_renta_correcto(
    interaction
):

    return (
        interaction.channel_id
        == RENT_CHANNEL_ID
    )


# =========================================================
# BOOKINGS - FUNCIONES
# =========================================================

def convertir_fecha(
    fecha_texto
):

    formatos = [
        "%d/%m",
        "%d/%m/%Y"
    ]

    for formato in formatos:

        try:

            fecha = datetime.strptime(
                fecha_texto,
                formato
            )

            if formato == "%d/%m":

                fecha = fecha.replace(
                    year=ahora().year
                )

            return fecha

        except ValueError:
            continue

    return None


def convertir_hora(
    hora_texto
):

    try:

        return datetime.strptime(
            hora_texto,
            "%H:%M"
        )

    except ValueError:

        return None


def calcular_duracion_horas(
    inicio,
    fin
):

    diferencia = fin - inicio

    return (
        diferencia.total_seconds()
        / 3600
    )


def existe_solapamiento(
    dummy,
    fecha,
    inicio,
    fin
):

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            user_id,
            user_name,
            start_time,
            end_time

        FROM bookings

        WHERE dummy = ?
        AND date = ?
        AND start_time < ?
        AND end_time > ?
    """, (
        dummy,
        fecha,
        fin,
        inicio
    ))

    resultado = cursor.fetchone()

    conn.close()

    return resultado


def guardar_reserva(
    user_id,
    user_name,
    dummy,
    fecha,
    inicio,
    fin
):

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bookings (
            user_id,
            user_name,
            dummy,
            date,
            start_time,
            end_time,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        user_name,
        dummy,
        fecha,
        inicio,
        fin,
        ahora().isoformat()
    ))

    reserva_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return reserva_id


def obtener_reservas():

    conn = conectar_db()
    cursor = conn.cursor()

    hoy = ahora().strftime(
        "%Y-%m-%d"
    )

    cursor.execute("""
        SELECT
            id,
            user_id,
            user_name,
            dummy,
            date,
            start_time,
            end_time

        FROM bookings

        WHERE date >= ?

        ORDER BY
            date ASC,
            dummy ASC,
            start_time ASC
    """, (
        hoy,
    ))

    resultado = cursor.fetchall()

    conn.close()

    return resultado


def obtener_reserva_usuario(
    reserva_id,
    user_id
):

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *

        FROM bookings

        WHERE id = ?
        AND user_id = ?
    """, (
        reserva_id,
        user_id
    ))

    resultado = cursor.fetchone()

    conn.close()

    return resultado


def borrar_reserva(
    reserva_id
):

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM bookings
        WHERE id = ?
    """, (
        reserva_id,
    ))

    conn.commit()
    conn.close()


# =========================================================
# PAYMENTS - FUNCIONES
# =========================================================

def registrar_pago(
    user_id,
    user_name,
    tipo,
    cantidad,
    registrado_por
):

    mes = mes_actual_db()

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO payments (
            user_id,
            user_name,
            payment_type,
            amount,
            month,
            registered_by,
            registered_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(
            user_id,
            payment_type,
            month
        )

        DO UPDATE SET
            user_name = excluded.user_name,
            amount = excluded.amount,
            registered_by = excluded.registered_by,
            registered_at = excluded.registered_at
    """, (
        user_id,
        user_name,
        tipo,
        cantidad,
        mes,
        registrado_por,
        ahora().isoformat()
    ))

    conn.commit()
    conn.close()


def eliminar_pago(
    user_id,
    tipo
):

    mes = mes_actual_db()

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM payments

        WHERE user_id = ?
        AND payment_type = ?
        AND month = ?
    """, (
        user_id,
        tipo,
        mes
    ))

    eliminado = (
        cursor.rowcount > 0
    )

    conn.commit()
    conn.close()

    return eliminado


def obtener_pagos_mes_actual():

    mes = mes_actual_db()

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            user_id,
            user_name,
            payment_type,
            amount,
            registered_by,
            registered_at

        FROM payments

        WHERE month = ?

        ORDER BY
            payment_type ASC,
            user_name ASC
    """, (
        mes,
    ))

    resultado = cursor.fetchall()

    conn.close()

    return resultado


# =========================================================
# BOOKING PANEL
# =========================================================

async def actualizar_panel_reservas():

    canal = bot.get_channel(
        SCHEDULE_CHANNEL_ID
    )

    if canal is None:

        print(
            "ERROR: I cannot find the "
            "booking channel."
        )

        return

    reservas = obtener_reservas()

    embed = discord.Embed(
        title="🏋️ Dummy Bookings",
        description=(
            "Official booking calendar "
            "for the **Existencia Guild House**.\n\n"
            "Use `/book` in the Guild House "
            "commands channel to create a booking."
        )
    )

    if not reservas:

        embed.add_field(
            name="📅 Bookings",
            value=(
                "There are currently no "
                "bookings."
            ),
            inline=False
        )

    else:

        fechas = {}

        for reserva in reservas:

            (
                reserva_id,
                user_id,
                user_name,
                dummy,
                fecha,
                inicio,
                fin
            ) = reserva

            fechas.setdefault(
                fecha,
                {}
            )

            fechas[fecha].setdefault(
                dummy,
                []
            )

            fechas[fecha][dummy].append(
                {
                    "id": reserva_id,
                    "user_id": user_id,
                    "inicio": inicio,
                    "fin": fin
                }
            )

        for fecha_db, dummies in list(
            fechas.items()
        )[:25]:

            fecha_obj = datetime.strptime(
                fecha_db,
                "%Y-%m-%d"
            )

            fecha_visible = (
                fecha_obj.strftime(
                    "%d/%m/%Y"
                )
            )

            texto = ""

            for dummy, lista in dummies.items():

                texto += (
                    f"**🏋️ {dummy}**\n"
                )

                for reserva in lista:

                    texto += (
                        f"`{reserva['inicio']} → "
                        f"{reserva['fin']}` "
                        f"<@{reserva['user_id']}> "
                        f"• ID `{reserva['id']}`\n"
                    )

                texto += "\n"

            embed.add_field(
                name=f"📅 {fecha_visible}",
                value=texto,
                inline=False
            )

    embed.set_footer(
        text=(
            "GH Existencia • "
            "Automatic update"
        )
    )

    message_id = obtener_setting(
        "schedule_message_id"
    )

    if message_id:

        try:

            mensaje = await canal.fetch_message(
                int(message_id)
            )

            await mensaje.edit(
                content=None,
                embed=embed
            )

            return

        except discord.NotFound:
            pass

        except discord.Forbidden:

            print(
                "ERROR: I cannot edit "
                "the booking panel."
            )

            return

    mensaje = await canal.send(
        embed=embed
    )

    guardar_setting(
        "schedule_message_id",
        mensaje.id
    )


# =========================================================
# PAYMENT PANEL
# =========================================================

async def actualizar_panel_pagos():

    canal = bot.get_channel(
        RENT_CHANNEL_ID
    )

    if canal is None:

        print(
            "ERROR: No encuentro "
            "the GH rent channel."
        )

        return

    pagos = obtener_pagos_mes_actual()

    pagos_renta = []
    pagos_dummy = []

    total_renta = 0
    total_tc = 0

    for pago in pagos:

        (
            pago_id,
            user_id,
            user_name,
            tipo,
            cantidad,
            registered_by,
            registered_at
        ) = pago

        if tipo == "renta":

            pagos_renta.append(
                pago
            )

            total_renta += cantidad

        elif tipo == "dummy":

            pagos_dummy.append(
                pago
            )

            total_tc += cantidad

    embed = discord.Embed(
        title=(
            f"💰 GH Management — "
            f"{mes_actual_visible()}"
        ),
        description=(
            "Monthly payment record "
            "for the Guild House."
        )
    )

    # -----------------------------------------------------
    # RENT
    # -----------------------------------------------------

    if pagos_renta:

        texto_renta = ""

        for pago in pagos_renta:

            (
                pago_id,
                user_id,
                user_name,
                tipo,
                cantidad,
                registered_by,
                registered_at
            ) = pago

            if cantidad > 0:

                cantidad_texto = (
                    f"{cantidad:,}"
                    .replace(",", ".")
                    + " gp"
                )

            else:

                cantidad_texto = "Paid"

            texto_renta += (
                f"✅ <@{user_id}> "
                f"— **{cantidad_texto}**\n"
            )

    else:

        texto_renta = (
            "There are no rent payments "
            "registered yet."
        )

    embed.add_field(
        name="🏠 GH Renters — Rent",
        value=texto_renta,
        inline=False
    )

    # -----------------------------------------------------
    # DUMMY
    # -----------------------------------------------------

    if pagos_dummy:

        texto_dummy = ""

        for pago in pagos_dummy:

            (
                pago_id,
                user_id,
                user_name,
                tipo,
                cantidad,
                registered_by,
                registered_at
            ) = pago

            texto_dummy += (
                f"✅ <@{user_id}> "
                f"— **{cantidad} TC**\n"
            )

    else:

        texto_dummy = (
            "There are no Dummy access payments "
            "registered yet."
        )

    embed.add_field(
        name="🏋️ Dummy Access",
        value=texto_dummy,
        inline=False
    )

    # -----------------------------------------------------
    # TOTALS
    # -----------------------------------------------------

    total_renta_texto = (
        f"{total_renta:,}"
        .replace(",", ".")
    )

    embed.add_field(
        name="📊 Summary",
        value=(
            f"🏠 Rent-paying members: "
            f"**{len(pagos_renta)}**\n"
            f"💰 Registered rent: "
            f"**{total_renta_texto} gp**\n\n"
            f"🏋️ Dummy payments: "
            f"**{len(pagos_dummy)}**\n"
            f"💎 TC generated: "
            f"**{total_tc} TC**"
        ),
        inline=False
    )

    embed.set_footer(
        text=(
            "GH Existencia • "
            "Payments are tracked monthly"
        )
    )

    message_id = obtener_setting(
        "rent_message_id"
    )

    if message_id:

        try:

            mensaje = await canal.fetch_message(
                int(message_id)
            )

            await mensaje.edit(
                content=None,
                embed=embed
            )

            return

        except discord.NotFound:
            pass

        except discord.Forbidden:

            print(
                "ERROR: I cannot edit "
                "the rent panel."
            )

            return

    mensaje = await canal.send(
        embed=embed
    )

    guardar_setting(
        "rent_message_id",
        mensaje.id
    )


# =========================================================
# /BOOK
# =========================================================

@bot.tree.command(
    name="book",
    description="Book a Guild House training dummy",
    guild=GUILD_OBJECT
)
@app_commands.describe(
    dummy="Select the dummy you want to book",
    fecha="Booking date, for example 22/08",
    inicio="Start time, for example 09:00",
    fin="End time, for example 13:00"
)
@app_commands.choices(
    dummy=[
        app_commands.Choice(
            name="Dummy 1",
            value="Dummy 1"
        )
    ]
)
async def book(
    interaction: discord.Interaction,
    dummy: app_commands.Choice[str],
    fecha: str,
    inicio: str,
    fin: str
):

    # CHANNEL
    if not canal_reservas_correcto(
        interaction
    ):

        await interaction.response.send_message(
            "❌ Use `/book` in the Guild House "
            "commands channel.",
            ephemeral=True
        )

        return

    # ROLE
    tipo_usuario = obtener_tipo_usuario(
        interaction
    )

    if tipo_usuario is None:

        await interaction.response.send_message(
            "❌ You do not have access to "
            "bookings.\n\n"
            f"You need **{RENTER_ROLE}** "
            f"or **{MEMBER_ROLE}**.",
            ephemeral=True
        )

        return

    limite_horas = obtener_limite_horas(
        tipo_usuario
    )

    # DATE
    fecha_obj = convertir_fecha(
        fecha
    )

    if fecha_obj is None:

        await interaction.response.send_message(
            "❌ Invalid date.\n\n"
            "Use `DD/MM`.\n"
            "Example: `22/08`",
            ephemeral=True
        )

        return

    fecha_db = fecha_obj.strftime(
        "%Y-%m-%d"
    )

    if (
        fecha_obj.date()
        < ahora().date()
    ):

        await interaction.response.send_message(
            "❌ You cannot book "
            "a past date.",
            ephemeral=True
        )

        return

    # TIMES
    inicio_obj = convertir_hora(
        inicio
    )

    fin_obj = convertir_hora(
        fin
    )

    if (
        inicio_obj is None
        or fin_obj is None
    ):

        await interaction.response.send_message(
            "❌ Invalid time.\n\n"
            "Use `HH:MM`.\n"
            "Example: `09:00`",
            ephemeral=True
        )

        return

    if fin_obj <= inicio_obj:

        await interaction.response.send_message(
            "❌ The end time must be "
            "later than the start time.",
            ephemeral=True
        )

        return

    # IF TODAY, DO NOT ALLOW PAST TIMES
    if (
        fecha_obj.date()
        == ahora().date()
    ):

        inicio_hoy = datetime(
            year=ahora().year,
            month=ahora().month,
            day=ahora().day,
            hour=inicio_obj.hour,
            minute=inicio_obj.minute,
            tzinfo=TIMEZONE
        )

        if inicio_hoy <= ahora():

            await interaction.response.send_message(
                "❌ That time slot has already "
                "started or passed.",
                ephemeral=True
            )

            return

    # DURATION
    duracion = calcular_duracion_horas(
        inicio_obj,
        fin_obj
    )

    if duracion > limite_horas:

        await interaction.response.send_message(
            f"❌ You exceed your booking limit.\n\n"
            f"👤 **{nombre_tipo_usuario(tipo_usuario)}**\n"
            f"⏱️ Maximum: **{limite_horas} hours**\n"
            f"🕐 Requested: **{duracion:g} hours**",
            ephemeral=True
        )

        return

    dummy_nombre = dummy.value

    # OVERLAP
    conflicto = existe_solapamiento(
        dummy_nombre,
        fecha_db,
        inicio,
        fin
    )

    if conflicto:

        (
            reserva_id,
            user_id,
            user_name,
            inicio_existente,
            fin_existente
        ) = conflicto

        await interaction.response.send_message(
            f"❌ **{dummy_nombre} is already "
            f"booked.**\n\n"
            f"👤 <@{user_id}>\n"
            f"🕐 `{inicio_existente} → "
            f"{fin_existente}`\n"
            f"🔢 Booking `{reserva_id}`",
            ephemeral=True
        )

        return

    # SAVE
    reserva_id = guardar_reserva(
        interaction.user.id,
        interaction.user.display_name,
        dummy_nombre,
        fecha_db,
        inicio,
        fin
    )

    await interaction.response.send_message(
        f"✅ **Booking created.**\n\n"
        f"🏋️ **{dummy_nombre}**\n"
        f"📅 **{fecha_obj.strftime('%d/%m/%Y')}**\n"
        f"🕐 `{inicio} → {fin}`\n"
        f"👤 **{nombre_tipo_usuario(tipo_usuario)}**\n"
        f"🔢 Booking `{reserva_id}`",
        ephemeral=True
    )

    await actualizar_panel_reservas()


# =========================================================
# /CANCEL
# =========================================================

@bot.tree.command(
    name="cancel",
    description="Cancel one of your bookings",
    guild=GUILD_OBJECT
)
@app_commands.describe(
    reserva_id="ID of the booking you want to cancel"
)
async def cancel(
    interaction: discord.Interaction,
    reserva_id: int
):

    if not canal_reservas_correcto(
        interaction
    ):

        await interaction.response.send_message(
            "❌ Use this command in "
            "the GH commands channel.",
            ephemeral=True
        )

        return

    tipo = obtener_tipo_usuario(
        interaction
    )

    if tipo is None:

        await interaction.response.send_message(
            "❌ You do not have access "
            "to the booking system.",
            ephemeral=True
        )

        return

    reserva = obtener_reserva_usuario(
        reserva_id,
        interaction.user.id
    )

    if reserva is None:

        await interaction.response.send_message(
            "❌ You do not have a booking "
            "with that ID.",
            ephemeral=True
        )

        return

    borrar_reserva(
        reserva_id
    )

    await interaction.response.send_message(
        f"🗑️ Booking `{reserva_id}` "
        "cancelled successfully.",
        ephemeral=True
    )

    await actualizar_panel_reservas()


# =========================================================
# /SCHEDULE
# =========================================================

@bot.tree.command(
    name="schedule",
    description="Refresh the booking schedule",
    guild=GUILD_OBJECT
)
async def schedule(
    interaction: discord.Interaction
):

    tipo = obtener_tipo_usuario(
        interaction
    )

    if tipo is None:

        await interaction.response.send_message(
            "❌ You do not have access.",
            ephemeral=True
        )

        return

    await actualizar_panel_reservas()

    await interaction.response.send_message(
        "✅ Schedule updated.",
        ephemeral=True
    )


# =========================================================
# /PAGO
# =========================================================

@bot.tree.command(
    name="payment",
    description="Register a Guild House payment",
    guild=GUILD_OBJECT
)
@app_commands.describe(
    usuario="Player who made the payment",
    tipo="Payment type",
    cantidad="Amount paid. Optional."
)
@app_commands.choices(
    tipo=[
        app_commands.Choice(
            name="🏠 Rent",
            value="renta"
        ),
        app_commands.Choice(
            name="🏋️ Dummy",
            value="dummy"
        )
    ]
)
async def pago(
    interaction: discord.Interaction,
    usuario: discord.Member,
    tipo: app_commands.Choice[str],
    cantidad: int | None = None
):

    # MANAGER
    if not es_gestor(
        interaction
    ):

        await interaction.response.send_message(
            f"❌ Only the role "
            f"**{ADMIN_ROLE}** puede "
            "register payments.",
            ephemeral=True
        )

        return

    # CHANNEL
    if not canal_renta_correcto(
        interaction
    ):

        await interaction.response.send_message(
            "❌ Use `/payment` "
            "in the GH rent channel.",
            ephemeral=True
        )

        return

    tipo_pago = tipo.value

    # -----------------------------------------------------
    # AMOUNT
    # -----------------------------------------------------

    if cantidad is not None and cantidad < 0:

        await interaction.response.send_message(
            "❌ The amount cannot "
            "be negative.",
            ephemeral=True
        )

        return

    if tipo_pago == "dummy":

        if cantidad is None:
            cantidad = DEFAULT_DUMMY_PRICE

    elif tipo_pago == "renta":

        if cantidad is None:
            cantidad = 0

    # -----------------------------------------------------
    # REGISTER
    # -----------------------------------------------------

    registrar_pago(
        usuario.id,
        usuario.display_name,
        tipo_pago,
        cantidad,
        interaction.user.id
    )

    # -----------------------------------------------------
    # ASSIGN ROLE
    # -----------------------------------------------------

    if tipo_pago == "renta":

        rol_nombre = RENTER_ROLE

    else:

        rol_nombre = MEMBER_ROLE

    ok, mensaje_rol = await dar_rol(
        usuario,
        rol_nombre
    )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    if tipo_pago == "renta":

        if cantidad > 0:

            cantidad_texto = (
                f"{cantidad:,}"
                .replace(",", ".")
                + " gp"
            )

        else:

            cantidad_texto = "Paid"

        nombre_pago = "🏠 Rent"

    else:

        cantidad_texto = (
            f"{cantidad} TC"
        )

        nombre_pago = "🏋️ Dummy"

    if ok:

        estado_rol = (
            f"✅ Role **{rol_nombre}** active."
        )

    else:

        estado_rol = (
            f"⚠️ {mensaje_rol}"
        )

    await interaction.response.send_message(
        f"✅ **Payment registered.**\n\n"
        f"👤 {usuario.mention}\n"
        f"💰 {nombre_pago}\n"
        f"💵 **{cantidad_texto}**\n"
        f"📅 {mes_actual_visible()}\n\n"
        f"{estado_rol}",
        ephemeral=True
    )

    await actualizar_panel_pagos()


# =========================================================
# /RETIRARPAGO
# =========================================================

@bot.tree.command(
    name="removepayment",
    description="Remove a payment registered this month",
    guild=GUILD_OBJECT
)
@app_commands.describe(
    usuario="Player",
    tipo="Payment you want to remove"
)
@app_commands.choices(
    tipo=[
        app_commands.Choice(
            name="🏠 Rent",
            value="renta"
        ),
        app_commands.Choice(
            name="🏋️ Dummy",
            value="dummy"
        )
    ]
)
async def retirarpago(
    interaction: discord.Interaction,
    usuario: discord.Member,
    tipo: app_commands.Choice[str]
):

    if not es_gestor(
        interaction
    ):

        await interaction.response.send_message(
            f"❌ Solo **{ADMIN_ROLE}** "
            "can modify payments.",
            ephemeral=True
        )

        return

    if not canal_renta_correcto(
        interaction
    ):

        await interaction.response.send_message(
            "❌ Use this command "
            "in the GH rent channel.",
            ephemeral=True
        )

        return

    tipo_pago = tipo.value

    eliminado = eliminar_pago(
        usuario.id,
        tipo_pago
    )

    if not eliminado:

        await interaction.response.send_message(
            "❌ That user does not have "
            "that payment registered this month.",
            ephemeral=True
        )

        return

    if tipo_pago == "renta":

        rol_nombre = RENTER_ROLE

    else:

        rol_nombre = MEMBER_ROLE

    ok, mensaje_rol = await quitar_rol(
        usuario,
        rol_nombre
    )

    await interaction.response.send_message(
        f"🗑️ **Payment removed.**\n\n"
        f"👤 {usuario.mention}\n"
        f"📅 {mes_actual_visible()}\n"
        f"🎭 Role: **{rol_nombre}**",
        ephemeral=True
    )

    await actualizar_panel_pagos()


# =========================================================
# /PAGOS
# =========================================================

@bot.tree.command(
    name="payments",
    description="Refresh the GH payment panel",
    guild=GUILD_OBJECT
)
async def pagos(
    interaction: discord.Interaction
):

    if not es_gestor(
        interaction
    ):

        await interaction.response.send_message(
            f"❌ Solo **{ADMIN_ROLE}** "
            "can use this command.",
            ephemeral=True
        )

        return

    await actualizar_panel_pagos()

    await interaction.response.send_message(
        "✅ Payment panel updated.",
        ephemeral=True
    )


# =========================================================
# STARTUP
# =========================================================

@bot.event
async def on_ready():

    global comandos_sincronizados

    crear_db()

    if not comandos_sincronizados:

        # Removes old global versions
        # of /book, /cancel, etc.
        bot.tree.clear_commands(
            guild=None
        )

        await bot.tree.sync()

        # Immediately synchronizes
        # the Existencia commands.
        comandos = await bot.tree.sync(
            guild=GUILD_OBJECT
        )

        comandos_sincronizados = True

        print(
            f"{len(comandos)} commands "
            "synchronized."
        )

    print("--------------------------------")
    print(f"Bot connected as {bot.user}")
    print("--------------------------------")

    await actualizar_panel_reservas()

    await actualizar_panel_pagos()


# =========================================================
# VALIDATION
# =========================================================

if not TOKEN:
    raise ValueError(
        "Missing DISCORD_TOKEN in .env"
    )

if GUILD_ID == 0:
    raise ValueError(
        "Missing GUILD_ID in .env"
    )

if COMMAND_CHANNEL_ID == 0:
    raise ValueError(
        "Missing COMMAND_CHANNEL_ID in .env"
    )

if SCHEDULE_CHANNEL_ID == 0:
    raise ValueError(
        "Missing SCHEDULE_CHANNEL_ID in .env"
    )

if RENT_CHANNEL_ID == 0:
    raise ValueError(
        "Missing RENT_CHANNEL_ID in .env"
    )


# =========================================================
# START
# =========================================================

bot.run(TOKEN)
