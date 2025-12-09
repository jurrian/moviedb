#!/usr/bin/env bash
# Auto-switch DB configuration and ensure DB exists on branch change, runs Django migrations

# 1. Determine DB name from branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
DB_NAME="moviedb_${BRANCH//[^a-zA-Z0-9]/_}"

# 2. Write config
echo "PGDATABASE=$DB_NAME" > .env.branch
echo "POSTGRES_DB=$DB_NAME" >> .env.branch

# 3. Load creds if present
[ -f .env ] && source .env

# 4. Require env vars
: "${PGHOST:?}" "${PGPORT:?}" "${PGUSER:?}" "${PGPASSWORD:?}"

# 5. Try create DB
OUTPUT=$(PGPASSWORD=$PGPASSWORD \
  psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" \
  -tAc "CREATE DATABASE \"$DB_NAME\";" 2>&1)

STATUS=$?

# 6. Determine whether DB was created
CREATED=0

if [ $STATUS -ne 0 ]; then
    if [[ "$OUTPUT" == *"already exists"* ]]; then
        CREATED=0
    else
        echo "DB error: $OUTPUT"
        exit $STATUS
    fi
else
    CREATED=1
fi

# 7. Print switch message
if [ $CREATED -eq 1 ]; then
    echo "Switched to DB $DB_NAME (created)"
else
    echo "Switched to DB $DB_NAME"
fi

# 8. Run migrations
if ! uv run python src/manage.py migrate --noinput; then
    echo "Migration failed"
    exit 1
fi
