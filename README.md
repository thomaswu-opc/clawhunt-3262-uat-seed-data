# UAT 测试数据准备脚本 · #3262

对应工单 **S4-UAT-029**。范围：生成一整套可重复的 UAT 数据（9 类实体、484 条记录）、
输出各岗位测试账号清单、保证无真实个人信息。CRM 等业务表不在本单内，数据以 JSON 交付、字段与工单名词对齐。

## 1. 目录

```
uat_seed/spec.py        数量与枚举的唯一声明（TARGET_COUNTS / ROLES / LIFECYCLE）
uat_seed/generator.py   LCG 确定性生成器 + digest + 账号清单
uat_seed/pii.py         真实个人信息的三条判据（号段 / 保留域名 / 禁止字段）
run_seed.py             入口：生成 JSON + CSV + digest，PII 不合规退出码 2
tests/test_acceptance.py 11 个用例（数量、覆盖、种子确定性、PII 判据正反向）
samples/                一次真实运行的产物（供核对，勿手改）
```

## 2. 数量与要求对齐

| 实体 | 要求 | 实得 |
|---|---|---|
| 会所 sites | 2 | 2 |
| 员工账号 employees | 12（覆盖全部岗位） | 12，12 个岗位各 1 |
| 会员企业 member_companies | 80（含不同生命周期与健康分） | 80，5 种生命周期、健康分 30–99 |
| 联系人 contacts | 200 | 200 |
| 线索 leads | 60 | 60 |
| 招商商机 opportunities | 30 | 30 |
| 活动 events | 10 | 10 |
| 供需条目 supply_demands | 50 | 50 |
| 租约 leases | 40 | 40 |
| **合计** | — | **484** |

表中"实得"列不是人工抄的：`spec.py` 的 `TARGET_COUNTS` 同时被生成器和测试引用，
`test_ac1_counts_equal_ticket_requirement` 逐项比对，改一处而另一处不跟就会失败。

## 3. 为什么自己写 LCG 而不用 `random`

`random.Random(seed)` 的序列在 CPython 同版本内稳定，但并不承诺跨版本稳定；
一旦升级解释器，同种子会产出不同数据，"可重复生成"就只是口号。
这里的 `LCG` 只用整数乘加与取高位，在 Python 3.8+ 上恒定，`digest` 因此可以作为验收凭证：

```
seed=20261126 → digest=4ff94ab31ee1848ddf08fbef02e905bbe72eb685d4a3ced0785155d31b8a7150
```

两次运行 digest 相同；测试里除了比 digest，还逐行比对 9 类实体，避免"整体一致但个别字段漂移"。

## 4. 真实个人信息怎么保证没有（AC-3）

不靠"看起来像"，靠三条可执行规则 + 反向用例：

| 规则 | 实现 |
|---|---|
| 手机号只在虚构号段 | 只生成 `138-0000-xxxx`，扫描器拒绝其它 11 位手机形态 |
| 邮箱只用保留域 | 只生成 `@example.test`（RFC 2606），别的一律判违规 |
| 不出现身份证/护照/银行卡 | 字段名黑名单，`run_seed.py` 命中即退出码 2 |
| 不出现客户名 | 客户名黑名单（工单要求"交付物中不出现客户名称"） |

判据本身也有测试：`test_ac3_scanner_catches_real_looking_email` 等三个反向用例证明扫描器不是永远返回空。

## 5. 运行与测试

```bash
python run_seed.py                                  # 生成到 out/
python run_seed.py --seed 20261201 --out ./out2     # 换种子
python run_seed.py --only roster                    # 只打印岗位账号清单
python -m unittest discover -s tests -t . -v        # 11 passed，零第三方依赖
```

退出码：`0` 成功；`2` 检测到疑似真实个人信息（GUI/CI 里可直接当门禁用）。

## 6. 边界与取舍

- **日期跨月**：租约结束日按 `min(start.day, 28)` 收敛，避免 2-31 这类非法日期；同月生成也保持单调。
- **岗位与员工 1:1**：12 个岗位各 1 人，不做冗余，因为工单要的是"覆盖全部岗位"而不是组织冗余度。
- **供需条目 kind 交替**：`supply` / `demand` 各 25 条，保证匹配场景两侧都有数据。
- **不写库**：交付 JSON + CSV；接你们测试库时只替换 `run_seed.py` 的输出段，生成逻辑不动。

## 7. 不在本单范围

CRM/租约等业务表的写入与去重（S2-CRM）、UAT 用例与测试报告、性能压测数据、环境部署。

## 8. 验收对照

| # | 验收原文 | 用例 | 实测 |
|---|---|---|---|
| 1 | 脚本执行后各类数据数量与要求一致（输出统计） | `test_ac1_counts_equal_ticket_requirement` 等 4 个 | 9 类实体 484 条逐项等于 `TARGET_COUNTS`；脚本运行时打印 `n / want OK` 统计行；账号清单覆盖 12 岗位 |
| 2 | 固定随机种子下两次生成结果一致（测试通过） | `test_ac2_same_seed_same_digest` 等 3 个 | 同种子 digest 相同且 9 类实体逐行相等；换种子 digest 必变 |
| 3 | 生成的数据中没有真实个人信息 | `test_ac3_generated_data_has_no_pii` 等 4 个 | 全量 484 条扫描 0 违规；扫描器对真实邮箱/手机/身份证字段均有反向用例 |
