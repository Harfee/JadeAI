import sqlite3

def conectar():
    """Conecta ao banco de dados."""
    conn = sqlite3.connect('jade_dados.db')
    return conn

def inicializar_db():
    """Cria todas as tabelas se elas não existirem."""
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de pontos/XP por servidor
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id INTEGER,
            servidor_id INTEGER,
            pontos INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, servidor_id)
        )
    ''')

    # Tabela de avisos de moderação
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS avisos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            servidor_id INTEGER,
            motivo TEXT,
            data TEXT
        )
    ''')

    # Tabela de economia (saldo de moedas separado dos pontos de XP)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economia (
            user_id INTEGER,
            servidor_id INTEGER,
            saldo INTEGER DEFAULT 0,
            ultimo_diario TEXT DEFAULT NULL,
            PRIMARY KEY (user_id, servidor_id)
        )
    ''')

    # Tabela da loja (itens compráveis com moedas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            servidor_id INTEGER,
            nome TEXT,
            preco INTEGER,
            cargo_id INTEGER
        )
    ''')

    # Tabela de configuração de boas-vindas por servidor
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_boasvindas (
            servidor_id INTEGER PRIMARY KEY,
            canal_id INTEGER,
            mensagem TEXT DEFAULT 'Olá {usuario}, bem vindo(a) ao {servidor}! 👋',
            cor TEXT DEFAULT '#5b8dee',
            cargo_id INTEGER DEFAULT NULL
        )
    ''')

    # Tabela de configuração de memes por servidor (país/idioma de origem dos memes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_memes (
            servidor_id INTEGER PRIMARY KEY,
            pais TEXT DEFAULT 'brasil'
        )
    ''')

    conn.commit()
    conn.close()
    print("『💾』Banco de dados inicializado com sucesso!")

# ═══════════════════════════════════════
# SISTEMA DE XP / PONTOS
# ═══════════════════════════════════════

def atualizar_pontos(user_id, servidor_id, quantidade):
    """Adiciona ou remove pontos de XP de um usuário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO usuarios (user_id, servidor_id, pontos) VALUES (?, ?, ?)
        ON CONFLICT(user_id, servidor_id) DO UPDATE SET pontos = pontos + ?
    ''', (user_id, servidor_id, quantidade, quantidade))
    conn.commit()
    conn.close()

def buscar_pontos(user_id, servidor_id):
    """Retorna os pontos de XP de um usuário em um servidor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT pontos FROM usuarios WHERE user_id = ? AND servidor_id = ?", (user_id, servidor_id))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else 0

def buscar_ranking(servidor_id, limite=10):
    """Retorna o ranking de XP de um servidor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, pontos FROM usuarios
        WHERE servidor_id = ?
        ORDER BY pontos DESC
        LIMIT ?
    ''', (servidor_id, limite))
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def buscar_ranking_global(limite=10):
    """Retorna o ranking global somando pontos de todos os servidores."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, SUM(pontos) as total FROM usuarios
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT ?
    ''', (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def calcular_nivel(pontos):
    """Calcula o nível baseado nos pontos. Fórmula: nível = raiz(pontos / 50)"""
    import math
    nivel = int(math.sqrt(pontos / 50))
    pontos_nivel_atual = 50 * (nivel ** 2)
    pontos_proximo_nivel = 50 * ((nivel + 1) ** 2)
    faltam = pontos_proximo_nivel - pontos
    return nivel, faltam, pontos_proximo_nivel

# ═══════════════════════════════════════
# SISTEMA DE MODERAÇÃO (AVISOS)
# ═══════════════════════════════════════

def adicionar_aviso(user_id, servidor_id, motivo):
    """Registra um aviso para um usuário."""
    from datetime import datetime
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime('%d/%m/%Y às %H:%M')
    cursor.execute('''
        INSERT INTO avisos (user_id, servidor_id, motivo, data)
        VALUES (?, ?, ?, ?)
    ''', (user_id, servidor_id, motivo, data))
    conn.commit()
    conn.close()

def buscar_avisos(user_id, servidor_id):
    """Retorna todos os avisos de um usuário em um servidor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, motivo, data FROM avisos
        WHERE user_id = ? AND servidor_id = ?
        ORDER BY id DESC
    ''', (user_id, servidor_id))
    resultado = cursor.fetchall()
    conn.close()
    return resultado

def limpar_avisos(user_id, servidor_id):
    """Remove todos os avisos de um usuário em um servidor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM avisos WHERE user_id = ? AND servidor_id = ?
    ''', (user_id, servidor_id))
    conn.commit()
    conn.close()

# ═══════════════════════════════════════
# SISTEMA DE ECONOMIA
# ═══════════════════════════════════════

def buscar_saldo(user_id, servidor_id):
    """Retorna o saldo de moedas de um usuário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT saldo FROM economia WHERE user_id = ? AND servidor_id = ?", (user_id, servidor_id))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else 0

