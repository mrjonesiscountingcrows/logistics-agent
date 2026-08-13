"""
Core data model. Get this right before writing any agent code - the tools,
loop, and harness all read/write through this shape.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Stop(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    route_id: int = Field(foreign_key="route.id")
    address: str
    lat: float
    lon: float
    sequence: int  # position in the route, 0-indexed

    # planning
    window_start: datetime
    window_end: datetime
    priority: str = "standard"  # standard | high

    # actuals, filled in as the simulation runs
    planned_eta: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: str = "pending"  # pending | en_route | delivered | delayed | rerouted


class Route(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    driver_name: str
    date: datetime
    status: str = "active"  # active | completed


class DecisionLogEntry(SQLModel, table=True):
    """
    The harness's audit trail. Every plan/act/observe cycle writes here.
    Not used yet in Phase 0 - table exists now so Phase 3 doesn't need a
    schema migration later.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    route_id: int = Field(foreign_key="route.id")
    trigger: str        # what caused this cycle (e.g. "eta_breach", "weather_alert")
    reasoning: str       # the agent's stated reasoning
    action_taken: str    # "reroute_proposed" | "no_action" | "flagged_for_review"
    outcome: Optional[str] = None  # filled in on the next observe step
