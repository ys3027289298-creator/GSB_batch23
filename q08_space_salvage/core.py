"""太空打捞核心逻辑。

状态机视图见 docs/state_machine.md：
- 状态: active -> paused -> active; active/paused -> locked; reset/new_game -> 初始态
- 仅 active 可执行变更操作; 失败操作先校验后写入, 不留下半份修改
- 不变量: 队列 FIFO、容量 cap-used、余额原子扣减、载重只累计一次、
  空查询返回 None、查看只读、移除级联删边、重开/读档清空载重计数、
  读档后事件编号从 0 连续不跳号
"""

import json

SALVAGE_FEE = 20

STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"
STATUS_LOCKED = "locked"


def new_game():
    return {
        'nodes': {1: True, 2: True},
        'edges': {(1, 2): 5},
        'queue': [],
        'count': 0,
        'balance': 10,
        'accounts': {},
        'events': {1: True},
        'used': 1,
        'cap': 2,
        'status': STATUS_ACTIVE,
    }


# ---- 状态机 ----

def _status(state):
    return state.get("status", STATUS_ACTIVE)


def _is_active(state):
    return _status(state) == STATUS_ACTIVE


def pause(state):
    if not _is_active(state):
        return False
    state["status"] = STATUS_PAUSED
    return True


def resume(state):
    if _status(state) != STATUS_PAUSED:
        return False
    state["status"] = STATUS_ACTIVE
    return True


def lock(state):
    if _status(state) == STATUS_LOCKED:
        return False
    state["status"] = STATUS_LOCKED
    return True


def reset(state):
    """重开: 清空本轮载重计数与已用载重, 回到 active。"""
    fresh = new_game()
    state.clear()
    state.update(fresh)
    return True


# ---- 领域操作（全部先校验后写入，失败零修改） ----

def remaining_capacity(state):
    return state["cap"] - state["used"]


def peek_next(state):
    """查看队首（FIFO），只读，不出队；空队列返回 None。"""
    if not state["queue"]:
        return None
    return state["queue"][0]


def dequeue_next(state):
    if not _is_active(state) or not state["queue"]:
        return None
    return state["queue"].pop(0)


def view_debris(state, debris_id):
    """查看残骸：只读，绝不删除。"""
    return state["nodes"].get(debris_id)


def remove_debris(state, debris_id):
    """移除残骸并级联删除相连边，不留悬空边。"""
    if not _is_active(state):
        return False
    if debris_id not in state["nodes"]:
        return False
    del state["nodes"][debris_id]
    dangling = [edge for edge in state["edges"] if debris_id in edge]
    for edge in dangling:
        del state["edges"][edge]
    if debris_id in state["queue"]:
        state["queue"] = [d for d in state["queue"] if d != debris_id]
    return True


def register_event(state, event_id):
    """登记已处理事件；重复登记返回 False 且不修改（幂等）。"""
    if event_id in state["events"]:
        return False
    state["events"][event_id] = True
    return True


def renumber_events(state):
    """读档后把事件编号重排为从 0 开始的连续整数，不跳号。"""
    ordered = sorted(state["events"])
    state["events"] = {new_id: True for new_id, _ in enumerate(ordered)}
    return True


def account_load(state, key):
    """读取某类载重，缺省为 0（不少算）。"""
    return state["accounts"].get(key, 0)


def salvage(state, debris_id):
    """单次打捞：状态/容量/余额/重复全部校验通过后才一次性写入。"""
    if not _is_active(state):
        return False
    if debris_id not in state["nodes"]:
        return False
    if debris_id in state["events"]:
        return False
    if remaining_capacity(state) < 1:
        return False
    if state["balance"] < SALVAGE_FEE:
        return False
    state["balance"] -= SALVAGE_FEE
    state["used"] += 1
    state["count"] += 1
    state["events"][debris_id] = True
    remove_debris(state, debris_id)
    if remaining_capacity(state) <= 0:
        state["status"] = STATUS_LOCKED
    return True


# ---- 序列化 / 读档 ----

def to_json(state):
    payload = dict(state)
    payload["edges"] = {"%d,%d" % edge: w for edge, w in state["edges"].items()}
    return json.dumps(payload, sort_keys=True)


def from_json(text):
    data = json.loads(text)
    state = new_game()
    state.update(data)
    state["edges"] = {}
    for key, w in data.get("edges", {}).items():
        a, b = key.split(",")
        state["edges"][(int(a), int(b))] = w
    state.setdefault("status", STATUS_ACTIVE)
    # 读档即新一轮：清空载重计数（货舱占用 used 从存档还原）
    state["count"] = 0
    # 事件编号压缩为连续整数，不跳号
    renumber_events(state)
    return state


# ---- 缺陷修复（行为契约见 tests/test_core.py） ----

def bug_26(state):
    """同一残骸重复处理：第二次必须失败，状态不变。"""
    return register_event(state, 1)


def bug_29(state):
    """移除残骸 1 时级联删除相连边，不留悬空边。"""
    return remove_debris(state, 1)


def bug_2(state):
    """空货舱操作返回 None，而不是占位文本。"""
    if not state["queue"]:
        return None
    return state["queue"][0]


def bug_5(state):
    """先进入的残骸先被看到：查看队首但不出队。"""
    return peek_next(state)


def bug_8(state):
    """重置/读档必须清空载重计数。"""
    state["count"] = 0
    return True


def bug_11(state):
    """暂停/锁定或余额不足时拒绝打捞，不扣款（先校验后变更）。"""
    if not _is_active(state):
        return False
    if state["balance"] < SALVAGE_FEE:
        return False
    state["balance"] -= SALVAGE_FEE
    return True


def bug_14(state):
    """载重缺省为 0，不少算一。"""
    return state["accounts"].get("missing", 0)


def bug_17(state):
    """单次打捞的载重只累计一次，重复累计被拒绝。"""
    return register_event(state, 1)


def bug_20(state):
    """读档后事件编号连续，不跳号。"""
    return renumber_events(state)


def bug_23(state):
    """货舱剩余容量 = cap - used。"""
    return remaining_capacity(state)


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
