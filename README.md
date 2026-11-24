# Score de Vendas Urba

Simulador (Streamlit) que classifica cada venda em **baixo, moderado ou alto risco** de distrato.
Projeto Classificador de Vendas · Comercial · Processos.

## Como rodar

```bash
pip install -r requirements.txt
# .streamlit/secrets.toml  (não vai para o GitHub)
# NEON_DATABASE_URL = "postgresql://usuario:senha@host/banco?sslmode=require"
streamlit run app.py
```

As tabelas são criadas/migradas sozinhas na primeira execução (inclusive a nova `parametros_score`).

## Estrutura

| Arquivo | O que faz |
|---|---|
| `app.py` | Entrada: login, topo, abas e roteamento |
| `db.py` | Banco (Neon/PostgreSQL): usuários, empreendimentos, histórico, parâmetros |
| `utils.py` | Regras do score, leitura do SPC, sugestões de melhoria |
| `styles.py` | Identidade visual Urba (CSS + componentes HTML leves) |
| `pages/` | Telas: login, simulador, histórico, parâmetros, usuários, empreendimentos |

## Score

Pontos = Σ (nota da faixa × peso da variável). Notas, pesos e limites são editados na aba
**Parâmetros** (admin). Cada alteração salva vira uma nova versão, e cada simulação guarda a
versão usada (coluna `parametros_id`). Sem versão salva, valem os padrões:

| Variável | Peso | Notas padrão |
|---|---|---|
| Score SPC | 5 | A-B 5 · C-D 3 · E-F 1 |
| % do ato | 5 | >4% 5 · 3-4% 4 · 2-3% 3 · 1-2% 2 · <1% 1 |
| Comprometimento de renda | 4 | ≤10% 5 · 10-20% 4 · 20-30% 3 · 30-50% 2 · >50% 1 |
| Faixa etária | 1 | 60+ 5 · 45-60 4 · 35-45 3 · ≤25 2 · 25-35 1 |
| Estado civil | 1 | casado 3 · divorciado 2 · solteiro 1 |

Máximo padrão: 78 pontos. Baixo risco ≥ 54 · Moderado ≥ 33 · Alto < 33.

## V2.0 — o que mudou

**Novo**
- Aba **Parâmetros**: edita notas, pesos e limites, mostra o impacto no histórico antes de
  salvar, guarda versões com autor e motivo e permite trazer uma versão antiga de volta.
- Redesign no padrão Urba: fonte Verdana (sem fonte externa), off-white + verde/laranja,
  topo em gradiente com o logo oficial, cards com a assinatura da marca, velocímetro do score,
  barras por variável e cards de sugestão. Layout funciona no celular.

- Login com visual inspirado na SpellUI (raios de luz, gradiente animado, título com blur reveal
  e shimmer, prévia do score em vidro, botão "rich"), tudo em CSS puro, sem JS. Barra de abas em pílula de vidro dentro do
  topo verde, com animação na aba ativa.

**Correções**
- **Login com dois cliques**: campos agora ficam num formulário (o clique não se perde
  mais, e Enter também entra). O botão também não se desloca mais no hover.
- Logo não aparecia (o código apontava para arquivos que não existiam no repositório).
- Conexões com o banco agora são sempre fechadas (antes ficavam abertas até o coletor de lixo).
- `init_db` roda uma vez por servidor, não a cada login.
- O PDF do SPC era relido a cada clique na tela. Agora é lido uma vez por arquivo.
- Empreendimento desativado sumia da tela do admin e não tinha como reativar.
- Mensagens de sucesso em Usuários/Empreendimentos sumiam no rerun.
- Remover usuário/unidade agora pede confirmação.
- CSV do histórico sai com `;` e vírgula decimal (abre direito no Excel em português).
- `plotly` removido do `requirements.txt` (não era usado).
