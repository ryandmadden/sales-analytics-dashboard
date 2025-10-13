"""
Email Sender Module
Handles sending automated performance reports via email
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class EmailSender:
    """Handles email sending functionality"""
    
    def __init__(self, config: Dict):
        """
        Initialize email sender with configuration
        
        Args:
            config: Email configuration dictionary
        """
        self.config = config
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.use_tls = config.get('use_tls', True)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_address = config.get('from_address', self.username)
        
    def create_html_body(
        self,
        person_name: str,
        totals: Dict[str, float],
        rates: Dict[str, float],
        date_range: str
    ) -> str:
        """
        Create HTML email body with summary statistics
        
        Args:
            person_name: Name of the lead generator
            totals: Dictionary of total metrics
            rates: Dictionary of conversion rates
            date_range: Date range string
            
        Returns:
            HTML string for email body
        """
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    background-color: #2E86AB;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px;
                }}
                .content {{
                    padding: 20px;
                }}
                .metrics {{
                    background-color: #f4f4f4;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .metric-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #ddd;
                }}
                .metric-label {{
                    font-weight: bold;
                    color: #555;
                }}
                .metric-value {{
                    color: #2E86AB;
                    font-weight: bold;
                }}
                .conversion {{
                    background-color: #e8f4f8;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #888;
                    font-size: 12px;
                }}
                .highlight {{
                    color: #06A77D;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Your Monthly Sales Performance</h1>
                <p>{date_range}</p>
            </div>
            
            <div class="content">
                <p>Hi {person_name},</p>
                
                <p>Here's your performance summary for the week. Great work out there!</p>
                
                <div class="metrics">
                    <h2>📈 Your Activity Metrics</h2>
                    <div class="metric-row">
                        <span class="metric-label">Doors Knocked:</span>
                        <span class="metric-value">{int(totals['doors_knocked'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Homeowners Talked:</span>
                        <span class="metric-value">{int(totals['homeowners_talked'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Qualified Leads:</span>
                        <span class="metric-value">{int(totals['qualified_leads'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Appointments Set:</span>
                        <span class="metric-value">{int(totals['appointments_set'])}</span>
                    </div>
                </div>
                
                <div class="conversion">
                    <h2>🎯 Your Conversion Rates</h2>
                    <div class="metric-row">
                        <span class="metric-label">Talk Rate:</span>
                        <span class="metric-value">{rates['talk_rate']:.1f}%</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Qualification Rate:</span>
                        <span class="metric-value">{rates['qualification_rate']:.1f}%</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Appointment Rate:</span>
                        <span class="metric-value">{rates['appointment_rate']:.1f}%</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Overall Conversion:</span>
                        <span class="metric-value highlight">{rates['overall_conversion']:.1f}%</span>
                    </div>
                </div>
                
                <p><strong>Attached Charts:</strong></p>
                <ul>
                    <li>Performance Metrics Overview</li>
                    <li>Sales Funnel Visualization</li>
                    <li>Daily Performance Trends</li>
                    <li>Team Comparison</li>
                    <li>Conversion Rates Breakdown</li>
                </ul>
                
                <p>Keep up the excellent work! If you have questions about your metrics, 
                reach out to your manager.</p>
                
                <p>Best regards,<br>
                <strong>Ryan the Sales Team Lead</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated report. Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        return html
    
    def send_report(
        self,
        to_email: str,
        person_name: str,
        chart_paths: Dict[str, str],
        totals: Dict[str, float],
        rates: Dict[str, float],
        date_range: str
    ) -> bool:
        """
        Send performance report email with chart attachments
        
        Args:
            to_email: Recipient email address
            person_name: Name of the lead generator
            chart_paths: Dictionary mapping chart names to file paths
            totals: Dictionary of total metrics
            rates: Dictionary of conversion rates
            date_range: Date range string
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('related')
            msg['From'] = self.from_address
            msg['To'] = to_email
            msg['Subject'] = f"Your Monthly Sales Performance - {date_range}"
            
            # Create HTML body
            html_body = self.create_html_body(person_name, totals, rates, date_range)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach charts
            for chart_name, chart_path in chart_paths.items():
                if Path(chart_path).exists():
                    with open(chart_path, 'rb') as f:
                        img_data = f.read()
                        image = MIMEImage(img_data, name=f"{chart_name}.png")
                        msg.attach(image)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
            
            print("SMTP connection test successful")
            return True
        except Exception as e:
            print(f"SMTP connection test failed: {str(e)}")
            return False

