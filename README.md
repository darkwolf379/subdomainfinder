# Subdomain Scanner 🔍

**Simple and efficient subdomain finder with Telegram notifications**

> ⚡ **SIMPLIFIED** - No more complex configurations or multiple test files!

## 🚀 Quick Start

### Option 1: Simple Scanner (Recommended)
**One-file solution for easy subdomain scanning:**

```bash
python simple_scanner.py example.com
```

### Option 2: Advanced Monitoring  
**Full monitoring system with database tracking:**

```bash
python main.py --mode interactive
```

## 📱 Telegram Integration

**Pre-configured and ready to use:**
- Bot Token: `7799744103:AAHxdjdV8ycmCcf9AgSA-6C3NMWLFWhg9R0`
- Chat ID: `6247017127`

## 🛠️ Installation

```bash
pip install -r requirements.txt
```

## 🎯 Features

✅ **Multiple API Sources**: crt.sh + HackerTarget + AlienVault OTX  
✅ **Telegram Notifications**: Instant results delivery  
✅ **Fast Scanning**: Concurrent API calls  
✅ **Simple Interface**: Minimal setup required  
✅ **No Test Complexity**: Clean, focused codebase  

## 📊 Usage Examples

### Quick domain scan:
```bash
python simple_scanner.py google.com
```

### Interactive mode:
```bash
python main.py
# Then use: add example.com, scan example.com, list, help
```

## 📋 Files Overview

- `simple_scanner.py` - **Single-file scanner (best for most users)**
- `main.py` - Advanced monitoring with database
- `scanner.py` - Core scanning engine with multiple APIs
- `telegram_bot.py` - Telegram notifications
- `config.py` - Configuration settings

## 🎮 Interactive Commands

- `add <domain>` - Add domain to monitoring
- `scan <domain>` - Scan specific domain  
- `list` - Show monitored domains
- `stats <domain>` - Domain statistics
- `help` - Show all commands
- `quit` - Exit

## 🔧 Configuration

**Works out of the box** with sensible defaults. For customization, edit `config.py`.

---

**🎯 Fast • Simple • Effective**