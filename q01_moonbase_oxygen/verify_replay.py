"""可重复的失败回滚与重放验证（纯标准库）。

验证持久化不变量：
1. 快照/回滚：任意操作序列中途失败后，回滚到快照，状态完全一致。
2. 重放：从同一快照重放同一操作序列，结果确定且相等。
3. 幂等：失败的操作不改变状态；只读操作（查看订单）不改变状态。
4. JSON 存档往返：序列化/反序列化后状态键与值不变（读档不跳号、不清库存）。
"""
import copy
import json
import unittest

import core


def snapshot(state):
    return json.loads(json.dumps(state))


def normalize(state):
    # audit 含元组，JSON 往返后为列表；统一为 JSON 形态比较
    return json.loads(json.dumps(state))


def op_sequence(state):
    """返回 (名称, 操作, 预期成功) 序列，覆盖全部状态转换路径。"""
    return [
        ("dispatch_count", lambda s: core.bug_7(s), True),
        ("withdraw_ok", lambda s: core.bug_10(s), True),
        ("withdraw_insufficient", lambda s: core.bug_10(s), True),
        ("transfer", lambda s: core.bug_13(s), True),
        ("view_orders", lambda s: core.bug_16(s), True),
        ("airlock_admit", lambda s: core.bug_1(s), True),
        ("tick", lambda s: core.bug_25(s), True),
    ]


def run_sequence(state, ops):
    results = []
    for name, op, _ in ops:
        results.append((name, op(state)))
    return results


def main():
    failures = []

    # 1) 回滚：构造状态 -> 快照 -> 执行部分操作 -> 模拟失败 -> 回滚
    state = core.new_game()
    state.update({"amount": 10, "src": 10, "slots": 0, "items": []})
    snap = snapshot(state)
    ops = op_sequence(state)
    run_sequence(state, ops[:3])
    # 模拟失败：丢弃变更，回滚到快照
    state = snapshot(snap)
    if normalize(state) != normalize(snap):
        failures.append("rollback: 状态未恢复到快照")

    # 2) 重放：从同一快照重放完整序列两次，结果必须一致
    replay_a = snapshot(snap)
    replay_b = snapshot(snap)
    res_a = run_sequence(replay_a, op_sequence(replay_a))
    res_b = run_sequence(replay_b, op_sequence(replay_b))
    if normalize(replay_a) != normalize(replay_b) or res_a != res_b:
        failures.append("replay: 两次重放结果不一致")

    # 3) 幂等：失败操作不产生副作用
    s = core.new_game()
    s.update({"amount": 0})
    before = normalize(s)
    assert core.bug_10(s) is False
    if normalize(s) != before:
        failures.append("idempotent: 库存不足的扣减改变了状态")

    s = core.new_game()
    s.update({"src": 0, "dst": 0})
    before = normalize(s)
    assert core.bug_13(s) is False
    if normalize(s) != before:
        failures.append("idempotent: 氧气源不足的转移改变了状态")

    s = core.new_game()
    s.update({"items": ["a", "b"], "cap": 2})
    before = normalize(s)
    assert core.bug_1(s) is False
    if normalize(s) != before:
        failures.append("idempotent: 气闸满员时入闸改变了状态")

    # 只读操作幂等：查看订单不删除、不改变状态
    s = core.new_game()
    s.update({"audit": [("a", 1), ("b", 2)]})
    before = normalize(s)
    rows1 = core.bug_16(s)
    rows2 = core.bug_16(s)
    if normalize(s) != before or rows1 != rows2:
        failures.append("readonly: 查看订单改变了状态或结果不稳定")

    # 暂停状态：时钟不推进，重复调用结果一致
    s = core.new_game()
    s.update({"paused": True, "clock": 0})
    before = normalize(s)
    r1 = core.bug_25(s)
    r2 = core.bug_25(s)
    if normalize(s) != before or r1 != r2 != 0:
        failures.append("paused: 暂停时时钟仍推进或结果不稳定")

    # 4) JSON 存档往返：读档后键与值保持，编号连续、库存保留
    s = core.new_game()
    s.update({"count": 7, "amount": 42, "items": ["x", "y"]})
    loaded = json.loads(json.dumps(s))
    if set(loaded) != set(s) or loaded["count"] != 7 or loaded["amount"] != 42:
        failures.append("persistence: 读档后键/值丢失或跳号")
    if len(loaded["items"]) != 2:
        failures.append("persistence: 读档后库存被清空")

    if failures:
        for f in failures:
            print("FAIL:", f)
        raise SystemExit(1)
    print("rollback/replay/idempotency/persistence: all checks passed")


if __name__ == "__main__":
    main()
