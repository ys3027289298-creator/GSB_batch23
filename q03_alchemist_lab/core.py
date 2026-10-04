import copy


TRANSFER_AMOUNT = 10  # 单次合成消耗的材料数
CRUCIBLE_CAP = 4      # 坩埚容量上限

_MANAGED_KEYS = ("events", "queue", "items", "next_id", "src", "dst", "closed", "done")


def _snapshot():
    return {
        "events": {1: (5, 6), 2: (1, 2)},
        "queue": [],
        "items": [],
        "next_id": 1,
        "src": 5,
        "dst": 0,
        "closed": False,
        "done": [],
    }


def new_game():
    return _snapshot()


def _normalize(state):
    """损坏状态恢复：缺失或类型错误的字段回退到默认值。"""
    defaults = _snapshot()
    for key in _MANAGED_KEYS:
        if not isinstance(state.get(key), type(defaults[key])):
            state[key] = copy.deepcopy(defaults[key])
    if state["next_id"] < 1:
        state["next_id"] = 1
    if state["src"] < 0:
        state["src"] = 0
    if state["dst"] < 0:
        state["dst"] = 0
    return state


def _is_open(state):
    return not state["closed"]


def _crucible_full(state):
    return len(state["items"]) >= CRUCIBLE_CAP


def _has_materials(state):
    return state["src"] >= TRANSFER_AMOUNT


def bug_0(state):
    """创建：处理当前配方。重复处理、锁定、坩埚满都会失败。"""
    _normalize(state)
    if not _is_open(state) or _crucible_full(state):
        return False
    if not state["events"]:
        return False
    recipe_id = min(state["events"])
    if recipe_id in state["done"]:
        return False
    state["done"].append(recipe_id)
    state["queue"].append(recipe_id)
    return True


def bug_3(state):
    """推进：按进入顺序取出下一个待处理配方（先进先出）。"""
    _normalize(state)
    if not state["queue"]:
        return None
    return state["queue"].pop(0)


def bug_6(state):
    """查询：坩埚内材料数量。"""
    _normalize(state)
    return len(state["items"])


def bug_9(state):
    """创建：分配下一个编号，先取后增，不允许跳号。"""
    _normalize(state)
    next_id = state["next_id"]
    state["next_id"] = next_id + 1
    return next_id


def bug_12(state):
    """推进：单次合成只扣一次材料；材料不足时整体失败、状态不变。"""
    _normalize(state)
    if not _is_open(state) or not _has_materials(state):
        return False
    state["src"] -= TRANSFER_AMOUNT
    state["dst"] += TRANSFER_AMOUNT
    return True


def bug_15(state):
    """查询：实验室是否可用（未暂停/未锁定）。"""
    _normalize(state)
    return _is_open(state)


def bug_18(state):
    """读档/重置：恢复初始快照并清空材料；已处于初始状态时返回失败。"""
    _normalize(state)
    snapshot = _snapshot()
    if all(state[key] == snapshot[key] for key in _MANAGED_KEYS):
        return False
    for key in _MANAGED_KEYS:
        state[key] = copy.deepcopy(snapshot[key])
    return True


def bug_21(state):
    """查询：坩埚是否达到上限。"""
    _normalize(state)
    return _crucible_full(state)


def bug_24(state):
    """回滚目标：查看最近进入的配方，只读不删除。"""
    _normalize(state)
    if not state["events"]:
        return None
    return max(state["events"])


def bug_27(state):
    """查询：坩埚下一个产出；空坩埚返回 None 而非占位文本。"""
    _normalize(state)
    if not state["items"]:
        return None
    return state["items"][-1]


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
