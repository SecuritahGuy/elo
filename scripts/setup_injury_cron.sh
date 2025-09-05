#!/bin/bash
# Setup Injury Data Update Cron Jobs

PROJECT_DIR="/Users/tim/Code/Personal/SportsEdge"
LOG_DIR="$PROJECT_DIR/artifacts/automated_collection"

echo "🏥 Setting up Injury Data Update Cron Jobs"
echo "=========================================="

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Make scripts executable
chmod +x "$PROJECT_DIR/update_injury_data.py"
chmod +x "$PROJECT_DIR/check_missed_jobs.py"

# Get current crontab
echo "📋 Getting current crontab..."
crontab -l > current_cron.txt 2>/dev/null || touch current_cron.txt

# Remove any existing injury data cron jobs
echo "🧹 Removing existing injury data cron jobs..."
grep -v "update_injury_data.py" current_cron.txt > temp_cron.txt
grep -v "check_missed_jobs.py" temp_cron.txt > current_cron.txt
rm temp_cron.txt

# Add new injury data cron jobs
echo "➕ Adding new injury data cron jobs..."

# Daily injury data update at 3:00 AM
INJURY_CRON_ENTRY="0 3 * * * cd $PROJECT_DIR && python update_injury_data.py --season $(date +%Y) >> $LOG_DIR/injury_updates.log 2>&1"

# Failover check every 6 hours (4 times per day)
FAILOVER_CRON_ENTRY="0 */6 * * * cd $PROJECT_DIR && python check_missed_jobs.py >> $LOG_DIR/failover.log 2>&1"

# Add the cron entries
echo "$INJURY_CRON_ENTRY" >> current_cron.txt
echo "$FAILOVER_CRON_ENTRY" >> current_cron.txt

# Install the new crontab
echo "💾 Installing new crontab..."
crontab current_cron.txt

# Clean up
rm current_cron.txt

echo ""
echo "✅ Injury Data Cron Jobs Setup Complete!"
echo "========================================"
echo ""
echo "📅 Scheduled Jobs:"
echo "   • Injury Data Update: Daily at 3:00 AM"
echo "   • Failover Check: Every 6 hours (12 AM, 6 AM, 12 PM, 6 PM)"
echo ""
echo "📁 Log Files:"
echo "   • Injury Updates: $LOG_DIR/injury_updates.log"
echo "   • Failover Logs: $LOG_DIR/failover.log"
echo ""
echo "🔧 Manual Commands:"
echo "   • Test injury update: python update_injury_data.py --dry-run"
echo "   • Check missed jobs: python check_missed_jobs.py --dry-run"
echo "   • View cron jobs: crontab -l"
echo ""
echo "⚠️  Note: The failover system will automatically run missed jobs"
echo "    if your computer wasn't running at the scheduled time."
