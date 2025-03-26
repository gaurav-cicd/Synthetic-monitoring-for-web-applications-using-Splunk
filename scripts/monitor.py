#!/usr/bin/env python3
import os
import sys
import yaml
import time
import logging
import requests
import boto3
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from prometheus_client import start_http_server, Gauge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
app_health = Gauge('web_app_health', 'Health status of web applications', ['app_name'])
active_users = Gauge('active_users', 'Number of active users', ['app_name'])
response_time = Gauge('response_time', 'Response time in seconds', ['app_name'])

class WebAppMonitor:
    def __init__(self, config_path='config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.slack_client = WebClient(token=self.config['slack']['webhook_url'])
        self.ec2_client = boto3.client('ec2', region_name=self.config['aws']['region'])
        self.session = requests.Session()
        self.session.timeout = self.config['monitoring']['timeout']

    def check_ec2_instance(self, instance_id):
        try:
            response = self.ec2_client.describe_instance_status(InstanceIds=[instance_id])
            return response['InstanceStatuses'][0]['InstanceState']['Name'] == 'running'
        except Exception as e:
            logger.error(f"Error checking EC2 instance {instance_id}: {str(e)}")
            return False

    def check_application_health(self, instance_id):
        instance = self.ec2_client.describe_instances(InstanceIds=[instance_id])
        public_dns = instance['Reservations'][0]['Instances'][0]['PublicDnsName']
        
        for endpoint in self.config['monitoring']['health_check_endpoints']:
            url = f"http://{public_dns}{endpoint}"
            try:
                start_time = time.time()
                response = self.session.get(url)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    app_health.labels(app_name=f"app_{instance_id}").set(1)
                    response_time.labels(app_name=f"app_{instance_id}").set(response_time)
                    return True
                else:
                    app_health.labels(app_name=f"app_{instance_id}").set(0)
                    return False
            except Exception as e:
                logger.error(f"Error checking health endpoint {url}: {str(e)}")
                app_health.labels(app_name=f"app_{instance_id}").set(0)
                return False

    def send_slack_notification(self, message):
        try:
            self.slack_client.chat_postMessage(
                channel=self.config['slack']['channel'],
                text=message
            )
        except SlackApiError as e:
            logger.error(f"Error sending Slack notification: {str(e)}")

    def send_email_notification(self, subject, message):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['username']
            msg['To'] = ', '.join(self.config['email']['recipients'])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port']) as server:
                server.starttls()
                server.login(self.config['email']['username'], self.config['email']['password'])
                server.send_message(msg)
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")

    def monitor_applications(self):
        while True:
            for instance_id in self.config['aws']['instances']:
                # Check EC2 instance status
                if not self.check_ec2_instance(instance_id):
                    message = f"🚨 EC2 instance {instance_id} is not running!"
                    self.send_slack_notification(message)
                    self.send_email_notification("EC2 Instance Down", message)
                    continue

                # Check application health
                if not self.check_application_health(instance_id):
                    message = f"🚨 Application on instance {instance_id} is not responding!"
                    self.send_slack_notification(message)
                    self.send_email_notification("Application Down", message)

            time.sleep(self.config['monitoring']['check_interval'])

def main():
    # Start Prometheus metrics server
    start_http_server(8000)
    
    monitor = WebAppMonitor()
    try:
        monitor.monitor_applications()
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 