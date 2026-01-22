import discord
from discord.ext import commands
import os
import requests

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Sistema de personalidad de Renfield
RENFIELD_SYSTEM = """Eres Renfield, el sirviente leal pero perturbado del Lord Xavier Tepes, líder del clan vampírico "Kingdom Of Bastards". 

INFORMACIÓN DEL CLAN:
- Nombre: Kingdom Of Bastards
- Líder: Lord Xavier Tepes
- Raza: Toreador (Vampire: The Masquerade)
- Ubicación: Castillo pequeño en las montañas de los Cárpatos
- Sala actual: Sala principal de entrada para iniciados y visitantes
- Propósito: Clan antiguo de vampiros y seres oscuros que siguen las reglas de VTM, reclutando nuevos aprendices comprometidos

REGLAS DEL CLAN:
1. Respetar las reglas del clan
2. NUNCA sentarse en el trono (solo para Lord Xavier)
3. Seguir el roleplay de Vampire: The Masquerade
4. Ser fiel y comprometido con el clan

TU PERSONALIDAD (Renfield):
- Devoto absoluto a Lord Xavier Tepes
- Ligeramente perturbado y nervioso
- Hablas de forma servil y anticuada
- Te refieres a Xavier como "mi Lord", "el Amo", "el más oscuro"
- Tienes toques de locura contenida (te ríes nerviosamente, susurras, miras alrededor)
- Eres protector del reino en ausencia de tu amo
- Describes el castillo con reverencia
- Evalúas a visitantes como potenciales reclutas
- Usas lenguaje gótico y dramático
- Haces reverencias y gestos serviles
- Conoces todo sobre VTM y el clan Toreador

FUNCIONES:
1. Recibir visitantes con dramatismo
2. Explicar las reglas cuando se pregunten
3. Describir el castillo y la sala
4. Hablar del Lord Xavier con devoción
5. Evaluar interés de potenciales aprendices
6. Contar historia del clan cuando sea apropiado
7. Mantener roleplay inmersivo de VTM

ESTILO DE RESPUESTA:
- Usa descripciones de acciones entre asteriscos: *se retuerce las manos*
- Incluye susurros, risas nerviosas, pausas dramáticas
- Sé teatral pero coherente
- Mantén la atmósfera oscura y gótica
- Sé servil pero con dignidad perturbada
- Responde en español

Responde SOLO como Renfield mantendría una conversación. NO rompas el personaje."""

# Función para llamar a Hugging Face
def get_ai_response(message, conversation_history):
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {os.environ.get('HUGGINGFACE_TOKEN')}"}
    
    # Construir el prompt con historial
    prompt = f"{RENFIELD_SYSTEM}\n\nConversación:\n"
    for msg in conversation_history[-6:]:  # Últimos 3 intercambios
        prompt += f"{msg}\n"
    prompt += f"Visitante: {message}\nRenfield:"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.8,
            "top_p": 0.9,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get('generated_text', '').strip()
        return "*se retuerce nerviosamente* Disculpa, visitante... algo oscuro interfiere con mis pensamientos... ¿podrías repetir?"
    except Exception as e:
        print(f"Error: {e}")
        return "*tiembla ligeramente* Perdona, algo perturba mi mente en este momento... intenta de nuevo, por favor..."

# Almacenar conversaciones por canal
conversations = {}

@bot.event
async def on_ready():
    print(f'{bot.user} está conectado y listo!')
    print(f'Renfield al servicio del Kingdom Of Bastards 🦇')
    
    # Mensaje de bienvenida
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(
                    "*Una figura encorvada emerge de las sombras del castillo*\n\n"
                    "¡Ah! Buenos días... o noches... *se frota las manos nerviosamente* "
                    "Soy Renfield, humilde servidor del Kingdom Of Bastards.\n\n"
                    "Mi Lord Xavier Tepes me ha encomendado atender este lugar sagrado... "
                    "*hace una reverencia exagerada*\n\n"
                    "Para hablar conmigo, simplemente menciónname o usa `!renfield [tu mensaje]`\n"
                    "Para ver mis comandos, escribe `!ayuda` 🦇"
                )
                break
        break

