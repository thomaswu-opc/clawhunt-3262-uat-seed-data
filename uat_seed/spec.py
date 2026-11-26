"""UAT 测试数据规格：数量、枚举、约束。

数量与枚举全部抄自工单原文，集中在一处声明，测试与生成器都从这里读 ——
这样"数量与要求一致"的验收不是靠人眼比对，而是靠一个共享常量。
"""
from __future__ import annotations

# 工单原文的量化要求：键 -> 条数
TARGET_COUNTS = {
    "sites": 2,
    "employees": 12,
    "member_companies": 80,
    "contacts": 200,
    "leads": 60,
    "opportunities": 30,
    "events": 10,
    "supply_demands": 50,
    "leases": 40,
}

# 员工必须覆盖全部岗位（1 个/岗位起，剩 2 个冗余分配给接待与招商）
ROLES = (
    "admin",            # 系统管理员
    "knowledge",        # 知识管理员
    "reception",        # 前台接待
    "sales",            # 招商业务员
    "space_ops",        # 空间运营
    "crm",              # CRM 专员
    "finance",          # 财务
    "content",          # 内容运营
    "member_success",   # 会员成功
    "marketing",        # 市场
    "it",               # IT 运维
    "manager",          # 管理层
)

LIFECYCLE = ("prospect", "active", "at_risk", "churned", "renewal")

# 虚构用词：刻意只用单字姓 + 通用地名 + 编号公司，避免撞上真实主体
SURNAMES = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
CITIES = ("静安", "浦东", "徐汇", "黄浦", "长宁", "普陀")
INDUSTRIES = ("智能制造", "数字文创", "供应链服务", "生物医药",
              "新能源", "企业服务", "文旅会展", "跨境电商")

# 真实个人信息的三条红线（AC-3 的判据）
PHONE_RE = r"^138-?0000-?\d{4}$"   # 只用 1380000xxxx 这一段虚构号段
EMAIL_DOMAIN = "example.test"      # RFC 2606 保留域名，不可能属于真实主体
ID_CARD_FORBIDDEN = True           # 不生成任何身份证号字段
