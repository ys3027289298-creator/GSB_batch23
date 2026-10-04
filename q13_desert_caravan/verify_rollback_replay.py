"""可重复的失败回滚与重放验证：python verify_rollback_replay.py

覆盖不变量：
1. 失败操作不改变状态，可回滚到失败前快照后重放成功路径；
2. 同一操作日志从零重放两次，最终状态完全一致（确定性/幂等）；
3. 存档-读档后键名、编号(count/clock)、audit 结构与水量守恒全部保持。
"""
import json
import os
import tempfile

import core


def apply_log(ops):
    """从 new_game 开始按顺序重放操作日志，返回最终状态。"""
    state = core.new_game()
    for name in ops:
        getattr(core, name)(state)
    return state


def main():
    # 1) 失败回滚：在快照之后触发必然失败的操作，状态必须可回滚。
    state = core.new_game()
    core.bug_19(state)
    core.bug_19(state)  # slots == cap
    snap = core.snapshot(state)

    assert core.bug_19(state) is False and state["slots"] == 2  # 槽位已满
    assert core.bug_10(state) is False and state["amount"] == 0  # 余额不足
    # 同一货物：首次装载成功，第二次重复处理失败且不改动状态（幂等）
    assert core.bug_1(state) is True and state["items"] == ["x"]
    assert core.bug_1(state) is False and state["items"] == ["x"]
    # 容量上限拒绝装载且不改队列
    full = core.new_game()
    full["items"] = ["a", "b"]
    assert core.bug_1(full) is False and full["items"] == ["a", "b"]

    core.rollback(state, snap)
    assert state == snap, "回滚后状态必须与快照一致"
    assert state["items"] == [], "回滚须撤销快照之后的成功装载"
    assert core.bug_25(state) == 1 and core.bug_25(state) == 2, "回滚后时钟连续不跳号"

    # 2) 重放确定性：同一条操作日志重放两次，结果逐键相同。
    ops = ["bug_19", "bug_13", "bug_7", "bug_1", "bug_1", "bug_7"]
    run_a = apply_log(ops)
    run_b = apply_log(ops)
    assert run_a == run_b, "重放必须得到相同状态"
    # 幂等：同一货物第二次装载失败且不改变状态
    assert run_a["items"] == ["x"], run_a["items"]
    # 水源每次装载只 +1，两次装载请求但只成功一次
    assert run_a["count"] == 2, run_a["count"]
    # 水量守恒
    assert run_a["src"] + run_a["dst"] == 10, (run_a["src"], run_a["dst"])

    # 3) 暂停路径：暂停期间时钟、装载均不推进。
    paused = core.new_game()
    paused["paused"] = True
    assert core.bug_25(paused) == 0 and paused["clock"] == 0
    assert core.bug_4(paused) is False

    # 4) 查看不删除：空驼队返回空值，有货时查看队首不改动队列。
    assert core.bug_28(core.new_game()) is False
    assert core.bug_16(paused) == [("a", 1)]
    assert paused["audit"] == [("a", 1), ("b", 2)], "查看不得修改 audit"

    # 5) 存档/读档：键名与编号保持，audit 结构恢复。
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "save.json")
        core.save_game(run_a, path)
        loaded = core.load_game(path)
        assert set(loaded.keys()) == set(run_a.keys()), "读档后键名集合必须一致"
        assert loaded["count"] == run_a["count"] and loaded["clock"] == run_a["clock"]
        assert loaded["audit"] == run_a["audit"], "audit 读档后须恢复为元组"
        assert loaded == run_a, "读档状态须与存档状态逐键一致"
        raw = json.load(open(path, encoding="utf-8"))
        assert sorted(raw.keys()) == sorted(core.new_game().keys())

    print("PASS: rollback / replay / idempotency / save-load 全部不变量成立")


if __name__ == "__main__":
    main()
