"""
Advanced subdomain scanner using crt.sh API with real-time capabilities
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

class SubdomainScanner:
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
    
    async def get_crtsh_subdomains(self, domain: str) -> Set[str]:
        """Get subdomains from crt.sh with enhanced parsing"""
        subdomains = set()
        
        # Multiple query approaches for comprehensive results
        queries = [
            f"%.{domain}",
            domain,
            f"%.%.{domain}",
        ]
        
        for query in queries:
            try:
                async with self.semaphore:
                    # Fixed URL format - using correct crt.sh API endpoint
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
                                    # Rate limited, wait and retry
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                                else:
                                    logging.warning(f"crt.sh returned status {response.status} for {domain}")
                                    break
                        except asyncio.TimeoutError:
                            logging.warning(f"Timeout for crt.sh query {query} (attempt {attempt + 1})")
                            if attempt == self.config.RETRY_ATTEMPTS - 1:
                                break
                            await asyncio.sleep(1)
                        except Exception as e:
                            logging.error(f"Error querying crt.sh for {query}: {e}")
                            break
                    
                    # Small delay to be respectful to the API
                    await asyncio.sleep(self.config.RATE_LIMIT_DELAY)
                    
            except Exception as e:
                logging.error(f"Failed to query crt.sh for {query}: {e}")
                continue
        
        return subdomains
    
    def _is_valid_subdomain(self, subdomain: str, domain: str) -> bool:
        """Validate if a subdomain is legitimate and should be included"""
        if not subdomain or not subdomain.endswith(domain):
            return False
        
        # Remove wildcards
        if subdomain.startswith('*.'):
            subdomain = subdomain[2:]
        
        # Basic validation
        if not re.match(r'^[a-zA-Z0-9.-]+$', subdomain):
            return False
        
        # Check against excluded patterns
        for excluded in self.config.EXCLUDED_SUBDOMAINS:
            if excluded.startswith('*.'):
                pattern = excluded[2:]
                if subdomain.endswith(pattern):
                    return False
            elif subdomain == excluded:
                return False
        
        # Check for reasonable length
        if len(subdomain) > 253:  # Max domain length
            return False
        
        # Check for consecutive dots or invalid characters
        if '..' in subdomain or subdomain.startswith('.') or subdomain.endswith('.'):
            return False
        
        return True
    
    async def resolve_subdomain_info(self, subdomain: str) -> Dict:
        """Resolve IP address and additional info for subdomain"""
        info = {
            'subdomain': subdomain,
            'ip_address': None,
            'ipv6_address': None,
            'cname': None,
            'mx_records': [],
            'txt_records': [],
            'is_active': False,
            'certificate_info': {}
        }
        
        try:
            # DNS Resolution
            try:
                # A record (IPv4)
                a_records = await self._resolve_dns(subdomain, 'A')
                if a_records:
                    info['ip_address'] = a_records[0]
                    info['is_active'] = True
            except:
                pass
            
            try:
                # AAAA record (IPv6)
                aaaa_records = await self._resolve_dns(subdomain, 'AAAA')
                if aaaa_records:
                    info['ipv6_address'] = aaaa_records[0]
                    info['is_active'] = True
            except:
                pass
            
            try:
                # CNAME record
                cname_records = await self._resolve_dns(subdomain, 'CNAME')
                if cname_records:
                    info['cname'] = cname_records[0]
            except:
                pass
            
            # Certificate information (if HTTPS is available)
            if info['is_active']:
                cert_info = await self._get_certificate_info(subdomain)
                if cert_info:
                    info['certificate_info'] = cert_info
                    
        except Exception as e:
            logging.debug(f"Error resolving {subdomain}: {e}")
        
        return info
    
    async def _resolve_dns(self, domain: str, record_type: str) -> List[str]:
        """Resolve DNS records asynchronously"""
        loop = asyncio.get_event_loop()
        
        def _sync_resolve():
            try:
                answers = self.resolver.resolve(domain, record_type)
                return [str(answer) for answer in answers]
            except:
                return []
        
        return await loop.run_in_executor(None, _sync_resolve)
    
    async def _get_certificate_info(self, domain: str) -> Optional[Dict]:
        """Get SSL certificate information"""
        try:
            loop = asyncio.get_event_loop()
            
            def _get_cert():
                try:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                    with socket.create_connection((domain, 443), timeout=5) as sock:
                        with context.wrap_socket(sock, server_hostname=domain) as ssock:
                            cert = ssock.getpeercert()
                            return {
                                'issuer': dict(x[0] for x in cert.get('issuer', [])),
                                'subject': dict(x[0] for x in cert.get('subject', [])),
                                'notAfter': cert.get('notAfter'),
                                'notBefore': cert.get('notBefore'),
                                'serialNumber': cert.get('serialNumber'),
                                'version': cert.get('version')
                            }
                except:
                    return None
            
            return await loop.run_in_executor(None, _get_cert)
        except:
            return None
    
    async def scan_domain_fast(self, domain: str) -> Tuple[List[Dict], float]:
        """Perform fast, comprehensive domain scan"""
        start_time = time.time()
        
        logging.info(f"Starting fast scan for {domain}")
        
        # Get subdomains from crt.sh
        subdomains = await self.get_crtsh_subdomains(domain)
        
        if not subdomains:
            logging.warning(f"No subdomains found for {domain}")
            return [], time.time() - start_time
        
        logging.info(f"Found {len(subdomains)} subdomains for {domain}, resolving...")
        
        # Resolve subdomain information in batches
        resolved_subdomains = []
        batch_size = self.config.MAX_CONCURRENT_REQUESTS
        
        for i in range(0, len(subdomains), batch_size):
            batch = list(subdomains)[i:i + batch_size]
            
            tasks = [
                self.resolve_subdomain_info(subdomain)
                for subdomain in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, dict) and not isinstance(result, Exception):
                    resolved_subdomains.append(result)
            
            # Small delay between batches
            if i + batch_size < len(subdomains):
                await asyncio.sleep(0.1)
        
        scan_duration = time.time() - start_time
        
        # Filter active subdomains
        active_subdomains = [
            sub for sub in resolved_subdomains 
            if sub.get('is_active') or sub.get('ip_address') or sub.get('cname')
        ]
        
        logging.info(f"Scan completed for {domain}: {len(active_subdomains)} active subdomains in {scan_duration:.2f}s")
        
        return active_subdomains, scan_duration
    
    async def scan_multiple_domains(self, domains: List[str]) -> Dict[str, Tuple[List[Dict], float]]:
        """Scan multiple domains concurrently"""
        tasks = []
        for domain in domains:
            task = asyncio.create_task(
                self.scan_domain_fast(domain),
                name=f"scan_{domain}"
            )
            tasks.append((domain, task))
        
        results = {}
        for domain, task in tasks:
            try:
                result = await task
                results[domain] = result
            except Exception as e:
                logging.error(f"Failed to scan {domain}: {e}")
                results[domain] = ([], 0.0)
        
        return results
