from __future__ import annotations
# db.py
# Score de Vendas Urba
# Módulo de conexão com Neon (PostgreSQL) + todas as funções de banco
# SEGURANÇA: CPF removido de todas as operações de banco de dados
#
# ALTERAÇÕES (V1.1):
# - Exclusão de simulações agora é lógica (soft delete) com registro de
#   quem excluiu, quando e por quê — o histórico é base da premiação.
# - Removida a função excluir_historico() ("apagar tudo").
# - Nova coluna preenchimento_manual: registra quais dados foram digitados
#   manualmente pelo vendedor (auditoria).
# - Erros técnicos vão para o log, não para a tela.
# - Migrações simplificadas com ADD/DROP COLUMN IF EXISTS.

import json
import logging

import bcrypt
import pandas as pd
import psycopg2
import psycopg2.extras
import streamlit as st

logger = logging.getLogger(__name__)

# ============================================================
# CONEXÃO
# ============================================================

def get_conn():
    return psycopg2.connect(
        st.secrets["NEON_DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def init_db():
    """
    Garante que todas as tabelas existam e aplica migrações.
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

        -- HISTORICO (CPF não é armazenado)
        CREATE TABLE IF NOT EXISTS historico_simulacoes (
            id                          SERIAL PRIMARY KEY,
            data_hora                   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            vendedor_email              TEXT,
            vendedor_nome               TEXT,
            empreendimento              TEXT,
            unidade                     TEXT,
            nome_proponente             TEXT,
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

        -- MIGRAÇÕES SEGURAS
        ALTER TABLE historico_simulacoes DROP COLUMN IF EXISTS cpf_proponente;
        ALTER TABLE historico_simulacoes ADD  COLUMN IF NOT EXISTS nome_proponente      TEXT;
        ALTER TABLE historico_simulacoes ADD  COLUMN IF NOT EXISTS preenchimento_manual TEXT;
        ALTER TABLE historico_simulacoes ADD  COLUMN IF NOT EXISTS excluido             BOOLEAN NOT NULL DEFAULT FALSE;
        ALTER TABLE historico_simulacoes ADD  COLUMN IF NOT EXISTS excluido_em          TIMESTAMPTZ;
        ALTER TABLE historico_simulacoes ADD  COLUMN IF NOT EXISTS excluido_por         TEXT;
        ALTER TABLE historico_simulacoes ADD  COLUMN IF NOT EXISTS motivo_exclusao      TEXT;

        -- ÍNDICES
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

    except Exception:
        # Detalhe técnico só no log — nunca na tela de login
        logger.exception("Falha na autenticação")
        st.error("Não foi possível validar o acesso agora. Tente novamente em instantes.")
        return None


# ============================================================
# USUÁRIOS — CRUD
# ============================================================

def listar_usuarios() -> pd.DataFrame:
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
    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
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
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE usuarios SET nome = %s, perfil = %s, ativo = %s WHERE id = %s",
                (nome.strip(), perfil, ativo, uid),
            )
        conn.commit()


def redefinir_senha(uid: int, nova_senha: str) -> None:
    senha_hash = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET senha_hash = %s WHERE id = %s", (senha_hash, uid))
        conn.commit()


def toggle_usuario(uid: int, ativo: bool) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET ativo = %s WHERE id = %s", (ativo, uid))
        conn.commit()


def remover_usuario(uid: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
        conn.commit()


# ============================================================
# EMPREENDIMENTOS
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def carregar_empreendimentos() -> pd.DataFrame:
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
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE empreendimentos SET ativo = %s WHERE id = %s", (ativo, eid))
        conn.commit()
    carregar_empreendimentos.clear()


def remover_empreendimento(eid: int) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM empreendimentos WHERE id = %s", (eid,))
        conn.commit()
    carregar_empreendimentos.clear()


# ============================================================
# HISTÓRICO DE SIMULAÇÕES
# ============================================================

def salvar_simulacao(d: dict, vendedor_email: str, vendedor_nome: str) -> None:
    """
    Salva uma simulação completa no histórico.
    SEGURANÇA: CPF não é salvo. O PDF do SPC não é salvo.
    """
    notas_json = json.dumps(d.get("notas", {}))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO historico_simulacoes (
                    vendedor_email, vendedor_nome,
                    empreendimento, unidade, nome_proponente,
                    idade, faixa_etaria, estado_civil,
                    score_proponente,
                    renda_proponente, qtd_clientes_adicionais,
                    renda_clientes_adicionais, renda_total,
                    ato_urba, percentual_ato, faixa_ato,
                    valor_proposta, primeira_mensal,
                    percentual_comprometimento, faixa_comprometimento,
                    score_final, classificacao, notas_json,
                    preenchimento_manual
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s
                )
                """,
                (
                    vendedor_email,
                    vendedor_nome,
                    d.get("empreendimento", ""),
                    d.get("unidade", ""),
                    d.get("nome_proponente", ""),
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
                    d.get("preenchimento_manual", ""),
                ),
            )
        conn.commit()


def carregar_historico() -> pd.DataFrame:
    """Retorna apenas simulações não excluídas."""
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
                    nome_proponente,
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
                    classificacao,
                    preenchimento_manual
                FROM historico_simulacoes
                WHERE excluido = FALSE
                ORDER BY data_hora DESC
                """
            )
            rows = cur.fetchall()
    return pd.DataFrame(rows)


def excluir_simulacao(sid: int, excluido_por: str, motivo: str) -> bool:
    """
    Exclusão LÓGICA: o registro continua no banco, marcado como excluído,
    com quem excluiu, quando e o motivo. Retorna True se algo foi excluído.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE historico_simulacoes
                SET excluido        = TRUE,
                    excluido_em     = NOW(),
                    excluido_por    = %s,
                    motivo_exclusao = %s
                WHERE id = %s AND excluido = FALSE
                """,
                (excluido_por, motivo.strip(), sid),
            )
            alterados = cur.rowcount
        conn.commit()
    return alterados > 0
