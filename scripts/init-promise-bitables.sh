#!/bin/bash
# 初始化 Promise 主表 + Trace 子表
# 使用：bash scripts/init-promise-bitables.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$REPO_ROOT/shared-context"
CONFIG_PATH="$CONFIG_DIR/promise-bitable-config.json"

echo "=== 初始化 Promise Bitable ==="

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "缺少命令: $1" >&2
    exit 1
  }
}

json_field_id() {
  python3 -c "import sys, json; print(json.load(sys.stdin)['data']['field']['id'])"
}

json_table_id() {
  python3 -c "import sys, json; print(json.load(sys.stdin)['data']['table_id'])"
}

json_app_token() {
  python3 -c "import sys, json; print(json.load(sys.stdin)['data']['app']['app_token'])"
}

json_default_table_id() {
  python3 -c "import sys, json; print(json.load(sys.stdin)['data']['app']['default_table_id'])"
}

create_text_field() {
  local app_token="$1"
  local table_id="$2"
  local name="$3"
  lark-cli base +field-create --base-token "$app_token" --table-id "$table_id" \
    --json "{\"name\":\"$name\",\"type\":\"text\"}" >/dev/null
  echo "  ✅ $name"
}

create_number_field() {
  local app_token="$1"
  local table_id="$2"
  local name="$3"
  lark-cli base +field-create --base-token "$app_token" --table-id "$table_id" \
    --json "{\"name\":\"$name\",\"type\":\"number\"}" >/dev/null
  echo "  ✅ $name"
}

create_datetime_field() {
  local app_token="$1"
  local table_id="$2"
  local name="$3"
  lark-cli base +field-create --base-token "$app_token" --table-id "$table_id" \
    --json "{\"name\":\"$name\",\"type\":\"datetime\"}" >/dev/null
  echo "  ✅ $name"
}

create_single_select_field() {
  local app_token="$1"
  local table_id="$2"
  local name="$3"
  local options_json="$4"
  local result field_id
  result=$(lark-cli base +field-create --base-token "$app_token" --table-id "$table_id" \
    --json "{\"name\":\"$name\",\"type\":\"single_select\"}")
  field_id=$(printf '%s' "$result" | json_field_id)
  lark-cli api PUT "/open-apis/bitable/v1/apps/$app_token/tables/$table_id/fields/$field_id" \
    --data "{\"field_name\":\"$name\",\"type\":3,\"property\":{\"options\":$options_json}}" >/dev/null
  echo "  ✅ $name"
}

require_cmd lark-cli
require_cmd python3

echo "1. 创建多维表格应用..."
APP_RESULT=$(lark-cli api POST '/open-apis/bitable/v1/apps' --data '{"name":"Promise Review Hub"}')
APP_TOKEN=$(printf '%s' "$APP_RESULT" | json_app_token)
MAIN_TABLE_ID=$(printf '%s' "$APP_RESULT" | json_default_table_id)
echo "  APP_TOKEN: $APP_TOKEN"
echo "  MAIN_TABLE_ID: $MAIN_TABLE_ID"

echo "2. 重命名默认主表..."
lark-cli api PATCH "/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$MAIN_TABLE_ID" \
  --data '{"name":"Promise Overview"}' >/dev/null

echo "3. 创建 Trace 子表..."
TRACE_RESULT=$(lark-cli api POST "/open-apis/bitable/v1/apps/$APP_TOKEN/tables" \
  --data '{"table":{"name":"Interaction Trace","default_view_name":"Grid View"}}')
TRACE_TABLE_ID=$(printf '%s' "$TRACE_RESULT" | json_table_id)
echo "  TRACE_TABLE_ID: $TRACE_TABLE_ID"

echo "4. 创建主表字段..."
create_text_field "$APP_TOKEN" "$MAIN_TABLE_ID" "promise_id"
create_text_field "$APP_TOKEN" "$MAIN_TABLE_ID" "title"
create_text_field "$APP_TOKEN" "$MAIN_TABLE_ID" "description"
create_text_field "$APP_TOKEN" "$MAIN_TABLE_ID" "source"
create_single_select_field "$APP_TOKEN" "$MAIN_TABLE_ID" "status" \
  '[{"name":"待处理"},{"name":"进行中"},{"name":"已完成"},{"name":"已过期"},{"name":"已拒绝"}]'
