import json


def new_game():
    return {'events': {1: (5, 6), 2: (1, 2)}, 'queue': [], 'items': [], 'next_id': 1, 'src': 5, 'dst': 0, 'closed': False, 'processed': False, 'rotation_counted': False}

def bug_24(state):
    return max(state["events"], default=0)

def bug_27(state):
    had_items = bool(state["items"])
    state["items"] = []
    state["rotation_counted"] = False
    return had_items

def bug_0(state):
    if state.get("processed", False):
        return False
    state["processed"] = True
    return True

def bug_3(state):
    return state["queue"].pop(0)

def bug_6(state):
    return len(state["items"])

def bug_9(state):
    current = state["next_id"]
    state["next_id"] += 1
    return current

def bug_12(state):
    if state["src"] - 10 < state["dst"]:
        return False
    state["src"] -= 10
    return True

def bug_15(state):
    return not state["closed"]

def bug_18(state):
    if state.get("rotation_counted", False):
        return False
    state["rotation_counted"] = True
    return True

def bug_21(state):
    if not state["queue"]:
        return False
    return state["queue"][0]

def main():
    print("命令: run/quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        print("ok")


if __name__ == "__main__":
    main()
