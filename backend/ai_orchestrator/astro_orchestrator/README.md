# Astro Orchestrator Framework

This project is a focused Autogen (Core + AgentChat) pipeline for astrological analysis. All agents share a single `OpenAIChatCompletionClient` configured for Gemini; there are no mock clients or fallbacks.

---
## 1. Quick Start

1. Supply Gemini credentials. Either export them:
   ```powershell
   setx GEMINI_API_KEY "<your-gemini-key>"
   setx GEMINI_MODEL "gemini-2.5-flash"   # optional override
   ```
   (Restart the shell so that the variables are visible.)  Alternatively, pass `model=` / `api_key=` directly to `build_chat_completion_client`.

2. Prepare a case directory with the expected JSON files:
   ```text
   devanssh/
     input/
       0001/
         lagna.json      # birth chart (D1)
         dasha.json      # Vimshottari timeline
         context.json    # optional, ignored by default
         meta.json       # optional, ignored by default
         dseries/
           d10.json      # Dasamsa chart
   ```
   You can maintain multiple cases under `devanssh/input/<case-id>`.

3. Run the orchestrator from the project root:
   ```powershell
   python -m astro_orchestrator.runtime `
       --case "devanssh/input/0001" `
       --question "Provide a concise life overview focusing on career and romantic relationships." `
       --user-output "reports/devanssh_0001_user.md" `
       --detailed-output "reports/devanssh_0001_detailed.md" `
       --verbose-tokens
   ```
   * `--case` - case folder containing `lagna.json`, `dasha.json`, and `dseries/d10.json`.
   * `--question` - user intent passed to the master writer agent.
   * `--user-output` - compact Markdown report for the end user (defaults to `reports/user_report.md`).
   * `--detailed-output` - full Markdown report with all intermediate summaries (defaults to `reports/detailed_report.md`).
   * `--verbose-tokens` - optional; prints streaming messages and token previews while the agents run.

After the Lagna team finishes its initial passes, the DEEP_DIVER agent pauses for a human clarification. Type a short, non-empty reply (for example, `Clarify how leadership roles in tech firms apply`) or `No additional context available` if you genuinely have nothing to add. The orchestrator will not proceed until it receives a response.

If `GEMINI_API_KEY` is missing the run aborts immediately with a `ValueError`.

---
## 2. Directory Overview

| Path | Purpose |
|------|---------|
| `astro_orchestrator/config/models.py` | Builds the Gemini `OpenAIChatCompletionClient`. |
| `astro_orchestrator/birth_chart/*.py` | Defines Lagna specialist agents (`H_s_p`, `p_n`, `C_Y_A`, `DEEP_DIVER`, `PSY_SIGNATURE`) and the sequential `BirthChartTeam`. |
| `astro_orchestrator/d_series/*.py` | Declares divisional specialists (D2-D60) plus the strategist and the MagenticOne `DSeriesTeam`. |
| `astro_orchestrator/dasha/*.py` | Mahadasha/Antar/Prati Antar agents and the sequential `DashaTeam`. |
| `astro_orchestrator/tools/registry.py` | Creates `TeamTool` wrappers for the birth chart, D-series, and dasha teams. |
| `astro_orchestrator/main/*.py` | Top-level agents, including the `MASTER_WRITER`, and the graph orchestrator. |
| `astro_orchestrator/runtime.py` | CLI entry point: loads case data, runs teams via `run_stream`, aggregates summaries, and writes user/detailed reports. |
| `astro_orchestrator/messages.py` | Placeholder for future structured message types (unused at present). |
| `astro_orchestrator/state.py` | Skeleton state models for future persistence requirements. |

---
## 3. Execution Flow

1. `runtime.run_case` loads JSON from `--case`, builds three task prompts (Lagna, D10, Dasha), and parses the user question for years/ages.
2. Specialist teams execute in isolation:
   * `BirthChartTeam` executes sequentially (H_s_p -> p_n -> C_Y_A -> DEEP_DIVER -> PSY_SIGNATURE).
   * `DSeriesTeam` uses MagenticOne to sample divisional specialists (D2-D60) plus the strategist.
   * `DashaTeam` runs the single dasha analyst over the Mahadasha -> Antar -> Pratyantar chain.
3. Each team returns a sceptic-framed summary which is passed, along with the user brief, to the master writer.
4. The master writer composes the final report using the new evidence-first outline.
5. `runtime.py` writes two Markdown files:
   * **Detailed report** - final forecast followed by the raw team summaries (for audit).
   * **User report** - only the master writer's forecast.
6. Token usage (prompt/completion/total) and per-team timings are emitted to stdout and logged in `logs/run_metrics.jsonl`.
7. Because every agent now challenges astrological claims, expect explicit notes about evidence gaps and real-world validation steps.


---
## 4. Key Agents & Teams

- **Lagna Specialists (`birth_chart/agents.py`)** - sceptic-framed assistants covering chart highlights, narrative hypotheses, yoga audits, contradiction hunting, and behavioural synthesis.
- **Divisional Specialists (`d_series/agents.py`)** - D2, D3, ..., D60 analysts plus the strategist; each now flags weak evidence and mundane explanations.
- **Dasha Analyst (`dasha/agents.py`)** - examines Mahadasha and sub-periods while advising how to fact-check every claim.
- **Master Writer (`main/agents.py`)** - astro-sceptical researcher producing the user-facing report with reality checks and experiment suggestions.
- **Human Proxy** - console prompt allowing a person to answer the Deep Diver's mandatory clarification.


---
## 5. Customisation Checklist

1. Replace the `system_message` strings in each agent file with your production prompts.
2. Extend `runtime.run_case` if you add more divisional JSON files (D9, D20, etc.) or additional data sources.
3. Register Pydantic message types in `messages.py` if you need structured payloads instead of plain text.
4. Implement `save_state()` / `load_state()` if you need to pause or resume long runs.
5. Adjust report formatting or add extra output formats (JSON, HTML) to suit downstream consumers.
6. Integrate telemetry/observability once the workflow scales.

---
## 6. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ValueError: Gemini API key missing` | `GEMINI_API_KEY` not set | Export the key or pass `api_key=` explicitly. |
| `ModuleNotFoundError: autogen_ext.models.openai` | Autogen OpenAI extension not installed | `pip install autogen-ext[openai]`. |
| `FileNotFoundError` for JSON | Case folder missing files | Ensure `lagna.json`, `dasha.json`, and `dseries/d10.json` exist. |
| Unexpected agent output | Prompt/data ambiguity | Tighten agent prompts and confirm JSON schema. |

---
## 7. Next Steps

- Embed domain-specific, production-ready prompts for every specialist.
- Add automated evaluation scripts covering multiple case folders.
- Experiment with shared memories, caching, and persistence to optimise repeated runs.

Once configured, each run is straightforward: drop chart JSON into a case folder, provide the user question, and the master writer returns a deeply cross-linked forecast along with a reviewer-friendly detailed log.
