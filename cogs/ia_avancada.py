import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import io
import sys
import os
from datetime import datetime

# Importa as chaves do main.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main as config

# ═══════════════════════════════════════
# MEMÓRIA DE CONVERSA por usuário
# Guarda o histórico de mensagens de cada usuário para o Gemini ter contexto
# ═══════════════════════════════════════
historicos = {}
MAX_HISTORICO = 20  # Máximo de mensagens lembradas por usuário

def get_historico(user_id):
    if user_id not in historicos:
        historicos[user_id] = []
    return historicos[user_id]

def adicionar_historico(user_id, role, texto):
    historico = get_historico(user_id)
    historico.append({"role": role, "parts": [{"text": texto}]})
    # Mantém só as últimas MAX_HISTORICO mensagens para não estourar o limite
    if len(historico) > MAX_HISTORICO:
        historico.pop(0)

def montar_instrucao_sistema(extra=None):
    """Monta a instrução de sistema sempre com a data atual real, para a IA não achar que está em outro ano."""
    agora = datetime.now()
    data_formatada = agora.strftime('%d/%m/%Y')

    base = (
        "Você é a Jade AI, uma assistente inteligente, simpática e divertida de um servidor Discord. "
        "Responda sempre em português de forma clara e objetiva. "
        f"A data de hoje é {data_formatada}. Sempre que precisar saber o ano, mês ou dia atual, "
        f"use {data_formatada} como referência — não use nenhuma outra data que você possa ter em sua memória de treinamento. "
        "Mantenha respostas com no máximo 1000 caracteres."
    )
    return extra or base

