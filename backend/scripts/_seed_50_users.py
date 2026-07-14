"""精简种子数据：只创建用户+标签+连接关系+匹配记录"""
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = r'D:\AI数智名片\backend\data\digital_brochure.db'

NAMES = [
    '陈明远','李文博','张思睿','刘嘉琳','王宇航',
    '赵婉清','孙志鹏','周雅雯','吴昊天','郑芷若',
    '林俊杰','郭思琪','黄浩然','唐语嫣','曹睿阳',
    '沈嘉琦','宋浩宇','苏雨桐','蒋子轩','蔡欣然',
    '贾博文','戴思颖','魏昊天','程雨欣','许智远',
    '何晓蔓','罗子轩','谢语桐','韩子涵','唐浩铭',
    '曹梓萱','邓思远','彭雨婷','潘俊哲','叶嘉琳',
    '邹浩然','苏婉怡','卢子豪','蒋思涵','崔昊天',
    '谭雨桐','汪思远','范语嫣','蔡俊杰','石嘉欣',
    '薛昊天','侯思琪','雷子轩','白雨桐','龙昊天',
]
COMPANIES = ['星辰科技','瀚海数据','云帆软件','金智咨询','蓝鲸资本','明道教育','锐思医疗','鼎新制造','拓荒投资','慧眼传媒']
TITLES = ['CEO','CTO','产品总监','技术总监','市场总监','销售总监','运营总监','全栈工程师','数据分析师','投资人']
PROVIDE_TAGS = [('AI技术',0.9),('软件开发',0.8),('数据分析',0.7),('产品设计',0.7),('市场渠道',0.8),('品牌营销',0.6),('技术研发',0.8),('股权投资',0.9),('企业咨询',0.7),('教育培训',0.7)]
NEED_TAGS = [('企业客户',0.9),('技术合作',0.8),('创业项目',0.8),('投资机会',0.8),('人才招聘',0.7),('品牌推广',0.6),('AI技术',0.7),('软件开发',0.6),('融资需求',0.7),('战略合作',0.7)]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("清空旧测试数据...")
c.execute("DELETE FROM user_tags WHERE user_id > 50")
c.execute("DELETE FROM match_records WHERE user_a_id > 50 OR user_b_id > 50")
c.execute("DELETE FROM connections WHERE user_id > 50 OR contact_id > 50")
c.execute("DELETE FROM brochures WHERE user_id > 50")
c.execute("DELETE FROM users WHERE id > 50")

print("创建50个用户...")
user_ids = []
now = datetime.utcnow()
for i in range(50):
    phone = f'138{random.randint(10000000,99999999)}'
    c.execute("""
        INSERT INTO users (phone,password_hash,name,company,title,intro,avatar,role,membership_tier,unlock_quota,created_at,updated_at)
        VALUES (?,'mock',?,?,?,'测试用户',?,'user',?,5,?,?)
    """, (phone, NAMES[i], random.choice(COMPANIES), random.choice(TITLES),
          '', random.choice(['free','pro','vip']), now, now))
    user_ids.append(c.lastrowid)
conn.commit()
print(f"  IDs: {user_ids[0]}~{user_ids[-1]}")

print("创建标签...")
for uid in user_ids:
    for tag, w in random.sample(PROVIDE_TAGS, 4):
        c.execute("INSERT INTO user_tags (user_id,tag_type,tag,weight,source) VALUES (?,'provide',?,?,'manual')", (uid, tag, w))
    for tag, w in random.sample(NEED_TAGS, 4):
        c.execute("INSERT INTO user_tags (user_id,tag_type,tag,weight,source) VALUES (?,'need',?,?,'manual')", (uid, tag, w))
conn.commit()

print("创建连接关系(25对x2)...")
for i in range(0, 48, 2):
    a, b = user_ids[i], user_ids[i+1]
    s = round(random.uniform(0.2,1.0), 2)
    src = random.choice(['auto_match','tag_match','smart_recommend'])
    lbl = random.choice(['合作方','商务伙伴','供应商','投资人'])
    c.execute("INSERT INTO connections (user_id,contact_id,source,status,strength,label,created_at,updated_at) VALUES (?,?,?,'accepted',?,?,?,?)", (a,b,src,s,lbl,now,now))
    c.execute("INSERT INTO connections (user_id,contact_id,source,status,strength,label,created_at,updated_at) VALUES (?,?,?,'accepted',?,?,?,?)", (b,a,src,s,lbl,now,now))
conn.commit()

print("创建匹配记录(~100条)...")
cnt = 0
for i in range(len(user_ids)):
    for j in range(i+1, len(user_ids)):
        if random.random() < 0.08:
            a, b = user_ids[i], user_ids[j]
            score = round(random.uniform(0.3,1.0), 4)
            st = random.choices(['pending','matched','positive','weak_positive'],[0.3,0.2,0.3,0.2])[0]
            src = random.choice(['auto_match','tag_match','smart_recommend'])
            c.execute("INSERT INTO match_records (user_a_id,user_b_id,match_score,status,source,common_tags,created_at) VALUES (?,?,?,?,?,?,?)", (a,b,score,st,src,'[]',now))
            cnt += 1
conn.commit()
print(f"  {cnt} 条")

conn.close()
print(f"\n✅ 完成! 用户:{len(user_ids)} 连接:50 匹配:{cnt}")
