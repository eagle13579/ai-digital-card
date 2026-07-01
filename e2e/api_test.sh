#!/usr/bin/env bash
# E2E 测试骨架: curl 脚本 — health, login, 创建画册, 获取画册
# 用法: bash e2e/api_test.sh [BASE_URL]
set -euo pipefail
BASE_URL="${1:-http://localhost:8201}"
PASS=0; FAIL=0
green() { echo -e "\033[32m✓ $1\033[0m"; }
red()   { echo -e "\033[31m✗ $1\033[0m"; }
check() { [ "$1" -eq 0 ] && green "$2" && PASS=$((PASS+1)) || red "$2" && FAIL=$((FAIL+1)); }
echo "========================================"
echo " E2E API 测试骨架 — ${BASE_URL}"
echo "========================================"

echo "--- Health ---"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
[ "$HEALTH" = "200" ] && check 0 "/health → 200" || check 1 "/health → $HEALTH"
API_HEALTH=$(curl -s "${BASE_URL}/api/health")
API_STATUS=$(echo "$API_HEALTH" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
[ "$API_STATUS" = "ok" ] && check 0 "/api/health status=ok" || check 1 "/api/health status=${API_STATUS:-N/A}"

echo "--- Auth ---"
REG_RESP=$(curl -s -X POST "${BASE_URL}/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"phone":"13888880001","password":"e2etest123","name":"E2E用户","username":"e2euser"}')
REG_STATUS=$(echo "$REG_RESP" | grep -o '"access_token":"[^"]*"')
[ -n "$REG_STATUS" ] && check 0 "注册成功 → access_token 存在" || check 1 "注册失败"
DUP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"phone":"13888880001","password":"e2etest123","name":"E2E用户"}')
[ "$DUP_STATUS" = "400" ] && check 0 "重复注册 → 400" || check 1 "重复注册 → ${DUP_STATUS}"
TOKEN=$(echo "$REG_RESP" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
LOGIN_RESP=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"phone":"13888880001","password":"e2etest123"}')
LOGIN_TOKEN=$(echo "$LOGIN_RESP" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
[ -n "$LOGIN_TOKEN" ] && check 0 "登录成功 → access_token" || check 1 "登录失败"
LOGIN_FAIL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" -d '{"phone":"13888880001","password":"wrong"}')
[ "$LOGIN_FAIL_STATUS" = "401" ] && check 0 "错误密码 → 401" || check 1 "错误密码 → ${LOGIN_FAIL_STATUS}"

echo "--- Brochure ---"
BROCHURE_RESP=$(curl -s -X POST "${BASE_URL}/api/brochures" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{"title":"E2E测试画册","purpose":"partner","pages":[{"sort_order":0,"content_type":"cover","content":"封面"},{"sort_order":1,"content_type":"text","content":"介绍"}]}')
BROCHURE_ID=$(echo "$BROCHURE_RESP" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
[ -n "$BROCHURE_ID" ] && [ "$BROCHURE_ID" -gt 0 ] 2>/dev/null && check 0 "创建画册 → id=$BROCHURE_ID" || check 1 "创建画册失败"
LIST_COUNT=$(curl -s "${BASE_URL}/api/brochures" -H "Authorization: Bearer ${TOKEN}" | grep -o '"id"' | wc -l)
[ "$LIST_COUNT" -ge 1 ] && check 0 "画册列表 ≥1 条" || check 1 "画册列表为空"
DETAIL_TITLE=$(curl -s "${BASE_URL}/api/brochures/${BROCHURE_ID}" | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
[ "$DETAIL_TITLE" = "E2E测试画册" ] && check 0 "画册详情 title正确" || check 1 "画册详情 title=${DETAIL_TITLE:-N/A}"
NOT_FOUND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/brochures/99999")
[ "$NOT_FOUND_STATUS" = "404" ] && check 0 "不存在画册 → 404" || check 1 "不存在画册 → ${NOT_FOUND_STATUS}"
TEMPLATE_VALID=$(curl -s "${BASE_URL}/api/brochures/template/client" | grep -o '"purpose":"client"')
[ -n "$TEMPLATE_VALID" ] && check 0 "模板 client 成功" || check 1 "模板获取失败"

echo "========================================"
echo " 结果: ${PASS} 通过, ${FAIL} 失败"
echo "========================================"
exit "$FAIL"