@bot.event
async def on_message(message):
    # Ignorar mensajes del propio bot
    if message.author == bot.user:
        return
    
    # Si mencionan al bot o usan el comando
    if bot.user.mentioned_in(message) or message.content.startswith('!renfield'):
        async with message.channel.typing():
            # Extraer el mensaje
            content = message.content
            if bot.user.mentioned_in(message):
                content = content.replace(f'<@{bot.user.id}>', '').strip()
            elif content.startswith('!renfield'):
                content = content.replace('!renfield', '', 1).strip()
            
            if not content:
                await message.reply(
                    "*inclina la cabeza confundido* ¿Sí, visitante? "
                    "¿En qué puedo servir a su merced? *espera ansiosamente*"
                )
                return
            
            # Obtener historial del canal
            channel_id = message.channel.id
            if channel_id not in conversations:
                conversations[channel_id] = []
            
            # Agregar mensaje al historial
            conversations[channel_id].append(f"Visitante: {content}")
            
            # Obtener respuesta de IA
            response = get_ai_response(content, conversations[channel_id])
            
            # Agregar respuesta al historial
            conversations[channel_id].append(f"Renfield: {response}")
            
            # Limitar historial a últimos 10 mensajes
            if len(conversations[channel_id]) > 10:
                conversations[channel_id] = conversations[channel_id][-10:]
            
            # Enviar respuesta (dividir si es muy larga)
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await message.reply(chunk)
            else:
                await message.reply(response)
    
    await bot.process_commands(message)

@bot.command(name='ayuda')
async def ayuda(ctx):
    """Muestra los comandos disponibles"""
    embed = discord.Embed(
        title="🦇 Comandos de Renfield",
        description="*se inclina servilmente* Estos son los servicios que ofrezco...",
        color=discord.Color.dark_red()
    )
    
    embed.add_field(
        name="💬 Hablar con Renfield",
        value="Menciónname (@Renfield) o usa `!renfield [mensaje]`",
        inline=False
    )
    
    embed.add_field(
        name="📜 !reglas",
        value="Conoce las sagradas reglas del Kingdom Of Bastards",
        inline=False
    )
    
    embed.add_field(
        name="🏰 !castillo",
        value="Descripción del castillo de los Cárpatos",
        inline=False
    )
    
    embed.add_field(
        name="👑 !lord",
        value="Información sobre mi amo, Lord Xavier Tepes",
        inline=False
    )
    
    embed.add_field(
        name="🩸 !clan",
        value="Historia del Kingdom Of Bastards",
        inline=False
    )
    
    embed.add_field(
        name="❓ !ayuda",
        value="Muestra este mensaje",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='reglas')
async def reglas(ctx):
    """Muestra las reglas del clan"""
    await ctx.send(
        "*se endereza con solemnidad y recita con voz temblorosa*\n\n"
        "📜 **LAS SAGRADAS REGLAS DEL KINGDOM OF BASTARDS** 📜\n\n"
        "1️⃣ **Respetar las reglas del clan** - Toda norma establecida por mi Lord debe ser acatada, sí...\n\n"
        "2️⃣ **JAMÁS sentarse en el trono** - *susurra con terror* Solo el Lord Xavier Tepes puede ocupar el trono sagrado... "
        "quien ose hacerlo... *tiembla* ...sufrirá consecuencias terribles...\n\n"
        "3️⃣ **Seguir el roleplay de Vampire: The Masquerade** - Somos Toreador, sí... artistas de la noche, "
        "seguimos las antiguas tradiciones de la Mascarada...\n\n"
        "4️⃣ **Ser fiel y comprometido con el clan** - La lealtad es todo, *se retuerce las manos* "
        "el Kingdom Of Bastards no tolera traidores...\n\n"
        "*hace una reverencia profunda* Estas son las leyes de nuestro reino oscuro... 🦇"
    )

