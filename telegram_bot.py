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
        """Send comprehensive help message with available commands"""
        message = """🤖 <b>Subdomain Monitor Bot - Complete Guide</b>

<b>🎯 Quick Start:</b>
1. Add a domain: <code>/add example.com</code>
2. Start monitoring: <code>/startmon</code>
3. Get real-time notifications for new subdomains!

<b>🔍 Domain Management:</b>
<code>/add &lt;domain&gt;</code> - Add domain to monitor list
<code>/remove &lt;domain&gt;</code> - Remove domain from monitoring
<code>/list</code> - Show all monitored domains
<code>/scan &lt;domain&gt;</code> - Perform immediate single scan
<code>/scanall</code> - Scan all monitored domains

<b>📊 Information & Statistics:</b>
<code>/stats &lt;domain&gt;</code> - Get detailed domain statistics
<code>/recent &lt;domain&gt;</code> - Show recently found subdomains
<code>/history &lt;domain&gt;</code> - Show scan history for domain

<b>⚙️ Monitoring Control:</b>
<code>/startmon</code> - Start automatic monitoring
<code>/stopmon</code> - Stop automatic monitoring
<code>/status</code> - Check bot and monitoring status
<code>/config</code> - Show current configuration

<b>📱 Usage Examples:</b>
<code>/add google.com</code>
<code>/scan facebook.com</code>
<code>/stats tesla.com</code>
<code>/recent example.org</code>

<b>🔔 About Notifications:</b>
• Real-time alerts when new subdomains are discovered
• Scan summaries with statistics
• Error notifications for failed scans
• Detailed subdomain information including IP addresses

<b>💡 Tips:</b>
• Use domain names without http:// or https://
• Monitoring checks domains every 5 minutes by default
• Add multiple domains for comprehensive monitoring
• Use <code>/status</code> to check if monitoring is active

<b>🆘 Need Help?</b>
Send any command to see available options or contact support.
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
