import discord
from discord import app_commands
from discord.ext import commands
import database
import random
import time

# Cooldown: guarda o timestamp da última mensagem por (user_id, servidor_id)
_cooldowns = {}
COOLDOWN_SEGUNDOS = 60

class Utilidades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='ajuda', description='『❓』Veja todos os meus comandos disponíveis')
    async def ajuda(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="『❓』𝑪𝒆𝒏𝒕𝒓𝒂𝒍 𝒅𝒆 𝑨𝒋𝒖𝒅𝒂",
            description="Aqui estão todos os comandos da **『🔮』𝑱𝒂𝒅𝒆 𝑨𝑰**:",
            color=discord.Color.blue()
        )
        embed.add_field(name="🛠️ Utilidades", value="`/jade` `/ping` `/userinfo` `/serverinfo` `/perfil` `/rank` `/rank-global`", inline=False)
        embed.add_field(name="⚔️ Moderação", value="`/kick` `/ban` `/mute` `/warn` `/avisos` `/limparavisos` `/limpar`", inline=False)
        embed.add_field(name="📈 Níveis", value="`/nivel`", inline=False)
        embed.add_field(name="💰 Economia", value="`/saldo` `/diario` `/transferir`", inline=False)
        embed.add_field(name="🤖 Inteligência Artificial", value="`/perguntar` `/resumir` `/imagemAI`", inline=False)
        embed.add_field(name="🎮 Entretenimento", value="`/beijar` `/tapa` `/sixseven` `/dado` `/cara-coroa` `/fato` `/meme`", inline=False)
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignora o próprio bot
        if message.author == self.bot.user:
            return

        # Ignora DMs
        if not message.guild:
            return

        # Sistema de XP com cooldown de 60s por usuário por servidor
        chave = (message.author.id, message.guild.id)
        agora = time.time()
        ultimo = _cooldowns.get(chave, 0)

        if agora - ultimo >= COOLDOWN_SEGUNDOS:
            xp_ganho = random.randint(1, 10)
            database.atualizar_pontos(message.author.id, message.guild.id, xp_ganho)
            _cooldowns[chave] = agora

        # Responde !help com o painel de ajuda
        if message.content.lower() == "!help":
            embed = discord.Embed(
                title="『❓』𝑪𝒆𝒏𝒕𝒓𝒂𝒍 𝒅𝒆 𝑨𝒋𝒖𝒅𝒂",
                description="Use os comandos barra (`/`) para interagir comigo!",
                color=discord.Color.blue()
            )
            embed.add_field(name="🛠️ Utilidades", value="`/jade` `/ping` `/userinfo` `/serverinfo` `/perfil` `/rank` `/rank-global`", inline=False)
            embed.add_field(name="⚔️ Moderação", value="`/kick` `/ban` `/mute` `/warn` `/avisos` `/limparavisos` `/limpar`", inline=False)
            embed.add_field(name="📈 Níveis", value="`/nivel`", inline=False)
            embed.add_field(name="💰 Economia", value="`/saldo` `/diario` `/transferir`", inline=False)
            embed.add_field(name="🤖 IA", value="`/perguntar` `/resumir` `/imagemAI`", inline=False)
            embed.add_field(name="🎮 Entretenimento", value="`/beijar` `/tapa` `/sixseven` `/dado` `/cara-coroa` `/fato` `/meme`", inline=False)
            await message.channel.send(embed=embed)

    # O comando /jade
    @app_commands.command(name='jade', description='『🔮』Apresentação da Jade AI')
    async def jade(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="『🔮』𝑱𝒂𝒅𝒆 𝑨𝑰",
            description=(
                "Olá! Eu sou a **Jade AI**.\n\n"
                "Sou uma inteligência artificial criada para ajudar a automatizar, gerenciar e trazer "
                "recursos inteligentes para o servidor.\n\n"
                "⚡ Módulos ativos: **Utilidades, Moderação, Níveis, Economia, IA e Entretenimento**\n\n"
                "⚙️ Ainda estou em **fase de testes!**"
            ),
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

    # O comando /ping
    @app_commands.command(name='ping', description='Mostra o tempo de resposta da Jade AI')
    async def ping(self, interaction: discord.Interaction):
        latencia = round(self.bot.latency * 1000)
        await interaction.response.send_message(f'🏓 **Pong!** Latência atual: `{latencia}ms`.')

    # O comando /userinfo
    @app_commands.command(name='userinfo', description='Mostra informações detalhadas de um usuário')
    @app_commands.describe(usuario='O usuário que deseja consultar (deixe em branco para ver o seu)')
    async def userinfo(self, interaction: discord.Interaction, usuario: discord.Member = None):
        usuario = usuario or interaction.user
        criado_em = usuario.created_at.strftime('%d/%m/%Y às %H:%M')
        entrou_em = usuario.joined_at.strftime('%d/%m/%Y às %H:%M')

        cargos = [cargo.mention for cargo in usuario.roles if cargo.name != "@everyone"]
        lista_cargos = ", ".join(cargos) if cargos else "Nenhum cargo"

        embed = discord.Embed(title=f"👤 Informações de {usuario.name}", color=discord.Color.teal())
        embed.set_thumbnail(url=usuario.display_avatar.url)
        embed.add_field(name="🆔 ID", value=usuario.id, inline=False)
        embed.add_field(name="📅 Conta criada em", value=criado_em, inline=True)
        embed.add_field(name="📥 Entrou no servidor em", value=entrou_em, inline=True)
        embed.add_field(name=f"🎖️ Cargos ({len(cargos)})", value=lista_cargos, inline=False)

        await interaction.response.send_message(embed=embed)

    # O comando /serverinfo
    @app_commands.command(name='serverinfo', description='Mostra informações gerais deste servidor')
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        criado_em = guild.created_at.strftime('%d/%m/%Y às %H:%M')

        embed = discord.Embed(title=f"🏰 {guild.name}", color=discord.Color.purple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👑 Dono", value=guild.owner.mention, inline=True)
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Criado em", value=criado_em, inline=False)
        embed.add_field(name="👥 Membros", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="💬 Canais", value=f"`{len(guild.channels)}`", inline=True)

        await interaction.response.send_message(embed=embed)

    # O comando /perfil
    @app_commands.command(name='perfil', description='『👤』Veja seu perfil neste servidor')
    async def perfil(self, interaction: discord.Interaction):
        pontos = database.buscar_pontos(interaction.user.id, interaction.guild.id)
        saldo  = database.buscar_saldo(interaction.user.id, interaction.guild.id)
        nivel, faltam, _ = database.calcular_nivel(pontos)

        embed = discord.Embed(
            title=f"『👤』Perfil de {interaction.user.display_name}",
            color=discord.Color.teal()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="✨ XP", value=f"`{pontos}` pontos", inline=True)
        embed.add_field(name="📈 Nível", value=f"`{nivel}`", inline=True)
        embed.add_field(name="⏳ Faltam para o próximo", value=f"`{faltam}` XP", inline=True)
        embed.add_field(name="💰 Saldo", value=f"`{saldo}` moedas", inline=True)

        await interaction.response.send_message(embed=embed)

    # O comando /rank
    @app_commands.command(name='rank', description='『🏆』Ranking de XP deste servidor')
    async def rank(self, interaction: discord.Interaction):
        ranking = database.buscar_ranking(interaction.guild.id, limite=10)

        if not ranking:
            await interaction.response.send_message("Nenhum XP registrado neste servidor ainda!")
            return

        embed = discord.Embed(
            title=f"『🏆』Ranking de {interaction.guild.name}",
            color=discord.Color.gold()
        )

        medalhas = ["🥇", "🥈", "🥉"]
        linhas = []

        for i, (user_id, pontos) in enumerate(ranking):
            medalha = medalhas[i] if i < 3 else f"`#{i + 1}`"
            membro = interaction.guild.get_member(user_id)
            nome = membro.display_name if membro else f"Usuário {user_id}"
            nivel, _, _ = database.calcular_nivel(pontos)
            linhas.append(f"{medalha} **{nome}** — `{pontos}` XP · Nível `{nivel}`")

        embed.description = "\n".join(linhas)
        await interaction.response.send_message(embed=embed)

    # O comando /rank-global
    @app_commands.command(name='rank-global', description='『🌍』Ranking global de XP entre todos os servidores')
    async def rank_global(self, interaction: discord.Interaction):
        ranking = database.buscar_ranking_global(limite=10)

        if not ranking:
            await interaction.response.send_message("Nenhum XP registrado ainda!")
            return

        embed = discord.Embed(
            title="『🌍』Ranking Global de XP",
            color=discord.Color.gold()
        )

        medalhas = ["🥇", "🥈", "🥉"]
        linhas = []

        for i, (user_id, pontos) in enumerate(ranking):
            medalha = medalhas[i] if i < 3 else f"`#{i + 1}`"
            # Tenta achar o usuário em qualquer servidor que o bot esteja
            usuario = self.bot.get_user(user_id)
            nome = usuario.display_name if usuario else f"Usuário {user_id}"
            nivel, _, _ = database.calcular_nivel(pontos)
            linhas.append(f"{medalha} **{nome}** — `{pontos}` XP · Nível `{nivel}`")

        embed.description = "\n".join(linhas)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilidades(bot))