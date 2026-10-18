#!/bin/sh
set -eu
if [ "${LOVDATA_SERVER_MODE:-actions}" = "mcp" ]; then
  exec lovdata-chat-mcp
fi
exec lovdata-actions-api
