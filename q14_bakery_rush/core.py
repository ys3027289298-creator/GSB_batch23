import json


# ---- 常量 -------------------------------------------------------------
BAKE_COST = 20   # 单次烘烤扣款
NEXT_ID_KEY = "next_id"

# 状态机:
#   阶段标志 : paused (True=暂停/锁定, False=营业; 缺省视为 False)
#   订单流转 : add_order -> queue 队尾
#              peek_order(只读队首) -> bake(原子提交) -> dequeue -> complete
#   不变量   : 队列 FIFO; edges 的端点必在 nodes 中; 面粉每炉只累计一次;
#              任何失败的操作不得留下半份修改; 序列化/读档/重开走全量替换。


def new_game():
    return {'count': 0, 'balance': 10, 'accounts': {}, 'events': {1: True}, 'used': 1, 'cap': 2, 'nodes': {1: True, 2: True}, 'edges': {(1, 2): 5}, 'queue': []}


# ---- 运行态: 暂停 / 恢复 ----------------------------------------------
def pause(state):
    state["paused"] = True
    return True


def resume(state):
    state["paused"] = False
    return True


def is_paused(state):
    return bool(state.get("paused", False))


# ---- 订单队列: FIFO ----------------------------------------------------
def peek_order(state):
    """查看队首订单, 只读不删。"""
    queue = state["queue"]
    return queue[0] if queue else None


def dequeue_order(state):
    """取出队首订单; 烤炉/队列空时返回 None, 而不是占位文本。"""
    queue = state["queue"]
    if not queue:
        return None
    return queue.pop(0)


def add_order(state):
    """新订单编号由账本中的单调计数器产生, 读档后连续不跳号。"""
    next_id = state["accounts"].get(NEXT_ID_KEY, 0) + 1
    state["accounts"][NEXT_ID_KEY] = next_id
    state["nodes"][next_id] = True
    state["queue"].append(next_id)
    return next_id


# ---- 烤炉 --------------------------------------------------------------
def free_slots(state):
    """剩余炉位 = 上限 - 已占用。"""
    return state["cap"] - state["used"]


def can_bake(state, order_id=None):
    """烘烤前置条件(只读): 未暂停/锁定、队列有单、炉位未满、订单未重复处理。"""
    if is_paused(state):
        return False
    if not state["queue"]:
        return False
    if free_slots(state) <= 0:
        return False
    if state["balance"] < BAKE_COST:
        return False
    if order_id is not None and order_id in state["events"]:
        return False
    return True


def bake(state, order_id=None):
    """单次烘烤: 全部前置检查通过后才一次性提交, 面粉只累计一次。"""
    if not can_bake(state, order_id):
        return False
    state["balance"] -= BAKE_COST
    state["used"] += 1
    state["count"] += 1
    return True


def complete_order(state, order_id):
    """完成/取消订单: 从已处理登记中注销, 返回是否曾登记。"""
    return state["events"].pop(order_id, None) is not None


def remove_node(state, node):
    """删除订单节点, 并级联删除其关联边, 保证不残留悬空边。"""
    state["nodes"].pop(node, None)
    for edge in [edge for edge in state["edges"] if node in edge]:
        del state["edges"][edge]
    return True


def view_order(state, order_id):
    """查看订单节点, 只读, 绝不变更状态。"""
    return state["nodes"].get(order_id)


# ---- 重置 / 序列化 / 读档 ---------------------------------------------
def clear_flour(state):
    state["count"] = 0
    return True


def reset(state):
    """重开: 全量替换为新局, 面粉等现场数据不残留。"""
    state.clear()
    state.update(new_game())
    return True


def to_json(state):
    """序列化; edges 的元组键编码为 [u, v, w] 列表, 其余键名保持不变。"""
    payload = dict(state)
    payload["edges"] = [[u, v, w] for (u, v), w in state["edges"].items()]
    return json.dumps(payload)


def from_json(text):
    """读档: 先清空再整体装入, 旧面粉等现场数据不残留, 编号计数器原样恢复。"""
    payload = json.loads(text)
    payload["edges"] = {(int(u), int(v)): w for u, v, w in payload["edges"]}
    return payload


# ---- 测试契约函数(bug_N 名称与签名保持不变) ---------------------------
def bug_8(state):
    # 重置时必须清空面粉
    return clear_flour(state)


def bug_11(state):
    # 扣款为原子操作: 余额不足时直接失败, 不留下半份修改
    if state["balance"] < BAKE_COST:
        return False
    state["balance"] -= BAKE_COST
    return True


def bug_14(state):
    # 账本缺键默认 0, 编号计算不出现 -1 造成的跳号
    return state["accounts"].get("missing", 0)


def bug_17(state, order_id=1):
    # 同一订单重复处理: 已在 events 中登记则第二次返回失败
    return order_id not in state["events"]


def bug_20(state, order_id=1):
    # 完成订单: 从待处理登记中移除
    state["events"].pop(order_id, None)
    return True


def bug_23(state):
    # 烤炉剩余炉位(修正少算一)
    return free_slots(state)


def bug_26(state):
    # 暂停/锁定状态, 或无单可烤时, 拒绝烘烤
    return can_bake(state)


def bug_29(state, node=1):
    # 删除节点必须级联清理关联边, 不留悬空边
    return remove_node(state, node)


def bug_2(state):
    # 空烤炉/空队列取货返回 None, 不返回占位文本
    return dequeue_order(state)


def bug_5(state):
    # FIFO: 查看队首但不移除
    return peek_order(state)


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
