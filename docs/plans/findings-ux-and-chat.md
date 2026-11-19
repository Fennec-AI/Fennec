# Plano: página de falhas (filtros, detalhes completos) e chat com a IA por falha

Status: **implementado em 2026-11-18**. A coleta descrita abaixo foi integrada aos filtros, detalhes e chat.

## Objetivo

1. Mostrar **exatamente** a falha encontrada, com todas as informações que o agente coletou.
2. Permitir **filtrar** falhas por site/alvo, severidade, scan e texto.
3. Deixar a página **mais clara**, sem dados fixos no código nem botões que não fazem nada.
4. Adicionar um **chat com a IA** sobre a falha selecionada.

Restrições do projeto (CLAUDE.md): sem banco de dados, sem autenticação, tudo assíncrono, prompts em `src/prompts/`.

---

## Diagnóstico (o que está errado hoje)

| Problema | Onde | Efeito |
|---|---|---|
| Detalhes casados por **posição na lista**, não por ID | `frontend/src/pages/FindingsPage.tsx` (overlay `richByJob` / `richSeen`) | Uma falha pode exibir impacto/evidência/remediação de outra |
| Descrição ausente cai no **resumo do scan inteiro** | `src/api/server.py`, montagem de `job.findings` (`description: ... or result.final_summary`) | O texto da falha não fala da falha |
| `reproduction_steps` recebe os **payloads**; `parameter` e `cwe_id` sempre vazios | `src/api/server.py`, mesmo trecho | Campos enganosos ou vazios |
| Link "ver falhas do alvo" compara **ID do alvo** com **ID do scan** | `TargetInventoryPage.tsx`, `DashboardPageV2.tsx` → `?target_id=`; filtro em `FindingsPage.tsx` | O filtro por site nunca encontra nada |
| Link vindo do scan usa `finding.id` numérico, que se repete entre scans | `AssessmentDetailPage.tsx` (`?finding_id=`) | O deep-link abre a falha errada |
| Dados fixos: nota "8.8", "3 tags", "Red Team", "Cred: None", "Unassigned" | `FindingsPage.tsx`, barra lateral direita | Informação inventada na tela |
| Botões sem ação: Patch, Resolve, Agent, AI Summary, Feedback, Comments | `FindingsPage.tsx` | Interface confusa |
| A evidência em texto só aparece quando não há pares request/response | `FindingsPage.tsx`, aba Evidence | Parte da evidência fica escondida |

## Já implementado (não commitado)

- Schema `PentesterResult`: `cwe_id`; `FindingEvidence.reproduction_steps`; chave `affected_parameter` no `breakdown`. O prompt em `src/prompts/builder.py` pede esses campos.
- `src/agents/pentester.py`: `_extract_tool_trace()` guarda os comandos executados (ferramenta, argumentos e saída truncada) em `finding_detail.commands_executed`. O `finding_detail` também passou a levar `reproduction_steps`, `affected_parameter`, `cwe_id` e `suggested_followups`.
- `agent.py`: cada falha leva `hypothesis_title` e `hypothesis_description`, e o `owasp_category` da hipótese é usado como fallback.
- `src/api/demo_seed.py`: os `pentester_results` de demonstração estão ligados ao `hypothesis_id` certo.

---

## Fase 1 — Backend: um registro único por falha

**Novo módulo `src/api/findings.py`** (funções puras, fáceis de testar):

- `host_of(url)`: extrai o hostname (aceita host sem esquema).
- `build_job_findings(job, rich, now)`: substitui a montagem que hoje fica inline em `_run_job`. Gera `job.findings` com **todos** os campos ricos e mantém `job.pentester_results` como está, porque a `AssessmentDetailPage` usa esse formato.
  - `description` = `description_overview` → `hypothesis_description` → `title`. **Nunca** `final_summary`.
  - `location` = `breakdown.affected_endpoint` → `target_url`.
  - `parameter` = `affected_parameter` (vazio se não houver).
  - `reproduction_steps` = os passos de verdade; os payloads ficam só em `evidence_payloads`.
  - `cwe_id` = o que o agente informou.
- `merged_findings(job)`: une `job.findings` com `job.pentester_results` por `hypothesis_id`, com fallback por posição só quando não houver ID. Serve para scans antigos e para o demo. Acrescenta o contexto do alvo: `target_id`, `target_url`, `host`, `job_name` e `job_created_at`.
- `filter_findings(records, severity, target_id, host, job_id, q)`.
- `facets(records)`: contagem por host, por severidade e por scan, para popular os filtros.

**Endpoints em `src/api/server.py`:**

| Método | Rota | Mudança |
|---|---|---|
| GET | `/dashboard/findings` | Retorna `merged_findings`; aceita `severity`, `target_id`, `host`, `job_id`, `q` e `limit` (padrão 200) |
| GET | `/dashboard/findings/facets` | Novo: listas de hosts, severidades e scans com contagens |
| GET | `/dashboard/findings/{finding_id}` | Novo: uma falha completa (404 se não existir) |

Os IDs de falha continuam no formato `"{job_id}-finding-{i}"` (string estável).

## Fase 2 — Frontend: tipos e API

- `frontend/src/types/index.ts`: novo tipo `Finding` com o registro mesclado. `FindingDetail` e `RichFinding` ficam só onde já são usados.
- `frontend/src/services/api.ts`: `findingsApi.list(filters)`, `findingsApi.facets()`, `findingsApi.get(id)` e `findingsApi.chat(id, messages)`.

