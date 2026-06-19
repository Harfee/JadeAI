import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os

# Caminho do FFmpeg: usa o local na pasta do bot (Windows) se existir,
# senão usa o "ffmpeg" do sistema (Linux/Railway, onde ele é instalado via Nixpacks)
_ffmpeg_local = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ffmpeg', 'bin', 'ffmpeg.exe')
FFMPEG_PATH = _ffmpeg_local if os.path.isfile(_ffmpeg_local) else 'ffmpeg'

# Opções do yt-dlp para baixar o áudio
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

# Opções do yt-dlp para buscar vídeos relacionados (recomendações)
YTDL_RELACIONADOS_OPTIONS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,
    'source_address': '0.0.0.0',
}

# Opções do FFmpeg para streaming
FFMPEG_OPTIONS = {
    'executable': FFMPEG_PATH,
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

# Fila de músicas por servidor
filas = {}

# Tempo de inatividade antes de sair (5 minutos)
TIMEOUT_INATIVIDADE = 5 * 60


def eh_link_spotify(texto):
    """Verifica se o texto enviado é um link do Spotify."""
    return 'open.spotify.com' in texto or 'spotify.com' in texto


def eh_link_playlist_youtube(texto):
    """Verifica se o link é de uma playlist do YouTube."""
    return 'list=' in texto


class BotoesPlayer(discord.ui.View):
    """Botões interativos para controlar a música direto no embed."""

    def __init__(self, cog, guild_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.secondary, custom_id="pausar_player")
    async def pausar(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("❌ Não estou tocando nada!", ephemeral=True)
            return

        if vc.is_playing():
            vc.pause()
            self.cog.iniciar_inatividade(interaction.guild.id, interaction.channel)
            button.emoji = "▶️"
            await interaction.response.edit_message(view=self)
        elif vc.is_paused():
            vc.resume()
            self.cog.cancelar_inatividade(interaction.guild.id)
            button.emoji = "⏸️"
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message("❌ Não estou tocando nada!", ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="pular_player")
    async def pular(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            await interaction.response.send_message("❌ Não estou tocando nada!", ephemeral=True)
            return

        await interaction.response.send_message("⏭️ Música pulada!")
        vc.stop()  # Dispara o callback "after" que toca a próxima automaticamente

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="parar_player")
    async def parar(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("❌ Não estou em nenhum canal de voz!", ephemeral=True)
            return

        self.cog._saida_intencional.add(interaction.guild.id)
        self.cog.cancelar_inatividade(interaction.guild.id)
        filas[interaction.guild.id] = []
        await vc.disconnect()

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("⏹️ Música parada e desconectado do canal de voz!")

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, custom_id="repetir_player")
    async def repetir(self, interaction: discord.Interaction, button: discord.ui.Button):
        info = self.cog._tocando_agora.get(interaction.guild.id)
        if not info:
            await interaction.response.send_message("❌ Não há música tocando para repetir!", ephemeral=True)
            return

        fila = self.cog.get_fila(interaction.guild.id)
        fila.insert(0, info)
        await interaction.response.send_message("🔁 Música adicionada de novo no início da fila!", ephemeral=True)


class BotoesRecomendacoes(discord.ui.View):
    """Botões com músicas recomendadas, mostrados quando a fila esvazia."""

    def __init__(self, cog, guild_id, canal_texto, recomendacoes):
        super().__init__(timeout=300)  # Expira em 5 minutos
        self.cog = cog
        self.guild_id = guild_id
        self.canal_texto = canal_texto

        # Cria um botão para cada recomendação (máximo 5 por linha de botões do Discord)
        for i, rec in enumerate(recomendacoes[:4]):
            titulo_curto = rec['titulo'][:60] + ("..." if len(rec['titulo']) > 60 else "")
            botao = discord.ui.Button(
                label=titulo_curto,
                style=discord.ButtonStyle.secondary,
                custom_id=f"rec_{i}"
            )
            botao.callback = self.criar_callback(rec)
            self.add_item(botao)

    def criar_callback(self, recomendacao):
        async def callback(interaction: discord.Interaction):
            try:
                await interaction.response.defer()
            except discord.errors.NotFound:
                return
            except discord.errors.HTTPException:
                return

            vc = interaction.guild.voice_client
            if not vc or not vc.is_connected():
                await interaction.followup.send("❌ Não estou mais conectado a um canal de voz!", ephemeral=True)
                return

            try:
                info = await self.cog.buscar_musica(recomendacao['url'])
            except Exception as e:
                await interaction.followup.send(f"❌ Não consegui carregar essa música: `{e}`", ephemeral=True)
                return

            fila = self.cog.get_fila(interaction.guild.id)

            if vc.is_playing() or vc.is_paused():
                fila.append(info)
                await interaction.followup.send(f"📋 **{info['titulo']}** adicionada à fila!")
            else:
                self.cog.cancelar_inatividade(interaction.guild.id)
                fila.append(info)
                self.cog.tocar_proxima(interaction.guild.id, interaction.channel)
                await interaction.followup.send(f"🎵 Tocando agora: **{info['titulo']}**")

        return callback


class Musica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Tarefa de inatividade por servidor
        self._tasks_inatividade = {}
        # Guarda se o bot foi desconectado intencionalmente (por /parar) para não duplicar avisos
        self._saida_intencional = set()
        # Guarda a última música tocada por servidor (para o botão de repetir)
        self._tocando_agora = {}

    def get_fila(self, guild_id):
        """Retorna a fila do servidor, criando uma se não existir."""
        if guild_id not in filas:
            filas[guild_id] = []
        return filas[guild_id]

    def cancelar_inatividade(self, guild_id):
        """Cancela a tarefa de inatividade de um servidor."""
        task = self._tasks_inatividade.get(guild_id)
        if task and not task.done():
            task.cancel()

    def iniciar_inatividade(self, guild_id, canal_texto):
        """Inicia o timer de inatividade — sai após 5 minutos sem tocar."""
        self.cancelar_inatividade(guild_id)

        async def aguardar_e_sair():
            await asyncio.sleep(TIMEOUT_INATIVIDADE)
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            vc = guild.voice_client
            if vc and not vc.is_playing() and not vc.is_paused():
                filas[guild_id] = []
                self._saida_intencional.add(guild_id)
                await vc.disconnect()
                try:
                    await canal_texto.send("⏹️ Saí do canal de voz por inatividade de **5 minutos**.")
                except Exception:
                    pass

        task = self.bot.loop.create_task(aguardar_e_sair())
        self._tasks_inatividade[guild_id] = task

    async def buscar_musica(self, query):
        """Busca a música no YouTube e retorna as informações."""
        loop = asyncio.get_event_loop()

        # Se for URL, usa direto. Se não, pesquisa no YouTube
        if not query.startswith('http'):
            query = f'ytsearch:{query}'

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))

        if 'entries' in data:
            data = data['entries'][0]

        return {
            'url': data['url'],
            'webpage_url': data.get('webpage_url', data['url']),
            'titulo': data.get('title', 'Desconhecido'),
            'duracao': data.get('duration', 0),
            'thumbnail': data.get('thumbnail', None),
            'autor': data.get('uploader', 'Desconhecido'),
            'video_id': data.get('id', None),
        }

    async def buscar_recomendacoes(self, video_id):
        """Busca vídeos relacionados a partir do ID de um vídeo do YouTube."""
        if not video_id:
            return []

        loop = asyncio.get_event_loop()

        def extrair():
            ytdl_rel = yt_dlp.YoutubeDL(YTDL_RELACIONADOS_OPTIONS)
            # Usa a busca por "mix" do YouTube baseada no vídeo atual
            url_mix = f"https://www.youtube.com/watch?v={video_id}&list=RD{video_id}"
            try:
                return ytdl_rel.extract_info(url_mix, download=False)
            except Exception:
                return None

        data = await loop.run_in_executor(None, extrair)

        if not data or 'entries' not in data:
            return []

        recomendacoes = []
        for entry in data['entries']:
            if not entry:
                continue
            # Ignora o próprio vídeo que está tocando
            if entry.get('id') == video_id:
                continue
            recomendacoes.append({
                'titulo': entry.get('title', 'Desconhecido'),
                'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
            })
            if len(recomendacoes) >= 4:
                break

        return recomendacoes

    def tocar_proxima(self, guild_id, canal_texto, avisar=True):
        """Toca a próxima música da fila automaticamente e avisa no canal."""
        fila = self.get_fila(guild_id)
        guild = self.bot.get_guild(guild_id)

        if not guild:
            return

        vc = guild.voice_client

        if not fila:
            # Fila vazia — inicia timer de inatividade e sugere recomendações
            self.iniciar_inatividade(guild_id, canal_texto)
            ultima_musica = self._tocando_agora.get(guild_id)
            if ultima_musica and ultima_musica.get('video_id'):
                asyncio.run_coroutine_threadsafe(
                    self.enviar_recomendacoes(guild_id, canal_texto, ultima_musica['video_id']),
                    self.bot.loop
                )
            return

        musica = fila.pop(0)
        self._tocando_agora[guild_id] = musica
        source = discord.FFmpegPCMAudio(musica['url'], **FFMPEG_OPTIONS)

        if vc and vc.is_connected():
            vc.play(
                source,
                after=lambda e: self.bot.loop.call_soon_threadsafe(
                    self.tocar_proxima, guild_id, canal_texto
                )
            )

            # Avisa no chat qual música começou a tocar agora
            if avisar:
                minutos = musica['duracao'] // 60
                segundos = musica['duracao'] % 60

                embed = discord.Embed(
                    title="🎵 Tocando Agora",
                    color=discord.Color.green()
                )
                embed.add_field(name="🎶 Música", value=musica['titulo'], inline=False)
                embed.add_field(name="👤 Canal", value=musica['autor'], inline=True)
                embed.add_field(name="⏱️ Duração", value=f"`{minutos}:{segundos:02d}`", inline=True)
                if musica['thumbnail']:
                    embed.set_thumbnail(url=musica['thumbnail'])
                embed.set_footer(text="Use os botões abaixo para controlar a música")

                view = BotoesPlayer(self, guild_id)
                asyncio.run_coroutine_threadsafe(canal_texto.send(embed=embed, view=view), self.bot.loop)

    async def enviar_recomendacoes(self, guild_id, canal_texto, video_id):
        """Busca e envia recomendações com botões quando a fila fica vazia."""
        try:
            recomendacoes = await self.buscar_recomendacoes(video_id)
        except Exception:
            return

        if not recomendacoes:
            return

        embed = discord.Embed(
            title="🎧 Que tal continuar ouvindo?",
            description="Aqui estão algumas recomendações baseadas na última música:",
            color=discord.Color.purple()
        )
        view = BotoesRecomendacoes(self, guild_id, canal_texto, recomendacoes)
        try:
            await canal_texto.send(embed=embed, view=view)
        except Exception:
            pass

    # ═══════════════════════════════════════
    # /tocar
    # ═══════════════════════════════════════
    @app_commands.command(name='tocar', description='『🎵』Toca uma música no canal de voz')
    @app_commands.describe(musica='Nome da música, URL do YouTube ou link do Spotify')
    async def tocar(self, interaction: discord.Interaction, musica: str):
        # SEMPRE defer primeiro — antes de qualquer outra coisa.
        # Isso garante que usamos o mínimo de tempo possível dos 3s que o
        # Discord dá para responder a uma interação, evitando o erro
        # "Unknown interaction" (404 / 10062).
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            # A interação já expirou antes do bot conseguir responder.
            # Não tem mais nada a fazer — o Discord já descartou essa interação.
            print(f"⚠️ Interação de /tocar expirou antes do defer (guild: {interaction.guild.id if interaction.guild else '??'})")
            return
        except discord.errors.HTTPException as e:
            print(f"⚠️ Erro HTTP ao tentar defer em /tocar: {e}")
            return

        # Verifica se o usuário está em um canal de voz
        if not interaction.user.voice:
            await interaction.followup.send("❌ Você precisa estar em um canal de voz!", ephemeral=True)
            return

        # Spotify ainda não é suportado diretamente — avisa o usuário
        if eh_link_spotify(musica):
            embed = discord.Embed(
                title="🎧 Spotify (em desenvolvimento)",
                description=(
                    "Ainda não consigo tocar diretamente de links do **Spotify**! 🚧\n\n"
                    "Por enquanto, me diga o **nome da música ou artista** e eu busco a versão "
                    "equivalente no YouTube para você. Essa funcionalidade está sendo desenvolvida!"
                ),
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        canal_voz = interaction.user.voice.channel
        canal_texto = interaction.channel
        vc = interaction.guild.voice_client

        # Conecta ao canal se ainda não estiver conectado
        if vc is None:
            vc = await canal_voz.connect()
        elif vc.channel != canal_voz:
            await vc.move_to(canal_voz)

        # Cancela timer de inatividade pois vai tocar algo
        self.cancelar_inatividade(interaction.guild.id)

        try:
            info = await self.buscar_musica(musica)
        except Exception as e:
            await interaction.followup.send(f"❌ Não consegui encontrar a música: `{e}`")
            return

        fila = self.get_fila(interaction.guild.id)

        # Se já tiver tocando, adiciona na fila
        if vc.is_playing() or vc.is_paused():
            fila.append(info)

            embed = discord.Embed(
                title="📋 Adicionado à Fila",
                color=discord.Color.blue()
            )
            embed.add_field(name="🎵 Música", value=info['titulo'], inline=False)
            embed.add_field(name="👤 Canal", value=info['autor'], inline=True)
            embed.add_field(name="📊 Posição na fila", value=f"`#{len(fila)}`", inline=True)
            if info['thumbnail']:
                embed.set_thumbnail(url=info['thumbnail'])
            await interaction.followup.send(embed=embed)
            return

        # Toca direto
        self._tocando_agora[interaction.guild.id] = info
        source = discord.FFmpegPCMAudio(info['url'], **FFMPEG_OPTIONS)
        vc.play(
            source,
            after=lambda e: self.bot.loop.call_soon_threadsafe(
                self.tocar_proxima, interaction.guild.id, canal_texto
            )
        )

        minutos = info['duracao'] // 60
        segundos = info['duracao'] % 60

        embed = discord.Embed(
            title="🎵 Tocando Agora",
            color=discord.Color.green()
        )
        embed.add_field(name="🎶 Música", value=info['titulo'], inline=False)
        embed.add_field(name="👤 Canal", value=info['autor'], inline=True)
        embed.add_field(name="⏱️ Duração", value=f"`{minutos}:{segundos:02d}`", inline=True)
        if info['thumbnail']:
            embed.set_thumbnail(url=info['thumbnail'])
        embed.set_footer(text="Use os botões abaixo para controlar • Saio após 5min de inatividade")

        view = BotoesPlayer(self, interaction.guild.id)
        await interaction.followup.send(embed=embed, view=view)

    # ═══════════════════════════════════════
    # /pausar
    # ═══════════════════════════════════════
    @app_commands.command(name='pausar', description='『⏸️』Pausa ou retoma a música')
    async def pausar(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc:
            await interaction.response.send_message("❌ Não estou tocando nada!", ephemeral=True)
            return

        if vc.is_playing():
            vc.pause()
            # Inicia timer de inatividade enquanto pausado
            self.iniciar_inatividade(interaction.guild.id, interaction.channel)
            await interaction.response.send_message("⏸️ Música pausada!")
        elif vc.is_paused():
            vc.resume()
            # Cancela timer pois voltou a tocar
            self.cancelar_inatividade(interaction.guild.id)
            await interaction.response.send_message("▶️ Música retomada!")
        else:
            await interaction.response.send_message("❌ Não estou tocando nada!", ephemeral=True)

    # ═══════════════════════════════════════
    # /pular
    # ═══════════════════════════════════════
    @app_commands.command(name='pular', description='『⏭️』Pula para a próxima música da fila')
    async def pular(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc or not vc.is_playing():
            await interaction.response.send_message("❌ Não estou tocando nada!", ephemeral=True)
            return

        fila = self.get_fila(interaction.guild.id)
        proxima = fila[0]['titulo'] if fila else None

        vc.stop()  # Isso dispara o callback "after" que chama tocar_proxima automaticamente

        if proxima:
            await interaction.response.send_message(f"⏭️ Música pulada! Tocando agora: **{proxima}**")
        else:
            await interaction.response.send_message("⏭️ Música pulada! A fila está vazia agora.")

    # ═══════════════════════════════════════
    # /parar
    # ═══════════════════════════════════════
    @app_commands.command(name='parar', description='『⏹️』Para a música e desconecta do canal de voz')
    async def parar(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client

        if not vc:
            await interaction.response.send_message("❌ Não estou em nenhum canal de voz!", ephemeral=True)
            return

        # Marca como saída intencional para não disparar o aviso de "fui removida"
        self._saida_intencional.add(interaction.guild.id)

        # Cancela timer de inatividade e limpa a fila
        self.cancelar_inatividade(interaction.guild.id)
        filas[interaction.guild.id] = []
        await vc.disconnect()
        await interaction.response.send_message("⏹️ Música parada e desconectado do canal de voz!")

    # ═══════════════════════════════════════
    # /fila
    # ═══════════════════════════════════════
    @app_commands.command(name='fila', description='『📋』Veja as músicas na fila')
    async def fila(self, interaction: discord.Interaction):
        fila = self.get_fila(interaction.guild.id)

        if not fila:
            await interaction.response.send_message("📋 A fila está vazia!", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Fila de Músicas",
            color=discord.Color.blue()
        )

        linhas = []
        for i, musica in enumerate(fila[:10], 1):
            minutos = musica['duracao'] // 60
            segundos = musica['duracao'] % 60
            linhas.append(f"`#{i}` **{musica['titulo']}** — `{minutos}:{segundos:02d}`")

        embed.description = "\n".join(linhas)

        if len(fila) > 10:
            embed.set_footer(text=f"E mais {len(fila) - 10} músicas na fila...")

        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # Detecta quando o bot é desconectado manualmente do canal de voz
    # (alguém clicou em "desconectar" ou o expulsou do canal)
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Só nos importa quando é o próprio bot saindo de um canal
        if member.id != self.bot.user.id:
            return

        # Verifica se o bot estava em um canal e agora não está mais (foi desconectado)
        if before.channel is not None and after.channel is None:
            guild_id = member.guild.id

            # Se a saída foi intencional (via /parar ou inatividade), não avisa de novo
            if guild_id in self._saida_intencional:
                self._saida_intencional.discard(guild_id)
                return

            # Foi desconectado manualmente por alguém — limpa a fila e avisa
            self.cancelar_inatividade(guild_id)
            filas[guild_id] = []

            # Tenta achar um canal de texto para avisar
            canal_texto = member.guild.system_channel
            if canal_texto is None:
                for ch in member.guild.text_channels:
                    if ch.permissions_for(member.guild.me).send_messages:
                        canal_texto = ch
                        break

            if canal_texto:
                try:
                    await canal_texto.send("⚠️ Fui desconectada do canal de voz! A música foi parada e a fila foi limpa.")
                except Exception:
                    pass

async def setup(bot):
    await bot.add_cog(Musica(bot))