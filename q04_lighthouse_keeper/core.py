import json


def new_game():
    return {'items': [], 'cap': 2, 'paused': False, 'count': 0, 'amount': 0, 'src': 10, 'dst': 0, 'audit': [('a', 1), ('b', 2)], 'slots': 0, 'clock': 0, 'seen': []}


def _locked(state):
    return bool(state.get('paused') or state.get('locked'))


def bug_28(state, ship=None):
    seen = state.setdefault('seen', [])
    if ship is None:
        if not state['items']:
            return None
        ship = state['items'][0]
    if ship in seen:
        return False
    if ship in state['items']:
        state['items'].remove(ship)
    seen.append(ship)
    return ship


def bug_1(state, ship='x'):
    if ship in state['items']:
        return False
    if len(state['items']) >= state['cap']:
        return False
    state['items'].append(ship)
    return True


def bug_4(state):
    return not _locked(state)


def bug_7(state):
    state['count'] += 1
    return state['count']


def bug_10(state, cost=5):
    if state['amount'] < cost:
        return False
    state['amount'] -= cost
    return True


def bug_13(state, fuel=5):
    if state['src'] < fuel:
        return False
    state['src'] -= fuel
    state['dst'] += fuel
    return True


def bug_16(state, ship='a'):
    return [tuple(row) for row in state['audit'] if row[0] == ship]


def bug_19(state):
    if _locked(state):
        return False
    if state['slots'] >= state['cap']:
        return False
    state['slots'] += 1
    return True


def bug_22(state):
    state.clear()
    state.update(new_game())
    return True


def bug_25(state):
    if _locked(state):
        return state['clock']
    state['clock'] += 1
    return state['clock']


def save_game(state):
    return json.dumps(state)


def load_game(blob):
    state = new_game()
    state.update(json.loads(blob))
    state['audit'] = [tuple(row) for row in state['audit']]
    return state


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
