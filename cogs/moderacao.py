import discord
from discord import app_commands
from discord.ext import commands
import database

class Moderacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════
    # /kick
    # ═══════════════════════════════════════
    @app_commands.command(name='kick', description='『⚔️』Expulsa um membro do servidor')
    @app_commands.describe(usuario='Membro a ser expulso', motivo='Motivo da expulsão')
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo informado"):
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Você não pode expulsar alguém com cargo igual ou superior ao seu!", ephemeral=True)
            return

        await usuario.kick(reason=motivo)

        embed = discord.Embed(
            title="⚔️ Membro Expulso",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 Usuário", value=usuario.mention, inline=True)
        embed.add_field(name="🛡️ Moderador", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # /ban
    # ═══════════════════════════════════════
    @app_commands.command(name='ban', description='『🔨』Bane um membro do servidor')
    @app_commands.describe(usuario='Membro a ser banido', motivo='Motivo do banimento')
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo informado"):
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Você não pode banir alguém com cargo igual ou superior ao seu!", ephemeral=True)
            return

        await usuario.ban(reason=motivo)

        embed = discord.Embed(
            title="🔨 Membro Banido",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 Usuário", value=usuario.mention, inline=True)
        embed.add_field(name="🛡️ Moderador", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # /mute (timeout do Discord)
    # ═══════════════════════════════════════
    @app_commands.command(name='mute', description='『🔇』Silencia um membro por um tempo determinado')
    @app_commands.describe(usuario='Membro a ser silenciado', minutos='Duração em minutos', motivo='Motivo')
    @app_commands.default_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, usuario: discord.Member, minutos: int, motivo: str = "Sem motivo informado"):
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Você não pode silenciar alguém com cargo igual ou superior ao seu!", ephemeral=True)
            return

        from datetime import timedelta
        duracao = timedelta(minutes=minutos)
        await usuario.timeout(duracao, reason=motivo)

        embed = discord.Embed(
            title="🔇 Membro Silenciado",
            color=discord.Color.dark_gray()
        )
        embed.add_field(name="👤 Usuário", value=usuario.mention, inline=True)
        embed.add_field(name="⏱️ Duração", value=f"`{minutos}` minutos", inline=True)
        embed.add_field(name="🛡️ Moderador", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # /warn
    # ═══════════════════════════════════════
    @app_commands.command(name='warn', description='『⚠️』Avisa um membro e registra o aviso')
    @app_commands.describe(usuario='Membro a ser avisado', motivo='Motivo do aviso')
    @app_commands.default_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str):
        database.adicionar_aviso(usuario.id, interaction.guild.id, motivo)
        total_avisos = len(database.buscar_avisos(usuario.id, interaction.guild.id))

        embed = discord.Embed(
            title="⚠️ Aviso Registrado",
            color=discord.Color.yellow()
        )
        embed.add_field(name="👤 Usuário", value=usuario.mention, inline=True)
        embed.add_field(name="🛡️ Moderador", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.add_field(name="📊 Total de avisos", value=f"`{total_avisos}`", inline=False)
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # /avisos
    # ═══════════════════════════════════════
    @app_commands.command(name='avisos', description='『📋』Lista os avisos de um membro')
    @app_commands.describe(usuario='Membro a consultar')
    @app_commands.default_permissions(moderate_members=True)
    async def avisos(self, interaction: discord.Interaction, usuario: discord.Member):
        lista = database.buscar_avisos(usuario.id, interaction.guild.id)

        embed = discord.Embed(
            title=f"📋 Avisos de {usuario.display_name}",
            color=discord.Color.yellow()
        )

        if not lista:
            embed.description = "✅ Este usuário não tem nenhum aviso!"
        else:
            for aviso_id, motivo, data in lista:
                embed.add_field(name=f"Aviso #{aviso_id} — {data}", value=motivo, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ═══════════════════════════════════════
    # /limparavisos
    # ═══════════════════════════════════════
    @app_commands.command(name='limparavisos', description='『🧹』Remove todos os avisos de um membro')
    @app_commands.describe(usuario='Membro a ter avisos removidos')
    @app_commands.default_permissions(administrator=True)
    async def limparavisos(self, interaction: discord.Interaction, usuario: discord.Member):
        database.limpar_avisos(usuario.id, interaction.guild.id)
        await interaction.response.send_message(f"✅ Todos os avisos de {usuario.mention} foram removidos.", ephemeral=True)

    # ═══════════════════════════════════════
    # /limpar
    # ═══════════════════════════════════════
    @app_commands.command(name='limpar', description='『🗑️』Apaga mensagens do canal')
    @app_commands.describe(quantidade='Quantidade de mensagens a apagar (máx. 100)')
    @app_commands.default_permissions(manage_messages=True)
    async def limpar(self, interaction: discord.Interaction, quantidade: int):
        if quantidade < 1 or quantidade > 100:
            await interaction.response.send_message("❌ Informe um número entre 1 e 100.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        apagadas = await interaction.channel.purge(limit=quantidade)
        await interaction.followup.send(f"🗑️ `{len(apagadas)}` mensagens apagadas.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderacao(bot))