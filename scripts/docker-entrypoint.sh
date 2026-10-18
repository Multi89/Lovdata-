#!/bin/sh
set -eu

DB_PATH="${LOVDATA_DB_PATH:-/app/data/lovdata.sqlite3}"
if [ ! -s "$DB_PATH" ] || [ "${LOVDATA_REBUILD_INDEX:-false}" = "true" ]; then
  mkdir -p "$(dirname "$DB_PATH")"
  FILTER="${LOVDATA_DATASET_FILTER:-gjeldende-lover,gjeldende-sentrale-forskrifter}"
  if [ "$FILTER" = "all" ]; then
    lovdata-sync --all --db "$DB_PATH"
  else
    OLD_IFS="$IFS"
    IFS=','
    set -- $FILTER
    IFS="$OLD_IFS"
    ARGS=""
    for pattern in "$@"; do
      ARGS="$ARGS --matching $pattern"
    done
    # shellcheck disable=SC2086
    lovdata-sync $ARGS --db "$DB_PATH"
  fi
fi

MODE="${LOVDATA_SERVER_MODE:-actions}"
case "$MODE" in
  actions)
    exec lovdata-actions-api
    ;;
  mcp)
    exec lovdata-chat-mcp
    ;;
  *)
    echo "Ukjent LOVDATA_SERVER_MODE: $MODE (bruk actions eller mcp)" >&2
    exit 2
    ;;
esac
