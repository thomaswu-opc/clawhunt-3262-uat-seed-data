"""AC-3 的判据：什么算"真实个人信息"。

不靠"看起来像"判断，靠三条可执行规则：
1. 手机号只能落在虚构号段 138-0000-xxxx；
2. 邮箱域名只能是 RFC 2606 保留域 example.test；
3. 不得出现任何身份证/护照/银行卡字段名 —— 这类数据没有任何 UAT 场景需要。
第 4 条兜底：不得出现工单里提到的真实客户名。
"""
from __future__ import annotations

import re

from uat_seed.spec import EMAIL_DOMAIN, PHONE_RE


class PIIViolation(ValueError):
    pass


FORBIDDEN_KEYS = ("id_card", "idcard", "passport", "bank_card", "ssn", "身份证", "护照")
CUSTOMER_NAMES = ("会员空间平台", "clawhunt")


def scan(data: dict) -> list[str]:
    """返回违规清单，空列表代表通过。"""
    problems: list[str] = []
    phone = re.compile(PHONE_RE)

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if any(bad in k.lower() for bad in FORBIDDEN_KEYS):
                    problems.append("%s.%s: forbidden field" % (path, k))
                walk(v, "%s.%s" % (path, k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, "%s[%d]" % (path, i))
        elif isinstance(node, str):
            low = node.lower()
            if "@" in node and not low.endswith("@" + EMAIL_DOMAIN):
                problems.append("%s: email domain not reserved (%s)" % (path, node))
            if re.fullmatch(r"1\d{2}-?\d{4}-?\d{4}", node.replace(" ", "")) and not phone.match(node):
                problems.append("%s: phone outside fictional range (%s)" % (path, node))
            for name in CUSTOMER_NAMES:
                if name in node:
                    problems.append("%s: mentions the customer name" % path)

    walk(data, "$")
    return problems


def assert_clean(data: dict) -> None:
    bad = scan(data)
    if bad:
        raise PIIViolation("; ".join(bad[:5]))
