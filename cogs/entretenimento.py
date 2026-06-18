import discord
from discord import app_commands
from discord.ext import commands
import random
import database

class Entretenimento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Comando /beijar
    @app_commands.command(name='beijar', description='Dê um beijo carinhoso em alguém!')
    @app_commands.describe(usuario='Quem você quer beijar?')
    async def beijar(self, interaction: discord.Interaction, usuario: discord.Member):
        gifs_beijo = [
            "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3ams3MzB6NzU4d3BuYWZla3dxNXdlamNlOTNjM29vaG00bHdmcHQxZCZlcD12MV9naWZzX3RyZW5kaW5nJmN0PWc/MDJ9IbxxvDUQM/giphy.gif"
        ]

        # +5 pontos de XP por usar o comando
        database.atualizar_pontos(interaction.user.id, interaction.guild.id, 5)

        embed = discord.Embed(
            description=f"💋 {interaction.user.mention} deu um beijo em {usuario.mention}!",
            color=discord.Color.brand_red()
        )
        embed.set_image(url=random.choice(gifs_beijo))
        await interaction.response.send_message(embed=embed)

    # Comando /tapa
    @app_commands.command(name='tapa', description='Dê um tapa de brincadeira em alguém!')
    @app_commands.describe(usuario='Quem vai levar o tapa?')
    async def tapa(self, interaction: discord.Interaction, usuario: discord.Member):
        gifs_tapa = [
            "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3Y3Nkdzg1anlwbHA1cTVqeHo3MHU0dWxtem94NG45MmYyZjB5MXF2aiZlcD12MV9naWZzX3JlbGF0ZWQmY3Q9Zw/JXuGatu6v9pUA/giphy.gif",
            "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExcXV0bDBhZjRyODk0MTV5ZWhqeTR3ejFnNGtvMzlxdmFnOGY5N2ZqZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/srD8JByP9u3zW/giphy.gif",
            "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3cWR5YzA1MjNiaWwwa3dqOTdnbHdoMmZkdm1iOWlvcDF2bGFpczRhNyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/YNmbs2TI41A7n3GNCW/giphy.gif"
        ]

        # +5 pontos de XP por usar o comando
        database.atualizar_pontos(interaction.user.id, interaction.guild.id, 5)

        embed = discord.Embed(
            description=f"💥 {interaction.user.mention} deu um tapa em {usuario.mention}!",
            color=discord.Color.orange()
        )
        embed.set_image(url=random.choice(gifs_tapa))
        await interaction.response.send_message(embed=embed)

    # Comando /sixseven
    @app_commands.command(name='sixseven', description='Faça um 6 7!')
    @app_commands.describe(usuario='Quem vai levar?')
    async def sixseven(self, interaction: discord.Interaction, usuario: discord.Member):
        six_seven = [
            "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3a2x4b3FhMDV4azR6cXkyOTE0Y2R4NG9xMnFqYjBlenVmMXhkMHpnayZlcD12MV9naWZzX3RyZW5kaW5nJmN0PWc/TKa7fQzChHylCQ89to/giphy.gif",
            "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExb2RvMjVjMjU5NTB3cHB0MGk5cnNiZjdlbmtqdHI0d3AwcG14Z3YxeiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/08uBcURaMq6vA93TGc/giphy.gif",
            "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExb2RvMjVjMjU5NTB3cHB0MGk5cnNiZjdlbmtqdHI0d3AwcG14Z3YxeiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/5u55OjbjPcho54asJ6/giphy.gif",
            "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExb2RvMjVjMjU5NTB3cHB0MGk5cnNiZjdlbmtqdHI0d3AwcG14Z3YxeiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/Rgx5zJxzPCB1AZOTNU/giphy.gif"
        ]

        # +5 pontos de XP por usar o comando
        database.atualizar_pontos(interaction.user.id, interaction.guild.id, 5)

        embed = discord.Embed(
            description=f"{interaction.user.mention} fez um 67 em {usuario.mention}!",
            color=discord.Color.blue()
        )
        embed.set_image(url=random.choice(six_seven))
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Entretenimento(bot))