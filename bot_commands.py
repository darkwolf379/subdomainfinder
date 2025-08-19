"""
Telegram Bot Commands Handler for Subdomain Monitor
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from telegram_bot import TelegramNotifier
from database import DatabaseManager
from scanner import SubdomainScanner
from config import Config

class TelegramCommandHandler:
    def __init__(self, config: Config, db_manager: DatabaseManager, notifier: TelegramNotifier):
        self.config = config
        self.db = db_manager
        self.notifier = notifier
        self.monitoring_active = False
        self.monitoring_task = None
        
    async def handle_webhook(self, update: Dict) -> Dict:
        """Handle incoming webhook from Telegram"""
        try:
            if 'message' not in update:
                return {'status': 'ok'}
            
            message = update['message']
            chat_id = str(message['chat']['id'])
            
            # Check if this is the authorized chat
            if chat_id != self.config.TELEGRAM_CHAT_ID:
                await self.notifier.send_message("❌ Unauthorized access")
                return {'status': 'unauthorized'}
            
            text = message.get('text', '').strip()
            
            if not text.startswith('/'):
                return {'status': 'ok'}
            
            # Parse command and arguments
            parts = text.split()
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Route to appropriate handler
            await self._route_command(command, args)
            
            return {'status': 'ok'}
            
        except Exception as e:
            logging.error(f"Error handling webhook: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _route_command(self, command: str, args: List[str]):
        """Route command to appropriate handler"""
        handlers = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/add': self._handle_add_domain,
            '/remove': self._handle_remove_domain,
            '/list': self._handle_list_domains,
            '/scan': self._handle_scan_domain,
            '/scanall': self._handle_scan_all,
            '/stats': self._handle_domain_stats,
            '/recent': self._handle_recent_subdomains,
            '/history': self._handle_scan_history,
            '/status': self._handle_status,
            '/config': self._handle_config,
            '/stopmon': self._handle_stop_monitoring,
            '/startmon': self._handle_start_monitoring,
        }
        
        handler = handlers.get(command)
        if handler:
            try:
                await handler(args)
            except Exception as e:
                logging.error(f"Error handling command {command}: {e}")
                await self.notifier.send_message(f"❌ Error executing command: {str(e)}")
        else:
            await self.notifier.send_message(
                f"❓ Unknown command: {command}\n"
                f"Use /help to see available commands."
            )
    
    async def _handle_start(self, args: List[str]):
        """Handle /start command"""
        message = """🚀 <b>Welcome to Advanced Subdomain Monitor!</b>

🔍 This bot monitors domains for new subdomains using crt.sh API and provides real-time notifications.

<b>Quick Start:</b>
1. Add a domain: <code>/add example.com</code>
2. Start monitoring: <code>/startmon</code>
3. Get notifications when new subdomains are found!

