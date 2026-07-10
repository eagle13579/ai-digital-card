#!/bin/bash
# Run health monitor (allows failure)
/var/www/ai-digital-card/backend/venv/bin/python3 /var/www/ai-digital-card/backend/health_monitor.py --once
HEALTH_EXIT=$?
# Run alerter regardless
/var/www/ai-digital-card/backend/venv/bin/python3 /var/www/ai-digital-card/backend/feishu_alerter.py
# Return the health check exit code so systemd knows if it failed
exit $HEALTH_EXIT
