import json


CAPACITY = 5

STATE_KEYS = ("queue", "items", "next_id", "src", "closed", "dst", "events")


def new_game():
    return {
        "queue": [],
        "items": [],
        "next_id": 1,
        "src": CAPACITY,
        "dst": 0,
        "closed": False,
        "events": {},
    }


def _as_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _clean_id_list(value):
    if not isinstance(value, list):
        return []
    ids = []
    for entry in value:
        item_id = _as_int(entry)
        if item_id is not None and item_id >= 1 and item_id not in ids:
            ids.append(item_id)
    return ids


def _clean_events(value):
    if not isinstance(value, dict):
        return {}
    events = {}
    for key, pair in value.items():
        if isinstance(key, str) and key.isdigit():
            key = int(key)
        exhibit_id = _as_int(key)
        if exhibit_id is None or exhibit_id < 1:
            continue
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        alert, order = _as_int(pair[0]), _as_int(pair[1])
        if alert is None or order is None:
            continue
        events[exhibit_id] = (alert, order)
    return events


def _snapshot(state):
    return json.loads(json.dumps(state))


def sanitize(state):
    if not isinstance(state, dict):
        return new_game()
    fresh = new_game()
    for key in list(state):
        if key not in fresh:
            del state[key]
    for key, value in fresh.items():
        state.setdefault(key, value)

    queue = _clean_id_list(state["queue"])
    items = _clean_id_list(state["items"])
    events = _clean_events(state["events"])

    used_ids = queue + items + list(events)
    next_free = max(used_ids) + 1 if used_ids else 1

    src = _as_int(state["src"])
    src = CAPACITY if src is None else min(max(src, 0), CAPACITY)
    dst = _as_int(state["dst"])
    dst = 0 if dst is None else min(max(dst, 0), CAPACITY)

    state["queue"] = queue
    state["items"] = items
    state["events"] = events
    state["next_id"] = next_free
    state["src"] = src
    state["dst"] = dst
    state["closed"] = bool(state["closed"])
    return state


def save_game(state):
    return json.dumps(sanitize(state), ensure_ascii=False)


def load_game(payload):
    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        data = None
    if not isinstance(data, dict):
        return new_game()
    return sanitize(data)


def reset_game(state):
    occupied = bool(state.get("queue") or state.get("items") or state.get("events"))
    state.clear()
    state.update(new_game())
    return occupied


def admit_exhibit(state):
    exhibit_id = state["next_id"]
    state["next_id"] = exhibit_id + 1
    state["queue"].append(exhibit_id)
    return exhibit_id


def take_exhibit(state):
    queue = state["queue"]
    if not queue:
        return None
    return queue.pop(0)


def hall_exhibit(state):
    items = state.get("items")
    if not isinstance(items, list) or not items:
        return None
    return items[0]


def alert_count(state):
    items = state.get("items")
    return len(items) if isinstance(items, list) else 0


def is_open(state):
    return not bool(state.get("closed", False))


def _head_id(state):
    queue = state.get("queue")
    if isinstance(queue, list) and queue:
        return queue[0]
    return state.get("next_id", 1)


def process_exhibit(state, exhibit_id=None):
    exhibit_id = exhibit_id if exhibit_id is not None else _head_id(state)
    items = state["items"]
    if exhibit_id in items:
        return False
    items.append(exhibit_id)
    return True


def record_alert(state, exhibit_id=None, alert=1, order=None):
    exhibit_id = exhibit_id if exhibit_id is not None else _head_id(state)
    events = state["events"]
    if exhibit_id in events:
        return False
    if order is None:
        order = state.get("dst", 0)
    events[exhibit_id] = (alert, order)
    return True


def least_guarded_exhibit(state):
    events = state.get("events")
    if not isinstance(events, dict) or not events:
        return None
    return min(events.items(), key=lambda pair: pair[1][0])[0]


def request_swap(state):
    if not is_open(state) or state["src"] >= CAPACITY:
        return False
    state["src"] += 1
    state["dst"] += 1
    return True


def advance(state):
    backup = _snapshot(state)
    try:
        if not is_open(state):
            return False
        if state["dst"] >= CAPACITY:
            return False
        if not state["queue"]:
            return False
        exhibit_id = state["queue"].pop(0)
        if exhibit_id in state["items"]:
            raise RuntimeError("duplicate exhibit")
        state["items"].append(exhibit_id)
        if not record_alert(state, exhibit_id, order=state["dst"]):
            raise RuntimeError("duplicate alert")
        state["dst"] += 1
        return True
    except Exception:
        state.clear()
        state.update(backup)
        return False


bug_0 = process_exhibit
bug_3 = take_exhibit
bug_6 = alert_count
bug_9 = admit_exhibit
bug_12 = request_swap
bug_15 = is_open
bug_18 = record_alert
bug_21 = hall_exhibit
bug_24 = least_guarded_exhibit
bug_27 = reset_game


def main():
    state = new_game()
    print("命令: run/quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        if raw == "run":
            if not state["queue"]:
                admit_exhibit(state)
            print("ok" if advance(state) else "失败")
        else:
            print("ok")


if __name__ == "__main__":
    main()
