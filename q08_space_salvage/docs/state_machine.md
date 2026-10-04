# 太空打捞 — 状态机视图（q08_space_salvage）

## 1. 状态（单一事实来源：一个 dict，JSON 键名固定不变）

| 键 | 类型 | 含义 |
|---|---|---|
| `nodes` | `{id: True}` | 残骸注册表：在场的残骸（图节点） |
| `edges` | `{(a, b): weight}` | 残骸之间的拖曳连线 |
| `queue` | `[id, ...]` | 待处理残骸队列，FIFO（队首 = 最先进入） |
| `count` | int | 本轮累计打捞次数（载重计数），重开/读档清零 |
| `balance` | int | 账户余额，单次打捞费用固定 20 |
| `accounts` | `{key: int}` | 载重分类账本，缺省值为 `0` |
| `events` | `{id: True}` | 已登记（已处理）残骸事件账本 |
| `used` / `cap` | int / int | 货舱已用载重 / 载重上限，恒有 `0 <= used <= cap` |
| `status` | `"active"/"paused"/"locked"` | 运行状态；旧档缺省时按 `active` 处理 |

## 2. 状态机

```
                pause()                      resume()
   ┌──────┐ ─────────────────> ┌────────┐ ─────────────────> ┌──────┐
   │active│                    │paused  │                    │active│
   └──────┘ <───────────────── └────────┘                    └──────┘
      │  lock() (货舱满或硬锁定)                                     
      v                                                             
   ┌──────┐                                                           
   │locked│  只有 reset()/new_game() 能离开（回到 active 初始态）       
   └──────┘                                                           
```

允许的转移：`active→paused`、`paused→active`、`active/paused→locked`、`任意→初始态(reset/new_game)`。
非法转移（如对已 paused 再 pause）返回 `False` 且不修改状态。

## 3. 守卫不变量（所有操作在 pause/resume/序列化/读档/重开前后都必须成立）

1. `nodes` 中的每个 id 不重复出现在 `queue`；`queue` 中每个 id 都在 `nodes`。
2. 已处理（在 `events` 中登记）的残骸不能再次打捞成功——重复处理返回 `False`，状态不变。
3. 仅 `active` 状态可执行打捞/入队/出队/查看删除等变更操作；`paused`/`locked` 一律拒绝且零修改。
4. 货舱剩余容量 = `cap - used`（不是 `cap-used-1`）；放不下时拒绝，余额、载重、队列都不变（原子失败）。
5. 余额不足支付打捞费时拒绝，不扣款（先校验后变更）。
6. 一次打捞对 `count` / `accounts` / `used` 只累计一次（无幂等键的变更不得重复生效）。
7. 空货舱/空队列的查询返回 `None`，不返回占位文本，也不修改被查询对象。
8. 查看残骸是只读操作：不得删除节点；显式移除残骸时级联删除与它相连的所有 `edges`，不留悬空边。
9. `reset()` / 读档必须清空 `count`（以及本轮临时载重累计），不把旧局的载重带入新局。
10. 读档后 `events` 的编号重排为从 0 开始的连续整数，不跳号；缺省 `status` 视为 `active`。

## 4. 失败原子性

每个变更操作先跑完全部前置校验（状态、容量、余额、重复登记、存在性），
全部通过后才一次性写入；任一校验失败立即返回 `False`/`None`，状态与调用前逐字节一致。

## 5. 持久化

`to_json(state)` → `json.dumps(..., sort_keys=True)`；`from_json(text)` 反序列化，
`edges` 的字符串键还原为整数元组键，`queue` 出队顺序保持，`events` 编号压缩，
`count` 归零（读档即新一轮）。JSON 键名与命令接口保持不变。
