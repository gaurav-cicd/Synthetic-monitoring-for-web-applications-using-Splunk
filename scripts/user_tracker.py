#!/usr/bin/env python3
import os
import sys
import yaml
import time
import logging
import requests
import boto3
from datetime import datetime, timedelta
from prometheus_client import Gauge
from splunk_sdk import client, service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
active_users = Gauge('active_users', 'Number of active users', ['app_name'])

class UserTracker:
    def __init__(self, config_path='config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.ec2_client = boto3.client('ec2', region_name=self.config['aws']['region'])
        self.session = requests.Session()
        self.session.timeout = self.config['monitoring']['timeout']
        
        # Initialize Splunk client
        self.splunk = client.connect(
            host=self.config['splunk']['host'],
            port=self.config['splunk']['port'],
            username=self.config['splunk']['username'],
            password=self.config['splunk']['password']
        )

    def get_instance_public_dns(self, instance_id):
        try:
            instance = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            return instance['Reservations'][0]['Instances'][0]['PublicDnsName']
        except Exception as e:
            logger.error(f"Error getting public DNS for instance {instance_id}: {str(e)}")
            return None

    def track_active_users(self, instance_id):
        public_dns = self.get_instance_public_dns(instance_id)
        if not public_dns:
            return

        try:
            # Query Splunk for active users in the last 30 minutes
            search_query = f'''
            search index={self.config['splunk']['index']} 
            host={public_dns} 
            earliest=-30m 
            | stats count by session_id 
            | stats count as active_users
            '''
            
            job = self.splunk.jobs.create(search_query)
            
            # Wait for the search to complete
            while not job.is_done():
                time.sleep(1)
            
            # Get the results
            results = job.results()
            
            if results and len(results) > 0:
                user_count = int(results[0]['active_users'])
                active_users.labels(app_name=f"app_{instance_id}").set(user_count)
                
                # Log the active users count
                logger.info(f"Active users for instance {instance_id}: {user_count}")
                
                # Store the data in Splunk
                self.store_user_data(instance_id, user_count)
            
        except Exception as e:
            logger.error(f"Error tracking users for instance {instance_id}: {str(e)}")

    def store_user_data(self, instance_id, user_count):
        try:
            # Create a new event in Splunk
            event = {
                'time': datetime.now().timestamp(),
                'host': self.get_instance_public_dns(instance_id),
                'source': 'user_tracking',
                'sourcetype': 'user_count',
                'event': {
                    'instance_id': instance_id,
                    'active_users': user_count,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            self.splunk.index_submit(event)
            
        except Exception as e:
            logger.error(f"Error storing user data in Splunk: {str(e)}")

    def track_all_applications(self):
        while True:
            for instance_id in self.config['aws']['instances']:
                self.track_active_users(instance_id)
            
            time.sleep(60)  # Check every minute

def main():
    tracker = UserTracker()
    try:
        tracker.track_all_applications()
    except KeyboardInterrupt:
        logger.info("User tracking stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 