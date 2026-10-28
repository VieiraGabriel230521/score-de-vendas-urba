from __future__ import annotations
# db.py
# Score de Vendas Urba
# Módulo de conexão com Neon (PostgreSQL) + todas as funções de banco

import json
from datetime import datetime
from zoneinfo import ZoneInfo
import bcrypt
import pandas as pd
import psycopg2
import psycopg2.extras
import streamlit as st

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")

# ============================================================
# CONEXÃO
# ============================================================

def get_conn():
    """Retorna uma conexão com o banco Neon."""
    return psycopg2.connect(
        st.secrets["NEON_DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def init_db():
    """
    Garante que todas as tabelas existam.
    Executado uma vez na inicialização do app.
    """
    sql = """
        -- USUARIOS
        CREATE TABLE IF NOT EXISTS usuarios (
            id            SERIAL PRIMARY KEY,
            nome          TEXT        NOT NULL,
            email         TEXT        NOT NULL UNIQUE,
            senha_hash    TEXT        NOT NULL,
            perfil        TEXT        NOT NULL
                          CHECK (perfil IN ('VENDEDOR', 'ADMINISTRADOR')),
            ativo         BOOLEAN     NOT NULL DEFAULT TRUE,
            criado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        -- EMPREENDIMENTOS
        CREATE TABLE IF NOT EXISTS empreendimentos (
            id             SERIAL PRIMARY KEY,
            empreendimento TEXT        NOT NULL,
            unidade        TEXT        NOT NULL,
            ativo          BOOLEAN     NOT NULL DEFAULT TRUE,
            criado_em      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (empreendimento, unidade)
        );

        -- HISTORICO
        CREATE TABLE IF NOT EXISTS historico_simulacoes (
            id                          SERIAL PRIMARY KEY,
            data_hora                   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            vendedor_email              TEXT,
            vendedor_nome               TEXT,
            empreendimento              TEXT,
            unidade                     TEXT,
            cpf_proponente              TEXT,
            idade                       INT,
            faixa_etaria                TEXT,
            estado_civil                TEXT,
            score_proponente            TEXT,
            renda_proponente            NUMERIC(14,2),
            qtd_clientes_adicionais     INT           DEFAULT 0,
            renda_clientes_adicionais   NUMERIC(14,2) DEFAULT 0,
            renda_total                 NUMERIC(14,2),
            ato_urba                    NUMERIC(14,2),
            percentual_ato              NUMERIC(8,4),
            faixa_ato                   TEXT,
            valor_proposta              NUMERIC(14,2),
            primeira_mensal             NUMERIC(14,2),
            percentual_comprometimento  NUMERIC(8,4),
            faixa_comprometimento       TEXT,
            score_final                 INT,
            classificacao               TEXT,
            notas_json                  JSONB
        );

        -- ÍNDICES
        CREATE INDEX IF NOT EXISTS idx_usuarios_email
            ON usuarios (email);
        CREATE INDEX IF NOT EXISTS idx_empreendimentos_nome
            ON empreendimentos (empreendimento);
        CREATE INDEX IF NOT EXISTS idx_hist_vendedor
            ON historico_simulacoes (vendedor_email);
        CREATE INDEX IF NOT EXISTS idx_hist_empreendimento
            ON historico_simulacoes (empreendimento);
        CREATE INDEX IF NOT EXISTS idx_hist_classificacao
            ON historico_simulacoes (classificacao);
        CREATE INDEX IF NOT EXISTS idx_hist_data
            ON historico_simulacoes (data_hora DESC);

        -- TRIGGER atualizado_em
        CREATE OR REPLACE FUNCTION fn_atualizar_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.atualizado_em = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_usuarios_atualizado_em ON usuarios;
        CREATE TRIGGER trg_usuarios_atualizado_em
            BEFORE UPDATE ON usuarios
            FOR EACH ROW
            EXECUTE FUNCTION fn_atualizar_timestamp();
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


# ============================================================
# USUÁRIOS — AUTENTICAÇÃO
# ============================================================

def autenticar_usuario(email: str, senha: str):
    """
    Verifica e-mail e senha.
    Retorna dict com dados do usuário ou None se inválido.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, nome, email, senha_hash, perfil, ativo
                    FROM usuarios
                    WHERE email = %s
                    """,
                    (email.strip().lower(),),
                )
                row = cur.fetchone()

        if not row:
            return None
        if not row["ativo"]:
            return None
        if not bcrypt.checkpw(senha.encode("utf-8"), row["senha_hash"].encode("utf-8")):
            return None

        return {
            "id":     row["id"],
            "nome":   row["nome"],
            "email":  row["email"],
            "perfil": row["perfil"],
        }

    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return None


# ============================================================
# USUÁRIOS — CRUD
# ============================================================

def listar_usuarios() -> pd.DataFrame:
    """Retorna todos os usuários ordenados por data de criação."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, nome, email, perfil, ativo, criado_em
                FROM usuarios
                ORDER BY criado_em DESC
                """
            )
            rows = cur.fetchall()
    return pd.DataFrame(rows)


def criar_usuario(nome: str, email: str, senha: str, perfil: str) -> None:
    """Cria um novo usuário com senha hasheada."""
    senha_hash = bcrypt.hashpw(
        senha.encode("utf-8"),
        bcrypt.gensalt(12)
    ).decode("utf-8")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO usuarios (nome, email, senha_hash, perfil)
                VALUES (%s, %s, %s, %s)
                """,
                (nome.strip(), email.strip().lower(), senha_hash, perfil),
            )
        conn.commit()


def atualizar_usuario(uid: int, nome: str, perfil: str, ativo: bool) -> None:
    """Atualiza nome, perfil e status de um usuário."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE usuarios
                SET nome = %s, perfil = %s, ativo = %s
                WHERE id = %s
                """,
                (nome.strip(), perfil, ativo, uid),
            )
        conn.commit()


