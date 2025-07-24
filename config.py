# config.py - Configuration file for HTML Page Change Detector

import json
from typing import List, Dict

class Config:
    """Configuration management for HTML Page Change Detector"""
    
    def __init__(self, config_file: str = "detector_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found. Creating default config...")
            default_config = self.create_default_config()
            self.save_config(default_config)
            return default_config
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}")
            return self.create_default_config()
    
    def save_config(self, config: Dict):
        """Save configuration to JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def create_default_config(self) -> Dict:
        """Create default configuration"""
        return {
            "database": {
                "path": "html_detector.db"
            },
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "recipients": []
            },
            "monitoring": {
                "scan_interval": 3600,
                "request_timeout": 30,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "max_retries": 3,
                "retry_delay": 60
            },
            "detection": {
                "generate_diff": True,
                "track_text_changes": True,
                "track_attribute_changes": True,
                "track_table_changes": True,
                "track_form_changes": True,
                "ignore_whitespace": True,
                "min_text_length": 3
            },
            "urls": [
                {
                    "url": "https://example.com",
                    "name": "Example Site",
                    "enabled": True,
                    "custom_headers": {},
                    "custom_selectors": []
                }
            ],
            "logging": {
                "level": "INFO",
                "file": "html_detector.log",
                "max_size_mb": 10,
                "backup_count": 5
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def update(self, key: str, value):
        """Update configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config(self.config)

# usage_examples.py - Examples of how to use the HTML Page Change Detector

