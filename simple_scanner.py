#!/usr/bin/env python3
"""
Simple Subdomain Scanner with Telegram Notifications
A streamlined tool for finding subdomains with minimal complexity
"""
import asyncio
import aiohttp
import json
import re
import sys
import time
from datetime import datetime
from typing import List, Dict, Set
from urllib.parse import quote

# Configuration - Simple and direct
TELEGRAM_API_TOKEN = "7799744103:AAHxdjdV8ycmCcf9AgSA-6C3NMWLFWhg9R0"
TELEGRAM_CHAT_ID = "6247017127"
USER_AGENT = "SimpleSubdomainScanner/1.0"

class SimpleSubdomainScanner:
    """Simple, efficient subdomain scanner using multiple API sources"""
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _is_valid_subdomain(self, subdomain: str, domain: str) -> bool:
        """Validate if a subdomain is legitimate"""
        if not subdomain:
            return False
        
        # Remove wildcards
        if subdomain.startswith('*.'):
            subdomain = subdomain[2:]
        
        # Must end with the domain (but not be exactly equal unless it's the root domain)
        if not subdomain.endswith(domain):
            return False
        
        # If it's exactly the domain, that's valid
        if subdomain == domain:
            return True
        
        # Must have a dot before the domain part (proper subdomain)
        domain_start = subdomain.rfind(domain)
        if domain_start > 0 and subdomain[domain_start - 1] != '.':
            return False
        
        # Basic character validation
        if not re.match(r'^[a-zA-Z0-9.-]+$', subdomain):
            return False
        
        # Check for consecutive dots or invalid positions
        if '..' in subdomain or subdomain.startswith('.') or subdomain.endswith('.'):
            return False
        
        return True
    
    async def get_crtsh_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from crt.sh API"""
        subdomains = set()
        
        try:
            # Use the correct crt.sh API URL format
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for cert in data:
                        # Extract common name
                        if cert.get('common_name'):
                            cn = cert['common_name'].lower().strip()
                            if self._is_valid_subdomain(cn, domain):
                                subdomains.add(cn)
                        
                        # Extract subject alternative names
                        if cert.get('name_value'):
                            names = cert['name_value'].split('\n')
                            for name in names:
                                name = name.lower().strip()
                                if self._is_valid_subdomain(name, domain):
                                    subdomains.add(name)
                
                else:
                    print(f"⚠️  crt.sh returned status {response.status}")
                    
        except Exception as e:
            print(f"❌ Error querying crt.sh: {e}")
        
        return subdomains
    
    async def get_hackertarget_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from HackerTarget API (free, no key required)"""
        subdomains = set()
        
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # Parse the response (format: subdomain,ip)
                    for line in text.split('\n'):
                        if ',' in line:
                            subdomain = line.split(',')[0].strip()
                            if self._is_valid_subdomain(subdomain, domain):
                                subdomains.add(subdomain)
                                
        except Exception as e:
            print(f"❌ Error querying HackerTarget: {e}")
        
        return subdomains
    
    async def get_alienvault_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from AlienVault OTX (free, no key required)"""
        subdomains = set()
        
        try:
            url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for record in data.get('passive_dns', []):
                        subdomain = record.get('hostname', '').lower().strip()
                        if self._is_valid_subdomain(subdomain, domain):
                            subdomains.add(subdomain)
                            
        except Exception as e:
            print(f"❌ Error querying AlienVault: {e}")
        
        return subdomains
    
    async def scan_domain(self, domain: str) -> List[str]:
        """Scan domain using multiple sources"""
        print(f"🔍 Scanning {domain}...")
        start_time = time.time()
        
        # Get subdomains from multiple sources concurrently
        tasks = [
            self.get_crtsh_subdomains(domain),
            self.get_hackertarget_subdomains(domain),
            self.get_alienvault_subdomains(domain)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all results
        all_subdomains = set()
        for result in results:
            if isinstance(result, set):
                all_subdomains.update(result)
        
        # Convert to sorted list
        subdomains = sorted(list(all_subdomains))
        
        scan_duration = time.time() - start_time
        
        print(f"✅ Found {len(subdomains)} subdomains in {scan_duration:.2f}s")
        
        return subdomains

class TelegramNotifier:
    """Simple Telegram notification sender"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(self, message: str) -> bool:
        """Send message to Telegram"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendMessage"
                data = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        print("📱 Telegram notification sent!")
                        return True
                    else:
                        print(f"❌ Failed to send Telegram notification: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            return False
    
    async def send_scan_results(self, domain: str, subdomains: List[str]) -> bool:
        """Send scan results to Telegram"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"🎯 <b>Subdomain Scan Results</b>\n\n"
        message += f"🌐 <b>Domain:</b> <code>{domain}</code>\n"
        message += f"📊 <b>Subdomains Found:</b> {len(subdomains)}\n"
        message += f"⏰ <b>Scan Time:</b> {timestamp}\n\n"
        
        if subdomains:
            message += "<b>📋 Subdomains:</b>\n"
            
            # Show first 20 subdomains to avoid message length limits
            for subdomain in subdomains[:20]:
                message += f"• <code>{subdomain}</code>\n"
            
            if len(subdomains) > 20:
                message += f"\n... and {len(subdomains) - 20} more subdomains"
        else:
            message += "❌ No subdomains found"
        
        return await self.send_message(message)

async def main():
    """Main function - simple and direct"""
    print("🚀 Simple Subdomain Scanner with Telegram Integration")
    print("=" * 60)
    
    # Get domain from command line or prompt user
    if len(sys.argv) > 1:
        domain = sys.argv[1].lower().strip()
    else:
        domain = input("Enter domain to scan: ").lower().strip()
    
    if not domain:
        print("❌ Please provide a domain")
        return
    
    # Remove protocol if present
    if domain.startswith(('http://', 'https://')):
        domain = domain.split('://', 1)[1]
    
    # Remove www. if present
    if domain.startswith('www.'):
        domain = domain[4:]
    
    print(f"🎯 Target domain: {domain}")
    print()
    
    try:
        # Scan for subdomains
        async with SimpleSubdomainScanner() as scanner:
            subdomains = await scanner.scan_domain(domain)
        
        # Display results
        print("\n📋 Results:")
        print("-" * 40)
        
        if subdomains:
            for i, subdomain in enumerate(subdomains, 1):
                print(f"{i:3d}. {subdomain}")
            
            print(f"\n✅ Total: {len(subdomains)} subdomains found")
            
            # Send Telegram notification
            if TELEGRAM_API_TOKEN and TELEGRAM_CHAT_ID:
                print("\n📱 Sending Telegram notification...")
                notifier = TelegramNotifier(TELEGRAM_API_TOKEN, TELEGRAM_CHAT_ID)
                await notifier.send_scan_results(domain, subdomains)
            
        else:
            print("❌ No subdomains found")
    
    except KeyboardInterrupt:
        print("\n⏹️  Scan cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during scan: {e}")

if __name__ == "__main__":
    asyncio.run(main())