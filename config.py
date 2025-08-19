"""
Configuration file for Subdomain Monitor
"""
import os
from typing import Dict, List

class Config:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7799744103:AAHxdjdV8ycmCcf9AgSA-6C3NMWLFWhg9R0')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '6247017127')
    
    # Database Configuration
    DATABASE_FILE = 'subdomain_monitor.db'
    
    # Monitoring Configuration
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # 5 minutes default
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT', '50'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))
    RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
    
    # API Configuration
    CRTSH_API_URL = "https://crt.sh/"
    VIRUSTOTAL_API_URL = "https://www.virustotal.com/vtapi/v2/domain/report"
    SECURITY_TRAILS_API_URL = "https://api.securitytrails.com/v1/domain"
    SHODAN_API_URL = "https://api.shodan.io/dns/domain"
    CHAOS_API_URL = "https://dns.projectdiscovery.io/dns"
    ALIENVAULT_API_URL = "https://otx.alienvault.com/api/v1/indicators/domain"
    
    # API Keys (optional - set via environment variables)
    VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY', '')
    SECURITY_TRAILS_API_KEY = os.getenv('SECURITY_TRAILS_API_KEY', '')
    SHODAN_API_KEY = os.getenv('SHODAN_API_KEY', '')
    CHAOS_API_KEY = os.getenv('CHAOS_API_KEY', '')
    
    USER_AGENT = "SubdomainMonitor/2.0 (Advanced Multi-Domain Scanner)"
    
    # Notification Settings
    ENABLE_TELEGRAM = True
    ENABLE_CONSOLE_LOG = True
    MAX_NOTIFICATION_BATCH = 20
    
    # Advanced Features
    ENABLE_WILDCARD_DETECTION = True
    ENABLE_SUBDOMAIN_VALIDATION = True
    ENABLE_IP_RESOLUTION = True
    ENABLE_PORT_SCANNING = False
    COMMON_PORTS = [80, 443, 8080, 8443, 3000, 8000]
    
    # Filtering Options
    EXCLUDED_SUBDOMAINS = [
        '*.local',
        '*.internal',
        '*.test',
        '*.staging'
    ]
    
    # Rate Limiting
    RATE_LIMIT_DELAY = 0.1  # Delay between requests in seconds
    BURST_SIZE = 10  # Number of requests allowed in burst
