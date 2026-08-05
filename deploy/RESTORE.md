# AI数字名片 数据恢复指南

## 恢复流程

### 1. 查看可用的备份

```bash
# 服务器上
ls -lt /var/www/ai-digital-card/backend/data/backups/digital_brochure_*.db.gz

# 本地
dir D:\AI数智名片\backups\digital_brochure_*.db.gz
```

### 2. 选择要恢复的日期，执行恢复

```bash
# 服务器上执行
# 假设要恢复到 2026-07-14
RESTORE_DATE="20260714"
gunzip -k /var/www/ai-digital-card/backend/data/backups/digital_brochure_${RESTORE_DATE}_*.db.gz
cp /var/www/ai-digital-card/backend/data/backups/digital_brochure_${RESTORE_DATE}_*.db \
   /var/www/ai-digital-card/backend/data/digital_brochure.db
systemctl restart ai-digital-card
```

### 3. 验证恢复

```bash
curl https://card.liankebao.top/health
# 应该返回 200 OK

# 检查用户数是否匹配恢复时的数据
ssh root@47.116.116.87 "sqlite3 /var/www/ai-digital-card/backend/data/digital_brochure.db 'SELECT COUNT(*) FROM users;'"
```
