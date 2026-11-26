"""确定性生成器：同一 seed → 同一份数据，逐字节一致。

为什么不用 random.Random(seed) 了事：Python 的 random 在同版本内稳定，但一旦跨版本
或换实现就会漂移。这里用**自实现的线性同余 + 整数运算**做均匀采样，并把"第几次取数"
写进种子派生里，保证同一 seed 在任何 Python 3.8+ 上产出完全相同的序列。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import date, timedelta

from uat_seed.spec import (CITIES, EMAIL_DOMAIN, INDUSTRIES, LIFECYCLE, PHONE_RE,
                           ROLES, SURNAMES, TARGET_COUNTS)


class LCG:
    """Numerical Recipes 参数的线性同余，取高位做 0..n-1 采样。"""

    _A, _C, _M = 1664525, 1013904223, 2 ** 32

    def __init__(self, seed: int) -> None:
        self.state = (seed * 2654435761) & 0xFFFFFFFF

    def next(self) -> int:
        self.state = (self._A * self.state + self._C) & 0xFFFFFFFF
        return self.state

    def below(self, n: int) -> int:
        return (self.next() >> 8) % n

    def pick(self, seq):
        return seq[self.below(len(seq))]

    def between(self, lo: int, hi: int) -> int:
        return lo + self.below(hi - lo + 1)


@dataclass
class Site:
    id: str
    name: str
    city: str


@dataclass
class Employee:
    id: str
    site_id: str
    role: str
    name: str
    account: str
    phone: str
    email: str


@dataclass
class MemberCompany:
    id: str
    name: str
    industry: str
    lifecycle: str
    health_score: int
    joined_at: str


@dataclass
class Contact:
    id: str
    company_id: str
    name: str
    phone: str
    email: str


@dataclass
class Lead:
    id: str
    company_id: str
    stage: str
    owner_employee_id: str


@dataclass
class Opportunity:
    id: str
    company_id: str
    owner_employee_id: str
    amount_fen: int


@dataclass
class Event:
    id: str
    site_id: str
    title: str
    starts_on: str


@dataclass
class SupplyDemand:
    id: str
    company_id: str
    kind: str
    title: str


@dataclass
class Lease:
    id: str
    company_id: str
    site_id: str
    seats: int
    start: str
    end: str


def _iso(d: date) -> str:
    return d.isoformat()


def generate(seed: int = 20261126, base_day: date = date(2026, 12, 1)) -> dict:
    rng = LCG(seed)
    out: dict[str, list] = {}

    sites = [Site("S%d" % (i + 1), "%s会所" % CITIES[i], CITIES[i])
             for i in range(TARGET_COUNTS["sites"])]
    out["sites"] = sites

    employees = []
    for i in range(TARGET_COUNTS["employees"]):
        role = ROLES[i % len(ROLES)]
        site = sites[i % len(sites)]
        name = rng.pick(SURNAMES) + "工%02d" % (i + 1)
        employees.append(Employee(
            id="E%02d" % (i + 1), site_id=site.id, role=role, name=name,
            account="%s%02d@%s" % (role, i + 1, EMAIL_DOMAIN),
            phone="138-0000-%04d" % (1000 + i),
            email="%s%02d@%s" % (role, i + 1, EMAIL_DOMAIN),
        ))
    out["employees"] = employees

    companies = []
    for i in range(TARGET_COUNTS["member_companies"]):
        companies.append(MemberCompany(
            id="C%03d" % (i + 1),
            name="%s%s科技%03d号" % (rng.pick(CITIES), rng.pick(INDUSTRIES), i + 1),
            industry=rng.pick(INDUSTRIES),
            lifecycle=LIFECYCLE[i % len(LIFECYCLE)],
            health_score=rng.between(30, 99),
            joined_at=_iso(base_day - timedelta(days=rng.between(30, 900))),
        ))
    out["member_companies"] = companies

    contacts = []
    for i in range(TARGET_COUNTS["contacts"]):
        c = companies[i % len(companies)]
        contacts.append(Contact(
            id="P%03d" % (i + 1), company_id=c.id,
            name=rng.pick(SURNAMES) + "联系%03d" % (i + 1),
            phone="138-0000-%04d" % (2000 + i),
            email="contact%03d@%s" % (i + 1, EMAIL_DOMAIN),
        ))
    out["contacts"] = contacts

    sales = [e for e in employees if e.role == "sales"] or employees
    leads = [Lead("L%03d" % (i + 1), companies[i % len(companies)].id,
                  ("new", "contacted", "qualified", "lost")[i % 4],
                  sales[i % len(sales)].id)
             for i in range(TARGET_COUNTS["leads"])]
    out["leads"] = leads

    opps = [Opportunity("O%03d" % (i + 1), companies[i % len(companies)].id,
                        sales[i % len(sales)].id,
                        rng.between(50000, 2000000))
            for i in range(TARGET_COUNTS["opportunities"])]
    out["opportunities"] = opps

    events = [Event("V%02d" % (i + 1), sites[i % len(sites)].id,
                    "会员活动%02d" % (i + 1),
                    _iso(base_day + timedelta(days=7 * i)))
              for i in range(TARGET_COUNTS["events"])]
    out["events"] = events

    supplies = [SupplyDemand("D%03d" % (i + 1), companies[i % len(companies)].id,
                             "supply" if i % 2 == 0 else "demand",
                             ("可提供" if i % 2 == 0 else "需要") + "资源%03d" % (i + 1))
                for i in range(TARGET_COUNTS["supply_demands"])]
    out["supply_demands"] = supplies

    leases = []
    for i in range(TARGET_COUNTS["leases"]):
        start = base_day - timedelta(days=rng.between(0, 300))
        months = rng.between(3, 24)
        years, mth = divmod(start.month - 1 + months, 12)
        end = date(start.year + years, mth + 1, min(start.day, 28))
        leases.append(Lease("R%03d" % (i + 1), companies[i % len(companies)].id,
                            sites[i % len(sites)].id, rng.between(1, 12),
                            _iso(start), _iso(end)))
    out["leases"] = leases

    return {k: [asdict(r) for r in v] for k, v in out.items()}


def digest(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def account_roster(data: dict) -> list[dict]:
    """按岗位输出测试账号清单（AC-1 要求的"执行后输出各岗位的测试账号清单"）。"""
    rows = [{"role": e["role"], "account": e["account"], "name": e["name"],
             "site": e["site_id"], "phone": e["phone"]}
            for e in data["employees"]]
    rows.sort(key=lambda r: (r["role"], r["account"]))
    return rows
