"""
Tool definitions in OpenAI's function-calling format. This is the "menu"
the model reads to know what tools exist, what each one does, and what
arguments to pass. The model itself decides whether/when to use these -
we're not calling them directly here, just describing them.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_route_status",
            "description": (
                "Get the current status of a delivery route: how many stops "
                "are on time vs. have missed their delivery window, and "
                "which specific stops are delayed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "route_id": {
                        "type": "integer",
                        "description": "The ID of the route to check.",
                    }
                },
                "required": ["route_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_reroute",
            "description": (
                "Given a route with disrupted/delayed stops, try reordering "
                "the stops to recover as many on-time deliveries as possible. "
                "Returns the current score, the best score found, and the "
                "proposed new stop order. Does not apply any change - only "
                "proposes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "route_id": {
                        "type": "integer",
                        "description": "The ID of the route to propose a reroute for.",
                    }
                },
                "required": ["route_id"],
            },
        },
    },
]