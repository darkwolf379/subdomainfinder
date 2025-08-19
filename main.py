"""
Main Subdomain Monitor Application
Advanced multi-domain subdomain finder with real-time monitoring and Telegram notifications
"""
import asyncio
import logging
import signal
import sys
import os
from datetime import datetime
from typing import Dict, Any

from config import Config
from database import DatabaseManager
from telegram_bot import TelegramNotifier
from bot_commands import TelegramCommandHandler
from scanner import SubdomainScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('subdomain_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SubdomainMonitor:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager(self.config.DATABASE_FILE)
        self.notifier = None
        self.command_handler = None
        self.running = False
        self.tasks = []
        
    async def initialize(self):
        """Initialize the application"""
        logger.info("🚀 Initializing Advanced Subdomain Monitor...")
        
        # Validate configuration
        if not self._validate_config():
            logger.error("❌ Configuration validation failed")
            return False
        
        # Initialize Telegram components
        self.notifier = TelegramNotifier(
            self.config.TELEGRAM_BOT_TOKEN,
            self.config.TELEGRAM_CHAT_ID
        )
        
        self.command_handler = TelegramCommandHandler(
            self.config, self.db, self.notifier
        )
        
        logger.info("✅ Application initialized successfully")
        return True
    
    def _validate_config(self) -> bool:
        """Validate configuration settings"""
        if self.config.TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            logger.error("❌ Please set TELEGRAM_BOT_TOKEN in environment or config")
            return False
        
        if self.config.TELEGRAM_CHAT_ID == 'YOUR_CHAT_ID_HERE':
            logger.error("❌ Please set TELEGRAM_CHAT_ID in environment or config")
            return False
        
        return True
    
    async def start_webhook_server(self):
        """Start webhook server for Telegram bot (for production use)"""
        from aiohttp import web, ClientSession
        
        app = web.Application()
        
        async def webhook_handler(request):
            try:
                data = await request.json()
                result = await self.command_handler.handle_webhook(data)
                return web.json_response(result)
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                return web.json_response({'status': 'error', 'message': str(e)})
        
        app.router.add_post('/webhook', webhook_handler)
        
        # Health check endpoint
        async def health_check(request):
            return web.json_response({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0'
            })
        
        app.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        
        logger.info("🌐 Webhook server started on http://0.0.0.0:8080")
        return runner
    
    async def start_polling(self):
        """Start polling mode for development/testing"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            offset = 0
            
            while self.running:
                try:
                    url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/getUpdates"
                    params = {
                        'offset': offset,
                        'timeout': 30,
                        'limit': 100
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('ok') and data.get('result'):
                                for update in data['result']:
                                    await self.command_handler.handle_webhook(update)
                                    offset = update['update_id'] + 1
                        else:
                            logger.error(f"Failed to get updates: {response.status}")
                            await asyncio.sleep(5)
                            
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Polling error: {e}")
                    await asyncio.sleep(5)
    
    async def run_interactive_mode(self):
        """Run in interactive command-line mode"""
        logger.info("🎮 Starting interactive mode...")
        logger.info("Type 'help' for available commands or 'quit' to exit")
        
        while self.running:
            try:
                command = await asyncio.get_event_loop().run_in_executor(
                    None, input, "\n📱 SubdomainMonitor> "
                )
                
                command = command.strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    break
                elif command == 'help':
                    self._print_interactive_help()
                elif command.startswith('add '):
                    domain = command[4:].strip()
                    await self._interactive_add_domain(domain)
                elif command.startswith('scan '):
                    domain = command[5:].strip()
                    await self._interactive_scan_domain(domain)
                elif command == 'list':
                    await self._interactive_list_domains()
                elif command.startswith('stats '):
                    domain = command[6:].strip()
                    await self._interactive_domain_stats(domain)
                elif command == 'startmon':
                    await self._interactive_start_monitoring()
                elif command == 'stopmon':
                    await self._interactive_stop_monitoring()
                elif command == 'status':
                    await self._interactive_status()
                else:
                    print(f"❓ Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                logger.error(f"Interactive mode error: {e}")
    
    def _print_interactive_help(self):
        """Print interactive mode help"""
        help_text = """
🎮 Interactive Mode Commands:

📊 Domain Management:
  add <domain>      - Add domain to monitoring
  scan <domain>     - Scan specific domain
  list              - List all monitored domains
  stats <domain>    - Show domain statistics

🔄 Monitoring Control:
  startmon          - Start automatic monitoring
  stopmon           - Stop automatic monitoring
  status            - Show current status

⚙️ System:
  help              - Show this help
  quit/exit/q       - Exit application
        """
        print(help_text)
    
    async def _interactive_add_domain(self, domain: str):
        """Add domain in interactive mode"""
        if not domain:
            print("❌ Please specify a domain")
            return
        
        domain_id = self.db.add_domain(domain)
        if domain_id:
            print(f"✅ Domain added: {domain} (ID: {domain_id})")
            
            # Perform initial scan
            print(f"🔍 Performing initial scan for {domain}...")
            async with SubdomainScanner(self.config) as scanner:
                subdomains, duration = await scanner.scan_domain_fast(domain)
            
            new_count = self.db.add_subdomains(domain_id, subdomains)
            self.db.update_domain_stats(domain_id)
            
            print(f"✅ Scan completed: {len(subdomains)} subdomains found in {duration:.2f}s")
        else:
            print(f"❌ Failed to add domain or already exists: {domain}")
    
    async def _interactive_scan_domain(self, domain: str):
        """Scan domain in interactive mode"""
        if not domain:
            print("❌ Please specify a domain")
            return
        
        # Check if domain exists
        domains = dict((v, k) for k, v in self.db.get_domains())
        if domain not in domains:
            print(f"❌ Domain not in monitoring list: {domain}")
            return
        
        print(f"🔍 Scanning {domain}...")
        
        domain_id = domains[domain]
        existing_subdomains = set(
            sub['subdomain'] for sub in self.db.get_subdomains(domain_id)
        )
        
        async with SubdomainScanner(self.config) as scanner:
            subdomains, duration = await scanner.scan_domain_fast(domain)
        
        new_count = self.db.add_subdomains(domain_id, subdomains)
        self.db.update_domain_stats(domain_id)
        
        print(f"✅ Scan completed:")
        print(f"   📊 Total subdomains: {len(subdomains)}")
        print(f"   🆕 New subdomains: {new_count}")
        print(f"   ⚡ Duration: {duration:.2f}s")
        
        # Show new subdomains
        if new_count > 0:
            new_subdomains = [
                sub for sub in subdomains 
                if sub['subdomain'] not in existing_subdomains
            ]
            print(f"\n🆕 New subdomains found:")
            for sub in new_subdomains[:10]:  # Show first 10
                print(f"   • {sub['subdomain']}")
                if sub.get('ip_address'):
                    print(f"     IP: {sub['ip_address']}")
            
            if len(new_subdomains) > 10:
                print(f"   ... and {len(new_subdomains) - 10} more")
    
    async def _interactive_list_domains(self):
        """List domains in interactive mode"""
        domains = self.db.get_domains()
        
        if not domains:
            print("📝 No domains are currently being monitored")
        else:
            print(f"📋 Monitored Domains ({len(domains)}):")
            for domain_id, domain in domains:
                stats = self.db.get_domain_stats(domain)
                subdomain_count = stats.get('total_subdomains', 0)
                last_checked = stats.get('last_checked', 'Never')
                print(f"   🌐 {domain} ({subdomain_count} subdomains, last: {last_checked})")
    
    async def _interactive_domain_stats(self, domain: str):
        """Show domain stats in interactive mode"""
        if not domain:
            print("❌ Please specify a domain")
            return
        
        stats = self.db.get_domain_stats(domain)
        
        if not stats:
            print(f"❌ Domain not found: {domain}")
            return
        
        print(f"\n📊 Statistics for {domain}:")
        print(f"   🗓️ Added: {stats.get('added_date', 'Unknown')}")
        print(f"   🔄 Last Checked: {stats.get('last_checked', 'Never')}")
        print(f"   📈 Total Subdomains: {stats.get('total_subdomains', 0)}")
        print(f"   ✅ Active Subdomains: {stats.get('current_subdomains', 0)}")
        
        recent_scans = stats.get('recent_scans', [])
        if recent_scans:
            print(f"\n📋 Recent Scans:")
            for scan in recent_scans[:5]:
                scan_date, found, new, duration, status = scan
                print(f"   • {scan_date}: {found} found, {new} new ({duration:.1f}s)")
    
    async def _interactive_start_monitoring(self):
        """Start monitoring in interactive mode"""
        if self.command_handler.monitoring_active:
            print("✅ Monitoring is already active!")
            return
        
        await self.command_handler._handle_start_monitoring([])
        print("🚀 Monitoring started!")
    
    async def _interactive_stop_monitoring(self):
        """Stop monitoring in interactive mode"""
        if not self.command_handler.monitoring_active:
            print("❌ Monitoring is not active!")
            return
        
        await self.command_handler._handle_stop_monitoring([])
        print("⏹️ Monitoring stopped!")
    
    async def _interactive_status(self):
        """Show status in interactive mode"""
        domains = self.db.get_domains()
        
        print(f"\n📊 Monitor Status:")
        print(f"   🔄 Monitoring: {'Active' if self.command_handler.monitoring_active else 'Inactive'}")
        print(f"   🌐 Domains: {len(domains)}")
        print(f"   ⚙️ Check Interval: {self.config.CHECK_INTERVAL}s")
        print(f"   🚀 Max Concurrent: {self.config.MAX_CONCURRENT_REQUESTS}")
        print(f"   ⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def run(self, mode: str = 'interactive'):
        """Run the application in specified mode"""
        if not await self.initialize():
            return False
        
        self.running = True
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info("🛑 Received shutdown signal")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            async with self.notifier:
                if mode == 'webhook':
                    runner = await self.start_webhook_server()
                    await self.notifier.send_message("🚀 Subdomain Monitor started in webhook mode!")
                    
                    # Keep running until shutdown
                    while self.running:
                        await asyncio.sleep(1)
                    
                    await runner.cleanup()
                    
                elif mode == 'polling':
                    await self.notifier.send_message("🚀 Subdomain Monitor started in polling mode!")
                    await self.start_polling()
                    
                elif mode == 'interactive':
                    await self.run_interactive_mode()
                
                else:
                    logger.error(f"❌ Unknown mode: {mode}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Application error: {e}")
            return False
        
        finally:
            logger.info("🛑 Shutting down...")
            if self.command_handler and self.command_handler.monitoring_active:
                await self.command_handler._handle_stop_monitoring([])
        
        return True

async def main():
    """Main application entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Subdomain Monitor')
    parser.add_argument(
        '--mode', 
        choices=['interactive', 'polling', 'webhook'], 
        default='interactive',
        help='Application mode (default: interactive)'
    )
    
    args = parser.parse_args()
    
    monitor = SubdomainMonitor()
    success = await monitor.run(args.mode)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
