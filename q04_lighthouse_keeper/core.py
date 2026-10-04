import json


def new_game():
    return {'items': [], 'cap': 2, 'paused': False, 'count': 0, 'amount': 0, 'src': 10, 'dst': 0, 'audit': [('a', 1), ('b', 2)], 'slots': 0, 'clock': 0}

def bug_28(state):
    fresh = new_game()
    if state == fresh:
        return False
    state.clear()
    state.update(fresh)
    return True

def bug_1(state):
    if state["paused"]:
        return False
    if len(state["items"]) >= state["cap"]:
        return False
    if "x" in state["items"]:
        return False
    state["items"].append("x")
    return True

def bug_4(state):
    if state["paused"]:
        return False
    return True

def bug_7(state):
    state["count"] += 1
    return state["count"]

def bug_10(state):
    if state["amount"] < 5:
        return False
    state["amount"] -= 5
    return True

def bug_13(state):
    if state["src"] < 5:
        return False
    state["src"] -= 5
    state["dst"] += 5
    return True

def bug_16(state):
    rows = state["audit"]
    if not rows:
        return []
    first = rows[0][0]
    return [row for row in rows if row[0] == first]

def bug_19(state):
    if state["paused"]:
        return False
    if state["slots"] >= state["cap"]:
        return False
    state["slots"] += 1
    return True

def bug_22(state):
    if state["paused"]:
        return False
    if len(state["items"]) >= state["cap"]:
        return False
    return True

def bug_25(state):
    if state["paused"]:
        return state["clock"]
    state["clock"] += 1
    return state["clock"]

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
