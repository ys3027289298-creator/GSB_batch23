"""太空打捞核心逻辑。

状态机视图
==========

状态（由同一份 state 字典派生）：
  - active : 正常打捞，events 为空且未暂停
  - paused : 已暂停（会话级标志），禁止打捞，允许查看与序列化
  - locked : 存在未处理事件（state["events"] 非空），禁止打捞

迁移：
  - pause      : active -> paused
  - resume     : paused -> active
  - 事件出现    : 任意  -> locked（events 非空即锁定）
  - 事件清除    : locked -> 原状态（bug_20）
  - reset/load : 任意  -> active，并清空载重计数 count

不变量（暂停、恢复、序列化、读档、重开前后都必须成立）：
  1. 0 <= used <= cap，count >= 0
  2. edges 只引用 nodes 中存在的残骸节点
  3. queue 先进先出，先进入的残骸先处理，查看不误删
  4. 同一残骸不可重复处理（events 登记过的编号再次处理返回失败）
  5. 失败操作不留下半份修改（先校验、后变更）
"""

import json


STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"
STATUS_LOCKED = "locked"

STATE_KEYS = ("nodes", "edges", "queue", "count", "balance",
              "accounts", "events", "used", "cap")

SALVAGE_COST = 20


def new_game():
    return {'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}, 'queue': [], 'count': 0, 'balance': 10, 'accounts': {}, 'events': {1: True}, 'used': 1, 'cap': 2}


def bug_26(state):
    # 同一残骸重复处理：events 已登记的编号直接失败，不再返回成功。
    if 1 in state["events"]:
        return False
    state["events"][1] = True
    return True


def bug_29(state):
    # 移除残骸节点时级联清理引用它的航道，维持不变量 2。
    state["nodes"].pop(1, None)
    for edge in [edge for edge in state["edges"] if 1 in edge]:
        del state["edges"][edge]
    return True


def bug_2(state):
    # 空货舱返回空值 None，而不是占位文本。
    if not state["queue"]:
        return None
    return list(state["queue"])


def bug_5(state):
    # 查看队首残骸：只读不删，先进先出。
    if not state["queue"]:
        return None
    return state["queue"][0]


def bug_8(state):
    # 重置/读档必须清空载重计数。
    state["count"] = 0
    return True


def bug_11(state):
    # 余额不足时拒绝扣款，且不留下半份修改。
    if state["balance"] < SALVAGE_COST:
        return False
    state["balance"] -= SALVAGE_COST
    return True


def bug_14(state):
    # 缺失编号按 0 处理，读档后编号不跳号。
    return state["accounts"].get("missing", 0)


def bug_17(state):
    # 锁定（有未处理事件）或货舱已满时拒绝打捞；
    # 成功时单次打捞只累计一次载重。
    if state["events"]:
        return False
    if state["used"] >= state["cap"]:
        return False
    state["used"] += 1
    state["count"] += 1
    return True


def bug_20(state):
    # 清除已处理事件，解除锁定。
    state["events"].pop(1, None)
    return True


def bug_23(state):
    # 剩余舱位 = cap - used，不少算一。
    return state["cap"] - state["used"]


def check_invariants(state):
    if not 0 <= state["used"] <= state["cap"]:
        raise ValueError("货舱用量越界: used=%r cap=%r" % (state["used"], state["cap"]))
    if state["count"] < 0:
        raise ValueError("载重计数为负: %r" % state["count"])
    for a, b in state["edges"]:
        if a not in state["nodes"] or b not in state["nodes"]:
            raise ValueError("航道引用了不存在的残骸节点: %r" % ((a, b),))
    return True


def next_debris_id(state):
    # 读档后编号从现有最大值继续，不跳号、不冲突。
    return max(state["nodes"], default=0) + 1


def serialize_state(state):
    check_invariants(state)
    payload = {
        "nodes": sorted(state["nodes"]),
        "edges": [[a, b, w] for (a, b), w in sorted(state["edges"].items())],
        "queue": list(state["queue"]),
        "count": state["count"],
        "balance": state["balance"],
        "accounts": dict(state["accounts"]),
        "events": sorted(state["events"]),
        "used": state["used"],
        "cap": state["cap"],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def deserialize_state(payload):
    data = json.loads(payload)
    state = {
        "nodes": {int(n): True for n in data["nodes"]},
        "edges": {(int(a), int(b)): w for a, b, w in data["edges"]},
        "queue": list(data["queue"]),
        "count": 0,
        "balance": data["balance"],
        "accounts": dict(data["accounts"]),
        "events": {int(e): True for e in data["events"]},
        "used": data["used"],
        "cap": data["cap"],
    }
    check_invariants(state)
    return state


def load_state(state, payload):
    # 先完整解析并校验，成功后才替换原状态，失败不留半份修改。
    loaded = deserialize_state(payload)
    state.clear()
    state.update(loaded)
    return True


def reset_state(state):
    fresh = new_game()
    state.clear()
    state.update(fresh)
    return True


class SalvageSession:
    """状态机视图：在同一份 state 上驱动暂停/恢复/打捞/序列化/读档/重开。"""

    def __init__(self, state=None):
        self.state = state if state is not None else new_game()
        self.paused = False

    def status(self):
        if self.paused:
            return STATUS_PAUSED
        if self.state["events"]:
            return STATUS_LOCKED
        return STATUS_ACTIVE

    def pause(self):
        if self.status() != STATUS_ACTIVE:
            return False
        self.paused = True
        return True

    def resume(self):
        if not self.paused:
            return False
        self.paused = False
        return True

    def salvage(self):
        # 暂停或锁定状态不执行打捞；货舱满拒绝；失败零副作用。
        if self.status() != STATUS_ACTIVE:
            return False
        if self.state["used"] >= self.state["cap"]:
            return False
        self.state["used"] += 1
        self.state["count"] += 1
        return True

    def reset(self):
        reset_state(self.state)
        self.paused = False
        return True

    def save(self):
        return serialize_state(self.state)

    def load(self, payload):
        try:
            load_state(self.state, payload)
        except (ValueError, KeyError, TypeError):
            return False
        self.paused = False
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