async def chamar_gemini(user_id, mensagem, system_prompt=None, tentativas=3):
    """Chama o Gemini com o histórico de conversa do usuário. Tenta novamente em caso de erro 503 (sobrecarga)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={config.GEMINI_API_KEY}"

    # Adiciona a mensagem do usuário no histórico
    adicionar_historico(user_id, "user", mensagem)

    payload = {
        "contents": get_historico(user_id),
        "systemInstruction": {
            "parts": [{"text": montar_instrucao_sistema(system_prompt)}]
        }
    }

    ultimo_erro = None

    for tentativa in range(tentativas):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 503:
                        # Servidor do Gemini sobrecarregado — espera um pouco e tenta de novo
                        ultimo_erro = "Erro 503: modelo sobrecarregado"
                        await asyncio.sleep(2 * (tentativa + 1))
                        continue

                    if resp.status != 200:
                        erro = await resp.text()
                        raise Exception(f"Erro {resp.status}: {erro}")

                    data = await resp.json()
                    resposta = data["candidates"][0]["content"]["parts"][0]["text"]

                    # Adiciona a resposta da IA no histórico
                    adicionar_historico(user_id, "model", resposta)
                    return resposta

        except aiohttp.ClientError as e:
            ultimo_erro = str(e)
            await asyncio.sleep(1)

    raise Exception(ultimo_erro or "Não foi possível contatar o Gemini após várias tentativas.")

def truncar_para_embed(texto, limite=1000):
    """Trunca o texto respeitando o limite de 1024 caracteres do Discord por campo de embed."""
    if len(texto) <= limite:
        return texto
    return texto[:limite - 3] + "..."

class IA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════
    # /ia — conversa livre com memória
    # ═══════════════════════════════════════
    @app_commands.command(name='ia', description='『🤖』Converse com a Jade AI — ela lembra o que você disse antes!')
    @app_commands.describe(mensagem='O que você quer dizer para a Jade AI?')
    async def ia(self, interaction: discord.Interaction, mensagem: str):
        await interaction.response.defer()

        try:
            resposta = await chamar_gemini(interaction.user.id, mensagem)

            embed = discord.Embed(color=discord.Color.dark_green())
            embed.add_field(name=f"💬 {interaction.user.display_name}", value=truncar_para_embed(mensagem), inline=False)
            embed.add_field(name="🤖 Jade AI", value=truncar_para_embed(resposta), inline=False)
            embed.set_footer(text="Powered by JadeAI · Use /limpar-ia para resetar a memória")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: `{e}`", ephemeral=True)

    # ═══════════════════════════════════════
    # /limpar-ia — reseta o histórico
    # ═══════════════════════════════════════
    @app_commands.command(name='limpar-ia', description='『🧹』Reseta a memória da Jade AI para você')
    async def limpar_ia(self, interaction: discord.Interaction):
        historicos[interaction.user.id] = []
        await interaction.response.send_message("🧹 Minha memória sobre você foi resetada! Podemos começar do zero.", ephemeral=True)

    # /perguntar — resposta do Gemini
    @app_commands.command(name='perguntar', description='『🤖』Faça uma pergunta para a Jade AI')
    @app_commands.describe(pergunta='O que você quer saber?')
    async def perguntar(self, interaction: discord.Interaction, pergunta: str):
        await interaction.response.defer()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={config.GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                montar_instrucao_sistema() + f"\n\nPergunta: {pergunta}"
                            )
                        }
                    ]
                }
            ]
        }

        try:
            resposta = None
            for tentativa in range(3):
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as resp:
                        if resp.status == 503:
                            await asyncio.sleep(2 * (tentativa + 1))
                            continue
                        if resp.status != 200:
                            await interaction.followup.send("❌ Não consegui processar sua pergunta agora.", ephemeral=True)
                            return
                        data = await resp.json()
                        resposta = data["candidates"][0]["content"]["parts"][0]["text"]
                        break

            if resposta is None:
                await interaction.followup.send("❌ O Gemini está sobrecarregado agora, tente novamente em alguns instantes.", ephemeral=True)
                return

            embed = discord.Embed(
                title="🤖 Jade AI responde",
                color=discord.Color.dark_green()
            )
            embed.add_field(name="❓ Pergunta", value=truncar_para_embed(pergunta), inline=False)
            embed.add_field(name="💬 Resposta", value=truncar_para_embed(resposta), inline=False)
            embed.set_footer(text="Powered by JadeAI")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: `{e}`", ephemeral=True)

    # /resumir — resume um texto com Gemini
    @app_commands.command(name='resumir', description='『📝』Resuma um texto com a ajuda da Jade AI')
    @app_commands.describe(texto='O texto que deseja resumir')
    async def resumir(self, interaction: discord.Interaction, texto: str):
        await interaction.response.defer()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={config.GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Você é a Jade AI. Resuma o texto abaixo de forma clara e objetiva em português. "
                                "O resumo deve ter no máximo 800 caracteres.\n\n"
                                f"Texto: {texto}"
                            )
                        }
                    ]
                }
            ]
        }

        try:
            resumo = None
            for tentativa in range(3):
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as resp:
                        if resp.status == 503:
                            await asyncio.sleep(2 * (tentativa + 1))
                            continue
                        if resp.status != 200:
                            await interaction.followup.send("❌ Não consegui processar seu resumo agora.", ephemeral=True)
                            return
                        data = await resp.json()
                        resumo = data["candidates"][0]["content"]["parts"][0]["text"]
                        break

            if resumo is None:
                await interaction.followup.send("❌ O Gemini está sobrecarregado agora, tente novamente em alguns instantes.", ephemeral=True)
                return

            embed = discord.Embed(
                title="📝 Resumo gerado pela Jade AI",
                color=discord.Color.dark_green()
            )
            embed.add_field(name="📄 Resumo", value=truncar_para_embed(resumo), inline=False)
            embed.set_footer(text="Powered by JadeAI")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: `{e}`", ephemeral=True)

    # ═══════════════════════════════════════
    # /traduzir
    # ═══════════════════════════════════════
    @app_commands.command(name='traduzir', description='『🌍』Traduza um texto para qualquer idioma')
    @app_commands.describe(texto='Texto a traduzir', idioma='Idioma de destino (ex: inglês, espanhol, japonês)')
    async def traduzir(self, interaction: discord.Interaction, texto: str, idioma: str = "inglês"):
        await interaction.response.defer()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={config.GEMINI_API_KEY}"

        payload = {
            "contents": [{"role": "user", "parts": [{"text": f"Traduza o texto abaixo para {idioma}. Responda APENAS com a tradução, sem explicações:\n\n{texto}"}]}],
        }

        try:
            traducao = None
            for tentativa in range(3):
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as resp:
                        if resp.status == 503:
                            await asyncio.sleep(2 * (tentativa + 1))
                            continue
                        if resp.status != 200:
                            await interaction.followup.send("❌ Não consegui processar sua tradução agora.", ephemeral=True)
                            return
                        data = await resp.json()
                        traducao = data["candidates"][0]["content"]["parts"][0]["text"]
                        break

            if traducao is None:
                await interaction.followup.send("❌ O Gemini está sobrecarregado agora, tente novamente em alguns instantes.", ephemeral=True)
                return

            embed = discord.Embed(title="🌍 Tradução", color=discord.Color.dark_green())
            embed.add_field(name="📝 Original", value=truncar_para_embed(texto, 900), inline=False)
            embed.add_field(name=f"🔤 Tradução ({idioma})", value=truncar_para_embed(traducao, 900), inline=False)
            embed.set_footer(text="Powered by JadeAI")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: `{e}`", ephemeral=True)

    # ═══════════════════════════════════════
    # /corrigir
    # ═══════════════════════════════════════
    @app_commands.command(name='corrigir', description='『✏️』Corrija erros de português ou inglês em um texto')
    @app_commands.describe(texto='Texto a ser corrigido')
    async def corrigir(self, interaction: discord.Interaction, texto: str):
        await interaction.response.defer()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={config.GEMINI_API_KEY}"

        payload = {
            "contents": [{"role": "user", "parts": [{"text": (
                f"Corrija os erros gramaticais, ortográficos e de pontuação do texto abaixo. "
                f"Mostre o texto corrigido e depois explique brevemente as correções feitas:\n\n{texto}"
            )}]}],
        }

        try:
            corrigido = None
            for tentativa in range(3):
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as resp:
                        if resp.status == 503:
                            await asyncio.sleep(2 * (tentativa + 1))
                            continue
                        if resp.status != 200:
                            await interaction.followup.send("❌ Não consegui processar sua correção agora.", ephemeral=True)
                            return
                        data = await resp.json()
                        corrigido = data["candidates"][0]["content"]["parts"][0]["text"]
                        break

            if corrigido is None:
                await interaction.followup.send("❌ O Gemini está sobrecarregado agora, tente novamente em alguns instantes.", ephemeral=True)
                return

            embed = discord.Embed(title="✏️ Texto Corrigido", color=discord.Color.dark_green())
            embed.add_field(name="📝 Original", value=truncar_para_embed(texto, 900), inline=False)
            embed.add_field(name="✅ Resultado", value=truncar_para_embed(corrigido, 900), inline=False)
            embed.set_footer(text="Powered by JadeAI")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: `{e}`", ephemeral=True)

    # /imagemAI — gera imagem com Stability AI
    @app_commands.command(name='imagemai', description='『🎨』Gere uma imagem com IA a partir de um texto')
    @app_commands.describe(descricao='Descreva a imagem que deseja gerar (em inglês funciona melhor)')
    async def imagemai(self, interaction: discord.Interaction, descricao: str):
        await interaction.response.defer()

        url = "https://api.stability.ai/v2beta/stable-image/generate/core"

        headers = {
            "Authorization": f"Bearer {config.STABILITY_KEY}",
            "Accept": "image/*"
        }

        # A v2beta usa multipart/form-data em vez de JSON
        form = aiohttp.FormData()
        form.add_field('prompt', descricao)
        form.add_field('output_format', 'png')

        try:
            conector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=conector) as session:
                async with session.post(url, data=form, headers=headers) as resp:
                    if resp.status != 200:
                        erro = await resp.text()
                        await interaction.followup.send(f"❌ Erro ao gerar imagem (`{resp.status}`). Verifique sua chave do Stability AI ou seu saldo de créditos.", ephemeral=True)
                        return

                    imagem_bytes = await resp.read()

            arquivo = discord.File(io.BytesIO(imagem_bytes), filename="jade_imagem.png")

            embed = discord.Embed(
                title="🎨 Imagem gerada pela Jade AI",
                description=f"**Prompt:** {truncar_para_embed(descricao, 900)}",
                color=discord.Color.purple()
            )
            embed.set_image(url="attachment://jade_imagem.png")
            embed.set_footer(text="Powered by JadeAI")
            await interaction.followup.send(embed=embed, file=arquivo)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: `{e}`", ephemeral=True)

    # Responde quando alguém marca o bot — com memória!
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or not message.guild:
            return

        # Se alguém mencionar o bot, responde com Gemini
        if self.bot.user in message.mentions:
            pergunta = message.content.replace(f"<@{self.bot.user.id}>", "").strip()

            if not pergunta:
                await message.reply("Olá! Me mencione com uma pergunta e eu respondo! 🤖 Use `/ia` para conversar comigo com memória.")
                return

            async with message.channel.typing():
                try:
                    resposta = await chamar_gemini(message.author.id, pergunta)
                    await message.reply(truncar_para_embed(resposta, 1900))
                except Exception:
                    await message.reply("❌ O Gemini está sobrecarregado agora, tente novamente em alguns instantes.")

async def setup(bot):
    await bot.add_cog(IA(bot))