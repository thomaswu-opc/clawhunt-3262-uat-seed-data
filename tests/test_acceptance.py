"""三条验收标准的机械验证。"""
from __future__ import annotations

import json
import unittest

from uat_seed import pii
from uat_seed.generator import account_roster, digest, generate
from uat_seed.spec import ROLES, TARGET_COUNTS

SEED = 20261126


class AC1CountsMatchRequirement(unittest.TestCase):
    def test_ac1_counts_equal_ticket_requirement(self):
        data = generate(SEED)
        for key, want in TARGET_COUNTS.items():
            self.assertEqual(len(data[key]), want, "%s 数量不符（期望 %d，实得 %d）"
                             % (key, want, len(data[key])))
        self.assertEqual(sum(len(v) for v in data.values()), sum(TARGET_COUNTS.values()))

    def test_ac1_roster_covers_every_role(self):
        roster = account_roster(generate(SEED))
        roles = {r["role"] for r in roster}
        self.assertEqual(roles, set(ROLES), "账号清单必须覆盖全部 12 个岗位")
        self.assertEqual(len(roster), TARGET_COUNTS["employees"])
        for row in roster:
            self.assertTrue(row["account"].endswith("@example.test"))
            self.assertRegex(row["phone"], r"^138-0000-\d{4}$")

    def test_ac1_leases_are_date_consistent(self):
        for lease in generate(SEED)["leases"]:
            self.assertLess(lease["start"], lease["end"], lease["id"])
            self.assertGreaterEqual(lease["seats"], 1)

    def test_ac1_companies_cover_every_lifecycle(self):
        got = {c["lifecycle"] for c in generate(SEED)["member_companies"]}
        self.assertIn("active", got)
        self.assertIn("churned", got)
        self.assertGreaterEqual(len(got), 3)


class AC2SeedDeterminism(unittest.TestCase):
    def test_ac2_same_seed_same_digest(self):
        a, b = generate(SEED), generate(SEED)
        self.assertEqual(digest(a), digest(b), "同一种子两次生成必须完全一致")
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_ac2_different_seed_differs(self):
        self.assertNotEqual(digest(generate(SEED)), digest(generate(SEED + 1)))

    def test_ac2_row_level_identity_not_just_hash(self):
        """哈希相同还不够，逐行比对，避免"整体一致但个别字段漂移"。"""
        a, b = generate(SEED), generate(SEED)
        for key in a:
            self.assertEqual(a[key], b[key], "%s 行级不一致" % key)


class AC3NoRealPII(unittest.TestCase):
    def test_ac3_generated_data_has_no_pii(self):
        self.assertEqual(pii.scan(generate(SEED)), [])

    def test_ac3_scanner_catches_real_looking_email(self):
        """反向验证判据本身有效 —— 否则"通过"没有意义。"""
        bad = {"contacts": [{"email": "zhang.san@company.com"}]}
        self.assertTrue(pii.scan(bad))

    def test_ac3_scanner_catches_real_looking_phone(self):
        bad = {"contacts": [{"phone": "13912345678"}]}
        self.assertTrue(pii.scan(bad))

    def test_ac3_scanner_rejects_id_card_field(self):
        bad = {"contacts": [{"id_card": "310101199001011234"}]}
        self.assertIn("forbidden field", " ".join(pii.scan(bad)))


if __name__ == "__main__":
    unittest.main(verbosity=2)