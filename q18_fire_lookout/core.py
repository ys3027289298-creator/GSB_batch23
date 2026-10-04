import json


def new_game():
    return {'items': [], 'next_id': 1, 'src': 5, 'dst': 0, 'closed': False, 'events': {}, 'queue': [], 'handled': False}

def bug_6(state):
    return len(state["items"])

def bug_9(state):
    current = state["next_id"]
    state["next_id"] += 1
    return current

def bug_12(state):
    state["dst"] += state["src"]
    return True

def bug_15(state):
    return not state["closed"]

def bug_18(state):
    if state["handled"]:
        return False
    state["handled"] = True
    return True

def bug_21(state):
    if not state["items"]:
        return None
    return state["items"][0]

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
    if state["closed"]:
        return False
    state["closed"] = True
    return True

def bug_3(state):
    if not state["queue"]:
        return None
    return state["queue"].pop(0)

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
