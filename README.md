# logistics-agent

A last-mile delivery routing agent, built from scratch — no LangChain,
CrewAI, or other agent framework — to learn the core architecture behind
agentic systems directly: **tools, skills, harness, and loop**.

Given a delivery route with disrupted stops (traffic, weather, etc.), the
agent checks the route's status, decides whether a reorder would help
recover on-time deliveries, proposes a new stop order using real
road-network drive times, and logs every decision it makes — without ever
auto-applying a change.

## Why build this from scratch

Frameworks like LangChain and CrewAI hide the plan → act → observe loop,
tool-calling machinery, and guardrail logic behind convenient
abstractions. Building those pieces by hand was the point of this
project — it forces real decisions about state management, error
handling, and stopping conditions that a framework normally makes for
you.

## Architecture

```
Harness: guardrails, decision logging, error handling
  |
  +-- Loop: plan -> act -> observe -> repeat
        |
        +-- Tools: narrow, single-purpose (routing, weather, evaluate)
        +-- Skills: composed from tools (disruption_response)
```

- **Tools** (`src/tools/`) — narrow, single-purpose functions: real
  routing via OpenRouteService, real geocoding via Nominatim, weather via
  OpenWeatherMap, and a route evaluator that scores any stop order by
  real drive time against each stop's delivery window.
- **Skills** (`src/agent/skills.py`) — `disruption_response`: a fixed,
  named recipe (check status → propose a reroute if needed) that the
  model can invoke as one action instead of reasoning through the same
  two steps from scratch every time.
- **Harness** (`src/agent/harness.py`) — every tool call passes through
  here: a daily reroute limit (guardrail), a full audit trail written to
  a `DecisionLogEntry` table, and error handling so a failed API call
  doesn't crash the run.
- **Loop** (`src/agent/loop.py`) — the plan → act → observe cycle,
  hand-written against the OpenAI API, bounded by a max-cycle cap.

## Setup

1. Get free API keys:
   - [OpenRouteService](https://openrouteservice.org/dev/#/signup) — real routing
   - [OpenWeatherMap](https://home.openweathermap.org/users/sign_up) — weather signal
   - [OpenAI](https://platform.openai.com/api-keys) — the agent loop (paid API)
2. `cp .env.example .env` and fill in your keys
3. `python -m venv venv && source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python scripts/init_db.py`
6. Edit `src/data/seed_addresses.py` with ~30 real addresses
7. `python scripts/generate_stops.py` — geocodes addresses, creates a route
8. `python scripts/regenerate_windows.py <route_id>` — sets delivery
   windows based on real drive time, so the undisrupted route is
   achievable

## Running it

```bash
# simulate a disruption
python scripts/inject_disruption.py <route_id>

# see the route's current on-time status
python scripts/test_evaluate.py <route_id>

# test the reroute logic directly, without the LLM
python scripts/test_reroute.py <route_id>

# run the full agent: model checks the route and decides what to do
python scripts/run_agent.py <route_id>
```

Every decision the agent makes — a status check, a proposed reroute, a
reroute blocked by the daily limit — is written to the `decisionlogentry`
table in `logistics.db`, queryable directly:

```bash
sqlite3 logistics.db "SELECT id, trigger, action_taken FROM decisionlogentry ORDER BY id DESC LIMIT 10;"
```

## Evaluation results

`scripts/simulate_evaluation.py` runs the disruption → reroute cycle
across many simulated days, comparing on-time performance with and
without the agent's proposed reroute:

```bash
python scripts/simulate_evaluation.py <route_id>
```

**Results across 10 simulated days** (5 stops randomly disrupted per day,
20–90 minute delays):

| | On-time stops (of 30) |
|---|---|
| Baseline (no intervention) | 12.3 average |
| With agent reroute | 15.6 average |
| **Improvement** | **+3.3 stops (~27% relative)** |
| Best baseline day | 16 |
| Worst baseline day | 6 |
| Best reroute day | 23 |
| Worst reroute day | 7 |

**Honest limitation**: the improvement isn't evenly distributed. On the
most severe disruption days, the agent's best effort still underperformed
what baseline achieved on an easy day — local reshuffling (small shifts +
move-to-end) has a real ceiling once a delay is large enough. Recovering
further would need route-level intervention beyond reordering: splitting
overflow stops to a second driver, or flagging some stops as unrecoverable
for the day rather than attempting them.

## What this project deliberately does not do

- No live GPS/driver data — synthetic disruptions on real, geocoded
  addresses and real road-network drive times
- No auto-execution — every proposed reroute requires human confirmation
  by design
- No continuous scheduling — the harness runs one cycle per invocation,
  not a long-running process checking routes on a timer
- Reordering only — no multi-driver load balancing or vehicle capacity
  constraints
