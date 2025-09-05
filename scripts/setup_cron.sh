#!/bin/bash
# Setup cron jobs for automated data collection

# Get the absolute path to the project
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH="$PROJECT_DIR/start_automated_collection.py"

echo "Setting up cron jobs for SportsEdge data collection..."
echo "Project directory: $PROJECT_DIR"

# Create cron jobs
# Action Network data collection every 15 minutes
(crontab -l 2>/dev/null; echo "*/15 * * * * cd $PROJECT_DIR && python3 $PYTHON_PATH --mode single --skip-health-check") | crontab -

# NFL stats collection every 6 hours
(crontab -l 2>/dev/null; echo "0 */6 * * * cd $PROJECT_DIR && python3 $PYTHON_PATH --mode single --skip-health-check") | crontab -

# Health check every hour
(crontab -l 2>/dev/null; echo "0 * * * * cd $PROJECT_DIR && python3 $PYTHON_PATH --mode health > artifacts/automated_collection/health_$(date +\%Y\%m\%d_\%H\%M\%S).log 2>&1") | crontab -

# Full collection cycle daily at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * cd $PROJECT_DIR && python3 $PYTHON_PATH --mode single") | crontab -

echo "Cron jobs installed successfully!"
echo "Current cron jobs:"
crontab -l

echo ""
echo "To remove cron jobs, run: crontab -r"
echo "To view cron jobs, run: crontab -l"
