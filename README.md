# Advanced Multi-Domain Subdomain Monitor 🔍

Sistem monitoring subdomain canggih dan real-time menggunakan API crt.sh dengan integrasi Telegram Bot untuk notifikasi instant.

## ✨ Fitur Utama

- 🚀 **Real-time monitoring** tanpa delay dengan arsitektur asynchronous
- 🔍 **Multi-domain scanning** dengan concurrency tinggi
- 📱 **Telegram Bot integration** dengan commands lengkap
- 💾 **Database tracking** untuk historical data dan statistics
- ⚡ **Fast response** dengan optimized API calls
- 🎯 **Smart filtering** untuk hasil yang akurat
- 📊 **Comprehensive reporting** dan analytics
- 🔄 **Automatic monitoring** dengan configurable intervals

## 🛠️ Instalasi & Setup

### 1. Clone Repository
```bash
git clone https://github.com/darkwolf379/subdomainfinder.git
cd subdomainfinder
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Telegram Bot

1. Buat bot baru di [@BotFather](https://t.me/BotFather)
2. Dapatkan bot token
3. Dapatkan chat ID dengan mengirim pesan ke bot dan mengakses:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```

### 4. Konfigurasi Environment

Buat file `.env` atau set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
export CHECK_INTERVAL="300"
export MAX_CONCURRENT="50"
```

## 🚀 Cara Penggunaan

### Mode Interactive (Development)
```bash
python main.py --mode interactive
```

### Mode Polling (Production)
```bash
python main.py --mode polling
```

### Mode Webhook (Server Production)
```bash
python main.py --mode webhook
```

## 📱 Commands Telegram Bot

### 🔍 Monitoring Commands
- `/add <domain>` - Tambah domain untuk monitoring
- `/remove <domain>` - Hapus domain dari monitoring
- `/scan <domain>` - Scan manual domain tertentu
- `/scanall` - Scan semua domain yang dimonitor

### 📊 Information Commands
- `/list` - List semua domain yang dimonitor
- `/stats <domain>` - Statistik detail domain
- `/recent <domain>` - Subdomain terbaru yang ditemukan
- `/history <domain>` - History scan domain

### ⚙️ Control Commands
- `/start` - Mulai bot dan lihat welcome message
- `/help` - Bantuan lengkap commands
- `/startmon` - Mulai automatic monitoring
- `/stopmon` - Stop automatic monitoring
- `/status` - Status sistem monitoring
- `/config` - Lihat konfigurasi saat ini

## 🎯 Contoh Penggunaan

### Menambah Domain
```
/add google.com
```

### Scan Manual
```
/scan facebook.com
```

### Lihat Statistik
```
/stats tesla.com
```

### Mulai Monitoring Otomatis
```
/startmon
```

## ⚙️ Konfigurasi Advanced

Edit file `config.py` untuk customisasi:

```python
# Monitoring Configuration
CHECK_INTERVAL = 300  # 5 menit
MAX_CONCURRENT_REQUESTS = 50
REQUEST_TIMEOUT = 10
RETRY_ATTEMPTS = 3

# Advanced Features
ENABLE_WILDCARD_DETECTION = True
ENABLE_SUBDOMAIN_VALIDATION = True
ENABLE_IP_RESOLUTION = True
ENABLE_PORT_SCANNING = False

# Rate Limiting
RATE_LIMIT_DELAY = 0.1
BURST_SIZE = 10
```

## 🔧 Fitur Advanced

### 1. Real-time Performance
- Asynchronous HTTP requests
- Connection pooling
- DNS caching
- Concurrent subdomain resolution

### 2. Smart Filtering
- Wildcard detection dan handling
- Invalid subdomain filtering
- Duplicate elimination
- Pattern-based exclusion

### 3. Comprehensive Data Collection
- IP address resolution (IPv4/IPv6)
- SSL certificate information
- CNAME records
- MX records (opsional)
- Port scanning (opsional)

### 4. Robust Error Handling
- Automatic retry dengan exponential backoff
- Rate limiting compliance
- Timeout handling
- Connection error recovery

### 5. Database Features
- SQLite database untuk persistence
- Historical data tracking
- Scan statistics
- Performance metrics

## 📊 Output Example

```
🎯 New Subdomains Found!
🌐 Domain: example.com
📊 Count: 15
⏰ Time: 2025-08-18 15:30:45

🔸 api.example.com
   📍 IP: 192.168.1.100

🔸 admin.example.com
   📍 IP: 192.168.1.101

🔸 dev.example.com
   📍 IP: 192.168.1.102

... and 12 more subdomains

🔍 Use /stats example.com for detailed information
```

## 🚀 Performance Optimizations

- **Concurrent scanning**: Multiple domains scan bersamaan
- **Batch processing**: Efficient database operations
- **Connection reuse**: HTTP connection pooling
- **DNS caching**: Reduced DNS lookup overhead
- **Rate limiting**: Respectful API usage
- **Memory efficient**: Streaming data processing

## 🔒 Security Features

- Input validation dan sanitization
- SQL injection protection
- Rate limiting untuk API calls
- Secure SSL certificate handling
- Error information sanitization

## 📈 Monitoring & Analytics

- Real-time scan progress
- Historical trend analysis
- Performance benchmarking
- Error rate tracking
- Notification delivery stats

## 🐛 Troubleshooting

### Common Issues

1. **Bot tidak respond**
   - Cek bot token dan chat ID
   - Pastikan bot sudah di-start dengan /start

2. **Scan lambat**
   - Increase MAX_CONCURRENT_REQUESTS
   - Decrease REQUEST_TIMEOUT
   - Check network connectivity

3. **Database errors**
   - Pastikan file permissions correct
   - Check disk space
   - Restart application

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
python main.py --mode interactive
```

## 📝 Logs

Semua aktivitas tercatat di:
- `subdomain_monitor.log` - Application logs
- Console output - Real-time status

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - lihat file LICENSE untuk detail.

## 🙏 Credits

- **crt.sh API** untuk certificate transparency data
- **Telegram Bot API** untuk notifications
- **Python asyncio** untuk high-performance async operations

## 📞 Support

Untuk support dan pertanyaan:
- GitHub Issues: [Create Issue](https://github.com/darkwolf379/subdomainfinder/issues)
- Telegram: [@darkwolf379](https://t.me/darkwolf379)

---

**⚡ Fast • 🎯 Accurate • 📱 User-friendly • 🔄 Real-time**