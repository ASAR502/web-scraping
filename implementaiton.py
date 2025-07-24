import asyncio
import time
from html_page_detector import HTMLPageDetector, ChangeDetails
from config import Config

class UsageExamples:
    """Examples demonstrating different use cases"""
    
    def __init__(self):
        self.config = Config()
        self.detector = HTMLPageDetector(self.config.config)
    
    def example_1_single_url_scan(self):
        """Example 1: Scan a single URL once"""
        print("=== Example 1: Single URL Scan ===")
        
        url = "https://httpbin.org/html"
        print(f"Scanning: {url}")
        
        changes_detected = self.detector.scan_url(url)
        
        if changes_detected:
            print("✅ Changes detected!")
        else:
            print("❌ No changes detected")
    
    def example_2_monitor_multiple_urls(self):
        """Example 2: Monitor multiple URLs"""
        print("=== Example 2: Monitor Multiple URLs ===")
        
        urls = [
            "https://httpbin.org/html",
            "https://jsonplaceholder.typicode.com",
            "https://example.com"
        ]
        
        print(f"Monitoring {len(urls)} URLs...")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            self.detector.monitor_urls(urls, interval=300)  # Check every 5 minutes
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
    
    def example_3_custom_configuration(self):
        """Example 3: Using custom configuration"""
        print("=== Example 3: Custom Configuration ===")
        
        # Custom configuration for specific monitoring needs
        custom_config = {
            'db_path': 'custom_detector.db',
            'email_enabled': True,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': 'your-monitoring@gmail.com',
            'email_password': 'your-app-password',
            'recipients': ['admin@company.com', 'dev-team@company.com'],
            'generate_diff': True,
            'scan_interval': 1800,  # 30 minutes
            'urls_to_monitor': [
                'https://your-ecommerce-site.com/products',
                'https://competitor-site.com/pricing',
                'https://news-site.com/latest'
            ]
        }
        
        # Initialize detector with custom config
        custom_detector = HTMLPageDetector(custom_config)
        
        # Scan with custom settings
        for url in custom_config['urls_to_monitor']:
            print(f"Scanning with custom config: {url}")
            custom_detector.scan_url(url)
    
    def example_4_table_structure_monitoring(self):
        """Example 4: Specific table structure monitoring"""
        print("=== Example 4: Table Structure Monitoring ===")
        
        # Monitor websites with important table data
        table_urls = [
            "https://finance-site.com/stock-prices",
            "https://sports-site.com/league-table",
            "https://data-portal.com/statistics"
        ]
        
        for url in table_urls:
            print(f"Analyzing table structure: {url}")
            
            # Fetch and analyze
            html_content = self.detector.fetch_page(url)
            if html_content:
                structure = self.detector.extract_xpath_structure(html_content)
                
                # Print table information
                tables = structure.get('tables', {})
                print(f"Found {len(tables)} tables:")
                
                for xpath, table_info in tables.items():
                    print(f"  Table XPath: {xpath}")
                    print(f"  Headers: {table_info.get('headers', [])}")
                    print(f"  Columns: {table_info.get('column_count', 0)}")
                    print(f"  Rows: {table_info.get('row_count', 0)}")
                    print()
    
    def example_5_form_monitoring(self):
        """Example 5: Form structure monitoring"""
        print("=== Example 5: Form Structure Monitoring ===")
        
        # Monitor forms for changes (useful for login forms, registration forms, etc.)
        form_urls = [
            "https://example-site.com/login",
            "https://example-site.com/register",
            "https://example-site.com/contact"
        ]
        
        for url in form_urls:
            print(f"Analyzing form structure: {url}")
            
            html_content = self.detector.fetch_page(url)
            if html_content:
                structure = self.detector.extract_xpath_structure(html_content)
                
                forms = structure.get('forms', {})
                print(f"Found {len(forms)} forms:")
                
                for xpath, form_info in forms.items():
                    print(f"  Form XPath: {xpath}")
                    print(f"  Action: {form_info.get('action', 'N/A')}")
                    print(f"  Method: {form_info.get('method', 'N/A')}")
                    print(f"  Input fields: {len(form_info.get('inputs', []))}")
                    
                    for inp in form_info.get('inputs', []):
                        print(f"    - {inp.get('type', 'unknown')} field: {inp.get('name', 'unnamed')}")
                    print()
    
    def example_6_scheduled_monitoring_with_reports(self):
        """Example 6: Scheduled monitoring with detailed reports"""
        print("=== Example 6: Scheduled Monitoring with Reports ===")
        
        import schedule
        import threading
        from datetime import datetime
        
        def generate_monitoring_report():
            """Generate a monitoring report"""
            print(f"\n📊 Monitoring Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            # Get URLs from config
            urls = self.config.get('urls', [])
            
            total_changes = 0
            for url_config in urls:
                if not url_config.get('enabled', True):
                    continue
                
                url = url_config['url']
                name = url_config.get('name', url)
                
                print(f"\n🔍 Scanning: {name}")
                print(f"   URL: {url}")
                
                try:
                    changes_detected = self.detector.scan_url(url)
                    if changes_detected:
                        print("   Status: ✅ Changes detected")
                        total_changes += 1
                    else:
                        print("   Status: ❌ No changes")
                        
                except Exception as e:
                    print(f"   Status: ❌ Error - {str(e)}")
            
            print(f"\n📈 Summary: {total_changes} sites with changes detected")
            print("=" * 60)
        
        # Schedule monitoring
        schedule.every(30).minutes.do(generate_monitoring_report)
        schedule.every().day.at("09:00").do(generate_monitoring_report)
        
        print("Scheduled monitoring started...")
        print("- Every 30 minutes")
        print("- Daily at 9:00 AM")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nScheduled monitoring stopped")
    
    def example_7_api_integration(self):
        """Example 7: Integration with REST API"""
        print("=== Example 7: API Integration ===")
        
        from flask import Flask, jsonify, request
        import json
        
        app = Flask(__name__)
        
        @app.route('/scan', methods=['POST'])
        def api_scan():
            """API endpoint to trigger a scan"""
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return jsonify({'error': 'URL is required'}), 400
            
            try:
                changes_detected = self.detector.scan_url(url)
                return jsonify({
                    'success': True,
                    'url': url,
                    'changes_detected': changes_detected,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/status', methods=['GET'])
        def api_status():
            """API endpoint to get monitoring status"""
            # Get recent scan results from database
            # This is a simplified example
            return jsonify({
                'status': 'active',
                'monitored_urls': len(self.config.get('urls', [])),
                'last_scan': datetime.now().isoformat()
            })
        
        print("Starting API server on http://localhost:5000")
        print("Endpoints:")
        print("  POST /scan - Trigger a scan")
        print("  GET /status - Get monitoring status")
        
        # In production, you'd run this with a proper WSGI server
        # app.run(host='0.0.0.0', port=5000, debug=False)
    
    def example_8_webhook_notifications(self):
        """Example 8: Webhook notifications"""
        print("=== Example 8: Webhook Notifications ===")
        
        import requests
        
        class WebhookNotifier:
            def __init__(self, webhook_url: str):
                self.webhook_url = webhook_url
            
            def send_notification(self, url: str, changes: list):
                """Send webhook notification"""
                payload = {
                    'event': 'html_change_detected',
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'changes_count': len(changes),
                    'changes': [
                        {
                            'type': change.change_type,
                            'xpath': change.xpath,
                            'element_type': change.element_type,
                            'old_value': change.old_value,
                            'new_value': change.new_value
                        }
                        for change in changes[:5]  # Limit to first 5 changes
                    ]
                }
                
                try:
                    response = requests.post(
                        self.webhook_url,
                        json=payload,
                        timeout=10
                    )
                    response.raise_for_status()
                    print(f"✅ Webhook notification sent successfully")
                except requests.RequestException as e:
                    print(f"❌ Failed to send webhook: {e}")
        
        # Example usage with Slack webhook
        slack_webhook = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        webhook_notifier = WebhookNotifier(slack_webhook)
        
        # Example payload (this would be integrated into the main detector)
        print("Webhook notification system configured")
        print(f"Webhook URL: {slack_webhook}")

# main.py - Main execution file

def main():
    """Main function to run examples"""
    import sys
    
    examples = UsageExamples()
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <example_number>")
        print("\nAvailable examples:")
        print("1 - Single URL scan")
        print("2 - Monitor multiple URLs")
        print("3 - Custom configuration")
        print("4 - Table structure monitoring")
        print("5 - Form monitoring")
        print("6 - Scheduled monitoring with reports")
        print("7 - API integration")
        print("8 - Webhook notifications")
        return
    
    example_num = sys.argv[1]
    
    example_methods = {
        '1': examples.example_1_single_url_scan,
        '2': examples.example_2_monitor_multiple_urls,
        '3': examples.example_3_custom_configuration,
        '4': examples.example_4_table_structure_monitoring,
        '5': examples.example_5_form_monitoring,
        '6': examples.example_6_scheduled_monitoring_with_reports,
        '7': examples.example_7_api_integration,
        '8': examples.example_8_webhook_notifications
    }
    
    if example_num in example_methods:
        example_methods[example_num]()
    else:
        print(f"Invalid example number: {example_num}")

if __name__ == "__main__":
    main()

# requirements.txt - Dependencies file
"""
requests>=2.28.0
beautifulsoup4>=4.11.0
lxml>=4.9.0
Flask>=2.2.0
schedule>=1.2.0
"""

# setup.py - Installation script
# from setuptools import setup, find_packages

# setup(
#     name="html-page-change-detector",
#     version="1.0.0",
#     author="Your Name",
#     author_email="your-email@example.com",
#     description="A comprehensive HTML page change detection and monitoring system",
#     long_description=open("README.md").read(),
#     long_description_content_type="text/markdown",
#     url="https://github.com/yourusername/html-page-change-detector",
#     packages=find_packages(),
#     classifiers=[
#         "Development Status :: 4 - Beta",
#         "Intended Audience :: Developers",
#         "License :: OSI Approved :: MIT License",
#         "Programming Language :: Python :: 3",
#         "Programming Language :: Python :: 3.8",
#         "Programming Language :: Python :: 3.9",
#         "Programming Language :: Python :: 3.10",
#         "Programming Language :: Python :: 3.11",
#     ],
#     python_requires=">=3.8",
#     install_requires=[
#         "requests>=2.28.0",
#         "beautifulsoup4>=4.11.0",
#         "lxml>=4.9.0",
#         "Flask>=2.2.0",
#         "schedule>=1.2.0",
#     ],
#     extras_require={
#         "dev": [
#             "pytest>=7.0.0",
#             "black>=22.0.0",
#             "flake8>=5.0.0",
#             "mypy>=0.990",
#         ],
#     },
# )