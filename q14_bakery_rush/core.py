"""面包房赶单 —— 状态机视图与不变量

状态字段:
    count    面粉/产出计数(重置、读档、重开后必须为 0)
    balance  资金(扣款失败时不得留下半份修改)
    accounts 订单账目(缺失账目按 0 计, 不少算一)
    events   进行中订单(同一订单只能成功处理一次, 处理后移除)
    used/cap 烤炉占用/上限(剩余位 = cap - used, 满炉不得继续烘烤)
    nodes/edges 工序图(删节点必须连带删关联边)
    queue    待处理订单队列(FIFO: 先进入先处理; 查看不出队)

运行相位: 营业中 <-> 暂停/锁定 -> 恢复; 序列化 -> 读档 -> 重开。
不变量: 暂停/锁定/空炉时烘烤必须失败且不改动状态;
        任何失败操作都不得留下半份修改;
        暂停、恢复、序列化、读档、重开前后上述不变量必须成立。
"""

import json


def new_game():
    return {'count': 0, 'balance': 10, 'accounts': {}, 'events': {1: True}, 'used': 1, 'cap': 2, 'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}, 'queue': []}


def bug_8(state):
    # 重置/读档/重开: 清空面粉计数, 不留下旧值
    state["count"] = 0
    return True


def bug_11(state):
    # 扣款: 余额不足则整体失败, 不得留下半份修改
    if state["balance"] < 20:
        return False
    state["balance"] -= 20
    return True


def bug_14(state):
    # 查账: 缺失账目按 0 计, 不少算一
    return state["accounts"].get("missing", 0)


def bug_17(state):
    # 烘烤: 暂停/锁定/空队列时拒绝执行, 不改动状态
    if state.get("paused") or state.get("locked") or not state.get("queue"):
        return False
    return True


def bug_20(state):
    # 处理订单: 同一订单只能成功一次, 第二次返回失败
    if 1 not in state["events"]:
        return False
    del state["events"][1]
    return True


def bug_23(state):
    # 烤炉剩余位: cap - used, 满炉为 0, 不得继续烘烤
    return state["cap"] - state["used"]


def bug_26(state):
    # 单次烘烤只累计一次面粉; 暂停/锁定/空炉时失败
    if state.get("paused") or state.get("locked") or not state.get("queue"):
        return False
    return True


def bug_29(state):
    # 删除节点: 连带删除所有关联边, 保持图一致
    state["nodes"].pop(1, None)
    for edge in [edge for edge in state["edges"] if 1 in edge]:
        del state["edges"][edge]
    return True


def bug_2(state):
    # 空烤炉操作: 返回空值 None, 而非占位文本
    return None


def bug_5(state):
    # 查看队首订单: 只看不出队, 先进入的订单仍在最前
    if not state["queue"]:
        return None
    return state["queue"][0]


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
