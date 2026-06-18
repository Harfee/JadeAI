import discord
from discord import app_commands
from discord.ext import commands
import database
import random
import time

# Cooldown compartilhado com utilidades para não contar XP duas vezes
_cooldowns = {}
COOLDOWN_SEGUNDOS = 60

class Niveis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignora bot e DMs
        if message.author == self.bot.user or not message.guild:
            return

        chave = (message.author.id, message.guild.id)
        agora = time.time()
        ultimo = _cooldowns.get(chave, 0)

        if agora - ultimo >= COOLDOWN_SEGUNDOS:
            # Busca nível antes
            pontos_antes = database.buscar_pontos(message.author.id, message.guild.id)
            nivel_antes, _, _ = database.calcular_nivel(pontos_antes)

            # Adiciona XP
            xp_ganho = random.randint(1, 10)
            database.atualizar_pontos(message.author.id, message.guild.id, xp_ganho)
            _cooldowns[chave] = agora

            # Busca nível depois
            pontos_depois = database.buscar_pontos(message.author.id, message.guild.id)
            nivel_depois, _, _ = database.calcular_nivel(pontos_depois)

            # Anuncia level up se subiu de nível
            if nivel_depois > nivel_antes:
                embed = discord.Embed(
                    title="🎉 LEVEL UP!",
                    description=(
                        f"Parabéns {message.author.mention}!\n"
                        f"Você subiu para o **Nível {nivel_depois}**! 🚀"
                    ),
                    color=discord.Color.gold()
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                await message.channel.send(embed=embed)

    # O comando /nivel
    @app_commands.command(name='nivel', description='『📈』Veja seu nível e progresso de XP')
    @app_commands.describe(usuario='Usuário a consultar (deixe em branco para ver o seu)')
    async def nivel(self, interaction: discord.Interaction, usuario: discord.Member = None):
        usuario = usuario or interaction.user
        pontos = database.buscar_pontos(usuario.id, interaction.guild.id)
        nivel_atual, faltam, pontos_proximo = database.calcular_nivel(pontos)

        # Barra de progresso visual
        pontos_nivel_atual = pontos_proximo - faltam
        progresso_total = pontos_proximo - (50 * (nivel_atual ** 2))
        progresso_feito = pontos - (50 * (nivel_atual ** 2))
        percentual = progresso_feito / progresso_total if progresso_total > 0 else 0
        barras_cheias = int(percentual * 20)
        barra = "█" * barras_cheias + "░" * (20 - barras_cheias)

        embed = discord.Embed(
            title=f"📈 Nível de {usuario.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=usuario.display_avatar.url)
        embed.add_field(name="🏅 Nível atual", value=f"`{nivel_atual}`", inline=True)
        embed.add_field(name="✨ XP total", value=f"`{pontos}`", inline=True)
        embed.add_field(name="⏳ Faltam para o próximo", value=f"`{faltam}` XP", inline=True)
        embed.add_field(name="📊 Progresso", value=f"`[{barra}]` {int(percentual * 100)}%", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Niveis(bot))