## Fase 3 — Página de falhas mais clara

`FindingsPage.tsx`, que hoje tem ~940 linhas, será dividida em componentes dentro de `frontend/src/components/findings/`:

- **`FindingsFilters`**: seletor de site (host), chips de severidade com contagem, seletor de scan, busca por texto e as abas Open/Resolved/Archived. O estado dos filtros fica na URL (`?host=&severity=&job_id=&q=`), para que links e o botão voltar funcionem.
- **`FindingsList`**: opção "agrupar por site"; cada item mostra severidade, título, host + endpoint e data.
- **`FindingDetail`**: cabeçalho com título, severidade, site, endpoint, parâmetro, CWE, OWASP e link para o scan. Abas:
  - *Descrição*: resumo, breakdown, detalhes técnicos e a hipótese de origem.
  - *Evidência*: pares request/response **e** a lista de evidências em texto, payloads e comportamento observado.
  - *Reprodução*: passos de reprodução + **comandos executados** (colapsáveis, com botão copiar).
  - *Impacto* e *Remediação*: como hoje.
- **Remover** os dados fixos e os botões sem ação. "Resolve" e "Archive" só voltam se for criado um status em memória no backend; senão saem da tela.
- **Corrigir os links:**
  - Páginas de alvo e dashboard → `/dashboard/findings?target_id=<id do alvo>`. O filtro passa a usar o `target_id` do registro.
  - `AssessmentDetailPage` → `?job_id=<scan>&hypothesis_id=<hid>`. O deep-link seleciona por esse par.
- Estados vazios distintos: "nenhuma falha ainda" e "nenhuma falha com esses filtros", este com um botão para limpar os filtros.

Decisão em aberto: renderizar Markdown (`description_technical` e remediação vêm em Markdown) com `react-markdown`, que seria uma dependência nova, ou manter texto pré-formatado.

## Fase 4 — Chat com a IA sobre a falha (backend)

**Endpoint:** `POST /findings/{finding_id}/chat`

- Corpo da requisição: `{ "messages": [{ "role": "user" | "assistant", "content": "..." }] }`. O histórico fica no front, então o endpoint é **stateless**, sem persistência (CLAUDE.md).
- Resposta: `{ "reply": "..." }`. Streaming via SSE é opcional numa segunda etapa.
- Limites: no máximo ~20 mensagens e ~4k caracteres por mensagem; o contexto da falha é truncado (por exemplo, saídas de comandos e respostas HTTP cortadas).
- Modelo: `get_default_llm()` com `.with_fallbacks(get_fallback_llms())`, para reaproveitar o suporte a vários providers. Sem ferramentas: o chat **só conversa**, não executa nada no alvo.
- Sem chave de API: retorna 503 com uma mensagem clara.

**Prompt em `src/prompts/finding_chat.py`:**

- Papel: explicar a falha, o impacto, como corrigir e como validar a correção, sempre com base nos dados da falha.
- Inclui um JSON enxuto da falha: título, severidade, endpoint, parâmetro, CWE/OWASP, descrição, evidência, passos e um resumo dos comandos.
- **Importante (prompt injection):** os dados da falha contêm conteúdo vindo do alvo (respostas HTTP, saídas de comandos). O prompt deve marcar esse bloco como **dados não confiáveis**, delimitado e nunca tratado como instrução.
- Responde no idioma do usuário.

## Fase 5 — Chat com a IA sobre a falha (frontend)

- Componente `FindingChat` na barra lateral direita, ou em uma aba "Chat" no detalhe, substituindo os botões Agent/AI Summary.
- Sugestões rápidas: "Explique esta falha", "Como corrigir no meu código?", "Como confirmo que a correção funcionou?".
- O histórico é guardado por `finding_id` em memória (state), e opcionalmente em `sessionStorage`. Ele zera ao trocar de falha.
- Estados de carregando e de erro (inclusive "sem chave de API configurada").

## Fase 6 — Testes e documentação

- `tests/test_findings.py` (sem rede):
  - `host_of` com e sem esquema.
  - `build_job_findings`: a descrição nunca usa `final_summary`, e os passos não são confundidos com payloads.
  - `merged_findings`: junção por `hypothesis_id`, inclusive com a ordem embaralhada.
  - `filter_findings` e `facets`.
  - Endpoints com `TestClient` usando o demo seed.
  - Chat com um modelo falso (`langchain_core` fake chat model): checar que o contexto da falha entra no prompt e que os limites são respeitados.
- Frontend: `npm run lint && npm run build`.
- Documentação: README (chat e filtros), CHANGELOG e `docs/ARCHITECTURE.md` (novo endpoint).

## Ordem sugerida e critérios de aceite

1. **Fase 1 + testes.** A API devolve cada falha completa e filtrável por site.
2. **Fases 2 e 3.** Os detalhes mostrados correspondem à falha selecionada (testar com o demo, `FENNEC_DEMO_SEED=1`). O filtro por site funciona a partir da página de alvos. Não sobra nenhum dado fixo.
3. **Fases 4 e 5.** O chat responde com base na falha selecionada, funciona com qualquer provider configurado e não executa ações.
4. **Fase 6.** `ruff`, `pytest` e o build do front passam.
