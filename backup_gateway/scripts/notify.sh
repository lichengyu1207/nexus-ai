#!/bin/bash
STATE=$2
VIP=$3

if [ "$STATE" == "MASTER" ]; then
    MESSAGE="🚨 VIP $VIP 已切换到当前节点，成为 MASTER"
elif [ "$STATE" == "BACKUP" ]; then
    MESSAGE="ℹ️ 当前节点成为 BACKUP"
else
    MESSAGE="⚠️ 状态异常: $STATE"
fi

WEBHOOK_URL="${WEBHOOK_URL:-}"
if [ -n "$WEBHOOK_URL" ]; then
    curl -X POST \
        -H "Content-Type: application/json" \
        -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$MESSAGE\"}}" \
        "$WEBHOOK_URL" 2>/dev/null || true
fi

logger -t keepalived-notify "$MESSAGE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - $MESSAGE" >> /var/log/keepalived-notify.log
