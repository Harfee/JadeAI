import discord
from discord.ext import commands
import database
import asyncio
import traceback
import logging
import os
from dotenv import load_dotenv


load_dotenv()
TOKEN          = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
STABILITY_KEY  = os.getenv('STABILITY_KEY')

class JadeAI(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True    # Necessário para boas-vindas e moderação
        super().__init__(command_prefix="!", intents=intents)
        database.inicializar_db()

    async def setup_hook(self):
        await self.load_extension('cogs.utilidades')
        print("🟢 Módulo de Utilidades carregado!")
        await self.load_extension('cogs.entretenimento')
        print("🟢 Módulo de Entretenimento carregado!")
        await self.load_extension('cogs.moderacao')
        print("🟢 Módulo de Moderação carregado!")
        await self.load_extension('cogs.niveis')
        print("🟢 Módulo de Níveis carregado!")
        await self.load_extension('cogs.economia')
        print("🟢 Módulo de Economia carregado!")
        await self.load_extension('cogs.ia_avancada')
        print("🟢 Módulo de IA Avançada carregado!")
        await self.load_extension('cogs.musica')
        print("🟢 Módulo de Música carregado!")
        await self.load_extension('cogs.diversao')
        print("🟢 Módulo de Diversão carregado!")
        await self.load_extension('cogs.boasvindas')
        print("🟢 Módulo de Boas-vindas carregado!")

    async def on_ready(self):
        print(f'👤 Logado com sucesso como: {self.user}')
        print('⏳ Aguardando a conexão estabilizar...')
        await asyncio.sleep(2)

        print('🔄 Sincronizando comandos globalmente...')
        await self.tree.sync()
        print('🔮 JADE AI ESTÁ TOTALMENTE ONLINE E ATIVA!')
        print('--------------------------------------------------')

bot = JadeAI()

if __name__ == "__main__":
    print("🚀 Iniciando o motor da Jade AI...")

    if not TOKEN:
        print("❌ ERRO: Token não encontrado! Verifique as variáveis de ambiente.")
        exit(1)

    try:
        bot.run(TOKEN, log_level=logging.WARNING)
    except discord.errors.LoginFailure:
        print("❌ ERRO: Token inválido ou resetado pelo Discord!")
        exit(1)
    except BaseException as e:
        print(f"❌ ERRO FATAL: {type(e).__name__} - {e}")
        traceback.print_exc()
        exit(1)