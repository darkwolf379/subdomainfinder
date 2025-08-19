#!/usr/bin/env python3
"""
Automated subdomain monitor with Telegram notifications
Runs continuously and monitors domains for new subdomains
"""
import asyncio
import logging
import time
from datetime import datetime
from config import Config
from database import DatabaseManager
from telegram_bot import TelegramNotifier
from scanner import SubdomainScanner

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AutoMonitor:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager(self.config.DATABASE_FILE)
        self.notifier = TelegramNotifier(self.config.TELEGRAM_BOT_TOKEN, self.config.TELEGRAM_CHAT_ID)
        self.running = False
        
    async def add_domain(self, domain: str):
        """Add a domain to monitor"""
        domain_id = self.db.add_domain(domain)
        await self.notifier.send_message(f"➕ Added domain for monitoring: {domain}")
        print(f"Added domain: {domain} (ID: {domain_id})")
        return domain_id
        
    async def scan_domain(self, domain: str):
        """Scan a single domain and notify of results"""
        print(f"\n🔍 Scanning {domain}...")
        start_time = time.time()
        
        try:
            async with SubdomainScanner(self.config) as scanner:
                # Get subdomains from crt.sh
                subdomains = await scanner.get_crtsh_subdomains(domain)
                
                # Get detailed info for new subdomains
                subdomain_data = []
                for subdomain in subdomains:
                    subdomain_data.append({
                        'subdomain': subdomain,
                        'ip_address': None,
                        'certificate_info': {}
                    })
                
                # Save to database
                domain_id = self.db.add_domain(domain)
                new_count = self.db.add_subdomains(domain_id, subdomain_data)
                self.db.update_domain_stats(domain_id)
                
                scan_duration = time.time() - start_time
                self.db.add_scan_history(domain_id, len(subdomains), new_count, scan_duration, 'success')
                
                # Send notification if new subdomains found
                if new_count > 0:
                    message = f"""
🚨 NEW SUBDOMAINS FOUND!

🌐 Domain: {domain}
🆕 New subdomains: {new_count}
📊 Total subdomains: {len(subdomains)}
⏱️ Scan time: {scan_duration:.1f}s

🔍 New subdomains:
{chr(10).join([f"• {data['subdomain']}" for data in subdomain_data[-new_count:]])}
                    """
                    await self.notifier.send_message(message.strip())
                
                print(f"✅ Scan completed: {len(subdomains)} total, {new_count} new")
                return len(subdomains), new_count
                
        except Exception as e:
            error_msg = f"❌ Error scanning {domain}: {str(e)}"
            print(error_msg)
            await self.notifier.send_message(error_msg)
            return 0, 0
    
    async def monitor_domains(self):
        """Monitor all domains continuously"""
        self.running = True
        await self.notifier.send_message("🤖 SubdomainFinder started monitoring!")
        
        while self.running:
            try:
                # Get all active domains
                domains = self.db.get_domains(active_only=True)
                
                if not domains:
                    print("No domains to monitor. Add domains first.")
                    await asyncio.sleep(60)
                    continue
                
                print(f"\n📡 Monitoring {len(domains)} domains...")
                
                # Scan each domain
                for domain_id, domain in domains:
                    if not self.running:
                        break
                        
                    await self.scan_domain(domain)
                    await asyncio.sleep(5)  # Small delay between scans
                
                # Wait for next cycle
                print(f"💤 Waiting {self.config.CHECK_INTERVAL} seconds until next scan...")
                await asyncio.sleep(self.config.CHECK_INTERVAL)
                
            except Exception as e:
                error_msg = f"❌ Monitor error: {str(e)}"
                print(error_msg)
                await self.notifier.send_message(error_msg)
                await asyncio.sleep(60)
    
    async def interactive_mode(self):
        """Interactive command mode"""
        await self.notifier.send_message("🎮 SubdomainFinder ready! Use commands to interact.")
        
        while True:
            try:
                print("\n" + "="*50)
                print("🤖 SubdomainFinder Interactive Mode")
                print("="*50)
                print("Commands:")
                print("1. add <domain>     - Add domain to monitor")
                print("2. scan <domain>    - Scan domain once") 
                print("3. list             - List monitored domains")
                print("4. start            - Start continuous monitoring")
                print("5. stop             - Stop monitoring")
                print("6. stats <domain>   - Show domain statistics")
                print("7. quit             - Exit application")
                
                cmd = input("\n📱 Command: ").strip().lower()
                
                if cmd.startswith('add '):
                    domain = cmd[4:].strip()
                    if domain:
                        await self.add_domain(domain)
                    else:
                        print("❌ Please specify a domain")
                
                elif cmd.startswith('scan '):
                    domain = cmd[5:].strip()
                    if domain:
                        await self.scan_domain(domain)
                    else:
                        print("❌ Please specify a domain")
                
                elif cmd == 'list':
                    domains = self.db.get_domains()
                    if domains:
                        print(f"\n📋 Monitored domains ({len(domains)}):")
                        for domain_id, domain in domains:
                            stats = self.db.get_domain_stats(domain)
                            print(f"  • {domain} - {stats.get('current_subdomains', 0)} subdomains")
                    else:
                        print("📭 No domains being monitored")
                
                elif cmd == 'start':
                    print("🚀 Starting continuous monitoring...")
                    monitor_task = asyncio.create_task(self.monitor_domains())
                    await monitor_task
                
                elif cmd == 'stop':
                    self.running = False
                    await self.notifier.send_message("⏹️ Monitoring stopped")
                    print("⏹️ Monitoring stopped")
                
                elif cmd.startswith('stats '):
                    domain = cmd[6:].strip()
                    if domain:
                        stats = self.db.get_domain_stats(domain)
                        if stats:
                            print(f"\n📊 Statistics for {domain}:")
                            print(f"  • Total subdomains: {stats.get('current_subdomains', 0)}")
                            print(f"  • Added: {stats.get('added_date', 'Unknown')}")
                            print(f"  • Last checked: {stats.get('last_checked', 'Never')}")
                        else:
                            print(f"❌ Domain {domain} not found")
                    else:
                        print("❌ Please specify a domain")
                
                elif cmd == 'quit':
                    self.running = False
                    await self.notifier.send_message("👋 SubdomainFinder shutting down")
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Unknown command. Type a number or command.")
                    
            except KeyboardInterrupt:
                self.running = False
                print("\n\n👋 Shutting down...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

async def main():
    """Main function"""
    monitor = AutoMonitor()
    
    # Send startup notification
    await monitor.notifier.send_message("🚀 SubdomainFinder is starting up...")
    
    # Start interactive mode
    await monitor.interactive_mode()

if __name__ == "__main__":
    asyncio.run(main())