def redefinir_senha(uid: int, nova_senha: str) -> None:
    """Redefine a senha de um usuário."""
    senha_hash = bcrypt.hashpw(
        nova_senha.encode("utf-8"),
        bcrypt.gensalt(12)
    ).decode("utf-8")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE usuarios SET senha_hash = %s WHERE id = %s",
                (senha_hash, uid),
            )
        conn.commit()


def toggle_usuario(uid: int, ativo: bool) -> None:
    """Ativa ou desativa um usuário."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE usuarios SET ativo = %s WHERE id = %s",
                (ativo, uid),
            )
        conn.commit()


def remover_usuario(uid: int) -> None:
    """Remove permanentemente um usuário."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
        conn.commit()


# ============================================================
# EMPREENDIMENTOS
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def carregar_empreendimentos() -> pd.DataFrame:
    """
    Retorna todos os empreendimentos ativos.
    Cache de 5 minutos para evitar consultas repetidas.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, empreendimento, unidade, ativo
                FROM empreendimentos
                WHERE ativo = TRUE
                ORDER BY empreendimento, unidade
                """
            )
            rows = cur.fetchall()
    return pd.DataFrame(rows)


def inserir_empreendimento(empreendimento: str, unidade: str) -> None:
    """Insere um novo par empreendimento/unidade."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO empreendimentos (empreendimento, unidade)
                VALUES (%s, %s)
                ON CONFLICT (empreendimento, unidade) DO NOTHING
                """,
                (empreendimento.strip(), unidade.strip()),
            )
        conn.commit()
    carregar_empreendimentos.clear()


