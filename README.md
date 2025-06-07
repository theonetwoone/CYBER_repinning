# 💀 CYBER SKULLS // ALGORAND NFT REPINNING PROTOCOL

A cyberpunk-themed tool for migrating Algorand NFT collections to reliable IPFS pinning services. Built for creators who want to ensure their NFTs remain accessible forever.

![Version](https://img.shields.io/badge/version-v2.1-00FF41) ![Python](https://img.shields.io/badge/python-3.8+-00FF41) ![Algorand](https://img.shields.io/badge/blockchain-Algorand-00FF41) ![IPFS](https://img.shields.io/badge/storage-IPFS-00FF41)

## 🎯 WHAT THIS TOOL DOES

**For NFT Creators:**
- 📥 **Import** your Algorand NFT collection (via wen.tools CSV or direct fetch)
- 🔍 **Analyze** collection structure (directory vs individual CIDs)
- 📌 **Migrate** all NFT assets to a reliable IPFS pinning service
- ✅ **Verify** successful migration with real-time status tracking
- 📊 **Export** results for your records

**Why You Need This:**
- ⚠️ Original IPFS nodes may go offline, making your NFTs inaccessible
- 🛡️ Professional pinning services provide redundant, reliable storage
- 💰 Costs as low as **$0.08/GB** with 4everland's free tier
- 🚀 **Directory collections** can pin 1 CID to cover 100+ individual assets efficiently

---

## 🚀 QUICK START GUIDE

### Step 1: Download & Setup

1. **Download the tool:**
   ```bash
   git clone https://github.com/theonetwoone/CYBER_repinning.git
   cd CYBER_repinning
   ```

2. **Install Python** (if not already installed):
   - Windows: Download from [python.org](https://python.org)
   - Mac: `brew install python3`
   - Linux: `sudo apt install python3 python3-pip`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Launch the Application

```bash
streamlit run app.py
```

Your browser will open to `http://localhost:8501` with the Cyber Skulls interface.

### Step 3: Load Your Collection

Choose one of three methods:

#### Option A: wen.tools CSV Upload (⚡ **FASTEST**)
1. Go to [wen.tools/download-arc19-collection-data](https://www.wen.tools/download-arc19-collection-data)
2. Enter your collection's asset ID or creator address
3. Download the CSV file
4. Upload it in the sidebar → "Upload wen.tools CSV"

#### Option B: Direct Algorand Fetch
1. Enter your Algorand creator address in the sidebar
2. Click "🔍 Fetch Collection Assets"
3. Wait for the tool to discover all your NFTs

#### Option C: Manual Entry
1. Use the manual entry option for specific assets
2. Input individual asset details

### Step 4: Choose Your Pinning Service

**🏆 RECOMMENDED: 4everland**
- ✅ Thoroughly tested with this tool
- ✅ **6GB FREE** storage + 100GB bandwidth
- ✅ Only **$0.08/GB** after free tier
- ✅ Handles directory collections perfectly

**Other Services Available:**
- Pinata, NFT.Storage, Web3.Storage, Filebase, Infura
- ⚠️ These are experimental/untested - use with caution

### Step 5: Configure API Key

1. Sign up for [4everland.org](https://dashboard.4everland.org/)
2. Create or select an IPFS Bucket
3. Go to the [Pinning Service page](https://dashboard.4everland.org/bucket/pinning-service)
4. Generate and copy your **Access Token** (this is your Bearer token)
5. Paste your Bearer token into the tool
6. Click "🧪 Test API Key" to verify

### Step 6: Run Migration

1. Review your collection in the main display
2. Check the **Migration Strategy** recommendation:
   - **Directory collections**: Pin base CIDs only (efficient)
   - **Individual collections**: Pin all unique CIDs
3. Click "▶️ Start Migration"
4. Monitor real-time progress
5. Download results when complete

---

## 🎓 BEGINNER'S GUIDE TO IPFS & PINNING

### What is IPFS?
**IPFS** (InterPlanetary File System) is a distributed storage network where files are identified by unique content hashes called **CIDs** (Content Identifiers).

### Why Pin Your NFTs?
- **Problem**: IPFS nodes can go offline, making your NFT images/metadata inaccessible
- **Solution**: "Pinning" ensures your files stay available on reliable nodes
- **Result**: Your NFTs remain viewable forever

### Understanding Collection Types

#### 🔗 Individual CID Collections
```
Asset 1: ipfs://bafybeiabc123.../metadata.json
Asset 2: ipfs://bafybeifgh456.../metadata.json
Asset 3: ipfs://bafybeijkl789.../metadata.json
```
**Strategy**: Pin each unique CID (3 pins for 3 assets)

#### 📁 Directory Collections
```
Asset 1: ipfs://bafybeibase123.../image001.png
Asset 2: ipfs://bafybeibase123.../image002.png
Asset 3: ipfs://bafybeibase123.../image003.png
```
**Strategy**: Pin the base CID once (1 pin covers all 3 assets) 🎯 **MUCH CHEAPER!**

---

## 💰 COST ESTIMATION

### 4everland Pricing (Recommended)
- **FREE TIER**: 6GB storage + 100GB bandwidth/month
- **PAID**: $0.08/GB storage + $0.08/GB bandwidth

### Example Collections:
- **Small collection** (50 assets, ~100MB): **FREE**
- **Medium collection** (500 assets, ~1GB): **FREE**
- **Large collection** (5000 assets, ~10GB): **~$0.32/month**
- **Directory collection** (1000 assets sharing 1 base CID): **Often FREE**

---

## 🛠️ TROUBLESHOOTING

### Common Issues

#### "No assets found"
- ✅ Verify your creator address is correct
- ✅ Ensure you've actually created NFTs with that address
- ✅ Try using wen.tools CSV method instead

#### "API connection failed"  
- ✅ Check your API key is correct
- ✅ Verify internet connection
- ✅ Try the "🧪 Test API Key" button

#### "Invalid CID format"
- ✅ Your NFTs may use non-standard IPFS URLs
- ✅ Try manual entry mode
- ✅ Contact support with your collection details

#### Migration shows "completed" but CSV still shows "pending"
- ✅ This was a known bug that's been fixed
- ✅ Try clicking "🔄 Refresh Data"
- ✅ Check the debug panel for real-time status

### Getting Help
1. Check the **Debug Panel** (expand at bottom of interface)
2. Enable debug mode: `streamlit run app.py --logger.level=debug`
3. Join our community Discord (link on cyberskulls.app)
4. Contact support: markus@cyberskulls.app

---

## ⚙️ ADVANCED FEATURES

### Collection Analysis
- Automatically detects directory vs individual CID structures
- Recommends optimal pinning strategies
- Shows efficiency gains (e.g., "Pin 1 CID to cover 162 assets")

### Smart Pinning Strategies
- **Directory Collections**: Pin base CIDs only (recommended)
- **Individual Collections**: Pin all unique CIDs
- **Mixed Collections**: Pin unique CIDs only (avoids duplicates)

### Verification & Monitoring
- Real-time status tracking during migration
- Pin verification to confirm successful uploads
- Detailed error reporting and retry functionality

### Export Options
- CSV export for spreadsheet analysis
- JSON export for programmatic access
- Status preservation across sessions

---

## 🔒 SECURITY & PRIVACY

- ✅ API keys stored locally only (never transmitted to us)
- ✅ All IPFS operations use secure HTTPS
- ✅ No personal data collected or stored
- ✅ Open source code for transparency

---

## 🌐 SUPPORTED SERVICES

### ✅ TESTED & RECOMMENDED
- **4everland** - Fully tested, optimized for NFT collections

### ⚠️ EXPERIMENTAL
- **Pinata** - Basic implementation (1GB free, $0.20/GB after)
- **NFT.Storage** - Basic implementation (free but limited)
- **Web3.Storage** - Basic implementation (free but limited)
- **Filebase** - Basic implementation ($5.99/month minimum)
- **Infura** - Basic implementation (5GB free, $0.50/GB after)

**Warning**: Experimental services may have compatibility issues with directory collections and limited error handling.

---

## 📖 ADDITIONAL RESOURCES

- **Official Website**: [cyberskulls.app](https://www.cyberskulls.app)
- **wen.tools**: [wen.tools](https://www.wen.tools) (CSV export for Algorand collections)
- **4everland**: [4everland.org](https://dashboard.4everland.org) (recommended pinning service)
- **IPFS Documentation**: [docs.ipfs.io](https://docs.ipfs.io)
- **Algorand Developer Portal**: [developer.algorand.org](https://developer.algorand.org)

---

## 🏴‍☠️ SUPPORT THE PROJECT

If this tool saved you time and money, consider supporting the Cyber Skulls project by buying our token:

**🪙 CYBER Token (CY💀)**  
**[Buy on Vestige DEX →](https://vestige.fi/asset/1141259202)**

- **Asset ID**: 1141259202
- **Ticker**: CY💀  
- **Current Price**: $0.0014
- **Market Cap**: $7,001

Your support helps us continue developing free tools for the Algorand NFT community!

---

## ⚡ CYBER SKULLS PROJECT

**Created by ThΞOneTwo (Markus Jensen)**  
🇩🇰 Denmark | AI & Graphic Design  

**Mission**: Creating tools and projects that community members can be proud to be part of. Combining artistic vision with technological innovation to build something truly unique in the crypto space.

---

*CYBER SKULLS REPINNING PROTOCOL v2.1 // OPTIMIZED FOR 4EVERLAND // CREATED BY ThΞOneTwo*

## 🌐 Gateway Risk Tester

A companion tool to analyze IPFS gateway availability and assess redundancy risk for your NFT collections.

### Features
- 👛 **Wallet Analysis**: Automatically test random assets from any Algorand wallet
- 🎯 **Strategic Sampling**: Tests assets from different parts of collections
- 📊 **Risk Assessment**: Categorizes CIDs by availability risk level
- 🌐 **Gateway Performance**: Real-time analysis of IPFS gateway reliability

### Quick Start
```bash
python run_gateway_tester.py
# Or double-click: run_gateway_tester.bat (Windows)
```

### Live Demo
🔗 [Gateway Risk Tester](https:/gatewaytester.streamlit.app) 