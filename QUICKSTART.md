# Quick Start Guide

## Simplified Subdomain Scanner Usage

### 🚀 Simple Method (Recommended)

**One command, instant results:**

```bash
python simple_scanner.py example.com
```

**Features:**
- ✅ 3 API sources (crt.sh, HackerTarget, AlienVault)
- ✅ Automatic Telegram notifications
- ✅ No configuration needed
- ✅ Single file solution

### 🔧 Advanced Method

**For monitoring and database tracking:**

```bash
python main.py --mode interactive
```

**Then use commands:**
- `add example.com` - Add domain
- `scan example.com` - Scan domain
- `list` - Show domains
- `quit` - Exit

## 📱 Telegram Setup

**Already configured:**
- Bot Token: `7799744103:AAHxdjdV8ycmCcf9AgSA-6C3NMWLFWhg9R0`
- Chat ID: `6247017127`

**Results are automatically sent to Telegram!**

## 🎯 Key Benefits

- **Simplified**: No more complex test scripts
- **Fast**: Multiple APIs run concurrently  
- **Accurate**: Enhanced validation logic
- **Clean**: Removed 8 unnecessary files
- **Ready**: Pre-configured Telegram integration

## 📊 Example Output

```
🚀 Simple Subdomain Scanner with Telegram Integration
============================================================
🎯 Target domain: example.com

🔍 Scanning example.com...
✅ Found 15 subdomains in 2.3s

📋 Results:
----------------------------------------
  1. api.example.com
  2. www.example.com
  3. mail.example.com
  ... 

✅ Total: 15 subdomains found
📱 Telegram notification sent!
```

---
**No more complexity, just results! 🎯**