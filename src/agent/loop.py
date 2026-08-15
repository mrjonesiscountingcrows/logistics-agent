"""
The agent loop: plan -> act -> observe cycles.

Tool execution now goes through the harness (src/agent/harness.py), which
adds guardrails, logging, and error handling - the loop itself just
handles the conversation with the model.
"""
import os
from openai import OpenAI

from src.agent.tool_schemas import TOOLS
from src.agent.harness import execute_tool_with_guardrails

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_CYCLES = 5


def run_loop(route_id: int):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a logistics dispatcher assistant. You have tools to "
                "check a route's status and propose reroutes when stops are "
                "delayed. Check the route status first. If stops have missed "
                "their windows, consider proposing a reroute. Explain your "
                "reasoning clearly."
            ),
        },
        {
            "role": "user",
            "content": f"Please check on route {route_id} and let me know if anything needs attention.",
        },
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
        )
    except Exception as e:
        print(f"Could not reach the model: {e}")
        return

    reply = response.choices[0].message
    cycles = 0

    while reply.tool_calls and cycles < MAX_CYCLES:
        cycles += 1
        messages.append(reply)

        for tool_call in reply.tool_calls:
            tool_name = tool_call.function.name
            import json
            arguments = json.loads(tool_call.function.arguments)

            print(f"\n[Agent is calling tool: {tool_name}({arguments})]")

            # this now goes through the harness - guardrails, logging,
            # and error handling all happen inside this one call
            result_text = execute_tool_with_guardrails(tool_name, arguments)

            print(f"[Tool result:]\n{result_text}\n")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_text,
            })

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
            )
        except Exception as e:
            print(f"Could not reach the model on a follow-up call: {e}")
            return

        reply = response.choices[0].message

    if cycles >= MAX_CYCLES:
        print(f"\n[Stopped after reaching the {MAX_CYCLES}-cycle limit.]")

    print("\n=== Agent's final response ===")
    print(reply.content)