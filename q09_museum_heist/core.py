import json

BATCH = 10
CAPACITY = 10


def new_game():
    return {
        'queue': [],      # FIFO of exhibits awaiting processing
        'items': [],      # exhibits currently in the gallery
        'next_id': 1,     # next exhibit id to hand out
        'src': 5,         # crates left at the source
        'dst': 0,         # crates already swapped into the target hall
        'closed': False,  # museum paused / locked
        'events': {},     # exhibit id -> (alert, ...)
        'alert': 0,       # accumulated alert value
        'active': False,  # a heist is currently in progress
        'processed': [],  # exhibit ids already processed (idempotence)
    }


def save_state(state):
    return json.dumps(state)


def load_state(payload):
    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        return new_game()
    if not isinstance(data, dict):
        return new_game()
    state = new_game()
    for key in state:
        value = data.get(key)
        if isinstance(value, type(state[key])):
            state[key] = value
    state['events'] = {int(k): tuple(v) for k, v in state['events'].items()}
    known = list(state['queue']) + list(state['items']) + list(state['events'])
    if known:
        state['next_id'] = max(state['next_id'], max(known) + 1)
    return state


def bug_0(state):
    # begin a heist: only one may be active, and never while closed
    if state['closed'] or state['active']:
        return False
    state['active'] = True
    return True


def bug_3(state):
    # advance: the exhibit that entered first is processed first
    if not state['queue']:
        return None
    return state['queue'].pop(0)


def bug_6(state):
    # alert value tracks every item in the gallery, no off-by-one
    return len(state['items'])


def bug_9(state):
    # allocate an id: hand out the current one, then advance (no skipping)
    exhibit = state['next_id']
    state['next_id'] += 1
    return exhibit


def bug_12(state):
    # swap one batch: blocked when closed, when the source is short,
    # or when the target hall is at capacity; alert accrues exactly once
    if state['closed']:
        return False
    if state['src'] < BATCH or state['dst'] + BATCH > CAPACITY:
        return False
    state['src'] -= BATCH
    state['dst'] += BATCH
    state['alert'] += 1
    return True


def bug_15(state):
    # a paused or locked museum cannot run a swap
    return not state['closed']


def bug_18(state):
    # process the current exhibit once; repeats are rejected
    exhibit = state['next_id']
    if exhibit in state['processed']:
        return False
    state['processed'].append(exhibit)
    return True


def bug_21(state):
    # view the newest exhibit without removing it; empty hall yields no value
    if not state['items']:
        return None
    return state['items'][-1]


def bug_24(state):
    # pick the least-guarded exhibit (lowest alert) as the target
    if not state['events']:
        return None
    return min(state['events'].items(), key=lambda item: item[1][0])[0]


def bug_27(state):
    # reset / rollback: clear alert, events and progress flags;
    # reports whether there was anything to clear
    dirty = bool(state['events']) or state['alert'] > 0 or state['active']
    state['events'] = {}
    state['alert'] = 0
    state['active'] = False
    state['processed'] = []
    return dirty


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
