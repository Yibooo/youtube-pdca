#!/bin/bash
# 上限が戻るまで1時間おきに upload_queue.py を再試行する（最大36回）
cd "$(dirname "$0")"
PY="/Users/yibozhou/Desktop/Claude開発APP/youtube-pdca/venv/bin/python"
for i in $(seq 1 36); do
  echo "=== try $i $(date '+%m/%d %H:%M')"
  "$PY" upload_queue.py "$@" 2>&1 | grep -E "uploaded:|thumbnail:|LIMIT|ALL DONE|Error|Traceback"
  rc=${PIPESTATUS[0]}
  if [ "$rc" = "0" ]; then echo FINISHED; exit 0; fi
  if [ "$rc" != "2" ]; then echo "STOPPED rc=$rc"; exit "$rc"; fi
  sleep 3600
done
echo "GAVE UP"
