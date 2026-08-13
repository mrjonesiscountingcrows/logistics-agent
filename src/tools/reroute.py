"""
Proposes a reordering of stops to recover from a disruption, by trying to
move disrupted stops a few positions later in the sequence - since a
delayed stop sitting early in the route is what causes everything behind
it to cascade late.

This does NOT touch the database. It only proposes - returns the best
order it found, plus the before/after score, for a human (or later, the
agent loop) to decide whether to apply it.
"""
from src.tools.evaluate import evaluate_stop_order

MAX_SHIFT_POSITIONS = 3  # how many spots later we'll try moving a disrupted stop


def move_stop_later(stops: list, index: int, shift: int) -> list:
    """
    Returns a NEW list with the stop at `index` moved `shift` positions
    later. Does not modify the original list.
    """
    new_order = stops.copy()
    stop = new_order.pop(index)
    new_index = min(index + shift, len(new_order))
    new_order.insert(new_index, stop)
    return new_order

def move_stop_to_end(stops: list, index: int) -> list:
    """
    Returns a NEW list with the stop at `index` moved all the way to the
    end of the route. A more aggressive move than move_stop_later - useful
    when a stop's delay is large enough that a small shift doesn't help.
    """
    new_order = stops.copy()
    stop = new_order.pop(index)
    new_order.append(stop)
    return new_order


def propose_reroute(stops: list, start_time) -> dict:
    """
    stops: current stop order (a list of Stop objects, as pulled from the
           database in their current sequence)
    start_time: when the driver begins the route

    Returns a dict with the baseline score, the best alternative found,
    and its score - so we can compare before vs. after.
    """
    baseline_result = evaluate_stop_order(stops, start_time)
    baseline_score = baseline_result["on_time_count"]

    best_order = stops
    best_score = baseline_score

    # find the disrupted stops - these are the ones worth trying to move
    disrupted_indexes = [
        i for i, stop in enumerate(stops) if stop.extra_delay_minutes > 0
    ]

    for index in disrupted_indexes:
        for shift in range(1, MAX_SHIFT_POSITIONS + 1):
            candidate_order = move_stop_later(best_order, index, shift)
            candidate_result = evaluate_stop_order(candidate_order, start_time)
            candidate_score = candidate_result["on_time_count"]

            if candidate_score > best_score:
                best_score = candidate_score
                best_order = candidate_order

        # also try the more aggressive move: push this stop to the very end
        candidate_order = move_stop_to_end(best_order, index)
        candidate_result = evaluate_stop_order(candidate_order, start_time)
        candidate_score = candidate_result["on_time_count"]

        if candidate_score > best_score:
            best_score = candidate_score
            best_order = candidate_order

    return {
        "baseline_score": baseline_score,
        "best_score": best_score,
        "improved": best_score > baseline_score,
        "proposed_order": best_order,
    }