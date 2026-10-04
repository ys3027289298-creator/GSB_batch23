"""海盗船叛变事件核心状态机。

状态视图（new_game 返回的 dict，JSON 键名固定）：
    accounts  船员忠诚度账户 {船员: 忠诚度}
    events    待处理的叛变事件 {编号: 是否活跃}
    queue     叛变事件 FIFO 队列，先进先出
    nodes     船舱节点 {编号: 是否可用}
    edges     船舱之间的连接 {(甲, 乙): 距离}
    used/cap  已用船舱数 / 船舱上限，不变量：0 <= used <= cap
    count     忠诚度计数，重置或读档后必须清零
    balance   金币余额，不变量：balance >= 0

不变量：
    - 同一叛变事件只能成功处理一次，重复处理返回失败。
    - 船舱达到上限后禁止继续镇压。
    - 暂停 / 锁定 / 队列空时镇压直接失败，且不留下半份修改。
    - 查看事件只读不删；处理事件才出队。
    - 单次镇压只累计一次忠诚度。
    - 失败操作不得修改任何状态。
"""

import json


def new_game():
    return {'accounts': {}, 'events': {1: True}, 'used': 1, 'cap': 2, 'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}, 'queue': [], 'count': 0, 'balance': 10}

def bug_14(state):
    return len(state["accounts"])

def bug_17(state):
    if not state["queue"]:
        return False
    return state["queue"].pop(0)

def bug_20(state):
    if 1 not in state["events"]:
        return False
    del state["events"][1]
    return True

def bug_23(state):
    return state["cap"] - state["used"]

def bug_26(state):
    if not state["queue"]:
        return False
    if state["used"] >= state["cap"]:
        return False
    state["queue"].pop(0)
    state["used"] += 1
    state["count"] += 1
    return True

def bug_29(state):
    state["nodes"].pop(1, None)
    for edge in [edge for edge in state["edges"] if 1 in edge]:
        del state["edges"][edge]
    return True

def bug_2(state):
    return state["accounts"].get("empty")

def bug_5(state):
    if not state["queue"]:
        return None
    return state["queue"][0]

def bug_8(state):
    state["count"] = 0
    return True

def bug_11(state):
    if state["balance"] < 20:
        return False
    state["balance"] -= 20
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