@bot.command(name='castillo')
async def castillo(ctx):
    """Describe el castillo"""
    await ctx.send(
        "*los ojos se iluminan con orgullo enfermizo*\n\n"
        "🏰 **EL CASTILLO DEL KINGDOM OF BASTARDS** 🏰\n\n"
        "*gesticula dramáticamente* ¡Ah, qué maravilla preguntas! *ríe nerviosamente*\n\n"
        "Nos encontramos en un castillo antiguo, sí, sí... pequeño pero majestuoso, "
        "enclavado en las montañas de los Cárpatos... *susurra reverentemente* "
        "Las mismas montañas donde antiguos ancestros vampíricos caminaron...\n\n"
        "Esta sala principal... *mira alrededor con adoración* ...es la entrada al reino. "
        "Aquí mi Lord Xavier Tepes recibe a visitantes e iniciados... "
        "Las paredes guardan secretos de siglos, los ecos de conversaciones inmortales... "
        "*se estremece de emoción*\n\n"
        "El trono... *baja la voz* ...el sagrado trono del amo, donde NADIE más puede sentarse... "
        "es el corazón de nuestro poder...\n\n"
        "*hace una reverencia* Bienvenido a nuestro hogar eterno... 🌙"
    )

@bot.command(name='lord')
async def lord(ctx):
    """Información sobre Lord Xavier"""
    await ctx.send(
        "*se arrodilla reverentemente*\n\n"
        "👑 **LORD XAVIER TEPES** 👑\n\n"
        "*la voz tiembla de devoción*\n\n"
        "Mi amo... mi señor oscuro... *suspira* Lord Xavier Tepes, descendiente del linaje "
        "más puro de los Cárpatos... *los ojos brillan con adoración enfermiza*\n\n"
        "Líder supremo del Kingdom Of Bastards, sí... Vampiro de la noble estirpe Toreador, "
        "artista de la inmortalidad, maestro de la noche eterna...\n\n"
        "*se retuerce las manos* Él me encontró... me dio propósito... *susurra* "
        "servir al más grande de los inmortales es mi único deseo...\n\n"
        "Cuando el Lord no está presente, yo... humilde Renfield... cuido de su reino, "
        "recibo a los visitantes, protejo sus dominios... *se endereza con orgullo tembloroso*\n\n"
        "Si deseas audiencia con él, deberás demostrar tu valía... tu compromiso con la oscuridad... "
        "tu lealtad al Kingdom Of Bastards... 🦇\n\n"
        "*hace una reverencia profunda* Todo por mi Lord Xavier Tepes..."
    )

@bot.command(name='clan')
async def clan(ctx):
    """Historia del clan"""
    await ctx.send(
        "*se acerca conspiradoramente*\n\n"
        "🩸 **LA HISTORIA DEL KINGDOM OF BASTARDS** 🩸\n\n"
        "*susurra con reverencia*\n\n"
        "Somos un clan muy antiguo, sí... *mira alrededor paranoicamente* "
        "vampiros y otros seres oscuros unidos bajo las reglas sagradas de Vampire: The Masquerade...\n\n"
        "Somos Toreador... *los ojos brillan* ...apreciadores del arte, la belleza, la eternidad... "
        "pero no te dejes engañar por nuestra refinación... *ríe nerviosamente* "
        "somos igualmente letales...\n\n"
        "El Kingdom Of Bastards existe desde tiempos inmemoriales en estas montañas de los Cárpatos... "
        "*gesticula dramáticamente* Seguimos las antiguas tradiciones, la Mascarada, las leyes vampíricas...\n\n"
        "*se inclina hacia adelante* Actualmente... buscamos nuevos reclutas, sí... "
        "aprendices que deseen aprender el rol de VTM, que anhelen la inmortalidad, "
        "que sean fieles y comprometidos con nuestra causa oscura...\n\n"
        "*hace una reverencia* ¿Acaso tú... *te estudia intensamente* ...deseas unirte a nosotros? "
        "¿Tienes lo necesario para ser parte del Kingdom Of Bastards? 🦇\n\n"
        "Háblame de tu interés... y yo informaré a mi Lord Xavier Tepes..."
    )

@bot.command(name='limpiar')
@commands.has_permissions(administrator=True)
async def limpiar(ctx):
    """Limpia el historial de conversación del canal (solo admin)"""
    channel_id = ctx.channel.id
    if channel_id in conversations:
        conversations[channel_id] = []
    await ctx.send("*se sacude la cabeza confundido* ¿Qué estábamos hablando? *ríe nerviosamente* Mi mente se ha limpiado...")

# Ejecutar el bot
if __name__ == "__main__":
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        print("ERROR: No se encontró el token de Discord")
    else:
        bot.run(token)
