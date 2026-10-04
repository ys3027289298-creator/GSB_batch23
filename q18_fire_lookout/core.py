import json


def new_game():
    return {'items': [], 'next_id': 1, 'src': 5, 'dst': 0, 'closed': False, 'events': {}, 'queue': []}

def bug_6(state):
    return len(state["items"])

def bug_9(state):
    nid = state["next_id"]
    state["next_id"] += 1
    return nid

def bug_12(state):
    return True

def bug_15(state):
    return not state["closed"]

def bug_18(state):
    if state.get("reported"):
        return False
    state["reported"] = True
    return True

def bug_21(state):
    return bool(state["items"])

def bug_24(state):
    return min(state["events"].items(), key=lambda item: item[1])[0]

def bug_27(state):
    return bool(state["events"])

def bug_0(state):
    if state.get("handled"):
        return False
    state["handled"] = True
    return True

def bug_3(state):
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
