"""
Enhanced subdomain scanner with multiple API sources
Supports crt.sh, VirusTotal, SecurityTrails, Shodan, Chaos, and more
"""
import asyncio
import aiohttp
import json
import socket
import ssl
import time
import re
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
import logging
from urllib.parse import quote
import dns.resolver
import ipaddress
import base64

class EnhancedSubdomainScanner:
    def __init__(self, config):
        self.config = config
        self.session = None
        self.semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 3
        self.resolver.lifetime = 5
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=self.config.MAX_CONCURRENT_REQUESTS,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config.REQUEST_TIMEOUT,
            connect=5,
            sock_read=10
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.config.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def scan_domain(self, domain: str) -> Dict:
        """Main scanning function that aggregates results from all sources"""
        start_time = time.time()
        logging.info(f"Starting comprehensive scan for {domain}")
        
        # Run all scanning methods concurrently
        tasks = [
            self.get_crtsh_subdomains(domain),
            self.get_virustotal_subdomains(domain),
            self.get_securitytrails_subdomains(domain),
            self.get_chaos_subdomains(domain),
            self.get_alienvault_subdomains(domain),
            self.get_hackertarget_subdomains(domain),
            self.get_threatcrowd_subdomains(domain),
            self.get_rapiddns_subdomains(domain)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine all results
            all_subdomains = set()
            source_stats = {}
            
            sources = ['crt.sh', 'virustotal', 'securitytrails', 'chaos', 
                      'alienvault', 'hackertarget', 'threatcrowd', 'rapiddns']
            
            for i, result in enumerate(results):
                source = sources[i]
                if isinstance(result, Exception):
                    logging.warning(f"Error from {source}: {result}")
                    source_stats[source] = 0
                else:
                    source_stats[source] = len(result)
                    all_subdomains.update(result)
            
            # Get detailed information for each subdomain
            subdomain_details = []
            if all_subdomains:
                logging.info(f"Found {len(all_subdomains)} unique subdomains, getting details...")
                detail_tasks = [self.get_subdomain_info(sub) for sub in all_subdomains]
                subdomain_details = await asyncio.gather(*detail_tasks, return_exceptions=True)
                subdomain_details = [d for d in subdomain_details if not isinstance(d, Exception)]
            
            scan_duration = time.time() - start_time
            
            return {
                'domain': domain,
                'subdomains': subdomain_details,
                'total_found': len(all_subdomains),
                'scan_duration': scan_duration,
                'source_stats': source_stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error during domain scan: {e}")
            return {
                'domain': domain,
                'subdomains': [],
                'total_found': 0,
                'scan_duration': time.time() - start_time,
                'source_stats': {},
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_crtsh_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from crt.sh - Fixed URL format"""
        subdomains = set()
        
        queries = [
            f"%.{domain}",
            domain,
            f"%.%.{domain}",
        ]
        
        for query in queries:
            try:
                async with self.semaphore:
                    # Fixed URL format
                    url = f"https://crt.sh/?q={quote(query)}&output=json"
                    
                    for attempt in range(self.config.RETRY_ATTEMPTS):
                        try:
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
                                    break
                                elif response.status == 429:
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                                else:
                                    logging.warning(f"crt.sh returned status {response.status}")
                                    break
                        except asyncio.TimeoutError:
                            logging.warning(f"Timeout for crt.sh query {query}")
                            await asyncio.sleep(1)
                        except Exception as e:
                            logging.error(f"Error querying crt.sh: {e}")
                            break
                    
                    await asyncio.sleep(self.config.RATE_LIMIT_DELAY)
                    
            except Exception as e:
                logging.error(f"Failed crt.sh query: {e}")
                continue
        
        return subdomains

    async def get_virustotal_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from VirusTotal API"""
        subdomains = set()
        
        if not self.config.VIRUSTOTAL_API_KEY:
            return subdomains
            
        try:
            async with self.semaphore:
                url = f"{self.config.VIRUSTOTAL_API_URL}"
                params = {
                    'apikey': self.config.VIRUSTOTAL_API_KEY,
                    'domain': domain
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'subdomains' in data:
                            for subdomain in data['subdomains']:
                                if self._is_valid_subdomain(subdomain, domain):
                                    subdomains.add(subdomain)
                        
                        # Also check detected URLs
                        if 'detected_urls' in data:
                            for url_info in data['detected_urls']:
                                url = url_info.get('url', '')
                                extracted = self._extract_subdomain_from_url(url, domain)
                                if extracted:
                                    subdomains.add(extracted)
                                    
        except Exception as e:
            logging.error(f"VirusTotal API error: {e}")
            
        return subdomains

    async def get_securitytrails_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from SecurityTrails API"""
        subdomains = set()
        
        if not self.config.SECURITY_TRAILS_API_KEY:
            return subdomains
            
        try:
            async with self.semaphore:
                url = f"{self.config.SECURITY_TRAILS_API_URL}/{domain}/subdomains"
                headers = {
                    'APIKEY': self.config.SECURITY_TRAILS_API_KEY,
                    'User-Agent': self.config.USER_AGENT
                }
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'subdomains' in data:
                            for subdomain in data['subdomains']:
                                full_subdomain = f"{subdomain}.{domain}"
                                if self._is_valid_subdomain(full_subdomain, domain):
                                    subdomains.add(full_subdomain)
                                    
        except Exception as e:
            logging.error(f"SecurityTrails API error: {e}")
            
        return subdomains

    async def get_chaos_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from ProjectDiscovery Chaos API"""
        subdomains = set()
        
        try:
            async with self.semaphore:
                url = f"{self.config.CHAOS_API_URL}/{domain}"
                headers = {}
                if self.config.CHAOS_API_KEY:
                    headers['Authorization'] = f"Bearer {self.config.CHAOS_API_KEY}"
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'subdomains' in data:
                            for subdomain in data['subdomains']:
                                if self._is_valid_subdomain(subdomain, domain):
                                    subdomains.add(subdomain)
                                    
        except Exception as e:
            logging.error(f"Chaos API error: {e}")
            
        return subdomains

    async def get_alienvault_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from AlienVault OTX"""
        subdomains = set()
        
        try:
            async with self.semaphore:
                url = f"{self.config.ALIENVAULT_API_URL}/{domain}/passive_dns"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'passive_dns' in data:
                            for record in data['passive_dns']:
                                hostname = record.get('hostname', '')
                                if self._is_valid_subdomain(hostname, domain):
                                    subdomains.add(hostname)
                                    
        except Exception as e:
            logging.error(f"AlienVault OTX error: {e}")
            
        return subdomains

    async def get_hackertarget_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from HackerTarget (free API)"""
        subdomains = set()
        
        try:
            async with self.semaphore:
                url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        lines = text.strip().split('\n')
                        for line in lines:
                            if ',' in line:
                                hostname = line.split(',')[0].strip()
                                if self._is_valid_subdomain(hostname, domain):
                                    subdomains.add(hostname)
                                    
        except Exception as e:
            logging.error(f"HackerTarget API error: {e}")
            
        return subdomains

    async def get_threatcrowd_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from ThreatCrowd"""
        subdomains = set()
        
        try:
            async with self.semaphore:
                url = f"https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'subdomains' in data:
                            for subdomain in data['subdomains']:
                                if self._is_valid_subdomain(subdomain, domain):
                                    subdomains.add(subdomain)
                                    
        except Exception as e:
            logging.error(f"ThreatCrowd API error: {e}")
            
        return subdomains

    async def get_rapiddns_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from RapidDNS"""
        subdomains = set()
        
        try:
            async with self.semaphore:
                url = f"https://rapiddns.io/subdomain/{domain}?full=1"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        # Parse HTML for subdomains (basic regex extraction)
                        pattern = r'([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+' + re.escape(domain)
                        matches = re.findall(pattern, text)
                        for match in matches:
                            subdomain = match[0] + domain if match[0] else domain
                            if self._is_valid_subdomain(subdomain, domain):
                                subdomains.add(subdomain)
                                
        except Exception as e:
            logging.error(f"RapidDNS error: {e}")
            
        return subdomains

    async def get_subdomain_info(self, subdomain: str) -> Dict:
        """Get detailed information about a subdomain"""
        info = {
            'subdomain': subdomain,
            'ip_addresses': [],
            'is_active': False,
            'certificate_info': {},
            'response_time': None
        }
        
        try:
            # DNS resolution
            start_time = time.time()
            try:
                answers = self.resolver.resolve(subdomain, 'A')
                info['ip_addresses'] = [str(answer) for answer in answers]
                info['is_active'] = True
                info['response_time'] = time.time() - start_time
            except Exception:
                try:
                    answers = self.resolver.resolve(subdomain, 'CNAME')
                    info['cname'] = [str(answer) for answer in answers]
                    info['is_active'] = True
                    info['response_time'] = time.time() - start_time
                except Exception:
                    pass
            
            # Certificate information (if HTTPS is available)
            if info['is_active']:
                cert_info = await self._get_certificate_info(subdomain)
                if cert_info:
                    info['certificate_info'] = cert_info
                    
        except Exception as e:
            logging.error(f"Error getting subdomain info for {subdomain}: {e}")
            
        return info

    async def _get_certificate_info(self, domain: str) -> Optional[Dict]:
        """Get SSL certificate information"""
        try:
            loop = asyncio.get_event_loop()
            
            def _get_cert():
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with socket.create_connection((domain, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        return cert
            
            cert = await loop.run_in_executor(None, _get_cert)
            
            if cert:
                return {
                    'subject': dict(x[0] for x in cert.get('subject', [])),
                    'issuer': dict(x[0] for x in cert.get('issuer', [])),
                    'version': cert.get('version'),
                    'serial_number': cert.get('serialNumber'),
                    'not_before': cert.get('notBefore'),
                    'not_after': cert.get('notAfter'),
                    'subject_alt_names': [x[1] for x in cert.get('subjectAltName', []) if x[0] == 'DNS']
                }
                
        except Exception as e:
            logging.debug(f"Could not get certificate for {domain}: {e}")
            
        return None

    def _is_valid_subdomain(self, subdomain: str, domain: str) -> bool:
        """Validate if a subdomain is legitimate"""
        if not subdomain or not subdomain.endswith(domain):
            return False
            
        # Remove wildcards
        if subdomain.startswith('*'):
            return False
            
        # Check for invalid characters
        if re.search(r'[^a-zA-Z0-9.-]', subdomain):
            return False
            
        # Check if it's in excluded list
        for excluded in self.config.EXCLUDED_SUBDOMAINS:
            if excluded.replace('*', '') in subdomain:
                return False
                
        return True

    def _extract_subdomain_from_url(self, url: str, domain: str) -> Optional[str]:
        """Extract subdomain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.netloc.lower()
            
            if hostname.endswith(domain) and self._is_valid_subdomain(hostname, domain):
                return hostname
        except Exception:
            pass
            
        return None
