import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


# =========================================================
# CONFIGURACIÓN
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
    "Miembro GH"
)

RENTER_ROLE = os.getenv(
    "RENTER_ROLE",
    "Socio GH"
)

ADMIN_ROLE = os.getenv(
    "ADMIN_ROLE",
    "Gestor GH"
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
# FECHA / HORA
# =========================================================

def ahora():
    return datetime.now(TIMEZONE)


MESES = {
    1: "ENERO",
    2: "FEBRERO",
    3: "MARZO",
    4: "ABRIL",
    5: "MAYO",
    6: "JUNIO",
    7: "JULIO",
    8: "AGOSTO",
    9: "SEPTIEMBRE",
    10: "OCTUBRE",
    11: "NOVIEMBRE",
    12: "DICIEMBRE"
}


def mes_actual_db():
    fecha = ahora()

    return fecha.strftime("%Y-%m")


def mes_actual_visible():
    fecha = ahora()

    return f"{MESES[fecha.month]} {fecha.year}"


# =========================================================
# BASE DE DATOS
# =========================================================

def conectar_db():
    return sqlite3.connect(
        DATABASE_FILE
    )


def crear_db():

    conn = conectar_db()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # RESERVAS
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
    # CONFIGURACIÓN / MENSAJES FIJOS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # -----------------------------------------------------
    # PAGOS
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
# ROLES
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

    # Socio tiene prioridad si tiene ambos
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
        return "Socio GH"

    if tipo == "member":
        return "Miembro GH"

    return "Sin acceso"


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
            f"No encuentro el rol "
            f"`{nombre_rol}`."
        )

    if rol in member.roles:
        return True, "Ya tenía el rol."

    try:

        await member.add_roles(
            rol,
            reason="Gestión automática GH"
        )

        return True, "Rol añadido."

    except discord.Forbidden:

        return False, (
            "El bot no tiene permiso para "
            f"asignar `{nombre_rol}`.\n"
            "Comprueba la jerarquía de roles."
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
            f"No encuentro el rol "
            f"`{nombre_rol}`."
        )

    if rol not in member.roles:
        return True, "No tenía el rol."

    try:

        await member.remove_roles(
            rol,
            reason="Gestión automática GH"
        )

        return True, "Rol retirado."

    except discord.Forbidden:

        return False, (
            "El bot no tiene permiso para "
            f"retirar `{nombre_rol}`."
        )


# =========================================================
# CANALES
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
# RESERVAS - FUNCIONES
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
# PAGOS - FUNCIONES
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
# PANEL DE RESERVAS
# =========================================================

