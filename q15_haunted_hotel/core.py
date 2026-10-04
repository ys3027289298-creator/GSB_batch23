import json

ROOM_COUNT = 5
PROCESS_OP = 'process_guest'
HAUNT_OP = 'haunt'


def new_game():
    return {
        'closed': False,
        'paused': False,
        'locked': False,
        'events': {},
        'queue': [],
        'items': [],
        'next_id': 1,
        'src': ROOM_COUNT,
        'dst': 0,
        'haunt': 0,
        'applied': [],
    }


def _normalize(state):
    fresh = new_game()
    if not isinstance(state, dict):
        return fresh
    for key, default in fresh.items():
        value = state.get(key, default)
        if not isinstance(value, type(default)):
            value = default
        state[key] = value
    if not isinstance(state['events'], dict):
        state['events'] = {}
    state['src'] = max(0, min(state['src'], ROOM_COUNT))
    state['dst'] = max(0, state['dst'])
    state['haunt'] = max(0, state['haunt'])
    state['next_id'] = max(1, state['next_id'])
    known_ids = []
    for key in state['events']:
        try:
            known_ids.append(int(key))
        except (TypeError, ValueError):
            continue
    if known_ids:
        state['next_id'] = max(state['next_id'], max(known_ids) + 1)
    return state


def _operational(state):
    return not (state.get('closed') or state.get('paused') or state.get('locked'))


def _apply_once(state, op):
    applied = state.setdefault('applied', [])
    if op in applied:
        return False
    applied.append(op)
    return True


def _transfer(state, amount):
    if not isinstance(amount, int) or isinstance(amount, bool):
        return False
    if amount < 0 or amount > state['src']:
        return False
    state['src'] -= amount
    state['dst'] += amount
    return True


def _advance_guest(state):
    if not _operational(state) or state['src'] <= 0 or not state['queue']:
        return False
    snapshot = (state['src'], state['dst'], len(state['queue']), len(state['items']))
    guest = state['queue'].pop(0)
    state['items'].append(guest)
    if not _transfer(state, 1):
        state['src'], state['dst'], queued, housed = snapshot
        state['queue'] = [guest] + state['queue']
        state['items'] = state['items'][:housed]
        return False
    return True


def _add_haunt(state):
    if not _apply_once(state, HAUNT_OP):
        return False
    state['haunt'] = state.get('haunt', 0) + len(state['items'])
    return True


def _peek_guest(state):
    queue = state.get('queue', [])
    return queue[0] if queue else None


def _next_guest_id(state):
    nid = state['next_id']
    state['next_id'] = nid + 1
    return nid


def _event_choice(state):
    return min(state['events'].items(), key=lambda entry: sum(entry[1]))[0]


def reset_state(state):
    state.clear()
    state.update(new_game())
    return state


def save_state(state, path):
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(state, handle)
    return True


def load_state(path):
    try:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return new_game()
    return _normalize(data)


def bug_15(state):
    return _operational(state)


def bug_18(state):
    if not _operational(state):
        return False
    return _apply_once(state, PROCESS_OP)


def bug_21(state):
    return _advance_guest(state)


def bug_24(state):
    return _event_choice(state)


def bug_27(state):
    return _peek_guest(state)


def bug_0(state):
    return _add_haunt(state)


def bug_3(state):
    if not state.get('queue'):
        return None
    return state['queue'].pop(0)


def bug_6(state):
    return len(state['items'])


def bug_9(state):
    return _next_guest_id(state)


def bug_12(state):
    return _transfer(state, 10)


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
