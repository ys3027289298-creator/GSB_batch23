import json

CRUCIBLE_CAP = 4
SYNTH_COST = 10


def new_game():
    return {
        'events': {1: (5, 6), 2: (1, 2)},
        'queue': [],
        'items': [],
        'done': [],
        'next_id': 1,
        'src': 5,
        'dst': 0,
        'closed': False,
        'dirty': True,
    }


def _normalize(state):
    if not isinstance(state, dict):
        raise TypeError("state must be a dict")
    events = state.get('events')
    if not isinstance(events, dict):
        events = {}
    repaired = {}
    for key, value in events.items():
        try:
            rid = int(key)
            repaired[rid] = (int(value[0]), int(value[1]))
        except (TypeError, ValueError, IndexError):
            continue
    state['events'] = repaired
    for key in ('queue', 'items', 'done'):
        if not isinstance(state.get(key), list):
            state[key] = []
    for key in ('next_id', 'src', 'dst'):
        value = state.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            state[key] = 0
    state['next_id'] = max(state['next_id'], 1)
    state['src'] = max(state['src'], 0)
    state['dst'] = max(state['dst'], 0)
    state['closed'] = bool(state.get('closed', False))
    state['dirty'] = bool(state.get('dirty', True))
    return state


def save_game(state):
    _normalize(state)
    return json.dumps(state, sort_keys=True)


def load_game(payload):
    try:
        state = json.loads(payload)
    except (TypeError, ValueError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    return _normalize(state)


def _next_recipe(state):
    if not state['events']:
        return None
    return min(state['events'].items(), key=lambda item: (item[1][0], item[0]))[0]


def bug_21(state):
    _normalize(state)
    return len(state['items']) >= CRUCIBLE_CAP


def bug_24(state):
    _normalize(state)
    return _next_recipe(state)


def bug_27(state):
    _normalize(state)
    if not state['items']:
        return None
    state['dirty'] = True
    return state['items'].pop()


def bug_0(state):
    _normalize(state)
    rid = _next_recipe(state)
    if rid is None or rid in state['done']:
        return False
    state['done'].append(rid)
    state['dirty'] = True
    return True


def bug_3(state):
    _normalize(state)
    if not state['queue']:
        return None
    state['dirty'] = True
    return state['queue'].pop(0)


def bug_6(state):
    _normalize(state)
    return len(state['items'])


def bug_9(state):
    _normalize(state)
    rid = state['next_id']
    state['next_id'] = rid + 1
    state['dirty'] = True
    return rid


def bug_12(state):
    _normalize(state)
    if state['closed'] or len(state['items']) >= CRUCIBLE_CAP:
        return False
    if state['src'] < SYNTH_COST:
        return False
    state['src'] -= SYNTH_COST
    state['dst'] += SYNTH_COST
    state['dirty'] = True
    return True


def bug_15(state):
    _normalize(state)
    return not state['closed']


def bug_18(state):
    _normalize(state)
    if not state['dirty']:
        return False
    state['items'] = []
    state['done'] = []
    state['queue'] = []
    state['next_id'] = max(state['next_id'], max(state['events'], default=0) + 1)
    state['dirty'] = False
    return True


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