async def actualizar_panel_reservas():

    canal = bot.get_channel(
        SCHEDULE_CHANNEL_ID
    )

    if canal is None:

        print(
            "ERROR: No encuentro el "
            "canal de reservas."
        )

        return

    reservas = obtener_reservas()

    embed = discord.Embed(
        title="🏋️ Reservas de Dummy",
        description=(
            "Calendario oficial de reservas "
            "de la **Guild House de Existencia**.\n\n"
            "Utiliza `/book` en el canal de "
            "comandos para realizar una reserva."
        )
    )

    if not reservas:

        embed.add_field(
            name="📅 Reservas",
            value=(
                "Actualmente no hay "
                "ninguna reserva."
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
            "Actualización automática"
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
                "ERROR: No puedo editar "
                "el panel de reservas."
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
# PANEL DE PAGOS
# =========================================================

async def actualizar_panel_pagos():

    canal = bot.get_channel(
        RENT_CHANNEL_ID
    )

    if canal is None:

        print(
            "ERROR: No encuentro "
            "el canal renta-gh."
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
            f"💰 Gestión GH — "
            f"{mes_actual_visible()}"
        ),
        description=(
            "Registro mensual de pagos "
            "de la Guild House."
        )
    )

    # -----------------------------------------------------
    # RENTA
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

                cantidad_texto = "Pagado"

            texto_renta += (
                f"✅ <@{user_id}> "
                f"— **{cantidad_texto}**\n"
            )

    else:

        texto_renta = (
            "Todavía no hay pagos "
            "de renta registrados."
        )

    embed.add_field(
        name="🏠 Socios GH — Renta",
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
            "Todavía no hay accesos "
            "de Dummy registrados."
        )

    embed.add_field(
        name="🏋️ Acceso Dummy",
        value=texto_dummy,
        inline=False
    )

    # -----------------------------------------------------
    # TOTALES
    # -----------------------------------------------------

    total_renta_texto = (
        f"{total_renta:,}"
        .replace(",", ".")
    )

    embed.add_field(
        name="📊 Resumen",
        value=(
            f"🏠 Socios pagando renta: "
            f"**{len(pagos_renta)}**\n"
            f"💰 Renta registrada: "
            f"**{total_renta_texto} gp**\n\n"
            f"🏋️ Pagos Dummy: "
            f"**{len(pagos_dummy)}**\n"
            f"💎 TC generadas: "
            f"**{total_tc} TC**"
        ),
        inline=False
    )

    embed.set_footer(
        text=(
            "GH Existencia • "
            "Los pagos se registran por mes"
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
                "ERROR: No puedo editar "
                "el panel de renta."
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
    description="Reserva una dummy de la Guild House",
    guild=GUILD_OBJECT
)
@app_commands.describe(
    dummy="Selecciona la dummy que quieres reservar",
    fecha="Fecha de la reserva, por ejemplo 22/08",
    inicio="Hora de inicio, por ejemplo 09:00",
    fin="Hora de finalización, por ejemplo 13:00"
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

    # CANAL
    if not canal_reservas_correcto(
        interaction
    ):

        await interaction.response.send_message(
            "❌ Utiliza `/book` en el canal "
            "de comandos de la Guild House.",
            ephemeral=True
        )

        return

    # ROL
    tipo_usuario = obtener_tipo_usuario(
        interaction
    )

    if tipo_usuario is None:

        await interaction.response.send_message(
            "❌ No tienes acceso a "
            "las reservas.\n\n"
            f"Necesitas **{RENTER_ROLE}** "
            f"o **{MEMBER_ROLE}**.",
            ephemeral=True
        )

        return

    limite_horas = obtener_limite_horas(
        tipo_usuario
    )

    # FECHA
    fecha_obj = convertir_fecha(
        fecha
    )

    if fecha_obj is None:

        await interaction.response.send_message(
            "❌ Fecha incorrecta.\n\n"
            "Utiliza `DD/MM`.\n"
            "Ejemplo: `22/08`",
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
            "❌ No puedes reservar "
            "una fecha pasada.",
            ephemeral=True
        )

        return

    # HORAS
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
            "❌ Hora incorrecta.\n\n"
            "Utiliza `HH:MM`.\n"
            "Ejemplo: `09:00`",
            ephemeral=True
        )

        return

    if fin_obj <= inicio_obj:

        await interaction.response.send_message(
            "❌ La hora final debe ser "
            "posterior a la inicial.",
            ephemeral=True
        )

        return

    # SI ES HOY, NO PERMITIR PASADO
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
                "❌ Ese horario ya "
                "ha comenzado o ha pasado.",
                ephemeral=True
            )

            return

    # DURACIÓN
    duracion = calcular_duracion_horas(
        inicio_obj,
        fin_obj
    )

    if duracion > limite_horas:

        await interaction.response.send_message(
            f"❌ Superas tu límite de reserva.\n\n"
            f"👤 **{nombre_tipo_usuario(tipo_usuario)}**\n"
            f"⏱️ Máximo: **{limite_horas} horas**\n"
            f"🕐 Solicitado: **{duracion:g} horas**",
            ephemeral=True
        )

        return

    dummy_nombre = dummy.value

    # SOLAPAMIENTO
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
            f"❌ **{dummy_nombre} ya "
            f"está reservada.**\n\n"
            f"👤 <@{user_id}>\n"
            f"🕐 `{inicio_existente} → "
            f"{fin_existente}`\n"
            f"🔢 Reserva `{reserva_id}`",
            ephemeral=True
        )

        return

    # GUARDAR
    reserva_id = guardar_reserva(
        interaction.user.id,
        interaction.user.display_name,
        dummy_nombre,
        fecha_db,
        inicio,
        fin
    )

    await interaction.response.send_message(
        f"✅ **Reserva creada.**\n\n"
        f"🏋️ **{dummy_nombre}**\n"
        f"📅 **{fecha_obj.strftime('%d/%m/%Y')}**\n"
        f"🕐 `{inicio} → {fin}`\n"
        f"👤 **{nombre_tipo_usuario(tipo_usuario)}**\n"
        f"🔢 Reserva `{reserva_id}`",
        ephemeral=True
    )

    await actualizar_panel_reservas()