def importar_empreendimentos_xlsx(df: pd.DataFrame) -> tuple[int, int]:
    """
    Importa empreendimentos a partir de um DataFrame (vindo do Excel).
    Retorna (inseridos, ignorados).
    """
    inseridos = 0
    ignorados = 0

    with get_conn() as conn:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                emp = str(row.get("Empreendimento", "")).strip()
                uni = str(row.get("Unidade", "")).strip()
                if not emp or not uni:
                    ignorados += 1
                    continue
                cur.execute(
                    """
                    INSERT INTO empreendimentos (empreendimento, unidade)
                    VALUES (%s, %s)
                    ON CONFLICT (empreendimento, unidade) DO NOTHING
                    """,
                    (emp, uni),
                )
                if cur.rowcount > 0:
                    inseridos += 1
                else:
                    ignorados += 1
        conn.commit()

    carregar_empreendimentos.clear()
    return inseridos, ignorados


def toggle_empreendimento(eid: int, ativo: bool) -> None:
    """Ativa ou desativa um empreendimento."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE empreendimentos SET ativo = %s WHERE id = %s",
                (ativo, eid),
            )
        conn.commit()
    carregar_empreendimentos.clear()


def remover_empreendimento(eid: int) -> None:
    """Remove permanentemente um empreendimento."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM empreendimentos WHERE id = %s",
                (eid,),
            )
        conn.commit()
    carregar_empreendimentos.clear()


# ============================================================
# HISTÓRICO DE SIMULAÇÕES
# ============================================================

def salvar_simulacao(d: dict, vendedor_email: str, vendedor_nome: str) -> None:
    """
    Salva uma simulação completa no histórico.
    d: dicionário com todos os dados calculados pelo simulador.
    """
    notas_json = json.dumps(d.get("notas", {}))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO historico_simulacoes (
                    vendedor_email, vendedor_nome,
                    empreendimento, unidade, cpf_proponente,
                    idade, faixa_etaria, estado_civil,
                    score_proponente,
                    renda_proponente, qtd_clientes_adicionais,
                    renda_clientes_adicionais, renda_total,
                    ato_urba, percentual_ato, faixa_ato,
                    valor_proposta, primeira_mensal,
                    percentual_comprometimento, faixa_comprometimento,
                    score_final, classificacao, notas_json
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
                """,
                (
                    vendedor_email,
                    vendedor_nome,
                    d.get("empreendimento", ""),
                    d.get("unidade", ""),
                    d.get("cpf_proponente", ""),
                    d.get("idade"),
                    d.get("faixa_idade", ""),
                    d.get("estado_civil", ""),
                    d.get("score_proponente", ""),
                    d.get("renda_proponente", 0),
                    d.get("qtd_clientes_adicionais", 0),
                    d.get("renda_adicionais", 0),
                    d.get("renda_total", 0),
                    d.get("ato_urba", 0),
                    d.get("perc_ato", 0),
                    d.get("faixa_at", ""),
                    d.get("valor_proposta", 0),
                    d.get("primeira_mensal", 0),
                    d.get("perc_comp", 0),
                    d.get("faixa_comp", ""),
                    d.get("score_final", 0),
                    d.get("classificacao", ""),
                    notas_json,
                ),
            )
        conn.commit()


def carregar_historico() -> pd.DataFrame:
    """Retorna todo o histórico de simulações ordenado por data."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    data_hora AT TIME ZONE 'America/Sao_Paulo' AS data_hora,
                    vendedor_nome,
                    vendedor_email,
                    empreendimento,
                    unidade,
                    cpf_proponente,
                    idade,
                    faixa_etaria,
                    estado_civil,
                    score_proponente,
                    renda_total,
                    ato_urba,
                    percentual_ato,
                    faixa_ato,
                    valor_proposta,
                    primeira_mensal,
                    percentual_comprometimento,
                    faixa_comprometimento,
                    score_final,
                    classificacao
                FROM historico_simulacoes
                ORDER BY data_hora DESC
                """
            )
            rows = cur.fetchall()
    return pd.DataFrame(rows)


def excluir_historico() -> None:
    """Remove todos os registros do histórico."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM historico_simulacoes")
        conn.commit()


def excluir_simulacao(sid: int) -> None:
    """Remove uma simulação específica pelo ID."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM historico_simulacoes WHERE id = %s",
                (sid,),
            )
        conn.commit()
