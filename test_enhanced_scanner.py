"""
Migration script to update the old scanner with enhanced multi-source capabilities
"""
import asyncio
import time
from enhanced_scanner import EnhancedSubdomainScanner
from config import Config
from database import DatabaseManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_enhanced_scanner():
    """Test the enhanced scanner with multiple sources"""
    config = Config()
    db = DatabaseManager(config.DATABASE_FILE)
    
    # Test domain
    test_domain = input("Enter domain to test (e.g., example.com): ").strip()
    
    if not test_domain:
        test_domain = "github.com"  # Default test domain
    
    print(f"\n🔍 Testing enhanced scanner with domain: {test_domain}")
    print("=" * 60)
    
    async with EnhancedSubdomainScanner(config) as scanner:
        result = await scanner.scan_domain(test_domain)
        
        print(f"\n📊 Scan Results for {test_domain}:")
        print(f"├── Total subdomains found: {result['total_found']}")
        print(f"├── Scan duration: {result['scan_duration']:.2f} seconds")
        print(f"└── Timestamp: {result['timestamp']}")
        
        print(f"\n📈 Source Statistics:")
        for source, count in result['source_stats'].items():
            print(f"├── {source.capitalize()}: {count} subdomains")
        
        if result['subdomains']:
            print(f"\n🎯 Found Subdomains (showing first 10):")
            for i, subdomain_info in enumerate(result['subdomains'][:10]):
                status = "✅ Active" if subdomain_info['is_active'] else "❌ Inactive"
                ip_info = f" ({', '.join(subdomain_info['ip_addresses'])})" if subdomain_info['ip_addresses'] else ""
                print(f"├── {subdomain_info['subdomain']}{ip_info} - {status}")
            
            if len(result['subdomains']) > 10:
                print(f"└── ... and {len(result['subdomains']) - 10} more")
        
        # Save to database
        domain_id = db.add_domain(test_domain)
        if domain_id:
            new_count = db.add_subdomains(domain_id, result['subdomains'])
            db.update_domain_stats(domain_id)
            db.add_scan_history(
                domain_id, 
                result['total_found'], 
                new_count, 
                result['scan_duration'], 
                'success'
            )
            print(f"\n💾 Saved {new_count} new subdomains to database")

def compare_apis():
    """Compare different subdomain enumeration APIs"""
    print("\n🔗 Available Subdomain Enumeration APIs:")
    print("=" * 60)
    
    apis = [
        {
            'name': 'crt.sh',
            'description': 'Certificate Transparency logs - Free, fast, comprehensive',
            'pros': ['Free', 'Fast', 'Historical data', 'No API key required'],
            'cons': ['Rate limited', 'Only certificate-based subdomains'],
            'url': 'https://crt.sh/?q=%.domain.com&output=json'
        },
        {
            'name': 'VirusTotal',
            'description': 'Security intelligence platform with subdomain data',
            'pros': ['High quality data', 'Active/malicious subdomain detection'],
            'cons': ['Requires API key', 'Rate limited', 'Limited free tier'],
            'url': 'https://www.virustotal.com/vtapi/v2/domain/report'
        },
        {
            'name': 'SecurityTrails',
            'description': 'DNS intelligence and subdomain discovery',
            'pros': ['Very comprehensive', 'Historical DNS data', 'Fast'],
            'cons': ['Paid API', 'Expensive for high volume'],
            'url': 'https://api.securitytrails.com/v1/domain/{domain}/subdomains'
        },
        {
            'name': 'ProjectDiscovery Chaos',
            'description': 'Community-driven subdomain dataset',
            'pros': ['High quality', 'Actively maintained', 'Free tier available'],
            'cons': ['Requires registration', 'Limited free requests'],
            'url': 'https://dns.projectdiscovery.io/dns/{domain}'
        },
        {
            'name': 'HackerTarget',
            'description': 'Free online vulnerability scanners',
            'pros': ['Completely free', 'No API key required', 'Simple'],
            'cons': ['Limited data', 'Rate limited', 'Basic features'],
            'url': 'https://api.hackertarget.com/hostsearch/?q={domain}'
        },
        {
            'name': 'ThreatCrowd',
            'description': 'Open source threat intelligence',
            'pros': ['Free', 'Threat intelligence context', 'No auth required'],
            'cons': ['Sometimes unreliable', 'Limited data freshness'],
            'url': 'https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}'
        }
    ]
    
    for api in apis:
        print(f"\n📡 {api['name']}")
        print(f"   Description: {api['description']}")
        print(f"   URL: {api['url']}")
        print(f"   ✅ Pros: {', '.join(api['pros'])}")
        print(f"   ❌ Cons: {', '.join(api['cons'])}")

def setup_api_keys():
    """Help user setup API keys"""
    print("\n🔑 API Key Setup Guide:")
    print("=" * 60)
    
    api_setup = [
        {
            'name': 'VirusTotal',
            'env_var': 'VIRUSTOTAL_API_KEY',
            'signup_url': 'https://www.virustotal.com/gui/join-us',
            'free_tier': '4 requests/minute',
            'instructions': 'Sign up → Profile → API Key'
        },
        {
            'name': 'SecurityTrails',
            'env_var': 'SECURITY_TRAILS_API_KEY', 
            'signup_url': 'https://securitytrails.com/corp/api',
            'free_tier': '50 requests/month',
            'instructions': 'Sign up → Dashboard → API'
        },
        {
            'name': 'Shodan',
            'env_var': 'SHODAN_API_KEY',
            'signup_url': 'https://account.shodan.io/register',
            'free_tier': '100 queries/month',
            'instructions': 'Sign up → Account → API Key'
        },
        {
            'name': 'ProjectDiscovery Chaos',
            'env_var': 'CHAOS_API_KEY',
            'signup_url': 'https://chaos.projectdiscovery.io/',
            'free_tier': '1000 requests/month',
            'instructions': 'Github auth → Dashboard → API Key'
        }
    ]
    
    for api in api_setup:
        print(f"\n🔧 {api['name']}:")
        print(f"   Signup: {api['signup_url']}")
        print(f"   Free Tier: {api['free_tier']}")
        print(f"   Setup: {api['instructions']}")
        print(f"   Environment Variable: export {api['env_var']}=your_api_key_here")

def create_env_file():
    """Create a .env file template"""
    env_content = """# Subdomain Finder API Keys
# Get these from the respective services (see setup guide)

# VirusTotal API (https://www.virustotal.com/gui/join-us)
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here

# SecurityTrails API (https://securitytrails.com/corp/api)
SECURITY_TRAILS_API_KEY=your_securitytrails_api_key_here

# Shodan API (https://account.shodan.io/register)
SHODAN_API_KEY=your_shodan_api_key_here

# ProjectDiscovery Chaos API (https://chaos.projectdiscovery.io/)
CHAOS_API_KEY=your_chaos_api_key_here

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Scanner Configuration
CHECK_INTERVAL=300
MAX_CONCURRENT=50
REQUEST_TIMEOUT=10
RETRY_ATTEMPTS=3
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n📄 Created .env file template")
    print("📝 Please edit .env file and add your API keys")

async def main():
    """Main function"""
    print("🚀 Enhanced Subdomain Scanner")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Test enhanced scanner")
        print("2. Compare APIs")
        print("3. Setup API keys guide")
        print("4. Create .env file template")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            await test_enhanced_scanner()
        elif choice == '2':
            compare_apis()
        elif choice == '3':
            setup_api_keys()
        elif choice == '4':
            create_env_file()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option, please try again")

if __name__ == "__main__":
    asyncio.run(main())
