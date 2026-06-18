import discord
from discord import app_commands
from discord.ext import commands
import database

class BoasVindas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def montar_embed_boasvindas(self, member: discord.Member):
        """Monta o embed de boas-vindas usando a configuração do servidor."""
        config = database.buscar_config_boasvindas(member.guild.id)

        # Substitui as variáveis da mensagem personalizada
        mensagem = config['mensagem'].format(
            usuario=member.mention,
            nome=member.display_name,
            servidor=member.guild.name,
        )

        # Converte a cor de hex (#5b8dee) para discord.Color
        try:
            cor = discord.Color(int(config['cor'].replace('#', ''), 16))
        except Exception:
            cor = discord.Color.blue()

        embed = discord.Embed(
            title="👋 Bem-vindo(a)!",
            description=mensagem,
            color=cor
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 ID do usuário", value=f"`{member.id}`", inline=False)
        embed.add_field(name="👥 Membro número", value=f"`#{member.guild.member_count}`", inline=True)
        embed.set_footer(text=member.guild.name, icon_url=member.guild.icon.url if member.guild.icon else None)
        embed.timestamp = discord.utils.utcnow()

        return embed, config

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Envia mensagem de boas-vindas quando alguém entra no servidor."""
        embed, config = self.montar_embed_boasvindas(member)

        # Usa o canal configurado, ou cai pro canal de sistema, ou pro primeiro disponível
        canal = None
        if config['canal_id']:
            canal = member.guild.get_channel(config['canal_id'])

        if canal is None:
            canal = member.guild.system_channel

        if canal is None:
            for ch in member.guild.text_channels:
                if ch.permissions_for(member.guild.me).send_messages:
                    canal = ch
                    break

        if canal:
            await canal.send(embed=embed)

        # Cargo automático, se configurado
        if config['cargo_id']:
            cargo = member.guild.get_role(config['cargo_id'])
            if cargo:
                try:
                    await member.add_roles(cargo, reason="Cargo automático de boas-vindas")
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Avisa quando alguém sai do servidor."""
        config = database.buscar_config_boasvindas(member.guild.id)

        canal = None
        if config['canal_id']:
            canal = member.guild.get_channel(config['canal_id'])

        if canal is None:
            canal = member.guild.system_channel

        if canal is None:
            for ch in member.guild.text_channels:
                if ch.permissions_for(member.guild.me).send_messages:
                    canal = ch
                    break

        if canal is None:
            return

        embed = discord.Embed(
            title="👋 Até logo!",
            description=f"**{member.display_name}** saiu do servidor. Sentiremos sua falta!",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await canal.send(embed=embed)

    # ═══════════════════════════════════════
    # /config-boasvindas — configura o sistema
    # ═══════════════════════════════════════
    @app_commands.command(name='config-boasvindas', description='『⚙️』Configura o sistema de boas-vindas do servidor')
    @app_commands.describe(
        canal='Canal onde as boas-vindas serão enviadas',
        mensagem='Mensagem personalizada. Use {usuario}, {nome} e {servidor}',
        cor='Cor do embed em hexadecimal (ex: #5b8dee)',
        cargo='Cargo dado automaticamente a quem entrar'
    )
    @app_commands.default_permissions(administrator=True)
    async def config_boasvindas(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel = None,
        mensagem: str = None,
        cor: str = None,
        cargo: discord.Role = None
    ):
        if canal is None and mensagem is None and cor is None and cargo is None:
            await interaction.response.send_message(
                "❌ Informe pelo menos uma configuração para alterar (canal, mensagem, cor ou cargo).",
                ephemeral=True
            )
            return

        if canal:
            database.definir_canal_boasvindas(interaction.guild.id, canal.id)
        if mensagem:
            database.definir_mensagem_boasvindas(interaction.guild.id, mensagem)
        if cor:
            # Valida o formato da cor
            cor_formatada = cor if cor.startswith('#') else f'#{cor}'
            try:
                int(cor_formatada.replace('#', ''), 16)
                database.definir_cor_boasvindas(interaction.guild.id, cor_formatada)
            except ValueError:
                await interaction.response.send_message("❌ Cor inválida! Use o formato hexadecimal, ex: `#5b8dee`.", ephemeral=True)
                return
        if cargo:
            database.definir_cargo_boasvindas(interaction.guild.id, cargo.id)

        config_atual = database.buscar_config_boasvindas(interaction.guild.id)

        embed = discord.Embed(
            title="⚙️ Configuração de Boas-vindas Atualizada",
            color=discord.Color.green()
        )
        canal_atual = interaction.guild.get_channel(config_atual['canal_id']) if config_atual['canal_id'] else None
        cargo_atual = interaction.guild.get_role(config_atual['cargo_id']) if config_atual['cargo_id'] else None

        embed.add_field(name="📍 Canal", value=canal_atual.mention if canal_atual else "Canal de sistema (padrão)", inline=False)
        embed.add_field(name="💬 Mensagem", value=config_atual['mensagem'], inline=False)
        embed.add_field(name="🎨 Cor", value=config_atual['cor'], inline=True)
        embed.add_field(name="🎖️ Cargo automático", value=cargo_atual.mention if cargo_atual else "Nenhum", inline=True)
        embed.set_footer(text="Use /testar-boasvindas para ver como vai ficar!")

        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # /testar-boasvindas — simula a entrada
    # ═══════════════════════════════════════
    @app_commands.command(name='testar-boasvindas', description='『🧪』Testa como a mensagem de boas-vindas vai aparecer')
    @app_commands.default_permissions(administrator=True)
    async def testar_boasvindas(self, interaction: discord.Interaction):
        # Usa o próprio usuário que rodou o comando como exemplo
        embed, config = self.montar_embed_boasvindas(interaction.user)

        await interaction.response.send_message(
            content="🧪 **Modo de teste** — é assim que vai aparecer quando alguém entrar:",
            embed=embed
        )

async def setup(bot):
    await bot.add_cog(BoasVindas(bot))