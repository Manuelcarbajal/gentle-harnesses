# Harness Audit — Filosofía, Límites y Arquitectura de Largo Plazo

Status: **Análisis completo — implementación pendiente** (fecha del análisis: 2026-07-26)

Revisión arquitectónica de `gentle-claude` y de todo lo vendorizado desde `gentle-pi`,
contrastado contra el código fuente real de `gentle-ai` (módulo Go cacheado localmente en
`gentleman-programming/gentle-ai@v1.49.0`, verificado además contra el binario instalado
v2.1.11) — no contra supuestos sobre lo que "debería" tener.

---

## 0. Hallazgo central: Gentle-AI ya es multi-host — el problema no es "adaptar", es "no duplicar"

La pregunta que guio este análisis fue "¿qué le pertenece a quién?". La respuesta cambió a
mitad de camino, al leer el código fuente real de `gentle-ai`:

**Gentle-AI ya tiene una abstracción de adaptador nativa para 16 hosts** —
`internal/agents/interface.go` define un `Adapter` con métodos como `SkillsDir`,
`SubAgentsDir`, `SettingsPath`, `MCPStrategy`, y `internal/agents/factory.go` conecta
implementaciones concretas para Claude Code, Cursor, Codex, Windsurf, Pi, OpenCode, Gemini
CLI, VS Code Copilot, Kilocode, Kimi, Qwen Code, Kiro, Antigravity, OpenClaw, Trae y Hermes.

Más aún: **gentle-ai ya empaqueta e instala nativamente casi todos los mismos skills y
agents que `vendor/gentle-pi/` vuelve a traer por sparse submodule.**
`internal/assets/skills/` contiene `branch-pr`, `chained-pr`, `cognitive-doc-design`,
`comment-writer`, `issue-creation`, `judgment-day`, `skill-creator`, `skill-improver`,
`skill-registry`, `work-unit-commits` y las 7 skills de SDD. `internal/assets/claude/agents/`
ya trae, con el formato correcto de subagente de Claude Code (herramientas en mayúscula, no
el vocabulario Pi en minúscula), los cuatro lentes de review, los tres roles de Judgment Day
y los doce agentes de SDD — instalados de forma nativa en `~/.claude/agents/` vía
`gentle-ai install`/`sync`.

Esto reformula el problema. No se trata de decidir "qué vendorizar de gentle-pi", sino de
reconocer que **gran parte de `vendor/gentle-pi/assets/agents/` y varios skills vendorizados
son, con altísima probabilidad, una segunda copia — con formato roto (frontmatter en el
dialecto de herramientas de Pi, no el de Claude Code) — de algo que `gentle-ai install` ya
coloca correctamente en `~/.claude/`.** El harness no necesita reinventar ni revendorizar esa
capa; necesita apoyarse en ella y limitarse a lo que ningún `install` en frío puede darle: el
cableado de hooks en vivo dentro de una sesión de Claude Code.

Un segundo hallazgo de igual peso: **ya existe una duplicación literal, no conceptual.**
`internal/components/sdd/inject.go:1454-1504` instala en `~/.claude/settings.json` un hook
`UserPromptSubmit` que ejecuta textualmente
`gentle-ai skill-registry refresh --quiet --no-gitignore --cwd "${CLAUDE_PROJECT_DIR:-$PWD}" || true`
— el mismo comando, carácter por carácter, que `plugin/claude-code/hooks/hooks.json:26-34` ya
declara como primer hook `UserPromptSubmit` del plugin. Un usuario que corrió
`gentle-ai install` para Claude Code *y* instaló el plugin gentle-claude dispara ese comando
dos veces por cada prompt.

---

## 1. Filosofía oficial del proyecto

**Gentle Harnesses conecta el ecosistema Gentle-AI con hosts que tienen un ciclo de vida de
sesión propio, en vivo, que Gentle-AI no puede alcanzar instalando archivos en frío.** Su
única razón de existir es esa brecha: hooks que se disparan durante una sesión real (arranque,
cada prompt, cada llamada a herramienta, fin de subagente, cierre), traduciendo el contrato
específico del host hacia llamadas contra la CLI estable de `gentle-ai`.

### Qué SÍ es la misión

- Traducir el contrato de hooks de un host concreto (formato de payload, variables de
  entorno, forma de bloquear/permitir una acción) hacia comandos de `gentle-ai`.
- Reaccionar a eventos que sólo ocurren en tiempo real dentro de la sesión (una llamada a
  `Bash`, un `git commit`, un subagente que termina) — nada de esto existe todavía en el
  momento de `gentle-ai install`.
