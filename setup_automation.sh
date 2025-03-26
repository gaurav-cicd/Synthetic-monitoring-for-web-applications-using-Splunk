#!/bin/bash

# Create log directory
sudo mkdir -p /var/log/web_monitoring
sudo chown -R $USER:staff /var/log/web_monitoring

# Copy plist files to LaunchAgents directory
cp com.webmonitoring.monitor.plist ~/Library/LaunchAgents/
cp com.webmonitoring.usertracker.plist ~/Library/LaunchAgents/

# Load the launchd jobs
launchctl load ~/Library/LaunchAgents/com.webmonitoring.monitor.plist
launchctl load ~/Library/LaunchAgents/com.webmonitoring.usertracker.plist

echo "Automated monitoring has been set up successfully!"
echo "The monitoring scripts will run every 5 minutes."
echo "You can check the logs in /var/log/web_monitoring/" 