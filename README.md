# logistics-agent

A last-mile delivery routing agent, built from scratch (no LangChain/CrewAI) to
learn agent architecture concepts directly: tools, skills, harness, loop.

Phase 0 scope (this commit): data foundation only. No agent logic yet.
- Real routing via OpenRouteService (real road network, real drive times)
- Synthetic delivery stops (real addresses, fake time windows)
- SQLite storage for routes/stops

## Setup

1. Get a free API key from https://openrouteservice.org/dev/#/signup
2. Copy `.env.example` to `.env` and fill in `ORS_API_KEY`
3. `python -m venv venv && source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python scripts/init_db.py` — creates the SQLite schema
6. `python scripts/generate_stops.py` — geocodes your address list and seeds
   synthetic stops with fake delivery windows

## Structure

```
src/
  models.py          # Route, Stop data models (sqlmodel)
  data/
    db.py            # SQLite engine/session setup
    seed_addresses.py  # edit this: your real address list
  tools/
    routing.py        # ORS wrapper: get_route(), get_eta()
    weather.py         # OpenWeatherMap wrapper: get_conditions()
scripts/
  init_db.py
  generate_stops.py
```

## Next phases (not yet built)
- Phase 1: tool functions as standalone, testable units (routing.py, weather.py
  stubs are here now, but need `propose_reroute` and disruption injection)
- Phase 2: the loop (plan/act/observe), hand-written
- Phase 3: the harness (guardrails, decision log, stop conditions)
- Phase 4: skills (disruption_response, exception_triage)
- Phase 5: simulation + evaluation
