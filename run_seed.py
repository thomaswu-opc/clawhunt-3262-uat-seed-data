#!/usr/bin/env python3
"""UAT 测试数据准备脚本。

用法：
    python run_seed.py                          # 默认种子，生成到 out/
    python run_seed.py --seed 20261201 --out ./out
    python run_seed.py --seed 20261201 --only roster    # 只打印账号清单

输出：
    out/uat_dataset.json      全量数据（按实体分键）
    out/account_roster.csv    各岗位测试账号清单（AC-1 要求）
    out/digest.txt            数据摘要，用于证明同种子可复现（AC-2）
退出码：0 成功；2 检测到疑似真实个人信息（AC-3）。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from uat_seed import pii  # noqa: E402
from uat_seed.generator import account_roster, digest, generate  # noqa: E402
from uat_seed.spec import TARGET_COUNTS  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261126)
    ap.add_argument("--out", default="out")
    ap.add_argument("--only", choices=["roster"])
    a = ap.parse_args()

    data = generate(a.seed)
    roster = account_roster(data)
    problems = pii.scan(data)

    print("seed=%d  实体=%d  记录=%d"
          % (a.seed, len(TARGET_COUNTS), sum(len(v) for v in data.values())))
    for key, want in TARGET_COUNTS.items():
        got = len(data[key])
        print("  %-18s %3d / %3d %s" % (key, got, want, "OK" if got == want else "MISMATCH"))

    if a.only == "roster":
        print("\n岗位账号清单：")
        for row in roster:
            print("  %-16s %-28s %s" % (row["role"], row["account"], row["phone"]))
        return 0 if not problems else 2

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "uat_dataset.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    with (out / "account_roster.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["role", "account", "name", "site", "phone"])
        w.writeheader()
        w.writerows(roster)

    dg = digest(data)
    (out / "digest.txt").write_text(dg + "\n", encoding="utf-8")
    print("\n输出目录：%s" % out.resolve())
    print("  uat_dataset.json / account_roster.csv / digest.txt")
    print("digest = %s" % dg)
    print("同种子再跑一次应得到同一 digest（AC-2）")

    if problems:
        print("\n[FAIL] 检测到疑似真实个人信息（AC-3）：", file=sys.stderr)
        for p in problems[:10]:
            print("  - %s" % p, file=sys.stderr)
        return 2
    print("PII 检查：通过（0 条违规）")
    return 0


if __name__ == "__main__":
    sys.exit(main())