import json


def new_game():
    return {'src': 5, 'dst': 0, 'closed': False, 'events': {}, 'queue': [], 'items': [], 'next_id': 1}

def bug_12(state):
    if state["src"] < 10:
        return False
    state["src"] -= 10
    return True

def bug_15(state):
    if state["closed"]:
        return False
    return True

def bug_18(state):
    if "dive" in state["events"]:
        return False
    state["events"]["dive"] = True
    return True

def bug_21(state):
    if not state["items"]:
        return False
    return state["items"].pop()

def bug_24(state):
    if not state["events"]:
        return None
    return min(state["events"].items(), key=lambda item: item[1][0])[0]

def bug_27(state):
    if state["dst"] == 0:
        return False
    state["dst"] = 0
    return True

def bug_0(state):
    if state["dst"] >= 1:
        return False
    state["dst"] += 1
    return True

def bug_3(state):
    return state["queue"].pop(0)

def bug_6(state):
    return len(state["items"])

def bug_9(state):
    next_id = state["next_id"]
    state["next_id"] = next_id + 1
    return next_id

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
