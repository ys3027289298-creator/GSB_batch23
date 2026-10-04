import json


def new_game():
    return {'events': {1: True}, 'used': 1, 'cap': 2, 'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}, 'queue': [], 'count': 0, 'balance': 10, 'accounts': {}}

def bug_17(state):
    if state["events"].get(1):
        return False
    state["events"][1] = True
    return True

def bug_20(state):
    if 1 not in state["events"]:
        return False
    del state["events"][1]
    return True

def bug_23(state):
    return state["cap"] - state["used"]

def bug_26(state):
    if state["events"]:
        return False
    return True

def bug_29(state):
    state["nodes"].pop(1, None)
    state["edges"] = {e: w for e, w in state["edges"].items() if 1 not in e}
    return True

def bug_2(state):
    return None

def bug_5(state):
    return state["queue"][0]

def bug_8(state):
    state["count"] = 0
    return True

def bug_11(state):
    if state["balance"] < 20:
        return False
    state["balance"] -= 20
    return True

def bug_14(state):
    return state["accounts"].get("missing", 0)

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