- Rellenar, de forma explícitamente temporal y documentada, huecos que la CLI nativa aún no
  cubre (el ejemplo correcto ya existe en el propio repo: `inject_adapter_skills()` trae un
  comentario `REMOVE this function if gentle-ai adds native support for these paths`).

### Qué NO es la misión

- No es reimplementar el motor de review, la clasificación de riesgo, el registro de skills o
  el modelo de agentes — eso ya existe en `gentle-ai` y, para varios casos, ya existe también
  empaquetado nativamente para Claude Code específicamente.
- No es mantener una segunda copia de contenido agnóstico de plataforma (skills, agentes,
  contratos) sólo porque gentle-pi lo trae — si gentle-ai ya lo instala nativamente,
  revendorizarlo es peso muerto con riesgo de desincronización.
- No es convertirse en el lugar donde vive la identidad de memoria, SDD o revisión del
  ecosistema — esas siguen siendo responsabilidad de gentle-ai / engram, tal como el propio
  `MIGRATION-RESEARCH.md` ya establece correctamente ("gentle-claude should not try to own
  memory either").

---

## 2. Principios arquitectónicos

1. **Fuente única de la verdad para toda política de ecosistema.** Umbrales de riesgo,
   taxonomía de comandos peligrosos, formato de skill registry: viven una sola vez, en
   `gentle-ai`. Si un harness necesita esa lógica, la invoca — no la reescribe en bash,
   TypeScript o donde sea.
2. **Antes de vendorizar, verificar si ya es nativo.** Todo contenido "agnóstico de
   plataforma" candidato a `vendor/` debe primero chequearse contra `internal/assets/` de
   gentle-ai. Si ya está ahí con el formato correcto para el host, no se vendoriza — se
   documenta como dependencia de `gentle-ai install`.
3. **Todo lo que se vendorice temporalmente debe estar etiquetado como removible**, con la
   condición exacta de remoción (ej. "remover cuando gentle-ai exponga X"). El patrón ya
   existe en este repo (`inject_adapter_skills()`); debe generalizarse, no ser la excepción.
4. **El harness traduce protocolos, no inventa política de seguridad.** Cuando por diseño la
   política debe vivir en el host (ej. el guard de comandos destructivos, que el propio
   `gentle-ai` declara intencionalmente fuera de su alcance), su contenido debe tener una
   única fuente versionada compartida entre hosts — no una copia manual por adaptador que
   puede divergir silenciosamente.
5. **Ningún hook debe fallar en silencio contra un comando inexistente.** Un `|| true` que
   traga un `unknown command` no es "fail-open", es un bug invisible sin cobertura de test.
6. **Un test por script de hook, sin excepción.** El propio `AGENTS.md` del harness ya lo
   exige; hay que cumplirlo, no solo declararlo.

---

## 3. Responsabilidades de Gentle-AI (verificadas en código, no asumidas)

| Capacidad | Evidencia | Estado real |
|---|---|---|
| Abstracción de adaptador multi-host (16 hosts) | `internal/agents/interface.go`, `factory.go:25-52` | Nativo y completo |
| Instalación / sync de config, skills y agents por host | `internal/cli/install.go`, `sync.go`, `internal/components/skills/inject.go` | Nativo y completo |
| Formato de skill registry (`.atl/skill-registry.md`) | `internal/skillregistry/registry.go:19-105` | Nativo, formato cerrado (ver §5) |
| Motor de review (start/finalize/validate/status), contrato v1 | `gentle-ai review --help`, `internal/reviewtransaction/` | Nativo — la CLI instalada (v2.1.11) expone la superficie unificada; el clasificador de riesgo (`ClassifyRisk`) existe como librería pero no está enganchado a ningún comando en la fuente auditada (v1.49.0) |
| Agentes de review (4R), Judgment Day, SDD — contenido y despliegue | `internal/assets/claude/agents/*.md`, instalados vía `SubAgentsDir` | Nativo, formato correcto de subagente de Claude Code |
| Skills agnósticos (branch-pr, chained-pr, comment-writer, etc.) | `internal/assets/skills/*` | Nativo |
| Comandos slash de SDD para Claude Code | `internal/assets/claude/commands/*.md` | Nativo — coincide con los `sdd-*` ya activos como skills instalados |
| `doctor` (salud del ecosistema) | `internal/cli/doctor.go:41,70-84` | Nativo — 4 chequeos (binarios conocidos, `state.json`, engram HTTP, disco). `codegraph` no estaba en la lista de binarios conocidos en v1.49.0; a reconfirmar contra v2.1.11 |
| Skill "release" (publicación npm de gentle-pi) | ausente en `internal/assets/skills/` | **No existe de forma nativa** — es genuinamente específico de Pi |
| Hooks de ciclo de vida en tiempo de sesión (SessionStart, PreToolUse, SubagentStop, Stop de Claude Code) | grep sin resultados en `internal/` más allá de la inyección puntual de `UserPromptSubmit` | **No existe** — es exactamente el vacío que el harness debe llenar |

---

## 4. Responsabilidades de Gentle Harnesses (y sólo éstas)

- **Cableado de hooks en vivo**: `hooks.json` + los scripts bash que Claude Code ejecuta en
  cada evento de sesión.
- **Traducción de payloads del host**: parsear `CLAUDE_TOOL_NAME`, `CLAUDE_TOOL_INPUT`,
  `CLAUDE_PLUGIN_ROOT`, el JSON de `SessionStart`/`PreToolUse`, y devolver las formas de
  salida que Claude Code espera (`systemMessage`, `hookSpecificOutput`, `decision:block`).
- **Resolución local del binario** (`$CLAUDE_PLUGIN_ROOT/bin/gentle-ai` antes que `PATH`).
- **Prompts operacionales adaptados** a la forma real del repo que los usa (gpr/gcl/gis/gwr
  sin las rutas de monorepo de Pi) — contenido genuinamente distinto por host, no candidato a
  compartirse.
- **Empaquetado e instalación de un solo comando** vía `.claude-plugin/marketplace.json` —
  mecánica de distribución específica de Claude Code.
- **Relleno temporal y etiquetado** de vacíos puntuales de la CLI (mientras existan).

Todo lo demás — política de riesgo, taxonomía de comandos peligrosos como fuente única,
contenido de skills/agentes agnósticos de plataforma, contratos de review — no le pertenece
al harness ni siquiera temporalmente salvo que esté documentado como préstamo con fecha de
vencimiento.

---

## 5. Análisis carpeta por carpeta — código nativo de gentle-claude

### `plugin/claude-code/hooks/hooks.json`
**MANTENER.** Responsabilidad bien definida: cablea 6 registros de hook contra 5 eventos de
Claude Code. El único punto flojo es que el `UserPromptSubmit` de skill-registry duplica
literalmente lo que `gentle-ai install` ya puede escribir en `~/.claude/settings.json` (ver
§0) — decisión a tomar en el roadmap, no un problema de diseño del archivo en sí.

### `plugin/claude-code/scripts/gentle_ai.sh`
**MANTENER.** El archivo mejor escrito del repo: wrappers finos de invocación de proceso,
verificados en vivo contra la forma real de salida de la CLI instalada. Cero lógica de
política propia.

### `plugin/claude-code/scripts/session-start.sh`
**ADAPTAR.** Correcto en su mayoría. Un chequeo redundante: verifica `command -v codegraph`
por separado de `gentle_ai_doctor` — redundante sólo si `doctor` ya cubre `codegraph` en la
versión instalada (no confirmado).

### `plugin/claude-code/scripts/user-prompt-submit.sh`
**ADAPTAR.** `inject_adapter_skills()` e `inject_asset_manifest()` son el patrón correcto de
duplicación temporal: están explícitamente marcadas para removerse. El único hueco real es
que sólo el estado `next_transition.kind == "review.start"` se advierte como bloqueante; el
estado `"collect"` (lineage ambigua) cae al mensaje genérico.

### `plugin/claude-code/scripts/pre-tool-use.sh`
**Hallazgo principal de todo el audit.** `classify_diff()` (líneas 26-51) reimplementa desde
cero un clasificador LOW/MED/HIGH — el mismo trabajo que, según su propio texto de ayuda, hace
`gentle-ai review start` ("derive the bounded review tier, lenses, and correction budget").
Pero **ningún hook de este repo llama nunca a `review start`** — sólo se invoca
`review validate --gate pre-commit/pre-push`, que valida un recibo ya existente, no lo crea.
Esto significa que la copia en bash no es un atajo local confirmado después por la CLI: es,
hoy, el único árbitro automático de si la puerta de revisión aplica siquiera.
`classify_command()` (líneas 56-98) reimplementa además, en bash, la misma taxonomía
hard-deny/confirm/allow que gentle-pi mantiene por separado en TypeScript
(`classifyGuardedCommand()`) — sin una fuente compartida versionada entre ambas copias.

### `plugin/claude-code/scripts/post-compaction.sh`
**MANTENER.** Correctamente acotado a traducción de payload; el bug histórico (comparaba
contra un campo `trigger` inexistente) ya está corregido y cubierto por test.

### `plugin/claude-code/scripts/subagent-stop.sh`
**Roto en producción.** Ejecuta `"$bin" mem capture --passive --quiet` — `gentle-ai mem` no
existe como subcomando (confirmado en vivo: `Error: unknown command "mem"`). El
`2>/dev/null || true` se traga el error, así que el hook es un no-op silencioso en cada
ejecución, contradiciendo la propia decisión de "delegar memoria a Engram MCP" que el resto
del repo respeta. Sin cobertura de test (no existe `test_subagent_stop.bats`), pese a que
`AGENTS.md` exige un test por script.

### `plugin/claude-code/scripts/session-stop.sh`
**A VERIFICAR.** El `systemMessage` de advertencia se emite dentro de un subshell en
background (`&`) después de que el hook ya devolvió `exit 0` — es probable que ese mensaje
nunca llegue a mostrarse, porque Claude Code lee la salida del hook en el momento en que el
proceso termina, no de un job detrás en segundo plano. El test actual sólo verifica el código
de salida, no si el mensaje se entrega.

### `plugin/claude-code/skills/gentle-ai/SKILL.md`
**MANTENER.** Identidad correcta del harness; la sección de memoria delega bien a Engram MCP.
El bloque de riesgo repite en prosa los mismos umbrales de `classify_diff()` — quinta
restatación de la misma política en todo el ecosistema (bash, esta skill, README, la skill Pi
vendorizada, y el `lib/review-risk.ts` original).

### `plugin/claude-code/prompts/*.md` (gpr, gcl, gis, gwr)
**MANTENER.** Adaptación legítima: quitan las rutas de monorepo de Pi, mantienen la
estructura. Único hueco: carecen del frontmatter YAML que sus originales vendorizados sí
tienen, y no hay confirmación en el repo de que Claude Code los registre como comandos `/gpr`
reales — a verificar antes de asumir que están "vivos".

### `.claude-plugin/plugin.json` + `marketplace.json`
**MANTENER.** Metadata correcta, versión sincronizada con `CHANGELOG.md`.

### `plugin/claude-code/tests/`
**ADAPTAR.** 47 tests reales, cobertura sólida de `classify_command`/`classify_diff`. Gap
concreto: cero cobertura de `subagent-stop.sh` (exactamente el script roto).
`helpers.bash` arrastra una ruta hardcodeada de la máquina del desarrollador y andamiaje de
la era Python que ya no se usa.

### Docs raíz (`README`, `CONTRIBUTING`, `DEVELOPMENT`, `CHANGELOG`, `docs/flow.md`)
**MANTENER.** Consistentes entre sí y con el comportamiento real. Un desvío menor:
`CONTRIBUTING.md` menciona un helper `log_info` que no existe en ningún script.

### `md/MIGRATION.MD` (gitignored)
**ELIMINAR.** Predata la reescritura bash→Python en horas, diagnostica defectos de archivos
`.py` que ya no existen, y su plan de remediación incremental quedó obsoleto por la
reescritura completa que realmente ocurrió. Es tierra de nadie: invisible en git, pero un
mapa erróneo para quien lo encuentre en disco.

### `.github/workflows/ci.yml`, `release.yml`
**MANTENER.** Automatización mínima y correcta, sin política de ecosistema embebida.

---

## 6. Análisis completo de `vendor/gentle-pi/`

Sparse submodule que materializa sólo `skills/`, `prompts/`, `contracts/`, `assets/`,
`docs/`. Cada fila fue leída completa y contrastada contra `internal/assets/` de gentle-ai.

### `skills/` — 12 carpetas + `_shared`

| Skill | ¿Ya nativo en gentle-ai? | Veredicto |
|---|---|---|
| `branch-pr`, `chained-pr`, `cognitive-doc-design`, `comment-writer`, `issue-creation`, `judgment-day`, `skill-creator`, `skill-improver`, `skill-registry`, `work-unit-commits` | Sí — confirmado byte a byte en `internal/assets/skills/` | Redundante con lo nativo |
| `gentle-ai/SKILL.md` (versión Pi) | No aplica — es identidad de Pi | Correctamente suprimida por la skill local |
| `release/SKILL.md` | **No** — confirmado ausente en `internal/assets/skills/` | Riesgo de mal uso (ver hallazgo abajo) |
| `_shared/review-ledger-contract.md` | Existe una copia mejor mantenida en `internal/assets/skills/_shared/` | Huérfano, inalcanzable por el patrón de inyección actual |

**El skill `release` vendorizado es el runbook de publicación npm de gentle-pi**
(`pnpm publish --dry-run`, `gh workflow run publish.yml --repo Gentleman-Programming/gentle-pi`),
y como no hay override local con ese nombre, se inyecta tal cual en cualquier proyecto que use
gentle-claude — incluido el propio gentle-claude, cuyo release real es tag → GitHub Release sin
npm. Es el hallazgo de mayor severidad de todo el análisis de vendor/: instrucciones activamente
equivocadas, no sólo peso muerto.

### `prompts/`
**MANTENER como referencia**, no inyectados (decisión correcta, documentada en `NOTICE`).
Cuatro de cinco ya tienen copia adaptada local; `skill-creation.md` es el único que quedó sin
adaptar — hueco menor, baja prioridad.

### `contracts/review-integration/v1/` — 18 archivos (8 schemas + 10 fixtures)
**A MOVER.** Es, literalmente, el protocolo de red del propio binario `gentle-ai`
(`$id: https://gentle-ai.dev/contracts/...`) — no le pertenece a gentle-pi ni a gentle-claude.
Hoy nada en este repo lo parsea ni lo valida; sólo se usa el identificador de string
`gentle-ai.review-integration/v1` pasado a la CLI. Candidato natural a vivir directamente en el
repo de `gentle-ai` (o consumirse desde ahí), no a llegar de rebote vía gentle-pi.

### `assets/orchestrator*.md`, `chains/`, `support/`, `agents/`
**MIXTO.** `orchestrator.md` está correctamente excluido de la inyección (placeholders
`{{GENTLE_PI_*}}` sin resolver, identidad de Pi). `orchestrator-delegation.md` y
`sdd-orchestrator-workflow.md` mezclan contenido genuinamente reutilizable (tabla de umbrales
de delegación, modelo de fases SDD) con nombres exclusivos de Pi no cubiertos por el filtro de
contexto actual en `SKILL.md` (`gentle-ai-explore/worker/verify`, `ask_user_question`,
`/gentle:sdd-preflight`). `support/strict-tdd*.md` y `sdd-status-contract.md` son agnósticos y
de alto valor. Los 26 archivos de `assets/agents/` tienen frontmatter en el vocabulario de
herramientas de Pi (minúsculas, `find`/`webfetch`/`mem_*`) que Claude Code no interpreta —
**22 de esos 26 ya existen, con el formato correcto, en `internal/assets/claude/agents/` de
gentle-ai**; sólo `gentle-ai-explore/worker/verify` y `review-validator.md` no tienen
equivalente nativo confirmado.

### `assets/migrations/*.json`, `assets/gentle-logo-only.png`
**ELIMINAR.** Manifiestos de checksum del instalador npm de gentle-pi y el logo de badge —
cero referencias en todo el repo, efecto secundario inevitable del sparse checkout a nivel de
directorio.

### `docs/`
`review-integration.md` y `skill-style-guide.md`: **mantener**, agnósticos y activamente
cargados. `native-authority-architecture.md`: **retirar del manifiesto lazy** — es un reporte
de ingeniería interna de la reescritura TypeScript de gentle-pi, cero contenido accionable
para una sesión de Claude Code.

### Raíz del submodule (`package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `.gitattributes`, `.gitignore`)
**Inertes** — efecto secundario del sparse checkout para un paquete npm que nunca se instala
aquí. `LICENSE` es la excepción: **obligatorio**, citado por el `NOTICE` raíz para
cumplimiento MIT. `README.md`: inerte pero legítimo como documentación de procedencia.

---

## 7. Recursos que deben eliminarse

- `md/MIGRATION.MD` — obsoleto, contradice el estado real del código.
- `skills/_shared/review-ledger-contract.md` vendorizado — huérfano, ya existe mejor en
  gentle-ai nativo.
- `docs/native-authority-architecture.md` del manifiesto lazy-load (el archivo puede seguir
  materializado por el sparse checkout, pero no debe inyectarse).
- Referencia a `log_info` en `CONTRIBUTING.md` — helper que no existe.
- Ruta hardcodeada de máquina de desarrollo en `tests/libs`/`helpers.bash`, y andamiaje de
  stub de Python ya no utilizado por ningún script actual.

## 8. Recursos que deben permanecer

- Los 6 scripts de hooks y `gentle_ai.sh` (con las correcciones puntuales de la fase 0/3 del
  roadmap).
- `plugin/claude-code/skills/gentle-ai/SKILL.md` — identidad del harness, insustituible.
- Los 4 prompts operacionales adaptados (`gpr`, `gcl`, `gis`, `gwr`).
- `vendor/gentle-pi/skills/gentle-ai/SKILL.md` (versión Pi) — correctamente suprimida, cero
  costo real.
- `vendor/gentle-pi/assets/support/*`, `orchestrator-memory.md`, `docs/review-integration.md`,
  `docs/skill-style-guide.md` — agnósticos y de valor, aun si algún día se promueven a
  gentle-ai no dejan de ser correctos aquí mientras tanto.
- `LICENSE` vendorizado — obligación legal.
- Toda la suite de tests (con el gap de `subagent-stop.sh` cerrado).

## 9. Recursos que deberían moverse a Gentle-AI

- `contracts/review-integration/v1/` completo — es el protocolo del propio binario;
  vendorizarlo vía gentle-pi es una ruta indirecta para algo que gentle-ai podría publicar o
  exponer directamente.
- Los 10 skills agnósticos ya duplicados nativamente (`branch-pr`, `chained-pr`,
  `cognitive-doc-design`, `comment-writer`, `issue-creation`, `judgment-day`, `skill-creator`,
  `skill-improver`, `skill-registry`, `work-unit-commits`) — no requieren "moverse" porque
  **ya están** en gentle-ai; lo que debe moverse es la dependencia de gentle-claude, de
  "vendorizar desde gentle-pi" a "confiar en `gentle-ai install`".
- Los 22 agentes de `assets/agents/` con equivalente nativo confirmado — misma lógica.
- La taxonomía de `classify_command()` (hard-deny/confirm/allow) — hoy vive por separado en
  bash (gentle-claude) y TypeScript (gentle-pi); necesita una fuente única versionada, y el
  lugar natural es gentle-ai, ya que ninguno de los dos hosts debería ser la autoridad.

## 10. Recursos que deberían reutilizarse directamente (ya nativos — dejar de vendorizar)

Esta es la categoría que más cambia respecto del planteo original: no son recursos por
promover a futuro, **ya existen hoy** en `gentle-ai` instalado, con mejor formato que la copia
vendorizada:

- Los 4 lentes de review (`review-risk`, `review-readability`, `review-reliability`,
  `review-resilience`) + `review-refuter`.
- Los 3 roles de Judgment Day (`jd-judge-a`, `jd-judge-b`, `jd-fix-agent`).
- Los 12 agentes de fase SDD (`sdd-apply` … `sdd-verify`) y los comandos slash
  correspondientes.
- El formato de skill registry (`.atl/skill-registry.md`) y su generación vía
  `gentle-ai skill-registry refresh`.

La condición para "dejar de vendorizar" no es automática: requiere confirmar que un
`gentle-ai install`/`sync` para Claude Code sea un prerrequisito documentado del harness (hoy
no lo es — el harness se instala solo, vía marketplace, sin depender de haber corrido la CLI
antes). Ese es exactamente el trade-off a resolver en el roadmap (fase 2).

## 11. Estrategia para minimizar mantenimiento

1. **Un solo test de "parity" contra la CLI instalada.** Antes de cada release, un test bats
   debe correr `gentle-ai --help`/`gentle-ai doctor` reales y comparar contra lo que los
   scripts asumen (nombres de comando, campos JSON) — así una CLI que cambia de superficie
   rompe CI en vez de romperse en silencio en producción, como ya pasó con `gentle-ai mem`.
2. **Eliminar toda restatación de política sin fuente única.** Los umbrales de riesgo hoy
   están escritos 5 veces (bash, SKILL.md, README, skill Pi vendorizada, TypeScript
   original). Un cambio de umbral requiere editar 5 lugares a mano; ninguno lo hace hoy.
3. **Confiar en `gentle-ai install`/`sync` en vez de re-vendorizar.** Reduce la superficie de
   archivos que este repo tiene que mantener sincronizados con gentle-pi.
4. **Borrar documentación que ya no describe el código** (`md/MIGRATION.MD`) en el momento en
   que queda obsoleta, no meses después.

## 12. Estrategia para evitar duplicación futura

- **Checklist obligatoria antes de vendorizar o escribir lógica nueva:** ¿existe ya en
  `internal/assets/` o `internal/cli/` de gentle-ai? Si sí, no se copia — se documenta como
  dependencia.
- **Todo lo vendorizado temporalmente lleva una condición de remoción explícita** en el propio
  archivo o en `ARCHITECTURE.md`, siguiendo el patrón ya usado en `inject_adapter_skills()`.
- **Ningún harness reimplementa un clasificador de riesgo o de seguridad propio** — sólo
  consume el que gentle-ai exponga, o, si gentle-ai deliberadamente delega esa política al
  host (como el guard de comandos), esa política vive en un solo repo compartido entre hosts,
  no copiada por adaptador.
- **Revisión periódica de `internal/assets/` de gentle-ai contra `vendor/`** — cada release de
  gentle-ai puede haber "alcanzado" contenido que hoy sigue vendorizado por costumbre.

---

## 13. Roadmap de refactorización (checklist accionable)

### Fase 0 — Bugs activos
Son roturas silenciosas hoy, no cuestiones de diseño — se arreglan antes de tocar arquitectura.

- [ ] Arreglar `subagent-stop.sh`: quitar la llamada a `gentle-ai mem` inexistente, delegar la
      captura pasiva al propio agente vía `mem_capture_passive` (MCP), no vía shell
- [ ] Agregar `test_subagent_stop.bats`
- [ ] Verificar si el `systemMessage` async de `session-stop.sh` llega a mostrarse; si no,
      rediseñar la entrega del mensaje

### Fase 1 — Riesgo del skill `release`
Es el único hallazgo que puede llevar a una acción activamente incorrecta (publicar en el
repo/paquete equivocado).

- [x] Crear `plugin/claude-code/skills/release/SKILL.md` con el runbook real de gentle-claude
      (tag → GitHub Release), mismo patrón que ya existe para `gentle-ai/SKILL.md`

### Fase 2 — Decisión de dependencia
Es la decisión que desbloquea todo el resto de la limpieza de `vendor/`.

- [x] Definir si el harness exige `gentle-ai install`/`sync` como prerrequisito documentado
- [x] Si sí: eliminar la duplicación del hook de skill-registry en `hooks.json`
- [x] Empezar a retirar los skills/agentes ya nativos de `vendor/` (ver §10)

### Fase 3 — Puente hacia `review start`
Elimina la duplicación más riesgosa (política de seguridad de review) sin perder el fail-safe
local.

- [ ] Hacer que `pre-tool-use.sh` invoque `gentle-ai review start` cuando corresponda (en vez
      de sólo `validate`)
- [ ] Usar el tier que la CLI devuelva
- [ ] Dejar `classify_diff()` como fallback documentado si la CLI no responde — no como
      árbitro único

### Fase 4 — Fuente única para `classify_command()`
Depende de coordinación con el mantenedor de gentle-ai — más lento, se planifica pero no
bloquea el resto.

- [ ] Proponer a gentle-ai una lista canónica versionada de patrones peligrosos (JSON/YAML)
- [ ] Consumida tanto por gentle-claude como por gentle-pi

### Fase 5 — Limpieza de vendor/
Bajo riesgo, alto valor de claridad — se hace en paralelo a lo anterior.

- [ ] Retirar `docs/native-authority-architecture.md` del manifiesto lazy
- [ ] Ampliar el filtro de contexto Pi en `SKILL.md` (cubrir `gentle-ai-explore/worker/verify`,
      `pi-subagents`, `ask_user_question`, `/gentle:sdd-preflight`)
- [ ] Borrar `md/MIGRATION.MD`
- [ ] Corregir referencia a `log_info` en `CONTRIBUTING.md`
- [ ] Limpiar ruta hardcodeada y andamiaje Python muerto en `tests/libs`/`helpers.bash`

### Fase 6 — Contratos
Depende de gentle-ai — se coordina en paralelo, no bloquea el resto del roadmap.

- [ ] Evaluar con gentle-ai si `contracts/review-integration/v1/` puede consumirse
      directamente desde su repo/release en vez de vía gentle-pi

---

## 14. Arquitectura objetivo v1.0 y soporte multi-host

```
gentle-ai  (motor + adaptador nativo de 16 hosts + skills/agents empaquetados)
   │
   │  install / sync escribe config, skills y agents nativos por host
   ▼
~/.claude/, ~/.cursor/, ~/.codex/, ~/.windsurf/, ...  (ya resuelto por gentle-ai, sin harness)

   ┌─ para hosts CON ciclo de vida de sesión propio (hooks en vivo) ─┐
   │                                                                  │
   ▼                                                                  ▼
gentle-harnesses/plugin/claude-code/     gentle-harnesses/plugin/<host>/
   hooks.json + scripts bash                 mismo patrón, otro protocolo
   (SOLO traducción de protocolo,             de hooks/eventos del host
    nada de política de ecosistema)
```

La pregunta original — "¿cómo organizar el repo si mañana aparecen `gentle-cursor`,
`gentle-codex`, `gentle-windsurf`?" — tiene una respuesta más acotada de lo que sugiere el
nombre: **gentle-ai ya resuelve Cursor, Codex y Windsurf a nivel de instalación** (los 16
adaptadores de `internal/agents/` ya los cubren). Un nuevo `plugin/<host>/` dentro de
`gentle-harnesses` sólo se justifica para hosts que, como Claude Code, exponen un mecanismo de
hooks en tiempo de sesión que valga la pena cablear — si un host no tiene ese mecanismo, no
hace falta ningún harness para él, `gentle-ai install` alcanza.

Para los que sí lo necesiten, la estructura ya adoptada
(`plugin/<host>/{hooks,scripts,skills,prompts,tests}/`) es correcta y escala sin cambios —
cada carpeta de host es un adaptador delgado, ninguno vendoriza contenido agnóstico por
separado. El `vendor/gentle-pi/` actual debería, a mediano plazo, reducirse a lo que ningún
otro mecanismo cubre: contenido de Pi verdaderamente específico (que no aplica a ningún otro
host) y nada más — todo lo agnóstico pasa a ser una dependencia de `gentle-ai install`,
compartida por todos los `plugin/<host>/` sin que ninguno tenga que volver a traerla.

---

## 15. Apéndice — Economía de sesión (delegación, cache, `/clear`)

Nota agregada durante la ejecución de la Fase 0 de este roadmap, con datos reales de esa
ejecución — no proyecciones.

### 15.1 Delegar a subagentes no ahorra tokens — ahorra contexto propio

El fix de Fase 0 (dos scripts de ~15 líneas + dos archivos de test) se delegó a un subagente
por regla explícita de `CLAUDE.md` ("2+ archivos no triviales → delegar"). Costo real medido:
**106.067 tokens y 47 llamadas a herramientas** en el subagente, más el overhead propio de
armar el prompt de delegación, leer el reporte, y releer los 4 archivos para verificar. Hacerlo
inline hubiera costado una fracción de eso — el fix ya estaba diagnosticado con línea exacta
desde el audit, no había nada que "explorar".

**Conclusión:** delegar optimiza *mi* ventana de contexto en una sesión larga (evita que el
contenido completo de archivos leídos se quede pegado en el historial y empuje a compactación
antes), no el costo total en tokens — que normalmente sube, no baja. La regla de umbral por
cantidad de archivos en `CLAUDE.md` no pesa el tamaño/complejidad real de la tarea; para fixes
chicos y ya diagnosticados, delegar es plata tirada.

### 15.2 Capacidad por sesión — no hay techo duro de tokens

Sonnet 5 (`claude-sonnet-5`) corre con ventana de contexto de **1M tokens** (ese valor es el
default y también el máximo — no es un tier separado que haya que activar) y 128K tokens de
salida máxima. Claude Code además capa por encima su propia compactación automática: cuando la
conversación crece, el contexto viejo se resume automáticamente y el trabajo sigue sin
interrupción — no existe un punto donde la sesión "se corta" por tamaño.

Lo que sí limita en la práctica:

- **Costo, no tokens disponibles.** La API es *stateless* — cada request reenvía el historial
  completo. Con prompt caching activo, ese historial se sirve mayormente desde cache (~0.1x el
  costo de input normal) — pero cada evento de compactación reescribe un tramo del historial en
  un resumen, lo cual invalida el prefijo cacheado en ese punto y fuerza una escritura de cache
  cara (1.25x–2x) para todo lo que sigue. Sesiones muy largas con compactaciones frecuentes
  pagan ese costo repetidas veces.
- **Pérdida de fidelidad.** Un resumen de compactación es lossy — detalles finos de intercambios
  viejos (número de línea exacto, redacción exacta de una decisión) se pueden perder o
  aproximar mal después de resumirse.

### 15.3 Cuándo hacer `/clear`

No es una decisión basada en cantidad de tokens — es una decisión de límite de tarea:

- **Hacé `/clear` al arrancar trabajo genuinamente no relacionado** (otro proyecto, otro
  objetivo). Evita pagar por re-enviar/cachear historial irrelevante y evita por completo el
  costo de compactación sobre ese contenido viejo.
- **No hagas `/clear` en medio de un hilo de trabajo relacionado** (como esta sesión: audit →
  fixes → commit → esta misma nota). Perder ese contexto obliga a re-derivar todo lo que ya se
  estableció — mucho más caro que dejar que la compactación automática lo resuma.
- Si el trabajo es una iniciativa sostenida a lo largo de todo un día, dejá que la compactación
  automática haga su trabajo en vez de limpiar manualmente — es exactamente para eso que existe.

---

*Análisis basado en lectura directa de `ARCHITECTURE.md`, `MIGRATION-RESEARCH.md`, `NOTICE`,
los 6 scripts de hooks completos, los 26 archivos de `vendor/gentle-pi/assets/agents/`, los 12
skills vendorizados, los 18 archivos de `contracts/review-integration/v1/`, y el código fuente
real de `gentle-ai@v1.49.0` (módulo Go cacheado localmente) contrastado contra el binario
v2.1.11 instalado. Versión interactiva con navegación y tablas: ver artefacto publicado en esta
conversación.*
