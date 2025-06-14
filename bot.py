import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime
import asyncio

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True  # ¡IMPORTANTE! Esto permite ver todos los miembros
intents.guilds = True   # Para acceso completo a servidores
intents.presences = True  # Opcional: para ver estado de usuarios
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuración personalizable
CONFIG = {
    "votos_requeridos": 3,
    "emoji_voto": "⭐",
    "color_nominar": 0xFFD700,  # Dorado
    "color_estrella": 0x00FF00,  # Verde
    "color_ranking": 0x0099FF,   # Azul
    "canal_publico": "estrellas", # Nombre del canal público
    "canal_moderacion": "mod-estrellas" # Nombre del canal de moderación
}

# Archivo para guardar datos
DATA_FILE = "estrellas_data.json"

# Cargar datos
def cargar_datos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"estrellas": {}, "nominaciones_activas": {}}

# Guardar datos
def guardar_datos(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Datos globales
datos = cargar_datos()

# Función para verificar si es moderador
def es_moderador(member):
    return any(role.permissions.manage_messages for role in member.roles)

# Clase para los botones de moderación
class VistaModeracion(discord.ui.View):
    def __init__(self, usuario_nominado, mensaje_gracioso, moderador):
        super().__init__(timeout=600)  # 10 minutos
        self.usuario_nominado = usuario_nominado
        self.mensaje_gracioso = mensaje_gracioso
        self.moderador = moderador

    @discord.ui.button(label='✨ que el pueblo decida', style=discord.ButtonStyle.primary, emoji='📊')
    async def crear_encuesta(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Verificar permisos
            if not es_moderador(interaction.user):
                await interaction.response.send_message("❌ solo los pete supremos podemos usar ese boton", ephemeral=True)
                return

            # Buscar canal público
            canal_publico = discord.utils.get(interaction.guild.channels, name=CONFIG["canal_publico"])
            if not canal_publico:
                await interaction.response.send_message(f"❌ no se encontró el canal #{CONFIG['canal_publico']}", ephemeral=True)
                return

            # Crear embed para la encuesta
            embed = discord.Embed(
                title="🌟 ¡nominación para estrella!",
                description=f"**{self.usuario_nominado.display_name}** dijo algo gracioso!\n\n"
                           f"**mensaje:** *{self.mensaje_gracioso}*\n\n"
                           f"¿merece recibir una estrella? reacciona con {CONFIG['emoji_voto']}",
                color=CONFIG["color_nominar"],
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=self.usuario_nominado.display_avatar.url)
            embed.add_field(
                name="📊 votación",
                value=f"se necesitan **{CONFIG['votos_requeridos']}** votos para otorgar la estrella",
                inline=False
            )
            embed.set_footer(text=f"nominado por {self.moderador.display_name}", icon_url=self.moderador.display_avatar.url)

            # Enviar mensaje de encuesta
            mensaje_encuesta = await canal_publico.send(embed=embed)
            await mensaje_encuesta.add_reaction(CONFIG["emoji_voto"])

            # Guardar nominación activa
            datos["nominaciones_activas"][str(mensaje_encuesta.id)] = {
                "usuario_id": self.usuario_nominado.id,
                "mensaje": self.mensaje_gracioso,
                "moderador_id": self.moderador.id,
                "votos_actuales": 0,
                "votantes": [],
                "canal_id": canal_publico.id
            }
            guardar_datos(datos)

            # Desactivar botón
            button.disabled = True
            await interaction.response.edit_message(view=self)

            # Confirmar al moderador
            await interaction.followup.send("✅ ¡encuesta creada exitosamente!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ error: {str(e)}", ephemeral=True)

    @discord.ui.button(label='❌ Cancelar', style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not es_moderador(interaction.user):
            await interaction.response.send_message("❌ solo los petes supremos pueden usar este botón.", ephemeral=True)
            return
        
        await interaction.response.edit_message(content="❌ nominación cancelada.", embed=None, view=None)

# Evento cuando el bot se conecta
@bot.event
async def on_ready():
    print(f'🌟 {bot.user} se ha conectado a Discord!')
    
    # Información sobre los servidores
    for guild in bot.guilds:
        print(f'📋 Servidor: {guild.name} - Miembros: {guild.member_count}')
        print(f'   Miembros en cache: {len(guild.members)}')
        
        # Si hay pocos miembros en cache, intentar cargarlos
        if len(guild.members) < guild.member_count:
            print(f'⚠️  Cargando miembros del servidor {guild.name}...')
            async for member in guild.fetch_members(limit=None):
                pass  # Solo cargar al cache
            print(f'✅ Miembros cargados: {len(guild.members)}')
    
    print("lluvia de estrellas activada ✨")
    
    try:
        synced = await bot.tree.sync()
        print(f"🔧 se sincronizaron {len(synced)} slash commands.")
    except Exception as e:
        print(f"error al sincronizar slash commands: {e}")

# Función para otorgar estrella - versión robusta unificada y mejorada
async def otorgar_estrella(mensaje, nominacion):
    try:
        guild = mensaje.guild
        
        usuario = None
        
        # Método 1: get_member (cache local)
        usuario = guild.get_member(nominacion["usuario_id"])
        print(f"🔍 Método 1 (get_member): {usuario.display_name if usuario else 'No encontrado'}")
        
        # Método 2: fetch_member (consulta a Discord)
        if not usuario:
            try:
                usuario = await guild.fetch_member(nominacion["usuario_id"])
                print(f"🔍 Método 2 (fetch_member): {usuario.display_name if usuario else 'No encontrado'}")
            except discord.NotFound:
                print(f"❌ Usuario con ID {nominacion['usuario_id']} no encontrado en el servidor")
            except discord.HTTPException as e:
                print(f"❌ Error HTTP al buscar usuario: {e}")
        
        # Método 3: buscar en el cache global del bot
        if not usuario:
            usuario = bot.get_user(nominacion["usuario_id"])
            print(f"🔍 Método 3 (bot.get_user): {usuario.display_name if usuario else 'No encontrado'}")
        
        # Método 4: fetch directo del bot
        if not usuario:
            try:
                usuario = await bot.fetch_user(nominacion["usuario_id"])
                print(f"🔍 Método 4 (bot.fetch_user): {usuario.display_name if usuario else 'No encontrado'}")
            except discord.NotFound:
                print(f"❌ Usuario con ID {nominacion['usuario_id']} no existe en Discord")
            except discord.HTTPException as e:
                print(f"❌ Error HTTP al buscar usuario globalmente: {e}")
        
        # Si NINGÚN método funciona, crear un "usuario fantasma"
        if not usuario:
            print("⚠️  Creando usuario fantasma para completar el proceso...")
            class UsuarioFantasma:
                def __init__(self, user_id):
                    self.id = user_id
                    self.display_name = f"Usuario #{str(user_id)[-4:]}"
                    self.mention = f"<@{user_id}>"
                    self.display_avatar = type('obj', (object,), {'url': 'https://cdn.discordapp.com/embed/avatars/0.png'})()
            usuario = UsuarioFantasma(nominacion["usuario_id"])
            print(f"👻 Usuario fantasma creado: {usuario.display_name}")

        # Obtener moderador (menos crítico)
        moderador = guild.get_member(nominacion["moderador_id"])
        if not moderador:
            try:
                moderador = await guild.fetch_member(nominacion["moderador_id"])
            except:
                moderador = None

        print(f"✅ Procesando estrella para: {usuario.display_name}")

        # Actualizar contador de estrellas
        user_id = str(usuario.id)
        if user_id not in datos["estrellas"]:
            datos["estrellas"][user_id] = {"count": 0, "historial": []}
        
        datos["estrellas"][user_id]["count"] += 1
        datos["estrellas"][user_id]["historial"].append({
            "fecha": datetime.now().isoformat(),
            "mensaje": nominacion["mensaje"],
            "moderador": moderador.display_name if moderador else "desconocido"
        })

        print(f"✅ {usuario.display_name} ahora tiene {datos['estrellas'][user_id]['count']} estrellas")

        # Crear embed de confirmación
        embed = discord.Embed(
            title="🌟 ¡estrella otorgada! felicidades <3",
            description=f"**{usuario.display_name}** ha recibido una estrella por su comentario gracioso!\n\n"
                       f"**mensaje premiado:** *{nominacion['mensaje']}*\n\n"
                       f"🌟 **total de estrellas:** {datos['estrellas'][user_id]['count']}",
            color=CONFIG["color_estrella"],
            timestamp=datetime.now()
        )
        
        # Solo establecer thumbnail si tenemos un usuario real
        if hasattr(usuario, 'display_avatar') and hasattr(usuario.display_avatar, 'url'):
            embed.set_thumbnail(url=usuario.display_avatar.url)
        
        embed.add_field(
            name="📊 votación final",
            value=f"**{nominacion['votos_actuales']}** usuarios votaron a favor",
            inline=True
        )
        embed.set_footer(text=f"nominado por {moderador.display_name if moderador else 'pete supremo'}")

        # Editar mensaje original
        await mensaje.edit(embed=embed)
        await mensaje.clear_reactions()

        # Felicitar al usuario (usar mention que siempre funciona)
        await mensaje.reply(f"🎉 ¡felicidades {usuario.mention}! has recibido una estrella ⭐")

        guardar_datos(datos)
        print("✅ ¡Estrella otorgada exitosamente!")
        return True

    except Exception as e:
        print(f"❌ Error crítico al otorgar estrella: {e}")
        import traceback
        traceback.print_exc()
        return False

# Comando para nominar (solo moderadores)
@bot.command(name='nominar')
async def nominar(ctx, miembro: discord.Member = None, *, mensaje=None):
    """nominar a un usuario para recibir una estrella (solo petes supremos)"""
    
    # Verificar si es moderador
    if not es_moderador(ctx.author):
        await ctx.send("❌ solo los petes supremos pueden nominar usuarios.")
        return

    # Verificar que esté en el canal correcto
    if ctx.channel.name != CONFIG["canal_moderacion"]:
        await ctx.send(f"❌ este comando solo puede usarse en #{CONFIG['canal_moderacion']}")
        return

    # Verificar parámetros
    if not miembro or not mensaje:
        await ctx.send("❌ uso: `!nominar @usuario mensaje que dijo`")
        return

    # Verificar que no se nomine a sí mismo
    if miembro == ctx.author:
        await ctx.send("❌ no te podes nominar a vos mismo, fantasma")
        return

    # Verificar que no sea un bot
    if miembro.bot:
        await ctx.send("❌ no podes nominar a un bot, no seas boludo")
        return

    # Crear embed de nominación
    embed = discord.Embed(
        title="🌟 nueva nominación",
        description=f"**usuario:** {miembro.display_name}\n"
                   f"**mensaje:** *{mensaje}*\n"
                   f"**pete supremo:** {ctx.author.display_name}",
        color=CONFIG["color_nominar"],
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=miembro.display_avatar.url)
    embed.add_field(
        name="📋 instrucciones",
        value="hace clic en el botón para crear la encuesta pública",
        inline=False
    )

    # Crear vista con botones
    vista = VistaModeracion(miembro, mensaje, ctx.author)
    
    await ctx.send(embed=embed, view=vista)

# Comando para ver estrellas propias
@bot.command(name='estrellas')
async def estrellas(ctx, miembro: discord.Member = None):
    """ver las estrellas de un usuario"""
    
    usuario = miembro if miembro else ctx.author
    user_id = str(usuario.id)
    
    if user_id not in datos["estrellas"] or datos["estrellas"][user_id]["count"] == 0:
        if usuario == ctx.author:
            await ctx.send("⭐ todavia no tenes estrellas. ¡deberias ser más gracioso para conseguir algunas!")
        else:
            await ctx.send(f"⭐ {usuario.display_name} todavia no tiene estrellas.")
        return

    estrellas_usuario = datos["estrellas"][user_id]
    
    embed = discord.Embed(
        title=f"🌟 estrellas de {usuario.display_name}",
        description=f"**total:** {estrellas_usuario['count']} estrella(s)",
        color=CONFIG["color_estrella"],
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=usuario.display_avatar.url)
    
    # Mostrar historial reciente (últimas 3)
    if estrellas_usuario["historial"]:
        historial_reciente = estrellas_usuario["historial"][-3:]
        historial_text = ""
        for i, entrada in enumerate(reversed(historial_reciente), 1):
            fecha = datetime.fromisoformat(entrada["fecha"]).strftime("%d/%m/%Y")
            mensaje_corto = entrada["mensaje"][:50] + "..." if len(entrada["mensaje"]) > 50 else entrada["mensaje"]
            historial_text += f"**{i}.** *{mensaje_corto}* ({fecha})\n"
        
        embed.add_field(
            name="📜 ultimas Estrellas",
            value=historial_text,
            inline=False
        )
    
    await ctx.send(embed=embed)

# Comando para ranking
@bot.command(name='ranking')
async def ranking(ctx):
    """mira el top 10 usuarios con más estrellas"""
    
    if not datos["estrellas"]:
        await ctx.send("📊 todavia no hay usuarios con estrellas.")
        return

    # Ordenar usuarios por cantidad de estrellas
    ranking_usuarios = []
    for user_id, data in datos["estrellas"].items():
        try:
            usuario = ctx.guild.get_member(int(user_id))
            if usuario and data["count"] > 0:
                ranking_usuarios.append((usuario, data["count"]))
        except:
            continue

    ranking_usuarios.sort(key=lambda x: x[1], reverse=True)
    
    if not ranking_usuarios:
        await ctx.send("📊 no hay usuarios activos con estrellas.")
        return

    embed = discord.Embed(
        title="🏆 ranking de estrellas",
        description="top 10 usuarios más graciosos del servidor",
        color=CONFIG["color_ranking"],
        timestamp=datetime.now()
    )

    # Emojis para los primeros puestos
    emojis = ["🥇", "🥈", "🥉"] + ["⭐"] * 7
    
    ranking_text = ""
    for i, (usuario, estrellas) in enumerate(ranking_usuarios[:10]):
        ranking_text += f"{emojis[i]} **{i+1}.** {usuario.display_name} - {estrellas} estrella(s)\n"
    
    embed.add_field(name="📊 clasificación", value=ranking_text, inline=False)
    
    # Estadísticas generales
    total_estrellas = sum(data["count"] for data in datos["estrellas"].values())
    embed.add_field(
        name="📈 estadísticas",
        value=f"**total de estrellas otorgadas:** {total_estrellas}\n"
              f"**usuarios con estrellas:** {len(ranking_usuarios)}",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Comando de ayuda
@bot.command(name='ayuda-estrellas')
async def ayuda_estrellas(ctx):
    """mostrar todos los comandos del sistema de estrellas"""
    
    embed = discord.Embed(
        title="🌟 sistema de estrellas - help",
        description="comandos disponibles para el sistema de estrellas",
        color=CONFIG["color_ranking"]
    )
    
    # Comandos para moderadores
    embed.add_field(
        name="👮‍♀️ para petes supremos",
        value=f"`!nominar @usuario mensaje` - nominar usuario\n"
              f"(Usar en #{CONFIG['canal_moderacion']})",
        inline=False
    )
    
    # Comandos para todos
    embed.add_field(
        name="👥 para todos los usuarios",
        value="`!estrellas` - ves tus estrellas\n"
              "`!estrellas @usuario` - ves las estrellas de otro usuario\n"
              "`!ranking` - ves el top 10 de estrellas\n"
              "`!ayuda-estrellas` - mostrar ayuda",
        inline=False
    )
    
    # Cómo funciona el sistema
    embed.add_field(
        name="⚙️ ¿como funciona?",
        value=f"1. los pete supremo nominan usuarios graciosos\n"
              f"2. se crea una encuesta en #{CONFIG['canal_publico']}\n"
              f"3. los usuarios votan con {CONFIG['emoji_voto']}\n"
              f"4. con {CONFIG['votos_requeridos']}+ votos se otorga la estrella",
        inline=False
    )
    
    embed.set_footer(text="¡tenes que ser mas gracioso y conseguis estrellas! ⭐")
    
    await ctx.send(embed=embed)

# Comando de configuración (solo administradores)
@bot.command(name='config-estrellas')
@commands.has_permissions(administrator=True)
async def config_estrellas(ctx, opcion=None, *, valor=None):
    """configurar el sistema de estrellas (solo administradores)"""
    
    opciones_validas = {
        "votos": "votos_requeridos",
        "emoji": "emoji_voto",
        "canal-publico": "canal_publico",
        "canal-mod": "canal_moderacion"
    }
    
    if not opcion:
        embed = discord.Embed(
            title="⚙️ configuración del sistema",
            color=0xFF9900
        )
        embed.add_field(
            name="configuración actual",
            value=f"**votos requeridos:** {CONFIG['votos_requeridos']}\n"
                  f"**emoji de voto:** {CONFIG['emoji_voto']}\n"
                  f"**canal público:** #{CONFIG['canal_publico']}\n"
                  f"**canal moderación:** #{CONFIG['canal_moderacion']}",
            inline=False
        )
        embed.add_field(
            name="comandos de configuración",
            value="`!config-estrellas votos [número]`\n"
                  "`!config-estrellas emoji [emoji]`\n"
                  "`!config-estrellas canal-publico [nombre]`\n"
                  "`!config-estrellas canal-mod [nombre]`",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    if opcion not in opciones_validas:
        await ctx.send("❌ opción no válida. usa `!config-estrellas` para ver las opciones.")
        return
    
    if not valor:
        await ctx.send(f"❌ tenes que proporcionar un valor para {opcion}")
        return
    
    # Aplicar configuración
    config_key = opciones_validas[opcion]
    
    if opcion == "votos":
        try:
            CONFIG[config_key] = int(valor)
        except ValueError:
            await ctx.send("❌ el número de votos debe ser un número entero.")
            return
    else:
        CONFIG[config_key] = valor
    
    await ctx.send(f"✅ configuración actualizada: **{opcion}** = `{valor}`")

# Manejo de errores
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ no tenes permisos para usar este comando.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignorar comandos no encontrados
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ usuario no encontrado.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ faltan argumentos. usa `!ayuda-estrellas` para ver los comandos.")
    else:
        print(f"error: {error}")

# COMANDO CON /

@bot.tree.command(name="estrellas", description="ver tus estrellas o las de otro usuario")
@app_commands.describe(usuario="usuario para ver sus estrellas")
async def slash_estrellas(interaction: discord.Interaction, usuario: discord.Member = None):
    usuario = usuario or interaction.user
    user_id = str(usuario.id)

    if user_id not in datos["estrellas"] or datos["estrellas"][user_id]["count"] == 0:
        if usuario == interaction.user:
            await interaction.response.send_message("⭐ todavía no tenés estrellas. ¡sé más gracioso!", ephemeral=True)
        else:
            await interaction.response.send_message(f"⭐ {usuario.display_name} todavía no tiene estrellas.", ephemeral=True)
        return

    estrellas_usuario = datos["estrellas"][user_id]

    embed = discord.Embed(
        title=f"🌟 estrellas de {usuario.display_name}",
        description=f"**total:** {estrellas_usuario['count']} estrella(s)",
        color=CONFIG["color_estrella"],
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=usuario.display_avatar.url)

    # últimas 3 estrellas
    if estrellas_usuario["historial"]:
        historial_reciente = estrellas_usuario["historial"][-3:]
        historial_text = ""
        for i, entrada in enumerate(reversed(historial_reciente), 1):
            fecha = datetime.fromisoformat(entrada["fecha"]).strftime("%d/%m/%Y")
            mensaje_corto = entrada["mensaje"][:50] + "..." if len(entrada["mensaje"]) > 50 else entrada["mensaje"]
            historial_text += f"**{i}.** *{mensaje_corto}* ({fecha})\n"

        embed.add_field(name="📜 últimas estrellas", value=historial_text, inline=False)

    await interaction.response.send_message(embed=embed)

# EJECUTO EL BOT: python bot.py en la terminal
if __name__ == "__main__":
    # REEMPLAZA EL TOKEN POR TU TOKEN REAL
    TOKEN = 'TOKEN ACAAAAAAAAAAAAAAAAAA'
    
    try:
        print("🌟 iniciando bot del sistema de estrellas...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ token inválido. verifica tu token de Discord.")
    except Exception as e:
        print(f"❌ error al iniciar el bot: {e}")

