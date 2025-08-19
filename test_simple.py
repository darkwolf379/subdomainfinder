#!/usr/bin/env python3
"""
Simple test script for subdomain scanner with Telegram notifications
"""
import asyncio
import logging
import json
from config import Config
from database import DatabaseManager
from telegram_bot import TelegramNotifier
from scanner import SubdomainScanner

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_scan_and_notify():
    """Test the scanner and Telegram notifications"""
    config = Config()
    db = DatabaseManager(config.DATABASE_FILE)
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    
    # Test domain
    test_domain = "example.com"
    
    print(f"🔍 Testing scan for domain: {test_domain}")
    print("=" * 50)
    
    try:
        # Send start notification
        await notifier.send_message(f"🚀 Starting subdomain scan for {test_domain}")
        
        # Run scan
        async with SubdomainScanner(config) as scanner:
            subdomains = await scanner.get_crtsh_subdomains(test_domain)
            
            print(f"📊 Found {len(subdomains)} subdomains:")
            for subdomain in list(subdomains)[:10]:  # Show first 10
                print(f"  • {subdomain}")
            
            if len(subdomains) > 10:
                print(f"  ... and {len(subdomains) - 10} more")
            
            # Add to database
            domain_id = db.add_domain(test_domain)
            
            # Convert to format expected by database
            subdomain_data = []
            for subdomain in list(subdomains)[:5]:  # Process first 5 for detailed info
                try:
                    info = await scanner.get_subdomain_info(subdomain)
                    subdomain_data.append(info)
                except Exception as e:
                    print(f"Error getting info for {subdomain}: {e}")
            
            # Save to database
            new_count = db.add_subdomains(domain_id, subdomain_data)
            db.update_domain_stats(domain_id)
            
            # Send results notification
            message = f"""
🎯 Scan completed for {test_domain}

📈 Results:
• Total subdomains found: {len(subdomains)}
• New subdomains: {new_count}
• Detailed analysis: {len(subdomain_data)} subdomains

🔍 Sample subdomains:
{chr(10).join([f"• {sub}" for sub in list(subdomains)[:5]])}
            """
            
            await notifier.send_message(message.strip())
            
            print(f"\n✅ Scan completed successfully!")
            print(f"📊 Results: {len(subdomains)} total, {new_count} new")
            print(f"📱 Notifications sent to Telegram")
            
    except Exception as e:
        error_msg = f"❌ Error during scan: {str(e)}"
        print(error_msg)
        try:
            await notifier.send_message(error_msg)
        except:
            print("Failed to send error notification to Telegram")

async def test_telegram_only():
    """Test only Telegram functionality"""
    config = Config()
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    
    print("📱 Testing Telegram notifications...")
    
    try:
        # Test basic message
        await notifier.send_message("🧪 Test message from SubdomainFinder!")
        print("✅ Basic message sent")
        
        # Test formatted message
        test_results = {
            'domain': 'test.com',
            'subdomains_found': 25,
            'new_subdomains': 3,
            'scan_time': 45.2
        }
        
        formatted_message = f"""
🎯 Subdomain Scan Results

🌐 Domain: {test_results['domain']}
📊 Total found: {test_results['subdomains_found']}
🆕 New subdomains: {test_results['new_subdomains']}
⏱️ Scan time: {test_results['scan_time']:.1f}s

🔍 Sample new subdomains:
• api.test.com
• staging.test.com  
• dev.test.com
        """
        
        await notifier.send_message(formatted_message.strip())
        print("✅ Formatted message sent")
        
        print("📱 Telegram test completed successfully!")
        
    except Exception as e:
        print(f"❌ Telegram test failed: {e}")

async def main():
    """Main test function"""
    print("🧪 SubdomainFinder Test Suite")
    print("=" * 50)
    
    while True:
        print("\nTest options:")
        print("1. Test Telegram notifications only")
        print("2. Test full scan with notifications")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            await test_telegram_only()
        elif choice == '2':
            await test_scan_and_notify()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    asyncio.run(main())
