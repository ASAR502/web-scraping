import requests
from bs4 import BeautifulSoup
from lxml import etree, html
import json
import hashlib
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional
import sqlite3
import os
from dataclasses import dataclass
from difflib import unified_diff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('html_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ChangeDetails:
    """Data class to store change details"""
    change_type: str
    xpath: str
    old_value: Optional[str]
    new_value: Optional[str]
    element_type: str
    timestamp: datetime

class DatabaseManager:
    """Manages SQLite database operations for storing scan history"""
    
    def __init__(self, db_path: str = "html_detector.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                html_hash TEXT NOT NULL,
                xpath_structure TEXT NOT NULL,
                changes_detected INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detected_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER,
                change_type TEXT NOT NULL,
                xpath TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                element_type TEXT,
                detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scan_id) REFERENCES scan_history (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_scan_result(self, url: str, html_hash: str, xpath_structure: str, changes: List[ChangeDetails]) -> int:
        """Save scan result to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert scan history
        cursor.execute('''
            INSERT INTO scan_history (url, html_hash, xpath_structure, changes_detected)
            VALUES (?, ?, ?, ?)
        ''', (url, html_hash, xpath_structure, len(changes)))
        
        scan_id = cursor.lastrowid
        
        # Insert detected changes
        for change in changes:
            cursor.execute('''
                INSERT INTO detected_changes 
                (scan_id, change_type, xpath, old_value, new_value, element_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (scan_id, change.change_type, change.xpath, change.old_value, 
                  change.new_value, change.element_type))
        
        conn.commit()
        conn.close()
        return scan_id
    
    def get_last_scan(self, url: str) -> Optional[Tuple[str, str]]:
        """Get last scan data for a URL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT html_hash, xpath_structure FROM scan_history 
            WHERE url = ? ORDER BY scan_time DESC LIMIT 1
        ''', (url,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result if result else None

class EmailNotifier:
    """Handles email notifications for detected changes"""
    
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
    
    def send_alert(self, recipient: str, url: str, changes: List[ChangeDetails], html_diff: str = ""):
        """Send email alert for detected changes"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient
            msg['Subject'] = f"HTML Change Detected: {url}"
            
            # Create email body
            body = self._create_email_body(url, changes, html_diff)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent to {recipient}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _create_email_body(self, url: str, changes: List[ChangeDetails], html_diff: str) -> str:
        """Create HTML email body"""
        change_summary = self._create_change_summary(changes)
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f44336; color: white; padding: 10px; }}
                .content {{ padding: 20px; }}
                .change {{ margin: 10px 0; padding: 10px; border-left: 3px solid #2196F3; }}
                .xpath {{ font-family: monospace; background-color: #f5f5f5; padding: 2px 4px; }}
                .diff {{ background-color: #f9f9f9; padding: 10px; font-family: monospace; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>HTML Change Detected</h2>
            </div>
            <div class="content">
                <h3>URL: {url}</h3>
                <p><strong>Detection Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Total Changes:</strong> {len(changes)}</p>
                
                <h3>Change Summary:</h3>
                {change_summary}
                
                {"<h3>HTML Diff:</h3><div class='diff'>" + html_diff + "</div>" if html_diff else ""}
            </div>
        </body>
        </html>
        """
        return body
    
    def _create_change_summary(self, changes: List[ChangeDetails]) -> str:
        """Create HTML summary of changes"""
        summary = ""
        for change in changes:
            summary += f"""
            <div class="change">
                <strong>Type:</strong> {change.change_type}<br>
                <strong>XPath:</strong> <span class="xpath">{change.xpath}</span><br>
                <strong>Element:</strong> {change.element_type}<br>
                {"<strong>Old Value:</strong> " + str(change.old_value) + "<br>" if change.old_value else ""}
                {"<strong>New Value:</strong> " + str(change.new_value) + "<br>" if change.new_value else ""}
            </div>
            """
        return summary

class HTMLPageDetector:
    """Main class for detecting HTML page changes"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db_manager = DatabaseManager(config.get('db_path', 'html_detector.db'))
        
        # Initialize email notifier if configured
        self.email_notifier = None
        if config.get('email_enabled', False):
            self.email_notifier = EmailNotifier(
                config['smtp_server'],
                config['smtp_port'],
                config['email'],
                config['email_password']
            )
        
        self.session = requests.Session()
        # Set user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def extract_xpath_structure(self, html_content: str) -> Dict:
        """Extract XPath-based structure from HTML"""
        try:
            # Parse HTML with lxml
            doc = html.fromstring(html_content)
            
            structure = {
                'elements': {},
                'attributes': {},
                'tables': {},
                'forms': {}
            }
            
            # Extract all elements with their XPaths
            for element in doc.iter():
                if element.tag:
                    xpath = self._get_element_xpath(element)
                    structure['elements'][xpath] = {
                        'tag': element.tag,
                        'text': (element.text or '').strip()[:100],  # Limit text length
                        'tail': (element.tail or '').strip()[:100]
                    }
                    
                    # Extract attributes
                    if element.attrib:
                        structure['attributes'][xpath] = dict(element.attrib)
            
            # Extract table structures
            tables = doc.xpath('//table')
            for i, table in enumerate(tables):
                table_xpath = self._get_element_xpath(table)
                structure['tables'][table_xpath] = self._extract_table_structure(table)
            
            # Extract form structures
            forms = doc.xpath('//form')
            for form in forms:
                form_xpath = self._get_element_xpath(form)
                structure['forms'][form_xpath] = self._extract_form_structure(form)
            
            print(f"Extracted structure from HTML content with {len(structure['elements'])} elements, "
                  f"{len(structure['tables'])} tables, and {len(structure['forms'])} forms.")
            logger.info(f"Extracted structure from HTML content with {len(structure['elements'])} elements, "
                        f"{len(structure['tables'])} tables, and {len(structure['forms'])} forms.") 
            
            return structure
            
        except Exception as e:
            logger.error(f"Failed to extract XPath structure: {e}")
            return {}
    
    def _get_element_xpath(self, element) -> str:
        """Generate XPath for an element"""
        try:
            return element.getroottree().getpath(element)
        except:
            return ""
    
    def _extract_table_structure(self, table) -> Dict:
        """Extract table structure including headers and row count"""
        structure = {
            'headers': [],
            'row_count': 0,
            'column_count': 0
        }
        
        try:
            # Extract headers
            headers = table.xpath('.//th | .//thead//td')
            structure['headers'] = [h.text_content().strip() for h in headers if h.text_content().strip()]
            
            # Count rows and columns
            rows = table.xpath('.//tr')
            structure['row_count'] = len(rows)
            
            if rows:
                first_row_cells = rows[0].xpath('.//td | .//th')
                structure['column_count'] = len(first_row_cells)
                
        except Exception as e:
            logger.error(f"Error extracting table structure: {e}")
        
        return structure
    
    def _extract_form_structure(self, form) -> Dict:
        """Extract form structure including input fields"""
        structure = {
            'action': form.get('action', ''),
            'method': form.get('method', ''),
            'inputs': []
        }
        
        try:
            inputs = form.xpath('.//input | .//select | .//textarea')
            for inp in inputs:
                input_info = {
                    'type': inp.get('type', inp.tag),
                    'name': inp.get('name', ''),
                    'id': inp.get('id', ''),
                    'class': inp.get('class', '')
                }
                structure['inputs'].append(input_info)
                
        except Exception as e:
            logger.error(f"Error extracting form structure: {e}")
        
        return structure
    
    def compare_structures(self, old_structure: Dict, new_structure: Dict) -> List[ChangeDetails]:
        """Compare two HTML structures and detect changes"""
        changes = []
        current_time = datetime.now()
        
        # Compare elements
        changes.extend(self._compare_elements(
            old_structure.get('elements', {}),
            new_structure.get('elements', {}),
            current_time
        ))
        
        # Compare attributes
        changes.extend(self._compare_attributes(
            old_structure.get('attributes', {}),
            new_structure.get('attributes', {}),
            current_time
        ))
        
        # Compare tables
        changes.extend(self._compare_tables(
            old_structure.get('tables', {}),
            new_structure.get('tables', {}),
            current_time
        ))
        
        # Compare forms
        changes.extend(self._compare_forms(
            old_structure.get('forms', {}),
            new_structure.get('forms', {}),
            current_time
        ))
        
        return changes
    
    def _compare_elements(self, old_elements: Dict, new_elements: Dict, timestamp: datetime) -> List[ChangeDetails]:
        """Compare element structures"""
        changes = []
        
        # Find removed elements
        for xpath in old_elements:
            if xpath not in new_elements:
                changes.append(ChangeDetails(
                    change_type="element_removed",
                    xpath=xpath,
                    old_value=str(old_elements[xpath]),
                    new_value=None,
                    element_type=old_elements[xpath].get('tag', 'unknown'),
                    timestamp=timestamp
                ))
        
        # Find added elements
        for xpath in new_elements:
            if xpath not in old_elements:
                changes.append(ChangeDetails(
                    change_type="element_added",
                    xpath=xpath,
                    old_value=None,
                    new_value=str(new_elements[xpath]),
                    element_type=new_elements[xpath].get('tag', 'unknown'),
                    timestamp=timestamp
                ))
        
        # Find modified elements
        for xpath in old_elements:
            if xpath in new_elements:
                old_elem = old_elements[xpath]
                new_elem = new_elements[xpath]
                
                if old_elem.get('text') != new_elem.get('text'):
                    changes.append(ChangeDetails(
                        change_type="element_text_changed",
                        xpath=xpath,
                        old_value=old_elem.get('text'),
                        new_value=new_elem.get('text'),
                        element_type=old_elem.get('tag', 'unknown'),
                        timestamp=timestamp
                    ))
        
        return changes
    
    def _compare_attributes(self, old_attrs: Dict, new_attrs: Dict, timestamp: datetime) -> List[ChangeDetails]:
        """Compare element attributes"""
        changes = []
        
        all_xpaths = set(old_attrs.keys()) | set(new_attrs.keys())
        
        for xpath in all_xpaths:
            old_attr = old_attrs.get(xpath, {})
            new_attr = new_attrs.get(xpath, {})
            
            # Find attribute changes
            all_attr_names = set(old_attr.keys()) | set(new_attr.keys())
            
            for attr_name in all_attr_names:
                old_value = old_attr.get(attr_name)
                new_value = new_attr.get(attr_name)
                
                if old_value != new_value:
                    change_type = "attribute_modified"
                    if old_value is None:
                        change_type = "attribute_added"
                    elif new_value is None:
                        change_type = "attribute_removed"
                    
                    changes.append(ChangeDetails(
                        change_type=change_type,
                        xpath=f"{xpath}/@{attr_name}",
                        old_value=old_value,
                        new_value=new_value,
                        element_type="attribute",
                        timestamp=timestamp
                    ))
        
        return changes
    
    def _compare_tables(self, old_tables: Dict, new_tables: Dict, timestamp: datetime) -> List[ChangeDetails]:
        """Compare table structures"""
        changes = []
        
        # Find removed tables
        for xpath in old_tables:
            if xpath not in new_tables:
                changes.append(ChangeDetails(
                    change_type="table_removed",
                    xpath=xpath,
                    old_value=str(old_tables[xpath]),
                    new_value=None,
                    element_type="table",
                    timestamp=timestamp
                ))
        
        # Find added tables
        for xpath in new_tables:
            if xpath not in old_tables:
                changes.append(ChangeDetails(
                    change_type="table_added",
                    xpath=xpath,
                    old_value=None,
                    new_value=str(new_tables[xpath]),
                    element_type="table",
                    timestamp=timestamp
                ))
        
        # Find modified tables
        for xpath in old_tables:
            if xpath in new_tables:
                old_table = old_tables[xpath]
                new_table = new_tables[xpath]
                
                # Compare headers
                if old_table.get('headers') != new_table.get('headers'):
                    changes.append(ChangeDetails(
                        change_type="table_headers_changed",
                        xpath=xpath,
                        old_value=str(old_table.get('headers')),
                        new_value=str(new_table.get('headers')),
                        element_type="table",
                        timestamp=timestamp
                    ))
                
                # Compare column count
                if old_table.get('column_count') != new_table.get('column_count'):
                    changes.append(ChangeDetails(
                        change_type="table_columns_changed",
                        xpath=xpath,
                        old_value=str(old_table.get('column_count')),
                        new_value=str(new_table.get('column_count')),
                        element_type="table",
                        timestamp=timestamp
                    ))
        
        return changes
    
    def _compare_forms(self, old_forms: Dict, new_forms: Dict, timestamp: datetime) -> List[ChangeDetails]:
        """Compare form structures"""
        changes = []
        
        all_xpaths = set(old_forms.keys()) | set(new_forms.keys())
        
        for xpath in all_xpaths:
            old_form = old_forms.get(xpath)
            new_form = new_forms.get(xpath)
            
            if old_form is None:
                changes.append(ChangeDetails(
                    change_type="form_added",
                    xpath=xpath,
                    old_value=None,
                    new_value=str(new_form),
                    element_type="form",
                    timestamp=timestamp
                ))
            elif new_form is None:
                changes.append(ChangeDetails(
                    change_type="form_removed",
                    xpath=xpath,
                    old_value=str(old_form),
                    new_value=None,
                    element_type="form",
                    timestamp=timestamp
                ))
            else:
                # Compare form inputs
                old_inputs = old_form.get('inputs', [])
                new_inputs = new_form.get('inputs', [])
                
                if len(old_inputs) != len(new_inputs) or old_inputs != new_inputs:
                    changes.append(ChangeDetails(
                        change_type="form_inputs_changed",
                        xpath=xpath,
                        old_value=str(old_inputs),
                        new_value=str(new_inputs),
                        element_type="form",
                        timestamp=timestamp
                    ))
        
        return changes
    
    def generate_html_diff(self, old_html: str, new_html: str) -> str:
        """Generate HTML diff for email alerts"""
        try:
            old_lines = old_html.splitlines()
            new_lines = new_html.splitlines()
            
            diff = unified_diff(
                old_lines, new_lines,
                fromfile='previous.html',
                tofile='current.html',
                lineterm=''
            )
            
            return '\n'.join(diff)
        except Exception as e:
            logger.error(f"Failed to generate HTML diff: {e}")
            return ""
    
    def scan_url(self, url: str) -> bool:
        """Scan a URL for changes"""
        logger.info(f"Scanning URL: {url}")
        
        # Fetch current HTML
        current_html = self.fetch_page(url)
        if not current_html:
            return False
        
        # Generate hash and structure
        current_hash = hashlib.md5(current_html.encode()).hexdigest()
        current_structure = self.extract_xpath_structure(current_html)
        
        # Get last scan data
        last_scan = self.db_manager.get_last_scan(url)
        
        changes = []
        html_diff = ""
        
        if last_scan:
            last_hash, last_structure_json = last_scan
            
            # Check if content changed
            if current_hash != last_hash:
                try:
                    last_structure = json.loads(last_structure_json)
                    changes = self.compare_structures(last_structure, current_structure)
                    
                    if changes:
                        logger.info(f"Detected {len(changes)} changes in {url}")
                        
                        # Generate HTML diff if configured
                        if self.config.get('generate_diff', False):
                            # We don't have the old HTML stored, so we'll skip diff generation
                            # In production, you might want to store the actual HTML content
                            html_diff = "HTML diff generation requires storing full HTML content"
                        
                        # Send alerts if configured
                        if self.email_notifier and self.config.get('recipients'):
                            for recipient in self.config['recipients']:
                                self.email_notifier.send_alert(recipient, url, changes, html_diff)
                    else:
                        logger.info(f"Content changed in {url} but no structural changes detected")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse stored structure: {e}")
            else:
                logger.info(f"No changes detected in {url}")
        else:
            logger.info(f"First scan for {url} - creating baseline")
        
        # Save current scan result
        self.db_manager.save_scan_result(
            url, current_hash, json.dumps(current_structure), changes
        )
        
        return len(changes) > 0
    
    def monitor_urls(self, urls: List[str], interval: int = 3600):
        """Monitor multiple URLs continuously"""
        logger.info(f"Starting monitoring for {len(urls)} URLs with {interval}s interval")
        
        while True:
            try:
                for url in urls:
                    self.scan_url(url)
                    time.sleep(5)  # Small delay between URLs
                
                logger.info(f"Completed scan cycle. Waiting {interval} seconds...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

# Configuration example
def create_sample_config():
    """Create sample configuration"""
    return {
        'db_path': 'html_detector.db',
        'email_enabled': False,  # Set to True to enable email alerts
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'email': 'your-email@gmail.com',
        'email_password': 'your-app-password',
        'recipients': ['recipient@example.com'],
        'generate_diff': True,
        'scan_interval': 3600,  # 1 hour
        'urls_to_monitor': [
            'https://example.com',
            'https://httpbin.org/html'
        ]
    }

# Example usage
if __name__ == "__main__":
    # Create configuration
    config = create_sample_config()
    
    # Initialize detector
    detector = HTMLPageDetector(config)
    
    # Single URL scan example
    url = "https://httpbin.org/html"
    detector.scan_url(url)
    
    # Continuous monitoring example (uncomment to use)
    # detector.monitor_urls(config['urls_to_monitor'], config['scan_interval'])