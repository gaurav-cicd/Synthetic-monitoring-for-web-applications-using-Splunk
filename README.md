<<<<<<< HEAD
# Synthetic Monitoring for Web Applications using Splunk

This project implements synthetic monitoring for web applications hosted on AWS EC2 using Splunk. It provides real-time monitoring, user activity tracking, and automated notifications via Slack and Email.

## Features

- Real-time monitoring of web applications
- Active user count tracking
- Automated health checks
- Slack and Email notifications for application downtime
- Integration with Splunk for data analysis and visualization
- Automated execution every 5 minutes using macOS launchd

## Prerequisites

- Splunk Enterprise or Splunk Cloud
- AWS EC2 instances hosting web applications
- Slack workspace for notifications
- SMTP server for email notifications
- Python 3.8+
- macOS (for automated execution)

## Project Structure

```
.
├── README.md
├── requirements.txt
├── config/
│   └── config.yaml
├── scripts/
│   ├── monitor.py
│   ├── user_tracker.py
│   └── notifier.py
├── splunk/
│   ├── apps/
│   │   └── web_monitoring/
│   │       ├── local/
│   │       │   ├── inputs.conf
│   │       │   ├── outputs.conf
│   │       │   └── props.conf
│   │       └── default/
│   │           └── web_monitoring.conf
│   └── dashboards/
│       └── web_monitoring.xml
├── com.webmonitoring.monitor.plist
├── com.webmonitoring.usertracker.plist
└── setup_automation.sh
```

## Setup Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your environment:
   - Update `config/config.yaml` with your AWS, Splunk, Slack, and email credentials
   - Deploy the Splunk app to your Splunk instance

3. Set up automated execution:
   ```bash
   chmod +x setup_automation.sh
   sudo ./setup_automation.sh
   ```

   This will:
   - Create a log directory at `/var/log/web_monitoring`
   - Set up launchd jobs to run the monitoring scripts every 5 minutes
   - Start the monitoring automatically

4. Verify the setup:
   ```bash
   launchctl list | grep webmonitoring
   ```

5. Check the logs:
   ```bash
   tail -f /var/log/web_monitoring/monitor.out
   tail -f /var/log/web_monitoring/usertracker.out
   ```

## Configuration

Update the `config/config.yaml` file with your specific settings:

```yaml
aws:
  region: your-region
  instances:
    - instance-id-1
    - instance-id-2

splunk:
  host: your-splunk-host
  port: 8089
  username: admin
  password: your-password

slack:
  webhook_url: your-slack-webhook-url
  channel: #monitoring

email:
  smtp_server: your-smtp-server
  smtp_port: 587
  username: your-email
  password: your-password
  recipients:
    - admin@example.com
```

## Monitoring Dashboard

Access the Splunk dashboard at:
```
http://your-splunk-host:8000/en-US/app/web_monitoring/dashboard
```

## Managing Automated Execution

### Starting the Monitoring
The monitoring scripts will start automatically after running `setup_automation.sh`. They will also start automatically when your system boots.

### Stopping the Monitoring
To stop the automated monitoring:
```bash
launchctl unload ~/Library/LaunchAgents/com.webmonitoring.monitor.plist
launchctl unload ~/Library/LaunchAgents/com.webmonitoring.usertracker.plist
```

### Checking Status
To check if the monitoring jobs are running:
```bash
launchctl list | grep webmonitoring
```

### Viewing Logs
Monitor the output of the scripts:
```bash
tail -f /var/log/web_monitoring/monitor.out
tail -f /var/log/web_monitoring/usertracker.out
```

## Troubleshooting

1. If the scripts are not running:
   - Check the log files in `/var/log/web_monitoring/`
   - Verify the plist files are in `~/Library/LaunchAgents/`
   - Ensure the paths in the plist files are correct

2. If you need to modify the monitoring interval:
   - Edit the `StartInterval` value in the plist files (value in seconds)
   - Reload the launchd jobs

## License

MIT License 
>>>>>>> 92a1c5b (Initial commit)
