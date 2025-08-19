"""
Database manager for subdomain monitoring
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Domains table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE NOT NULL,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    last_checked TIMESTAMP,
                    total_subdomains INTEGER DEFAULT 0
                )
            ''')
            
            # Subdomains table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subdomains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id INTEGER,
                    subdomain TEXT NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    ip_address TEXT,
                    certificate_info TEXT,
                    FOREIGN KEY (domain_id) REFERENCES domains (id),
                    UNIQUE(domain_id, subdomain)
                )
            ''')
            
            # Notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id INTEGER,
                    subdomain TEXT,
                    notification_type TEXT,
                    message TEXT,
                    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY (domain_id) REFERENCES domains (id)
                )
            ''')
            
            # Scan history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id INTEGER,
                    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subdomains_found INTEGER,
                    new_subdomains INTEGER,
                    scan_duration REAL,
                    status TEXT,
                    FOREIGN KEY (domain_id) REFERENCES domains (id)
                )
            ''')
            
            conn.commit()
    
    def add_domain(self, domain: str) -> int:
        """Add a new domain to monitor"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO domains (domain) VALUES (?)',
                    (domain,)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Domain already exists, return its ID
                cursor.execute('SELECT id FROM domains WHERE domain = ?', (domain,))
                result = cursor.fetchone()
                return result[0] if result else None
    
    def get_domains(self, active_only: bool = True) -> List[Tuple[int, str]]:
        """Get all monitored domains"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute('SELECT id, domain FROM domains WHERE is_active = 1')
            else:
                cursor.execute('SELECT id, domain FROM domains')
            return cursor.fetchall()
    
    def remove_domain(self, domain: str) -> bool:
        """Remove a domain from monitoring"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE domains SET is_active = 0 WHERE domain = ?', (domain,))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_subdomains(self, domain_id: int, subdomains: List[Dict]) -> int:
        """Add new subdomains for a domain"""
        new_count = 0
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            for sub_data in subdomains:
                subdomain = sub_data.get('subdomain')
                ip_address = sub_data.get('ip_address')
                cert_info = json.dumps(sub_data.get('certificate_info', {}))
                
                try:
                    cursor.execute('''
                        INSERT INTO subdomains (domain_id, subdomain, ip_address, certificate_info)
                        VALUES (?, ?, ?, ?)
                    ''', (domain_id, subdomain, ip_address, cert_info))
                    new_count += 1
                except sqlite3.IntegrityError:
                    # Subdomain exists, update last_seen
                    cursor.execute('''
                        UPDATE subdomains SET last_seen = CURRENT_TIMESTAMP, 
                               ip_address = ?, certificate_info = ?
                        WHERE domain_id = ? AND subdomain = ?
                    ''', (ip_address, cert_info, domain_id, subdomain))
            
            conn.commit()
        return new_count
    
    def get_subdomains(self, domain_id: int, active_only: bool = True) -> List[Dict]:
        """Get subdomains for a domain"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute('''
                    SELECT subdomain, first_seen, last_seen, ip_address, certificate_info
                    FROM subdomains WHERE domain_id = ? AND is_active = 1
                    ORDER BY first_seen DESC
                ''', (domain_id,))
            else:
                cursor.execute('''
                    SELECT subdomain, first_seen, last_seen, ip_address, certificate_info
                    FROM subdomains WHERE domain_id = ?
                    ORDER BY first_seen DESC
                ''', (domain_id,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'subdomain': row[0],
                    'first_seen': row[1],
                    'last_seen': row[2],
                    'ip_address': row[3],
                    'certificate_info': json.loads(row[4]) if row[4] else {}
                })
            return results
    
    def update_domain_stats(self, domain_id: int):
        """Update domain statistics"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE domains SET 
                    last_checked = CURRENT_TIMESTAMP,
                    total_subdomains = (
                        SELECT COUNT(*) FROM subdomains 
                        WHERE domain_id = ? AND is_active = 1
                    )
                WHERE id = ?
            ''', (domain_id, domain_id))
            conn.commit()
    
    def add_scan_history(self, domain_id: int, subdomains_found: int, 
                        new_subdomains: int, scan_duration: float, status: str):
        """Add scan history record"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_history 
                (domain_id, subdomains_found, new_subdomains, scan_duration, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (domain_id, subdomains_found, new_subdomains, scan_duration, status))
            conn.commit()
    
    def get_domain_stats(self, domain: str) -> Dict:
        """Get comprehensive domain statistics"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Get domain info
            cursor.execute('''
                SELECT d.id, d.domain, d.added_date, d.last_checked, d.total_subdomains,
                       COUNT(s.id) as current_subdomains
                FROM domains d
                LEFT JOIN subdomains s ON d.id = s.domain_id AND s.is_active = 1
                WHERE d.domain = ?
                GROUP BY d.id
            ''', (domain,))
            
            domain_info = cursor.fetchone()
            if not domain_info:
                return {}
            
            # Get recent scan history
            cursor.execute('''
                SELECT scan_date, subdomains_found, new_subdomains, scan_duration, status
                FROM scan_history
                WHERE domain_id = ?
                ORDER BY scan_date DESC
                LIMIT 10
            ''', (domain_info[0],))
            
            scan_history = cursor.fetchall()
            
            return {
                'domain': domain_info[1],
                'added_date': domain_info[2],
                'last_checked': domain_info[3],
                'total_subdomains': domain_info[4],
                'current_subdomains': domain_info[5],
                'recent_scans': scan_history
            }
