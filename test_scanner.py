"""
Example configuration and quick test script
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from scanner import SubdomainScanner

async def test_scanner():
    """Test the subdomain scanner functionality"""
    print("🔍 Testing Subdomain Scanner...")
    
    config = Config()
    test_domain = "google.com"
    
    print(f"📊 Testing with domain: {test_domain}")
    print(f"⚙️ Max concurrent requests: {config.MAX_CONCURRENT_REQUESTS}")
    print(f"⏱️ Request timeout: {config.REQUEST_TIMEOUT}s")
    print()
    
    try:
        async with SubdomainScanner(config) as scanner:
            print(f"🚀 Starting scan for {test_domain}...")
            subdomains, duration = await scanner.scan_domain_fast(test_domain)
            
            print(f"✅ Scan completed in {duration:.2f} seconds")
            print(f"📊 Found {len(subdomains)} subdomains")
            print()
            
            # Show first 10 results
            print("🔸 Sample results:")
            for i, subdomain_data in enumerate(subdomains[:10]):
                subdomain = subdomain_data['subdomain']
                ip = subdomain_data.get('ip_address', 'N/A')
                is_active = subdomain_data.get('is_active', False)
                
                status = "🟢" if is_active else "🔴"
                print(f"   {status} {subdomain}")
                if ip and ip != 'N/A':
                    print(f"      📍 IP: {ip}")
            
            if len(subdomains) > 10:
                print(f"   ... and {len(subdomains) - 10} more subdomains")
            
            print()
            print("🎉 Scanner test completed successfully!")
            
    except Exception as e:
        print(f"❌ Scanner test failed: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("🧪 Advanced Subdomain Monitor - Test Suite")
    print("=" * 50)
    
    success = await test_scanner()
    
    if success:
        print("\n✅ All tests passed!")
        print("\n📋 Next steps:")
        print("1. Set up your Telegram bot tokens in environment variables")
        print("2. Run: python main.py --mode interactive")
        print("3. Try commands like: add google.com, scan google.com")
    else:
        print("\n❌ Some tests failed!")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    asyncio.run(main())
