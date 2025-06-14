🌟 bot de discord - sistema de estrellas
un bot de discord que permite a los moderadores crear un sistema de reconocimiento divertido donde los usuarios pueden ganar estrellas por ser graciosos.
🚀 características
✅ sistema de nominaciones para moderadores
✅ botones interactivos
✅ encuestas automáticas con reacciones
✅ contador de estrellas persistente
✅ ranking de usuarios
✅ verificación de permisos
✅ mensajes embebidos elegantes
📁 estructura del proyecto
discord-star-bot/
├── bot.js          # código principal del bot
├── config.json     # configuración del bot
├── package.json    # dependencias y scripts
├── .env.example    # ejemplo de variables de entorno
├── .gitignore      # archivos a ignorar en git
└── README.md       # este archivo
⚙️ configuración inicial
1. clonar y configurar
bashgit clone <tu-repo>
cd discord-star-bot
npm install
2. configurar el bot
copia config.json y edita los valores:
json{
  "TOKEN": "tu_bot_token_aqui",
  "MOD_CHANNEL_ID": "id_del_canal_de_mods",
  "PUBLIC_CHANNEL_ID": "id_del_canal_publico",
  "REQUIRED_REACTIONS": 3,
  "STAR_EMOJI": "⭐"
}
3. crear el bot en discord

ve a discord developer portal
crea una nueva aplicación
ve a la sección "bot" y crea un bot
copia el token al archivo config.json
habilita los "privileged gateway intents":

message content intent
server members intent



4. obtener ids de canales

habilita el modo desarrollador en discord
clic derecho en el canal → copiar id
pega los ids en config.json

5. permisos del bot
el bot necesita estos permisos:

leer mensajes/ver canales
enviar mensajes
insertar enlaces
añadir reacciones
usar emojis externos
leer historial de mensajes
mencionar @everyone, @here y todos los roles

🎮 comandos
para moderadores (canal privado):

!nominar @usuario mensaje - crear nominación para estrella

para todos los usuarios:

!estrellas - ver tus estrellas
!estrellas @usuario - ver estrellas de otro usuario
!ranking - ver top 10 de estrellas
!ayuda-estrellas - mostrar comandos disponibles

🔄 flujo de trabajo

moderador ve algo gracioso → usa !nominar @usuario lo que dijo
bot crea botón interactivo → moderador hace clic para crear encuesta
encuesta pública automática → usuarios votan con reacciones ⭐
al alcanzar el límite de votos → se otorga estrella automáticamente
mensaje de felicitación → usuario recibe reconocimiento público

🏃‍♂️ ejecutar el bot
bash# modo normal
npm start

# modo desarrollo (con nodemon)
npm run dev
📊 personalización
puedes modificar en config.json:

número de reacciones requeridas
emoji utilizado para votar
canales utilizados

🛡️ seguridad

el archivo config.json está en .gitignore por seguridad
solo usuarios con permisos de "gestionar mensajes" pueden usar comandos de moderador
verificación automática de permisos en todas las interacciones

copyright 2025 sofia lorenz
