#!/bin/bash
# 承诺承诺主表初始化脚本
# 用途：创建飞书多维表格 + 字段定义 + 选项配置
# 使用：bash scripts/init-promise-bitables.sh

set -e

echo "=== 初始化承诺承诺主表 ==="

# 1. 创建多维表格
echo "1. 创建多维表格..."
RESULT=$(lark-cli api POST '/open-apis/bitable/v1/apps' --data '{"name": "承诺承诺主表"}')
APP_TOKEN=$(echo "$RESULT" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['app']['app_token'])")
TABLE_ID=$(echo "$RESULT" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['app']['default_table_id'])")
echo "  APP_TOKEN: $APP_TOKEN"
echo "  TABLE_ID: $TABLE_ID"

# 2. 重命名默认表
echo "2. 重命名表..."
lark-cli api PATCH "/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID" \
  --data '{"name":"承诺承诺主表"}' > /dev/null
echo "  ✅ 表已重命名"

# 3. 创建字段
echo "3. 创建字段..."

# promise_id (text)
lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"promise_id","type":"text"}' > /dev/null
echo "  ✅ promise_id"

# title (text)
lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"title","type":"text"}' > /dev/null
echo "  ✅ title"

# description (text)
lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"description","type":"text"}' > /dev/null
echo "  ✅ description"

# source (text)
lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"source","type":"text"}' > /dev/null
echo "  ✅ source"

# status (single_select)
STATUS_RESULT=$(lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"status","type":"single_select"}')
STATUS_FIELD_ID=$(echo "$STATUS_RESULT" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['field']['id'])")
echo "  ✅ status ($STATUS_FIELD_ID)"

# priority (single_select)
PRIORITY_RESULT=$(lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"priority","type":"single_select"}')
PRIORITY_FIELD_ID=$(echo "$PRIORITY_RESULT" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['field']['id'])")
echo "  ✅ priority ($PRIORITY_FIELD_ID)"

# created_at (datetime)
lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"created_at","type":"datetime"}' > /dev/null
echo "  ✅ created_at"

# due_date (datetime)
lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"due_date","type":"datetime"}' > /dev/null
echo "  ✅ due_date"

# completed_at (datetime)
lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"completed_at","type":"datetime"}' > /dev/null
echo "  ✅ completed_at"

# flowmind_candidate_id (text)
lark-cli base +field-create --base-token "$APP_TOKEN" --table-id "$TABLE_ID" \
  --json '{"name":"flowmind_candidate_id","type":"text"}' > /dev/null
echo "  ✅ flowmind_candidate_id"

# 4. 为单选字段添加选项
echo "4. 添加选项..."

# status 选项
lark-cli api PUT "/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/fields/$STATUS_FIELD_ID" \
  --data '{"field_name":"status","type":3,"property":{"options":[{"name":"待处理"},{"name":"进行中"},{"name":"已完成"},{"name":"已过期"},{"name":"已拒绝"}]}}' > /dev/null
echo "  ✅ status 选项: 待处理/进行中/已完成/已过期/已拒绝"

# priority 选项
lark-cli api PUT "/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/fields/$PRIORITY_FIELD_ID" \
  --data '{"field_name":"priority","type":3,"property":{"options":[{"name":"P0"},{"name":"P1"},{"name":"P2"},{"name":"P3"}]}}' > /dev/null
echo "  ✅ priority 选项: P0/P1/P2/P3"

# 5. 输出配置信息
echo ""
echo "=== 初始化完成 ==="
echo "APP_TOKEN: $APP_TOKEN"
echo "TABLE_ID: $TABLE_ID"
echo "URL: https://bcn7uazoofu0.feishu.cn/base/$APP_TOKEN"
echo ""
echo "请更新 daily-promise-review.py 中的配置："
echo "  BITABLE_APP_TOKEN = \"$APP_TOKEN\""
echo "  BITABLE_TABLE_ID = \"$TABLE_ID\""
echo ""
echo "下一步：在 Web UI 中创建甘特图视图"
