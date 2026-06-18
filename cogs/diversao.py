import discord
from discord import app_commands
from discord.ext import commands
import random
import aiohttp
import database

# ═══════════════════════════════════════
# Subreddits de memes por país/idioma
# ═══════════════════════════════════════
SUBREDDITS_POR_PAIS = {
    'brasil':   ['HUEstation', 'circojeca', 'okbuddyhasbara_br', 'BrasilMemes', 'estudantesdeengenharia'],
    'eua':      ['memes', 'dankmemes', 'me_irl'],
    'global':   ['memes', 'funny'],
}

NOMES_PAISES = {
    'brasil': '🇧🇷 Brasil',
    'eua': '🇺🇸 Estados Unidos',
    'global': '🌍 Global (sem filtro de país)',
}

class Diversao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # O comando /dado
    @app_commands.command(name='dado', description='『🎲』Role um dado!')
    @app_commands.describe(lados='Número de lados do dado (padrão: 6)')
    async def dado(self, interaction: discord.Interaction, lados: int = 6):
        if lados < 2:
            await interaction.response.send_message("❌ O dado precisa ter pelo menos 2 lados!", ephemeral=True)
            return

        resultado = random.randint(1, lados)

        embed = discord.Embed(
            title="🎲 Dado Rolado!",
            description=f"{interaction.user.mention} rolou um dado de **{lados}** lados e tirou... **{resultado}**!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    # O comando /cara-coroa
    @app_commands.command(name='cara-coroa', description='『🪙』Jogue cara ou coroa!')
    async def cara_coroa(self, interaction: discord.Interaction):
        resultado = random.choice(["🟡 Cara!", "⚪ Coroa!"])

        embed = discord.Embed(
            title="🪙 Cara ou Coroa",
            description=f"{interaction.user.mention} jogou a moeda... e saiu **{resultado}**",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    # O comando /fato
    @app_commands.command(name='fato', description='『💡』Receba um fato aleatório e curioso!')
    async def fato(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Lista de fatos curiosos em português
        fatos = [
            "🧠 O cérebro humano tem aproximadamente 86 bilhões de neurônios.",
            "🐙 Os polvos têm três corações e sangue azul.",
            "🌍 A Terra tem mais de 4,5 bilhões de anos.",
            "🦋 As borboletas provam os alimentos com os pés.",
            "🍯 O mel nunca estraga — arqueólogos já encontraram mel de 3000 anos comestível.",
            "🐘 Os elefantes são os únicos animais que não conseguem pular.",
            "🌊 O oceano cobre cerca de 71% da superfície da Terra.",
            "⚡ Um raio é 5 vezes mais quente que a superfície do Sol.",
            "🦈 Os tubarões são mais antigos que as árvores — existem há mais de 400 milhões de anos.",
            "🐬 Os golfinhos dormem com um olho aberto.",
            "🍕 A palavra 'pizza' aparece pela primeira vez em um documento do ano 997 d.C.",
            "🦴 Bebês nascem com cerca de 270 ossos, adultos têm apenas 206.",
            "🌙 A Lua se afasta da Terra cerca de 3,8 cm por ano.",
            "🐜 As formigas conseguem carregar até 50 vezes o seu próprio peso.",
            "🎵 Ouvir música pode reduzir a ansiedade em até 65%, segundo estudos.",
        ]

        embed = discord.Embed(
            title="💡 Fato Curioso",
            description=random.choice(fatos),
            color=discord.Color.teal()
        )
        embed.set_footer(text="Sabia disso? 🤔")
        await interaction.followup.send(embed=embed)

    # O comando /meme
    @app_commands.command(name='meme', description='『😂』Receba um meme aleatório!')
    async def meme(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Busca a configuração de país do servidor (padrão: brasil)
        pais = database.buscar_pais_memes(interaction.guild.id)
        subreddits = SUBREDDITS_POR_PAIS.get(pais, SUBREDDITS_POR_PAIS['brasil'])

        # Sorteia um subreddit da lista do país configurado
        subreddit_escolhido = random.choice(subreddits)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://meme-api.com/gimme/{subreddit_escolhido}",
                    headers={"User-Agent": "JadeAI Discord Bot"}
                ) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ Não consegui buscar um meme agora. Tente de novo!", ephemeral=True)
                        return

                    data = await resp.json()

            # Filtra conteúdo NSFW
            if data.get("nsfw", False):
                await interaction.followup.send("❌ O meme gerado era inapropriado, tente de novo!", ephemeral=True)
                return

            embed = discord.Embed(
                title=data.get("title", "Meme"),
                color=discord.Color.orange()
            )
            embed.set_image(url=data["url"])
            embed.set_footer(text=f"👍 {data.get('ups', 0)} upvotes · r/{data.get('subreddit', subreddit_escolhido)} · {NOMES_PAISES.get(pais, pais)}")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao buscar meme: `{e}`", ephemeral=True)

    # ═══════════════════════════════════════
    # /config-memes — escolhe o país de origem dos memes
    # ═══════════════════════════════════════
    @app_commands.command(name='config-memes', description='『⚙️』Configura de qual país vêm os memes do servidor')
    @app_commands.describe(pais='País/região de origem dos memes')
    @app_commands.choices(pais=[
        app_commands.Choice(name='🇧🇷 Brasil', value='brasil'),
        app_commands.Choice(name='🇺🇸 Estados Unidos', value='eua'),
        app_commands.Choice(name='🌍 Global (sem filtro)', value='global'),
    ])
    @app_commands.default_permissions(administrator=True)
    async def config_memes(self, interaction: discord.Interaction, pais: app_commands.Choice[str]):
        database.definir_pais_memes(interaction.guild.id, pais.value)

        embed = discord.Embed(
            title="⚙️ Configuração de Memes Atualizada",
            description=f"Os memes deste servidor agora vêm de: **{NOMES_PAISES.get(pais.value, pais.value)}**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Diversao(bot))