def atualizar_saldo(user_id, servidor_id, quantidade):
    """Adiciona ou remove moedas de um usuário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO economia (user_id, servidor_id, saldo) VALUES (?, ?, ?)
        ON CONFLICT(user_id, servidor_id) DO UPDATE SET saldo = saldo + ?
    ''', (user_id, servidor_id, quantidade, quantidade))
    conn.commit()
    conn.close()

def buscar_ultimo_diario(user_id, servidor_id):
    """Retorna a data do último resgate diário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT ultimo_diario FROM economia WHERE user_id = ? AND servidor_id = ?", (user_id, servidor_id))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def atualizar_ultimo_diario(user_id, servidor_id, data):
    """Atualiza a data do último resgate diário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO economia (user_id, servidor_id, ultimo_diario) VALUES (?, ?, ?)
        ON CONFLICT(user_id, servidor_id) DO UPDATE SET ultimo_diario = ?
    ''', (user_id, servidor_id, data, data))
    conn.commit()
    conn.close()

def transferir_saldo(de_user_id, para_user_id, servidor_id, quantidade):
    """Transfere moedas entre dois usuários."""
    conn = conectar()
    cursor = conn.cursor()

    # Remove do remetente
    cursor.execute('''
        INSERT INTO economia (user_id, servidor_id, saldo) VALUES (?, ?, ?)
        ON CONFLICT(user_id, servidor_id) DO UPDATE SET saldo = saldo - ?
    ''', (de_user_id, servidor_id, -quantidade, quantidade))

    # Adiciona ao destinatário
    cursor.execute('''
        INSERT INTO economia (user_id, servidor_id, saldo) VALUES (?, ?, ?)
        ON CONFLICT(user_id, servidor_id) DO UPDATE SET saldo = saldo + ?
    ''', (para_user_id, servidor_id, quantidade, quantidade))

    conn.commit()
    conn.close()

# ═══════════════════════════════════════
# SISTEMA DE BOAS-VINDAS
# ═══════════════════════════════════════

def buscar_config_boasvindas(servidor_id):
    """Retorna a configuração de boas-vindas de um servidor (ou padrão se não existir)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT canal_id, mensagem, cor, cargo_id FROM config_boasvindas WHERE servidor_id = ?
    ''', (servidor_id,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        return {
            'canal_id': resultado[0],
            'mensagem': resultado[1] or 'Olá {usuario}, bem vindo(a) ao {servidor}! 👋',
            'cor': resultado[2] or '#5b8dee',
            'cargo_id': resultado[3],
        }

    # Configuração padrão se o servidor nunca configurou nada
    return {
        'canal_id': None,
        'mensagem': 'Olá {usuario}, bem vindo(a) ao {servidor}! 👋',
        'cor': '#5b8dee',
        'cargo_id': None,
    }

def definir_canal_boasvindas(servidor_id, canal_id):
    """Define o canal de boas-vindas de um servidor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO config_boasvindas (servidor_id, canal_id) VALUES (?, ?)
        ON CONFLICT(servidor_id) DO UPDATE SET canal_id = ?
    ''', (servidor_id, canal_id, canal_id))
    conn.commit()
    conn.close()

def definir_mensagem_boasvindas(servidor_id, mensagem):
    """Define a mensagem de boas-vindas de um servidor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO config_boasvindas (servidor_id, mensagem) VALUES (?, ?)
        ON CONFLICT(servidor_id) DO UPDATE SET mensagem = ?
    ''', (servidor_id, mensagem, mensagem))
    conn.commit()
    conn.close()

def definir_cor_boasvindas(servidor_id, cor):
    """Define a cor do embed de boas-vindas de um servidor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO config_boasvindas (servidor_id, cor) VALUES (?, ?)
        ON CONFLICT(servidor_id) DO UPDATE SET cor = ?
    ''', (servidor_id, cor, cor))
    conn.commit()
    conn.close()

def definir_cargo_boasvindas(servidor_id, cargo_id):
    """Define o cargo automático ao entrar no servidor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO config_boasvindas (servidor_id, cargo_id) VALUES (?, ?)
        ON CONFLICT(servidor_id) DO UPDATE SET cargo_id = ?
    ''', (servidor_id, cargo_id, cargo_id))
    conn.commit()
    conn.close()

# ═══════════════════════════════════════
# SISTEMA DE MEMES (PAÍS/IDIOMA)
# ═══════════════════════════════════════

def buscar_pais_memes(servidor_id):
    """Retorna o país configurado para os memes do servidor (padrão: brasil)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT pais FROM config_memes WHERE servidor_id = ?", (servidor_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else 'brasil'

def definir_pais_memes(servidor_id, pais):
    """Define o país de origem dos memes para um servidor."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO config_memes (servidor_id, pais) VALUES (?, ?)
        ON CONFLICT(servidor_id) DO UPDATE SET pais = ?
    ''', (servidor_id, pais, pais))
    conn.commit()
    conn.close()