Use /help for all available commands.
        """
        await self.notifier.send_message(message)
    
    async def _handle_help(self, args: List[str]):
        """Handle /help command"""
        await self.notifier.send_help_message()
    
    async def _handle_add_domain(self, args: List[str]):
        """Handle /add command"""
        if not args:
            await self.notifier.send_message(
                "❌ Please specify a domain to add.\n"
                "Usage: <code>/add example.com</code>"
            )
            return
        
        domain = args[0].lower().strip()
        
        # Basic domain validation
        if not self._is_valid_domain(domain):
            await self.notifier.send_message(
                f"❌ Invalid domain format: <code>{domain}</code>\n"
                f"Please enter a valid domain (e.g., example.com)"
            )
            return
        
        # Add to database
        domain_id = self.db.add_domain(domain)
        if domain_id:
            await self.notifier.send_message(
                f"✅ Domain added successfully!\n"
                f"🌐 <b>Domain:</b> <code>{domain}</code>\n"
                f"🆔 <b>ID:</b> {domain_id}\n\n"
                f"Use <code>/scan {domain}</code> to perform initial scan."
            )
            
            # Perform initial scan
            await self._perform_domain_scan(domain)
        else:
            await self.notifier.send_message(
                f"❌ Failed to add domain or domain already exists: <code>{domain}</code>"
            )
    
    async def _handle_remove_domain(self, args: List[str]):
        """Handle /remove command"""
        if not args:
            await self.notifier.send_message(
                "❌ Please specify a domain to remove.\n"
                "Usage: <code>/remove example.com</code>"
            )
            return
        
        domain = args[0].lower().strip()
        
        if self.db.remove_domain(domain):
            await self.notifier.send_message(
                f"✅ Domain removed from monitoring: <code>{domain}</code>"
            )
        else:
            await self.notifier.send_message(
                f"❌ Domain not found: <code>{domain}</code>"
            )
    
    async def _handle_list_domains(self, args: List[str]):
        """Handle /list command"""
        domains = self.db.get_domains()
        await self.notifier.send_domain_list(domains)
    
    async def _handle_scan_domain(self, args: List[str]):
        """Handle /scan command"""
        if not args:
            await self.notifier.send_message(
                "❌ Please specify a domain to scan.\n"
                "Usage: <code>/scan example.com</code>"
            )
            return
        
        domain = args[0].lower().strip()
        
        # Check if domain is in monitoring list
        domains = dict(self.db.get_domains())
        if domain not in domains.values():
            await self.notifier.send_message(
                f"❌ Domain not in monitoring list: <code>{domain}</code>\n"
                f"Use <code>/add {domain}</code> to add it first."
            )
            return
        
        await self.notifier.send_message(f"🔍 Starting scan for <code>{domain}</code>...")
        await self._perform_domain_scan(domain)
    
    async def _handle_scan_all(self, args: List[str]):
        """Handle /scanall command"""
        domains = self.db.get_domains()
        
        if not domains:
            await self.notifier.send_message("❌ No domains to scan.")
            return
        
        await self.notifier.send_message(f"🔍 Starting scan for {len(domains)} domains...")
        
        for domain_id, domain in domains:
            await self._perform_domain_scan(domain)
            await asyncio.sleep(1)  # Small delay between scans
    
    async def _handle_domain_stats(self, args: List[str]):
        """Handle /stats command"""
        if not args:
            await self.notifier.send_message(
                "❌ Please specify a domain.\n"
                "Usage: <code>/stats example.com</code>"
            )
            return
        
        domain = args[0].lower().strip()
        stats = self.db.get_domain_stats(domain)
        await self.notifier.send_domain_stats(stats)
    
    async def _handle_recent_subdomains(self, args: List[str]):
        """Handle /recent command"""
        if not args:
            await self.notifier.send_message(
                "❌ Please specify a domain.\n"
                "Usage: <code>/recent example.com</code>"
            )
            return
        
        domain = args[0].lower().strip()
        
        # Get domain ID
        domains = dict((v, k) for k, v in self.db.get_domains())
        if domain not in domains:
            await self.notifier.send_message(f"❌ Domain not found: <code>{domain}</code>")
            return
        
        domain_id = domains[domain]
        subdomains = self.db.get_subdomains(domain_id)
        
        if not subdomains:
            await self.notifier.send_message(f"❌ No subdomains found for <code>{domain}</code>")
            return
        
        message = f"📋 <b>Recent Subdomains for {domain}</b>\n\n"
        
        for i, sub in enumerate(subdomains[:15]):  # Limit to 15
            subdomain = sub['subdomain']
            first_seen = sub['first_seen']
            ip = sub.get('ip_address', 'N/A')
            
            message += f"🔸 <code>{subdomain}</code>\n"
            message += f"   📅 First seen: {first_seen}\n"
            if ip and ip != 'N/A':
                message += f"   📍 IP: <code>{ip}</code>\n"
            message += "\n"
        
        if len(subdomains) > 15:
            message += f"... and {len(subdomains) - 15} more subdomains\n"
        
        await self.notifier.send_message(message)
    
    async def _handle_scan_history(self, args: List[str]):
        """Handle /history command"""
        if not args:
            await self.notifier.send_message(
                "❌ Please specify a domain.\n"
                "Usage: <code>/history example.com</code>"
            )
            return
        
        domain = args[0].lower().strip()
        stats = self.db.get_domain_stats(domain)
        
        if not stats:
            await self.notifier.send_message(f"❌ Domain not found: <code>{domain}</code>")
            return
        
        recent_scans = stats.get('recent_scans', [])
        
        if not recent_scans:
            await self.notifier.send_message(f"❌ No scan history for <code>{domain}</code>")
            return
        
        message = f"📊 <b>Scan History for {domain}</b>\n\n"
        
        for scan in recent_scans:
            scan_date, found, new, duration, status = scan
            message += f"📅 <b>{scan_date}</b>\n"
            message += f"   📊 Found: {found} subdomains\n"
            message += f"   🆕 New: {new} subdomains\n"
            message += f"   ⚡ Duration: {duration:.1f}s\n"
            message += f"   ✅ Status: {status}\n\n"
        
        await self.notifier.send_message(message)
    
    async def _handle_status(self, args: List[str]):
        """Handle /status command"""
        domains = self.db.get_domains()
        
        message = f"📊 <b>Monitor Status</b>\n\n"
        message += f"🔄 <b>Monitoring:</b> {'Active' if self.monitoring_active else 'Inactive'}\n"
        message += f"🌐 <b>Domains:</b> {len(domains)}\n"
        message += f"⚙️ <b>Check Interval:</b> {self.config.CHECK_INTERVAL}s\n"
        message += f"🚀 <b>Max Concurrent:</b> {self.config.MAX_CONCURRENT_REQUESTS}\n"
        message += f"⏰ <b>Current Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        await self.notifier.send_message(message)
    
    async def _handle_config(self, args: List[str]):
        """Handle /config command"""
        message = f"⚙️ <b>Configuration</b>\n\n"
        message += f"🔄 <b>Check Interval:</b> {self.config.CHECK_INTERVAL}s\n"
        message += f"🚀 <b>Max Concurrent:</b> {self.config.MAX_CONCURRENT_REQUESTS}\n"
        message += f"⏱️ <b>Request Timeout:</b> {self.config.REQUEST_TIMEOUT}s\n"
        message += f"🔁 <b>Retry Attempts:</b> {self.config.RETRY_ATTEMPTS}\n"
        message += f"💬 <b>Telegram Notifications:</b> {'Enabled' if self.config.ENABLE_TELEGRAM else 'Disabled'}\n"
        message += f"🔍 <b>Subdomain Validation:</b> {'Enabled' if self.config.ENABLE_SUBDOMAIN_VALIDATION else 'Disabled'}\n"
        message += f"🌐 <b>IP Resolution:</b> {'Enabled' if self.config.ENABLE_IP_RESOLUTION else 'Disabled'}\n"
        
        await self.notifier.send_message(message)
    
    async def _handle_start_monitoring(self, args: List[str]):
        """Handle /startmon command"""
        if self.monitoring_active:
            await self.notifier.send_message("✅ Monitoring is already active!")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        await self.notifier.send_message(
            f"🚀 <b>Monitoring Started!</b>\n"
            f"🔄 Check interval: {self.config.CHECK_INTERVAL}s\n"
            f"📊 You'll receive notifications for new subdomains."
        )
    
    async def _handle_stop_monitoring(self, args: List[str]):
        """Handle /stopmon command"""
        if not self.monitoring_active:
            await self.notifier.send_message("❌ Monitoring is not active!")
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        await self.notifier.send_message("⏹️ <b>Monitoring Stopped!</b>")
    
    async def _perform_domain_scan(self, domain: str):
        """Perform a comprehensive scan for a domain"""
        try:
            # Get domain ID
            domains = dict((v, k) for k, v in self.db.get_domains())
            if domain not in domains:
                await self.notifier.send_message(f"❌ Domain not in monitoring list: <code>{domain}</code>")
                return
            
            domain_id = domains[domain]
            
            # Get existing subdomains
            existing_subdomains = set(
                sub['subdomain'] for sub in self.db.get_subdomains(domain_id)
            )
            
            # Perform scan
            async with SubdomainScanner(self.config) as scanner:
                subdomains, scan_duration = await scanner.scan_domain_fast(domain)
            
            # Add new subdomains to database
            new_count = self.db.add_subdomains(domain_id, subdomains)
            
            # Update domain stats
            self.db.update_domain_stats(domain_id)
            
            # Add scan history
            self.db.add_scan_history(
                domain_id, len(subdomains), new_count, scan_duration, 'completed'
            )
            
            # Send notifications
            if new_count > 0:
                new_subdomains = [
                    sub for sub in subdomains 
                    if sub['subdomain'] not in existing_subdomains
                ]
                await self.notifier.send_new_subdomains_alert(domain, new_subdomains)
            
            await self.notifier.send_scan_summary(domain, len(subdomains), new_count, scan_duration)
            
        except Exception as e:
            logging.error(f"Error scanning domain {domain}: {e}")
            await self.notifier.send_error_alert(domain, str(e))
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                domains = self.db.get_domains()
                
                if domains:
                    logging.info(f"Starting monitoring cycle for {len(domains)} domains")
                    
                    for domain_id, domain in domains:
                        if not self.monitoring_active:
                            break
                        
                        await self._perform_domain_scan(domain)
                        await asyncio.sleep(5)  # Small delay between domain scans
                
                # Wait for next cycle
                await asyncio.sleep(self.config.CHECK_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain format"""
        import re
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, domain)) and len(domain) <= 253
