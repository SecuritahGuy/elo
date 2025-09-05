#!/bin/bash
# Setup Daily ELO Update Cron Job

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create log directory if it doesn't exist
mkdir -p "$PROJECT_DIR/artifacts/automated_collection"

# Create the cron job entry
CRON_ENTRY="0 2 * * * cd $PROJECT_DIR && python automated_weekly_elo_updater.py --season 2025 >> $PROJECT_DIR/artifacts/automated_collection/elo_updates.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Daily ELO update cron job added:"
echo "   Runs every day at 2:00 AM"
echo "   Updates ELO ratings for 2025 season"
echo "   Logs to: $PROJECT_DIR/artifacts/automated_collection/elo_updates.log"
echo ""
echo "To view current crontab: crontab -l"
echo "To remove this cron job: crontab -e"
