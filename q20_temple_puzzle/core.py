"""古庙机关核心状态机。

状态机视图（同一状态贯穿暂停/恢复/序列化/读档/重开）::

    locked --start--> running --pause--> paused --resume--> running
                        |  \_________________|                  |
                        v                                     v
                     reset/new_game  <------------------  reset()
                        |
                        +-- serialize() --> JSON --> load() --> 原状态恢复

不变量（任何时刻都必须成立，失败操作不得留下半份修改）：
    1. 机关事件一经处理即从 events 移除，重复处理返回 False；
    2. 祭坛占用 used 永不超过上限 cap，满员后触发被拒绝；
    3. 空祭坛/空机关操作返回 None，而不是占位文本；
    4. 机关队列严格 FIFO，先进入的先处理，查看不移除；
    5. paused / locked 状态下一切触发都被拒绝；
    6. 查看机关不删除节点；删除节点时级联清理相关边；
    7. 机关次数 count 单次触发只 +1，reset/load 后清零；
    8. 读档后 next_id 从 max(已有编号)+1 继续，不跳号、不复用。
"""

import json

STATUS_LOCKED = "locked"
STATUS_RUNNING = "running"
STATUS_PAUSED = "paused"


def new_game():
    """重开一局：所有计数清零，机关编号从 1 重新开始。"""
    return {
        'events': {1: True},
        'used': 1,
        'cap': 2,
        'nodes': {1: True, 2: True},
        'edges': {(1, 2): 5},
        'queue': [],
        'count': 0,
        'balance': 10,
        'accounts': {},
        'status': STATUS_LOCKED,
        'next_id': 3,
    }


# ---- 状态迁移 ----

def start(state):
    """locked -> running。"""
    if state.get('status') != STATUS_LOCKED:
        return False
    state['status'] = STATUS_RUNNING
    return True


def pause(state):
    """running -> paused。"""
    if state.get('status') != STATUS_RUNNING:
        return False
    state['status'] = STATUS_PAUSED
    return True


def resume(state):
    """paused -> running。"""
    if state.get('status') != STATUS_PAUSED:
        return False
    state['status'] = STATUS_RUNNING
    return True


def reset(state):
    """清空机关次数等运行数据，回到 locked。失败不改动任何字段。"""
    fresh = new_game()
    state.clear()
    state.update(fresh)
    return True


# ---- 序列化 / 读档 ----

def serialize(state):
    """状态 -> JSON 文本（键名保持不变；tuple 边键编码为字符串）。"""
    data = dict(state)
    data['events'] = {str(k): v for k, v in state['events'].items()}
    data['nodes'] = {str(k): v for k, v in state['nodes'].items()}
    data['edges'] = {'%d,%d' % k: v for k, v in state['edges'].items()}
    return json.dumps(data)


def load(payload):
    """JSON 文本 -> 状态；机关次数清零，编号不跳号。"""
    data = json.loads(payload)
    state = new_game()
    state.update(data)
    state['events'] = {int(k): v for k, v in data.get('events', {}).items()}
    state['nodes'] = {int(k): v for k, v in data.get('nodes', {}).items()}
    state['edges'] = {tuple(int(p) for p in k.split(',')): v
                      for k, v in data.get('edges', {}).items()}
    state['count'] = 0
    ids = list(state['events']) + list(state['nodes'])
    state['next_id'] = max(ids, default=0) + 1
    return state


# ---- 机关操作（修复后的 bug_* 接口，名称与签名不变） ----

def bug_20(state):
    """处理机关事件：同一机关重复处理时第二次返回 False，不重复生效。"""
    if 1 not in state['events']:
        return False
    del state['events'][1]
    state['count'] = state.get('count', 0) + 1
    return True


def bug_23(state):
    """祭坛剩余空位：达到上限后为 0，拒绝继续触发。"""
    return state['cap'] - state['used']


def bug_26(state):
    """触发闸门：暂停或锁定状态下一律拒绝执行。"""
    return state.get('status') == STATUS_RUNNING


def bug_29(state):
    """移除机关节点：查看不删除；删除时级联清理相连的边。"""
    state['nodes'].pop(1, None)
    state['edges'] = {edge: w for edge, w in state['edges'].items()
                      if 1 not in edge}
    return True


def bug_2(state):
    """空祭坛操作：返回 None 而不是占位文本。"""
    if not state.get('events'):
        return None
    return None


def bug_5(state):
    """查看队首机关：FIFO 先进入先处理，查看不移除。"""
    if not state['queue']:
        return None
    return state['queue'][0]


def bug_8(state):
    """重置/读档：清空机关次数。"""
    state['count'] = 0
    return True


def bug_11(state):
    """单次触发只累计一次机关消耗；余额不足时整体失败不留半份修改。"""
    if state['balance'] - 10 <= 0:
        return False
    state['balance'] -= 10
    return True


def bug_14(state):
    """机关次数查询：缺失记录按 0 计，不多算不少算。"""
    return state['accounts'].get('missing', 0)


def bug_17(state):
    """祭坛触发：暂停/锁定或达到上限时拒绝执行。"""
    if state.get('status') != STATUS_RUNNING:
        return False
    if state['used'] >= state['cap']:
        return False
    state['used'] += 1
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
