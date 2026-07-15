#!/bin/bash
# AI数字名片 数据库自动备份脚本
# 放在服务器 /usr/local/bin/backup-ai-card.sh
# 每天凌晨3点运行，保留最近30天

DB=/var/www/ai-digital-card/backend/data/digital_brochure.db
BACKUP_DIR=/var/www/ai-digital-card/backend/data/backups
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30

mkdir -p $BACKUP_DIR

# 用 sqlite3 .backup 安全备份（不会损坏正在写入的数据库）
sqlite3 $DB ".backup $BACKUP_DIR/digital_brochure_$DATE.db"

# 压缩
gzip -f $BACKUP_DIR/digital_brochure_$DATE.db

# 删旧备份
find $BACKUP_DIR -name "digital_brochure_*.db.gz" -mtime +$KEEP_DAYS -delete

echo "[$(date)] 备份完成: digital_brochure_$DATE.db.gz" >> $BACKUP_DIR/backup.log
