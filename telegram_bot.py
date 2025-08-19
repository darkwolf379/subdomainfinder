"""
Telegram bot integration for subdomain monitoring notifications
"""
import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    return True
                else:
                    logging.error(f"Failed to send Telegram message: {response.status}")
                    return False
                    
        except Exception as e:
            logging.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_new_subdomains_alert(self, domain: str, new_subdomains: List[Dict]) -> bool:
        """Send alert for new subdomains found"""
        if not new_subdomains:
            return True
            
        emoji_map = {
            'high': '🔴',
            'medium': '🟡', 
            'low': '🟢',
            'info': 'ℹ️'
        }
        
        message = f"🎯 <b>New Subdomains Found!</b>\n"
        message += f"🌐 <b>Domain:</b> <code>{domain}</code>\n"
        message += f"📊 <b>Count:</b> {len(new_subdomains)}\n"
        message += f"⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for i, subdomain_data in enumerate(new_subdomains[:10]):  # Limit to 10 for readability
            subdomain = subdomain_data.get('subdomain', 'Unknown')
            ip = subdomain_data.get('ip_address', 'N/A')
            
            message += f"🔸 <code>{subdomain}</code>\n"
            if ip and ip != 'N/A':
                message += f"   📍 IP: <code>{ip}</code>\n"
            message += "\n"
        
        if len(new_subdomains) > 10:
            message += f"... and {len(new_subdomains) - 10} more subdomains\n"
        
        message += f"\n🔍 Use <code>/stats {domain}</code> for detailed information"
        
        return await self.send_message(message)
    
    async def send_scan_summary(self, domain: str, total_found: int, 
                               new_count: int, scan_duration: float) -> bool:
        """Send scan completion summary"""
        message = f"✅ <b>Scan Completed</b>\n"
        message += f"🌐 <b>Domain:</b> <code>{domain}</code>\n"
        message += f"📊 <b>Total Subdomains:</b> {total_found}\n"
        message += f"🆕 <b>New Subdomains:</b> {new_count}\n"
        message += f"⚡ <b>Scan Duration:</b> {scan_duration:.2f}s\n"
        message += f"⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message)
    
    async def send_error_alert(self, domain: str, error_message: str) -> bool:
        """Send error alert"""
        message = f"❌ <b>Scan Error</b>\n"
        message += f"🌐 <b>Domain:</b> <code>{domain}</code>\n"
        message += f"🚨 <b>Error:</b> {error_message}\n"
        message += f"⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message)
    
    async def send_help_message(self) -> bool:
        """Send help message with available commands"""
        message = """🤖 <b>Subdomain Monitor Bot Commands</b>

<b>🔍 Monitoring Commands:</b>
/add &lt;domain&gt; - Add domain to monitor
/remove &lt;domain&gt; - Remove domain from monitoring
/scan &lt;domain&gt; - Perform immediate scan
/scanall - Scan all monitored domains

<b>📊 Information Commands:</b>
/list - List all monitored domains
/stats &lt;domain&gt; - Get domain statistics
/recent &lt;domain&gt; - Show recent subdomains
/history &lt;domain&gt; - Show scan history

<b>⚙️ Control Commands:</b>
/start - Start monitoring service
/stop - Stop monitoring service
/status - Check service status
/config - Show current configuration

<b>📱 Examples:</b>
<code>/add example.com</code>
<code>/scan google.com</code>
<code>/stats facebook.com</code>
<code>/recent tesla.com</code>

🔔 <b>Notifications:</b>
You'll receive real-time alerts when new subdomains are discovered!
        """
        
        return await self.send_message(message)
    
    async def send_domain_list(self, domains: List[tuple]) -> bool:
        """Send list of monitored domains"""
        if not domains:
            message = "📝 <b>No domains are currently being monitored.</b>\n\n"
            message += "Use <code>/add &lt;domain&gt;</code> to start monitoring a domain."
        else:
            message = f"📋 <b>Monitored Domains ({len(domains)})</b>\n\n"
            for domain_id, domain in domains:
                message += f"🌐 <code>{domain}</code>\n"
            message += f"\n💡 Use <code>/stats &lt;domain&gt;</code> for detailed information"
        
        return await self.send_message(message)
    
    async def send_domain_stats(self, stats: Dict) -> bool:
        """Send detailed domain statistics"""
        if not stats:
            message = "❌ Domain not found in monitoring list."
            return await self.send_message(message)
        
        domain = stats['domain']
        message = f"📊 <b>Statistics for {domain}</b>\n\n"
        message += f"🗓️ <b>Added:</b> {stats.get('added_date', 'Unknown')}\n"
        message += f"🔄 <b>Last Checked:</b> {stats.get('last_checked', 'Never')}\n"
        message += f"📈 <b>Total Subdomains:</b> {stats.get('total_subdomains', 0)}\n"
        message += f"✅ <b>Active Subdomains:</b> {stats.get('current_subdomains', 0)}\n\n"
        
        recent_scans = stats.get('recent_scans', [])
        if recent_scans:
            message += "📋 <b>Recent Scans:</b>\n"
            for scan in recent_scans[:5]:
                scan_date, found, new, duration, status = scan
                message += f"• {scan_date}: {found} found, {new} new ({duration:.1f}s)\n"
        
        return await self.send_message(message)
