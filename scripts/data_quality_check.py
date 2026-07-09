"""芯森态·数据质量检查脚本
检查: 邮箱格式/评分范围/分级有效性/日期合理性/外键完整性
用法: python code/scripts/data_quality_check.py
输出: logs/data_quality_report.json
退出: 违规数
"""
import json, os, sqlite3, sys

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api", "data", "xinsentai.db")
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), os.pardir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
REPORT = os.path.join(LOG_DIR, "data_quality_report.json")
issues = []

def check(desc, sql, cond, msg_fmt):
    c = sqlite3.connect(DB)
    cur = c.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    c.close()
    for row in rows:
        if not cond(row):
            issues.append({"检查项": desc, "问题": msg_fmt(row)})

c = sqlite3.connect(DB)

# 1. auth_accounts 邮箱格式
check("邮箱格式", "SELECT id, email FROM auth_accounts WHERE email IS NOT NULL AND email != ''",
      lambda r: "@" in str(r[1]), lambda r: f"账号ID{r[0]} email异常: {r[1]}")

# 2. scores 评分范围(0-100)
for dim in ['score_活跃度','score_购买力','score_内容共鸣','score_影响力','score_城市匹配','score_信任度']:
    check(f"评分范围({dim})", f"SELECT id, user_id, {dim} FROM scores",
          lambda r, d=dim: r[2] is not None and 0 <= r[2] <= 100,
          lambda r, d=dim: f"评分{r[0]} {d}={r[2]} 超出[0,100]")

# 3. dealer_grades 分级有效性
check("分级有效性", "SELECT id, user_id, grade FROM dealer_grades WHERE grade IS NOT NULL",
      lambda r: str(r[2]).upper() in ('A','B','C','D'),
      lambda r: f"分级{r[0]} 等级={r[2]} 不在A/B/C/D")

# 4. contracts 日期合理性
check("合同日期", "SELECT id, contract_no, signed_at, expired_at FROM contracts WHERE signed_at IS NOT NULL AND expired_at IS NOT NULL",
      lambda r: str(r[2]) < str(r[3]),
      lambda r: f"合同{r[1]} 签署{r[2]} >= 到期{r[3]}")

# 5. 孤立数据 - scores引用不存在的user
check("孤立评分", "SELECT s.id, s.user_id FROM scores s LEFT JOIN users u ON s.user_id=u.user_id WHERE u.user_id IS NULL",
      lambda r: False, lambda r: f"评分{r[0]} 引用了不存在用户: {r[1]}")

# 6. 孤立数据 - dealer_grades引用不存在的user
check("孤立分级", "SELECT d.id, d.user_id FROM dealer_grades d LEFT JOIN users u ON d.user_id=u.user_id WHERE u.user_id IS NULL",
      lambda r: False, lambda r: f"分级{r[0]} 引用了不存在用户: {r[1]}")

c.close()

report = {"检查时间": __import__('datetime').datetime.now().isoformat(),
          "总违规数": len(issues), "数据库": DB, "违规详情": issues}
with open(REPORT, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"数据质量检查完成：{len(issues)} 项违规")
for i in issues:
    print(f"  [{i['检查项']}] {i['问题']}")
sys.exit(len(issues))
