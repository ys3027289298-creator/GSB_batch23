import json

# 统一状态模型：
#   closed  —— 暂停/锁定标记，锁定期间禁止入住类操作
#   events  —— 灵异记录（灵异值），按房客编号各记一条，重置/读档时清空
#   queue   —— 等候队列，先进先出
#   items   —— 已入住客房
#   next_id —— 编号游标，先取后增，读档后由 normalize_state 校正，不跳号
#   src/dst —— 资源账目，转账不足时整体回滚，不留半截状态

DEFAULTS = {
    'closed': False,
    'events': {},
    'queue': [],
    'items': [],
    'next_id': 1,
    'src': 5,
    'dst': 0,
}

ROOM_CAPACITY = 8
TRANSFER_AMOUNT = 10


def new_game():
    """创建/重置：返回干净初始状态，灵异记录清空，编号从 1 开始。"""
    return {key: (value.copy() if isinstance(value, (dict, list)) else value)
            for key, value in DEFAULTS.items()}


def normalize_state(state):
    """损坏状态恢复：补齐缺失字段，并把编号游标抬到已知编号之后。"""
    for key, default in DEFAULTS.items():
        if state.get(key) is None:
            state[key] = default.copy() if isinstance(default, (dict, list)) else default
    known = [gid for gid in list(state['events']) + list(state['queue']) + list(state['items'])
             if isinstance(gid, int)]
    if known and state['next_id'] <= max(known):
        state['next_id'] = max(known) + 1
    return state


def save_game(state):
    return json.dumps(state)


def load_game(raw):
    """读档：在干净状态上合并存档，清空灵异记录并校正编号游标。"""
    state = new_game()
    try:
        saved = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        saved = None
    if isinstance(saved, dict):
        for key in DEFAULTS:
            if key in saved:
                state[key] = saved[key]
    state['events'] = {}
    return normalize_state(state)


def bug_15(state):
    """入住前置检查：暂停/锁定状态拒绝执行。"""
    return not state.get('closed', False)


def bug_18(state):
    """处理当前房客并记录灵异值：同一房客重复处理时失败，且不重复累计。"""
    gid = state['next_id']
    if gid in state['events']:
        return False
    state['events'][gid] = (gid, 0)
    return True


def bug_21(state):
    """入住：锁定、空队列、客房满员均失败，成功时按先来后到从队列入住。"""
    if state.get('closed'):
        return False
    if not state['queue']:
        return False
    if len(state['items']) >= ROOM_CAPACITY:
        return False
    state['items'].append(state['queue'].pop(0))
    return True


def bug_24(state):
    """灵异值数量。"""
    return len(state['events'])


def bug_27(state):
    """退房：空客房时失败，不返回占位结果。"""
    if not state['items']:
        return False
    state['items'].pop(0)
    return True


def bug_0(state):
    """开业：一次性操作，重复调用失败。"""
    if state.get('opened'):
        return False
    state['opened'] = True
    return True


def bug_3(state):
    """推进：先进入的房客先处理；空队列返回空值。"""
    if not state['queue']:
        return None
    return state['queue'].pop(0)


def bug_6(state):
    """查看房客：只读不删除；空客房返回空值。"""
    if not state['items']:
        return None
    return state['items'][0]


def bug_9(state):
    """分配编号：先取后增，读档/重置后不跳号。"""
    gid = state['next_id']
    state['next_id'] = gid + 1
    return gid


def bug_12(state):
    """转账：余额不足时整体回滚，状态保持不变。"""
    if state['src'] < TRANSFER_AMOUNT:
        return False
    state['src'] -= TRANSFER_AMOUNT
    state['dst'] += TRANSFER_AMOUNT
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
