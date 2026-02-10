"""
Notification System for Smart Timetable App
"""
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

class NotificationManager:
    def __init__(self):
        self.config_file = 'data/config.json'
        self.load_config()
    
    def load_config(self):
        """Load email configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender_email': '',
                'sender_password': '',
                'notification_enabled': False
            }
            self.save_config()
    
    def save_config(self):
        """Save email configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def update_config(self, smtp_server, smtp_port, sender_email, sender_password, enabled=True):
        """Update email configuration"""
        self.config = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'sender_email': sender_email,
            'sender_password': sender_password,
            'notification_enabled': enabled
        }
        self.save_config()
        return True
    
    def send_email_notification(self, recipient, subject, message):
        """Send email notification to user"""
        if not self.config.get('notification_enabled', False):
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['sender_email']
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'html'))
            
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)
            
            print(f"Email sent to {recipient}: {subject}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def check_upcoming_schedule(self, schedule_data, hours_before=1):
        """Check for upcoming schedule items"""
        notifications = []
        now = datetime.now()
        
        for item in schedule_data:
            if 'time' in item:
                try:
                    item_time = datetime.strptime(item['time'], '%Y-%m-%d %H:%M:%S')
                    time_diff = item_time - now
                    
                    # Check if item is within the notification window
                    if timedelta(0) < time_diff <= timedelta(hours=hours_before):
                        notification = {
                            'type': 'schedule',
                            'title': item.get('title', 'Upcoming Item'),
                            'time': item['time'],
                            'details': item.get('details', ''),
                            'recipient': item.get('email', '')
                        }
                        notifications.append(notification)
                except ValueError:
                    continue
        
        return notifications
    
    def send_bulk_notifications(self, notifications):
        """Send multiple notifications"""
        sent_count = 0
        for notification in notifications:
            subject = f"Reminder: {notification['title']}"
            message = f"""
            <html>
            <body>
                <h2>Schedule Reminder</h2>
                <p>You have an upcoming item: <strong>{notification['title']}</strong></p>
                <p>Time: {notification['time']}</p>
                <p>Details: {notification['details']}</p>
                <p>Please be prepared!</p>
            </body>
            </html>
            """
            
            if self.send_email_notification(notification['recipient'], subject, message):
                sent_count += 1
        
        return sent_count

# Create instance
notification_manager = NotificationManager()