# =========================================================
# /CANCEL
# =========================================================

@bot.tree.command(
    name="cancel",
    description="Cancela una de tus reservas",
    guild=GUILD_OBJECT
)
@app_commands.describe(
    reserva_id="ID de la reserva que quieres cancelar"
)
async def cancel(
    interaction: discord.Interaction,
    reserva_id: int
):

    if not canal_reservas_correcto(
        interaction
    ):

        await interaction.response.send_message(
            "❌ Utiliza este comando en "
            "el canal de comandos GH.",
            ephemeral=True
        )

        return

    tipo = obtener_tipo_usuario(
        interaction
    )

    if tipo is None:

        await interaction.response.send_message(
            "❌ No tienes acceso "
            "al sistema de reservas.",
            ephemeral=True
        )

        return

    reserva = obtener_reserva_usuario(
        reserva_id,
        interaction.user.id
    )

    if reserva is None:

        await interaction.response.send_message(
            "❌ No existe una reserva "
            "tuya con ese ID.",
            ephemeral=True
        )

        return

    borrar_reserva(
        reserva_id
    )

    await interaction.response.send_message(
        f"🗑️ Reserva `{reserva_id}` "
        "cancelada correctamente.",
        ephemeral=True
    )

    await actualizar_panel_reservas()


# =========================================================
# /SCHEDULE
# =========================================================

@bot.tree.command(
    name="schedule",
    description="Actualiza el calendario de reservas",
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
            "❌ No tienes acceso.",
            ephemeral=True
        )

        return

    await actualizar_panel_reservas()

    await interaction.response.send_message(
        "✅ Calendario actualizado.",
        ephemeral=True
    )


# =========================================================
# /PAGO
# =========================================================

