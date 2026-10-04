import copy
import json


def new_game():
    return {'items': [], 'cap': 2, 'paused': False, 'count': 0, 'amount': 0, 'src': 10, 'dst': 0, 'audit': [('a', 1), ('b', 2)], 'slots': 0, 'clock': 0}


def bug_1(state):
    # 装载货物：同一货物重复装载直接失败（幂等），达到容量上限拒绝装载。
    if "x" in state["items"]:
        return False
    if len(state["items"]) >= state["cap"]:
        return False
    state["items"].append("x")
    return True


def bug_4(state):
    # 暂停或锁定状态下禁止执行装载。
    if state["paused"]:
        return False
    return True


def bug_7(state):
    # 单次装载只累计一次水源。
    state["count"] += 1
    return state["count"]


def bug_10(state):
    # 支出不得超过存量，失败时不改动状态（可安全回滚）。
    if state["amount"] < 5:
        return False
    state["amount"] -= 5
    return True


def bug_13(state):
    # 转运保持总量守恒：源减少多少，目的地就增加多少。
    if state["src"] < 5:
        return False
    state["src"] -= 5
    state["dst"] += 5
    return True


def bug_16(state):
    # 查看货物只读取、不删除，返回符合条件的记录副本。
    return [row for row in state["audit"] if row[0] == "a"]


def bug_19(state):
    # 占用槽位：达到上限后拒绝继续分配。
    if state["slots"] >= state["cap"]:
        return False
    state["slots"] += 1
    return True


def bug_22(state):
    return True


def bug_25(state):
    # 暂停时时钟不推进，恢复后从原编号继续，不跳号。
    if state["paused"]:
        return state["clock"]
    state["clock"] += 1
    return state["clock"]


def bug_28(state):
    # 空驼队返回空值；非空时按先进先出查看队首，不出队。
    if not state["items"]:
        return False
    return state["items"][0]


def snapshot(state):
    # 深拷贝快照，用于失败回滚。
    return copy.deepcopy(state)


def rollback(state, snap):
    # 就地回滚到快照，保留同一 state 对象引用。
    state.clear()
    state.update(copy.deepcopy(snap))
    return state


def save_game(state, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False)


def load_game(path):
    # 读档：键名不变，audit 恢复为元组列表，编号（count/clock）原样续接。
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    state = new_game()
    state.update(data)
    state["audit"] = [tuple(row) for row in state["audit"]]
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