create_single_select_field "$APP_TOKEN" "$MAIN_TABLE_ID" "priority" \
  '[{"name":"P0"},{"name":"P1"},{"name":"P2"},{"name":"P3"}]'
create_datetime_field "$APP_TOKEN" "$MAIN_TABLE_ID" "created_at"
create_datetime_field "$APP_TOKEN" "$MAIN_TABLE_ID" "due_date"
create_datetime_field "$APP_TOKEN" "$MAIN_TABLE_ID" "completed_at"
create_text_field "$APP_TOKEN" "$MAIN_TABLE_ID" "flowmind_candidate_id"
create_text_field "$APP_TOKEN" "$MAIN_TABLE_ID" "flowmind_status"
create_datetime_field "$APP_TOKEN" "$MAIN_TABLE_ID" "last_trace_at"
create_text_field "$APP_TOKEN" "$MAIN_TABLE_ID" "trace_summary"
create_number_field "$APP_TOKEN" "$MAIN_TABLE_ID" "trace_event_count"
create_text_field "$APP_TOKEN" "$MAIN_TABLE_ID" "last_trace_summary"
create_text_field "$APP_TOKEN" "$MAIN_TABLE_ID" "timeline_url"

echo "5. 创建 Trace 子表字段..."
create_text_field "$APP_TOKEN" "$TRACE_TABLE_ID" "trace_id"
create_text_field "$APP_TOKEN" "$TRACE_TABLE_ID" "promise_id"
create_text_field "$APP_TOKEN" "$TRACE_TABLE_ID" "candidate_id"
create_single_select_field "$APP_TOKEN" "$TRACE_TABLE_ID" "direction" \
  '[{"name":"Hermes→FlowMind"},{"name":"FlowMind→Hermes"}]'
create_single_select_field "$APP_TOKEN" "$TRACE_TABLE_ID" "flowmind_module" \
  '[{"name":"candidate-ingress"},{"name":"review"},{"name":"truth"},{"name":"feedback"},{"name":"context-pack"},{"name":"bridge"}]'
create_text_field "$APP_TOKEN" "$TRACE_TABLE_ID" "action"
create_text_field "$APP_TOKEN" "$TRACE_TABLE_ID" "request_payload"
create_text_field "$APP_TOKEN" "$TRACE_TABLE_ID" "response_summary"
create_single_select_field "$APP_TOKEN" "$TRACE_TABLE_ID" "status" \
  '[{"name":"success"},{"name":"failed"},{"name":"pending"}]'
create_datetime_field "$APP_TOKEN" "$TRACE_TABLE_ID" "timestamp"
create_number_field "$APP_TOKEN" "$TRACE_TABLE_ID" "latency_ms"

mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_PATH" <<EOF
{
  "bitable": {
    "app_token": "$APP_TOKEN",
    "main_table_id": "$MAIN_TABLE_ID",
    "trace_table_id": "$TRACE_TABLE_ID",
    "url": "https://bcn7uazoofu0.feishu.cn/base/$APP_TOKEN"
  },
  "flowmind": {
    "base_url": "http://111.229.194.203:3301",
    "api_key": "flowmind-dev-token"
  },
  "webui": {
    "timeline_base_url": "http://111.229.194.203/manage/timeline"
  },
  "feishu": {
    "chat_id": "oc_bbde428675a7c267d55c3f0663ca701d"
  }
}
EOF

echo
echo "=== 初始化完成 ==="
echo "APP_TOKEN: $APP_TOKEN"
echo "MAIN_TABLE_ID: $MAIN_TABLE_ID"
echo "TRACE_TABLE_ID: $TRACE_TABLE_ID"
echo "URL: https://bcn7uazoofu0.feishu.cn/base/$APP_TOKEN"
echo "CONFIG: $CONFIG_PATH"
echo
echo "后续脚本读取方式："
echo "  PROMISE_BITABLE_CONFIG_PATH=$CONFIG_PATH python3 scripts/daily-promise-review.py"
echo
echo "下一步：在飞书 Web UI 中给 Promise Overview 手动创建甘特图视图。"