@bot.tree.command(
    name="pago",
    description="Registra un pago de la Guild House",
    guild=GUILD_OBJECT
)
@app_commands.describe(
    usuario="Jugador que ha realizado el pago",
    tipo="Tipo de pago",
    cantidad="Cantidad pagada. Opcional."
)
@app_commands.choices(
    tipo=[
        app_commands.Choice(
            name="🏠 Renta",
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

    # GESTOR
    if not es_gestor(
        interaction
    ):

        await interaction.response.send_message(
            f"❌ Solo el rol "
            f"**{ADMIN_ROLE}** puede "
            "registrar pagos.",
            ephemeral=True
        )

        return

    # CANAL
    if not canal_renta_correcto(
        interaction
    ):

        await interaction.response.send_message(
            "❌ Utiliza `/pago` "
            "en el canal de renta GH.",
            ephemeral=True
        )

        return

    tipo_pago = tipo.value

    # -----------------------------------------------------
    # CANTIDAD
    # -----------------------------------------------------

    if cantidad is not None and cantidad < 0:

        await interaction.response.send_message(
            "❌ La cantidad no puede "
            "ser negativa.",
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
    # REGISTRAR
    # -----------------------------------------------------

    registrar_pago(
        usuario.id,
        usuario.display_name,
        tipo_pago,
        cantidad,
        interaction.user.id
    )

    # -----------------------------------------------------
    # ASIGNAR ROL
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
    # RESPUESTA
    # -----------------------------------------------------

    if tipo_pago == "renta":

        if cantidad > 0:

            cantidad_texto = (
                f"{cantidad:,}"
                .replace(",", ".")
                + " gp"
            )

        else:

            cantidad_texto = "Pagado"

        nombre_pago = "🏠 Renta"

    else:

        cantidad_texto = (
            f"{cantidad} TC"
        )

        nombre_pago = "🏋️ Dummy"

    if ok:

        estado_rol = (
            f"✅ Rol **{rol_nombre}** activo."
        )

    else:

        estado_rol = (
            f"⚠️ {mensaje_rol}"
        )

    await interaction.response.send_message(
        f"✅ **Pago registrado.**\n\n"
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
    name="retirarpago",
    description="Elimina un pago registrado este mes",
    guild=GUILD_OBJECT
)
@app_commands.describe(
    usuario="Jugador",
    tipo="Pago que quieres retirar"
)
@app_commands.choices(
    tipo=[
        app_commands.Choice(
            name="🏠 Renta",
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
            "puede modificar pagos.",
            ephemeral=True
        )

        return

    if not canal_renta_correcto(
        interaction
    ):

        await interaction.response.send_message(
            "❌ Utiliza este comando "
            "en el canal de renta GH.",
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
            "❌ Ese usuario no tiene "
            "ese pago registrado este mes.",
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
        f"🗑️ **Pago retirado.**\n\n"
        f"👤 {usuario.mention}\n"
        f"📅 {mes_actual_visible()}\n"
        f"🎭 Rol: **{rol_nombre}**",
        ephemeral=True
    )

    await actualizar_panel_pagos()


# =========================================================
# /PAGOS
# =========================================================

@bot.tree.command(
    name="pagos",
    description="Actualiza el panel de pagos GH",
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
            "puede utilizar este comando.",
            ephemeral=True
        )

        return

    await actualizar_panel_pagos()

    await interaction.response.send_message(
        "✅ Panel de pagos actualizado.",
        ephemeral=True
    )


# =========================================================
# ARRANQUE
# =========================================================

@bot.event
async def on_ready():

    global comandos_sincronizados

    crear_db()

    if not comandos_sincronizados:

        # Elimina versiones globales antiguas
        # de /book, /cancel, etc.
        bot.tree.clear_commands(
            guild=None
        )

        await bot.tree.sync()

        # Sincroniza inmediatamente
        # los comandos de Existencia.
        comandos = await bot.tree.sync(
            guild=GUILD_OBJECT
        )

        comandos_sincronizados = True

        print(
            f"{len(comandos)} comandos "
            "sincronizados."
        )

    print("--------------------------------")
    print(f"Bot conectado como {bot.user}")
    print("--------------------------------")

    await actualizar_panel_reservas()

    await actualizar_panel_pagos()


# =========================================================
# VALIDACIÓN
# =========================================================

if not TOKEN:
    raise ValueError(
        "Falta DISCORD_TOKEN en .env"
    )

if GUILD_ID == 0:
    raise ValueError(
        "Falta GUILD_ID en .env"
    )

if COMMAND_CHANNEL_ID == 0:
    raise ValueError(
        "Falta COMMAND_CHANNEL_ID en .env"
    )

if SCHEDULE_CHANNEL_ID == 0:
    raise ValueError(
        "Falta SCHEDULE_CHANNEL_ID en .env"
    )

if RENT_CHANNEL_ID == 0:
    raise ValueError(
        "Falta RENT_CHANNEL_ID en .env"
    )


# =========================================================
# INICIAR
# =========================================================

bot.run(TOKEN)
