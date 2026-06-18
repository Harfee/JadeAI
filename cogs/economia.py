import discord
from discord import app_commands
from discord.ext import commands
import database
import random
from datetime import datetime, date

class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # O comando /saldo
    @app_commands.command(name='saldo', description='『💰』Veja seu saldo de moedas neste servidor')
    @app_commands.describe(usuario='Usuário a consultar (deixe em branco para ver o seu)')
    async def saldo(self, interaction: discord.Interaction, usuario: discord.Member = None):
        usuario = usuario or interaction.user
        saldo = database.buscar_saldo(usuario.id, interaction.guild.id)

        embed = discord.Embed(
            title=f"💰 Saldo de {usuario.display_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=usuario.display_avatar.url)
        embed.add_field(name="💵 Moedas", value=f"`{saldo}` moedas", inline=False)
        await interaction.response.send_message(embed=embed)

    # O comando /diario
    @app_commands.command(name='diario', description='『🎁』Resgate suas moedas diárias')
    async def diario(self, interaction: discord.Interaction):
        hoje = str(date.today())
        ultimo = database.buscar_ultimo_diario(interaction.user.id, interaction.guild.id)

        if ultimo == hoje:
            embed = discord.Embed(
                title="⏳ Já resgatado hoje!",
                description="Você já pegou suas moedas diárias hoje. Volte amanhã!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Valor aleatório entre 50 e 200
        ganho = random.randint(50, 200)
        database.atualizar_saldo(interaction.user.id, interaction.guild.id, ganho)
        database.atualizar_ultimo_diario(interaction.user.id, interaction.guild.id, hoje)

        saldo_atual = database.buscar_saldo(interaction.user.id, interaction.guild.id)

        embed = discord.Embed(
            title="🎁 Moedas Diárias Resgatadas!",
            color=discord.Color.green()
        )
        embed.add_field(name="✨ Você ganhou", value=f"`{ganho}` moedas", inline=True)
        embed.add_field(name="💰 Saldo total", value=f"`{saldo_atual}` moedas", inline=True)
        embed.set_footer(text="Volte amanhã para mais moedas!")
        await interaction.response.send_message(embed=embed)

    # O comando /transferir
    @app_commands.command(name='transferir', description='『💸』Transfira moedas para outro usuário')
    @app_commands.describe(usuario='Para quem deseja transferir', quantidade='Quantidade de moedas')
    async def transferir(self, interaction: discord.Interaction, usuario: discord.Member, quantidade: int):
        if usuario == interaction.user:
            await interaction.response.send_message("❌ Você não pode transferir para si mesmo!", ephemeral=True)
            return

        if quantidade <= 0:
            await interaction.response.send_message("❌ Informe uma quantidade válida!", ephemeral=True)
            return

        saldo_atual = database.buscar_saldo(interaction.user.id, interaction.guild.id)

        if saldo_atual < quantidade:
            await interaction.response.send_message(
                f"❌ Saldo insuficiente! Você tem apenas `{saldo_atual}` moedas.",
                ephemeral=True
            )
            return

        database.transferir_saldo(interaction.user.id, usuario.id, interaction.guild.id, quantidade)

        embed = discord.Embed(
            title="💸 Transferência Realizada!",
            color=discord.Color.green()
        )
        embed.add_field(name="📤 De", value=interaction.user.mention, inline=True)
        embed.add_field(name="📥 Para", value=usuario.mention, inline=True)
        embed.add_field(name="💵 Valor", value=f"`{quantidade}` moedas", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economia(bot))