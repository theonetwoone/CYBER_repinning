import streamlit as st
import pandas as pd
import requests
import random
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import utils  # Import our existing utils

# Try to import plotly, but make it optional
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="🌐 IPFS Gateway Risk Tester",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with cyber theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
    
    .main-header {
        font-family: 'VT323', monospace;
        font-size: 3rem;
        color: #00FF41;
        text-align: center;
        text-shadow: 0 0 10px #00FF41;
        margin-bottom: 2rem;
    }
    
    .cyber-box {
        border: 2px solid #00FF41;
        border-radius: 10px;
        padding: 1rem;
        background: rgba(0, 255, 65, 0.1);
        margin: 1rem 0;
    }
    
    .risk-high {
        color: #FF4444;
        font-weight: bold;
    }
    
    .risk-medium {
        color: #FFAA44;
        font-weight: bold;
    }
    
    .risk-low {
        color: #44FF44;
        font-weight: bold;
    }
    
    .gateway-stats {
        font-family: 'VT323', monospace;
        font-size: 1.1rem;
    }
    
    .stSelectbox > div > div > div {
        background-color: #0a0a0a;
        color: #00FF41;
    }
</style>
""", unsafe_allow_html=True)

class IPFSGatewayTesterUI:
    def __init__(self):
        # Comprehensive list organized by risk level
        self.reliable_gateways = [
            "https://ipfs.io/ipfs/",
            "https://gateway.ipfs.io/ipfs/",
            "https://dweb.link/ipfs/",
            "https://cloudflare-ipfs.com/ipfs/",
            "https://cf-ipfs.com/ipfs/",
        ]
        
        self.pinning_service_gateways = {
            "https://gateway.pinata.cloud/ipfs/": "Pinata",
            "https://infura-ipfs.io/ipfs/": "Infura", 
            "https://ipfs.fleek.co/ipfs/": "Fleek",
        }
        
        # CRITICAL: old.web3.storage gateways (shutting down)
        self.old_web3_storage_gateways = {
            "https://nftstorage.link/ipfs/": "NFT.Storage",
            "https://w3s.link/ipfs/": "Web3.Storage"
        }
        
        self.other_public_gateways = [
            "https://gateway.temporal.cloud/ipfs/",
            "https://hardbin.com/ipfs/",
            "https://gateway.originprotocol.com/ipfs/",
            "https://ipfs.best-practice.se/ipfs/",
            "https://jorropo.net/ipfs/",
            "https://ipfs.joaoleitao.org/ipfs/",
            "https://ipfs.telos.miami/ipfs/",
        ]
        
        # Combined list for random selection
        self.all_gateways = (self.reliable_gateways + 
                           list(self.pinning_service_gateways.keys()) + 
                           list(self.old_web3_storage_gateways.keys()) + 
                           self.other_public_gateways)
        
        # FIXED: Gateway type mapping (dictionary, not list)
        self.gateway_types = {}
        
        # Populate gateway types
        for gw in self.reliable_gateways:
            self.gateway_types[gw] = "reliable_public"
        for gw in self.pinning_service_gateways.keys():
            self.gateway_types[gw] = "pinning_service"
        for gw in self.old_web3_storage_gateways.keys():
            self.gateway_types[gw] = "old_web3_storage"
        for gw in self.other_public_gateways:
            self.gateway_types[gw] = "other_public"

    def select_random_gateways(self, count: int = 5) -> List[str]:
        """Select random gateways for testing."""
        return random.sample(self.all_gateways, min(count, len(self.all_gateways)))

    def test_gateway_availability(self, gateway_url: str, cid: str, timeout: int = 10) -> Tuple[bool, str, float]:
        """Test if a CID is available through a specific IPFS gateway."""
        start_time = time.time()
        try:
            url = f"{gateway_url}{cid}"
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return True, f"✅ Available (HTTP {response.status_code})", response_time
            else:
                return False, f"❌ HTTP {response.status_code}", response_time
                
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return False, "⏰ Timeout", response_time
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            return False, "🔌 Connection Error", response_time
        except Exception as e:
            response_time = time.time() - start_time
            return False, f"❌ Error: {str(e)[:50]}", response_time

    def test_multiple_cids_with_progress(self, cids: List[str], gateways: List[str], progress_bar, status_text) -> Dict:
        """Enhanced testing with proper risk assessment and shutdown analysis."""
        total_tests = len(cids) * len(gateways)
        completed_tests = 0
        
        all_results = []
        risk_analysis = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': [],
            'unreachable': [],
            'gateway_performance': {},
            'pinning_services': {}
        }
        
        # Initialize gateway performance tracking
        for gateway in gateways:
            risk_analysis['gateway_performance'][gateway] = {
                'success_count': 0,
                'total_tests': 0,
                'avg_response_time': 0,
                'total_response_time': 0,
                'successful_cids': []
            }
        
        # Initialize pinning service tracking
        for gateway, service_name in self.pinning_service_gateways.items():
            if gateway in gateways:
                risk_analysis['pinning_services'][service_name] = {
                    'available_cids': [],
                    'total_tested': 0,
                    'success_rate': 0
                }
        
        for i, cid in enumerate(cids):
            status_text.text(f"🔍 Testing CID {i+1}/{len(cids)}: {cid[:20]}...")
            
            cid_result = {
                'cid': cid,
                'gateway_results': {},
                'pinning_services_available': [],
                'summary': {
                    'total_gateways': len(gateways),
                    'available_count': 0,
                    'pinning_service_count': 0,
                    'old_web3_storage_count': 0,
                    'reliable_public_count': 0,
                    'fastest_gateway': None,
                    'fastest_time': float('inf'),
                    'network_available': False
                }
            }
            
            # Test each gateway for this CID
            for gateway in gateways:
                is_available, status, response_time = self.test_gateway_availability(gateway, cid, timeout=8)
                
                # FIXED: Use dictionary lookup instead of list.get()
                gateway_type = self.gateway_types.get(gateway, "unknown")
                
                cid_result['gateway_results'][gateway] = {
                    'available': is_available,
                    'status': status,
                    'response_time': response_time,
                    'gateway_type': gateway_type
                }
                
                # Update gateway performance stats
                stats = risk_analysis['gateway_performance'][gateway]
                stats['total_tests'] += 1
                stats['total_response_time'] += response_time
                
                if is_available:
                    cid_result['summary']['available_count'] += 1
                    cid_result['summary']['network_available'] = True
                    stats['success_count'] += 1
                    stats['successful_cids'].append(cid)
                    
                    # Categorize by gateway type
                    if gateway_type == "pinning_service":
                        cid_result['summary']['pinning_service_count'] += 1
                        service_name = self.pinning_service_gateways.get(gateway, "Unknown")
                        cid_result['pinning_services_available'].append(service_name)
                        risk_analysis['pinning_services'][service_name]['available_cids'].append(cid)
                    elif gateway_type == "old_web3_storage":
                        cid_result['summary']['old_web3_storage_count'] += 1
                    elif gateway_type == "reliable_public":
                        cid_result['summary']['reliable_public_count'] += 1
                    
                    if response_time < cid_result['summary']['fastest_time']:
                        cid_result['summary']['fastest_time'] = response_time
                        cid_result['summary']['fastest_gateway'] = gateway
                
                completed_tests += 1
                progress_bar.progress(completed_tests / total_tests)
            
            # Risk assessment based on actual storage guarantees
            pinning_count = cid_result['summary']['pinning_service_count']
            old_web3_count = cid_result['summary']['old_web3_storage_count']
            network_available = cid_result['summary']['network_available']
            
            if not network_available:
                risk_analysis['unreachable'].append(cid_result)
            elif pinning_count == 0 and old_web3_count > 0:
                risk_analysis['high_risk'].append(cid_result)  # Only on shutting-down services
            elif pinning_count == 0:
                risk_analysis['high_risk'].append(cid_result)  # No confirmed pinning services
            elif pinning_count == 1:
                risk_analysis['medium_risk'].append(cid_result)  # Single point of failure
            else:
                risk_analysis['low_risk'].append(cid_result)  # Good redundancy
            
            all_results.append(cid_result)
        
        # Calculate final gateway performance stats
        for gateway, stats in risk_analysis['gateway_performance'].items():
            if stats['total_tests'] > 0:
                stats['success_rate'] = stats['success_count'] / stats['total_tests']
                stats['avg_response_time'] = stats['total_response_time'] / stats['total_tests']
            else:
                stats['success_rate'] = 0
                stats['avg_response_time'] = 0
        
        # Calculate pinning service stats
        for service_name, service_stats in risk_analysis['pinning_services'].items():
            service_stats['total_tested'] = len(cids)
            if service_stats['total_tested'] > 0:
                service_stats['success_rate'] = len(service_stats['available_cids']) / service_stats['total_tested']
        
        return {
            'individual_results': all_results,
            'risk_analysis': risk_analysis,
            'summary': {
                'total_cids_tested': len(cids),
                'gateways_used': gateways,
                'high_risk_count': len(risk_analysis['high_risk']),
                'medium_risk_count': len(risk_analysis['medium_risk']),
                'low_risk_count': len(risk_analysis['low_risk']),
                'unreachable_count': len(risk_analysis['unreachable']),
                'pinning_services_tested': list(risk_analysis['pinning_services'].keys())
            }
        }

    def check_4everland_via_api(self, cid: str, api_key: str = None) -> Tuple[bool, str]:
        """Check if a CID exists on 4everland via their API."""
        if not api_key:
            return False, "No API key provided"
        
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"https://api.4everland.dev/pins?cid={cid}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                pins = data.get('results', [])
                for pin in pins:
                    if pin.get('pin', {}).get('cid') == cid and pin.get('status') == 'pinned':
                        return True, "✅ Pinned on 4everland"
                return False, "❌ Not pinned on 4everland"
            else:
                return False, f"❌ API Error: {response.status_code}"
                
        except Exception as e:
            return False, f"❌ Error: {str(e)[:50]}"

    def analyze_shutdown_risk(self, cid_results: List[Dict]) -> Dict:
        """Analyze old.web3.storage shutdown risk."""
        shutdown_analysis = {
            'critical_risk': [],      # Only on old.web3.storage
            'at_risk': [],           # Available elsewhere but also on old.web3.storage  
            'safe': [],              # Not dependent on old.web3.storage
            'unreachable': []        # Not available anywhere
        }
        
        for result in cid_results:
            # Check availability on different gateway types
            old_web3_available = []
            other_available = []
            
            for gateway, gw_result in result['gateway_results'].items():
                if gw_result['available']:
                    if gateway in self.old_web3_storage_gateways:
                        service_name = self.old_web3_storage_gateways[gateway]
                        old_web3_available.append(service_name)
                    else:
                        other_available.append(gateway)
            
            # Add shutdown analysis to result
            result['shutdown_analysis'] = {
                'old_web3_services': old_web3_available,
                'other_sources': len(other_available),
                'total_available': len(old_web3_available) + len(other_available)
            }
            
            # Categorize shutdown risk
            if result['shutdown_analysis']['total_available'] == 0:
                shutdown_analysis['unreachable'].append(result)
            elif len(other_available) == 0 and len(old_web3_available) > 0:
                shutdown_analysis['critical_risk'].append(result)  # ONLY on old.web3.storage
            elif len(old_web3_available) > 0:
                shutdown_analysis['at_risk'].append(result)        # Available elsewhere but depends on old.web3.storage
            else:
                shutdown_analysis['safe'].append(result)           # Not dependent on old.web3.storage
        
        return shutdown_analysis

def extract_cids_from_assets(assets: List[dict]) -> List[str]:
    """Enhanced CID extraction with better debugging and filtering."""
    cids = []
    successful_extractions = 0
    failed_extractions = 0
    
    print(f"🔍 DEBUG: Starting CID extraction from {len(assets)} assets...")
    
    for asset in assets:
        asset_id = asset.get('index', 'Unknown')
        asset_name = asset.get('params', {}).get('name', 'Unknown')
        
        try:
            # Try metadata CID first
            metadata_cid = utils.extract_cid_from_asset(asset)
            
            if metadata_cid:
                cids.append(metadata_cid)
                successful_extractions += 1
                print(f"✅ Asset {asset_id} ({asset_name}): {metadata_cid[:20]}...")
                
                # For ARC-19, also try to get image CID
                asset_params = asset.get('params', {})
                arc_standard = utils.detect_arc_standard(asset_params)
                
                if arc_standard == 'arc19':
                    try:
                        image_cid, _ = utils.fetch_metadata_and_extract_image_cid(metadata_cid)
                        if image_cid and image_cid != metadata_cid:
                            cids.append(image_cid)
                            print(f"🖼️ Asset {asset_id} image CID: {image_cid[:20]}...")
                    except Exception as e:
                        print(f"⚠️ Failed to fetch image CID for {asset_id}: {str(e)}")
            else:
                failed_extractions += 1
                # Debug why extraction failed
                asset_params = asset.get('params', {})
                url = asset_params.get('url', '')
                reserve = asset_params.get('reserve', '')
                
                print(f"❌ Asset {asset_id} ({asset_name}): No CID extracted")
                print(f"   URL: {url[:50] if url else 'None'}...")
                print(f"   Reserve: {'Present' if reserve else 'None'}")
                print(f"   Deleted: {asset.get('deleted', False)}")
                
        except Exception as e:
            failed_extractions += 1
            print(f"❌ Error processing asset {asset_id}: {str(e)}")
    
    unique_cids = list(set(cids))  # Remove duplicates
    print(f"📊 Extraction Summary:")
    print(f"   ✅ Successful: {successful_extractions}")
    print(f"   ❌ Failed: {failed_extractions}")
    print(f"   🎯 Unique CIDs: {len(unique_cids)}")
    
    return unique_cids

def sample_assets_strategically(assets: List[dict], sample_size: int = 5) -> List[dict]:
    """Enhanced strategic sampling with better filtering."""
    print(f"🎯 Starting strategic sampling from {len(assets)} total assets...")
    
    # Filter out deleted and invalid assets first
    valid_assets = []
    for asset in assets:
        if asset.get('deleted', False):
            continue
            
        # Check if asset has any useful data
        asset_params = asset.get('params', {})
        url = asset_params.get('url', '')
        reserve = asset_params.get('reserve', '')
        
        # Keep assets that have either URL or reserve field
        if url or reserve:
            valid_assets.append(asset)
    
    print(f"📋 Filtered to {len(valid_assets)} valid assets")
    
    if len(valid_assets) <= sample_size:
        print(f"🎯 Using all {len(valid_assets)} valid assets")
        return valid_assets
    
    sampled = []
    total = len(valid_assets)
    
    # Take from different segments for diversity
    segments = [
        (0, min(10, total)),                         # Beginning (first 10)
        (total//4, total//4 + 10),                  # First quarter
        (total//2 - 5, total//2 + 5),               # Middle
        (3*total//4, 3*total//4 + 10),              # Third quarter
        (max(0, total-10), total)                    # End (last 10)
    ]
    
    print(f"🔍 Sampling from {len(segments)} segments...")
    
    # Sample one from each segment
    for i, (start, end) in enumerate(segments):
        if len(sampled) < sample_size and start < total:
            segment_assets = valid_assets[start:min(end, total)]
            if segment_assets:
                # Try to pick an asset that's likely to have a CID
                selected = None
                for asset in segment_assets:
                    asset_params = asset.get('params', {})
                    url = asset_params.get('url', '')
                    # Prioritize assets with IPFS URLs or template URLs
                    if url.startswith('ipfs://') or url.startswith('template-ipfs://'):
                        selected = asset
                        break
                
                if not selected:
                    selected = random.choice(segment_assets)
                
                sampled.append(selected)
                asset_name = selected.get('params', {}).get('name', 'Unknown')
                asset_id = selected.get('index', 'Unknown')
                print(f"   Segment {i+1}: Asset {asset_id} ({asset_name})")
    
    # Fill remaining slots with random samples from different areas
    remaining_assets = [a for a in valid_assets if a not in sampled]
    while len(sampled) < sample_size and remaining_assets:
        # Pick randomly but try to avoid clustering
        random_asset = random.choice(remaining_assets)
        sampled.append(random_asset)
        remaining_assets.remove(random_asset)
        
        asset_name = random_asset.get('params', {}).get('name', 'Unknown')
        asset_id = random_asset.get('index', 'Unknown')
        print(f"   Random: Asset {asset_id} ({asset_name})")
    
    print(f"✅ Strategic sampling complete: {len(sampled)} assets selected")
    return sampled

def create_simple_charts(results):
    """Updated charts with corrected risk understanding."""
    
    # Risk distribution chart
    st.markdown("### 📈 Risk Distribution (Based on Actual Pinning)")
    risk_data = {
        'High Risk': results['summary']['high_risk_count'],
        'Medium Risk': results['summary']['medium_risk_count'], 
        'Low Risk': results['summary']['low_risk_count'],
        'Unreachable': results['summary']['unreachable_count']
    }
    st.bar_chart(risk_data)
    
    # Gateway type availability
    st.markdown("### 🌐 Gateway Type Analysis")
    
    # Aggregate gateway type stats
    type_stats = {
        'Pinning Services': 0,
        'Public Access': 0,
        'Deprecated': 0
    }
    
    for result in results['individual_results']:
        if result['summary']['pinning_service_count'] > 0:
            type_stats['Pinning Services'] += 1
        if result['summary']['old_web3_storage_count'] > 0:
            type_stats['Deprecated'] += 1
        if result['summary']['reliable_public_count'] > 0:
            type_stats['Public Access'] += 1
    
    st.bar_chart(type_stats)

def create_plotly_charts(results):
    """Create fancy charts using Plotly (if available)."""
    
    # Risk distribution pie chart
    st.markdown("### 📈 Risk Distribution")
    
    risk_data = {
        'Risk Level': ['High Risk', 'Medium Risk', 'Low Risk', 'Unreachable'],
        'Count': [
            results['summary']['high_risk_count'],
            results['summary']['medium_risk_count'], 
            results['summary']['low_risk_count'],
            results['summary']['unreachable_count']
        ],
        'Color': ['#FF4444', '#FFAA44', '#44FF44', '#888888']
    }
    
    fig = px.pie(
        values=risk_data['Count'], 
        names=risk_data['Risk Level'],
        color_discrete_sequence=risk_data['Color'],
        title="CID Risk Distribution"
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Gateway performance chart
    st.markdown("### 🌐 Gateway Performance")
    
    perf_data = results['risk_analysis']['gateway_performance']
    gateway_names = [gw.replace('https://', '').replace('/ipfs/', '') for gw in perf_data.keys()]
    success_rates = [stats['success_rate'] * 100 for stats in perf_data.values()]
    response_times = [stats['avg_response_time'] for stats in perf_data.values()]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Success Rate (%)', 'Average Response Time (s)'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    fig.add_trace(
        go.Bar(x=gateway_names, y=success_rates, name="Success Rate", marker_color='#00FF41'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=gateway_names, y=response_times, name="Response Time", marker_color='#FF6B6B'),
        row=1, col=2
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        showlegend=False
    )
    
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.markdown('<h1 class="main-header">🌐 IPFS Gateway Risk Tester 🛡️</h1>', unsafe_allow_html=True)
    
    # Show plotly status
    if not PLOTLY_AVAILABLE:
        st.info("📊 Using simplified charts (plotly not installed). Install plotly for enhanced visualizations.")
    
    tester = IPFSGatewayTesterUI()
    
    # Sidebar configuration
    st.sidebar.markdown("## ⚙️ Configuration")
    
    num_gateways = st.sidebar.slider("🌐 Number of gateways to test", 5, 15, 10)
    
    # IMPORTANT: Always include old.web3.storage gateways for shutdown analysis
    include_old_web3 = st.sidebar.checkbox(
        "🚨 Include old.web3.storage gateways", 
        value=True,
        help="Essential for detecting shutdown risk"
    )
    
    # NEW: 4everland API key option
    st.sidebar.markdown("### 🔒 4everland API Check")
    everland_api_key = st.sidebar.text_input(
        "4everland API Key (optional)",
        type="password",
        help="Enter your 4everland API key to check if CIDs are pinned there"
    )
    
    st.sidebar.markdown("## 🎯 Testing Options")
    
    test_mode = st.sidebar.radio(
        "Choose testing mode:",
        ["🎲 Quick Test (Random CIDs)", "📝 Manual CID Entry", "👛 Wallet Analysis", "📄 File Upload"],
        index=2  # Default to Wallet Analysis
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown('<div class="cyber-box">', unsafe_allow_html=True)
        st.markdown("### 🛡️ Risk Levels")
        st.markdown('<span class="risk-high">🔴 HIGH:</span> Only on shutting-down gateways', unsafe_allow_html=True)
        st.markdown('<span class="risk-medium">🟡 MEDIUM:</span> Available on few gateways', unsafe_allow_html=True)
        st.markdown('<span class="risk-low">🟢 LOW:</span> Widely available', unsafe_allow_html=True)
        st.markdown("⚫ **UNREACHABLE:** Not found anywhere")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col1:
        cids_to_test = []
        
        if test_mode == "🎲 Quick Test (Random CIDs)":
            st.markdown("### 🎲 Quick Random Test")
            st.info("Test well-known CIDs to check gateway performance")
            
            num_test_cids = st.slider("Number of test CIDs", 1, 10, 5)
            
            known_test_cids = [
                "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",  # README from IPFS
                "QmZULkCELmmk5XNfCgTnCyFgAVxBRBXyDHGGMVoLFLiXEN",  # Hello World
                "QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o",  # Test file
                "QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc",  # Common test CID
                "QmSrCRJmzE4zE1nAfWPbzVfanKQNBhp7ZWmMnEdkAAUEgh",  # Another common one
                "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi", # CIDv1 example 
                "bafkreifjjcie6lypi6ny7amxnfftagclbuxndqonfipmb64f2km2devei4", # Another CIDv1
            ]
            
            if st.button("🚀 Start Quick Test"):
                cids_to_test = random.sample(known_test_cids, min(num_test_cids, len(known_test_cids)))
        
        elif test_mode == "📝 Manual CID Entry":
            st.markdown("### 📝 Manual CID Entry")
            cid_input = st.text_area(
                "Enter CIDs (one per line):",
                placeholder="QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG\nbafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
                height=100
            )
            
            if st.button("🔍 Test These CIDs"):
                cids_to_test = [cid.strip() for cid in cid_input.split('\n') if cid.strip()]
        
        elif test_mode == "👛 Wallet Analysis":
            st.markdown("### 👛 Algorand Wallet Analysis")
            st.info("Automatically fetch and test random assets from an Algorand wallet")
            
            wallet_address = st.text_input(
                "Algorand Wallet Address:",
                placeholder="ANT36DHMAAUWZ3LPTRE7WNPQILWKJN24F66VQA22NIJ5D5CQDBB5333ZEU"
            )
            
            sample_size = st.slider("Number of random assets to test", 1, 15, 8)  # Increased max and default
            
            if st.button("🔍 Analyze Wallet Assets") and wallet_address:
                with st.spinner("🔎 Fetching wallet assets..."):
                    try:
                        # Fetch all assets from wallet
                        assets, error = utils.get_all_creator_assets(wallet_address)
                        
                        if error:
                            st.error(f"❌ Error fetching assets: {error}")
                        elif not assets:
                            st.warning("⚠️ No assets found in this wallet")
                        else:
                            st.success(f"✅ Found {len(assets)} total assets in wallet")
                            
                            # Show asset breakdown
                            deleted_count = sum(1 for a in assets if a.get('deleted', False))
                            valid_count = len(assets) - deleted_count
                            
                            with st.expander("📊 Asset Breakdown"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Assets", len(assets))
                                with col2:
                                    st.metric("Valid Assets", valid_count)
                                with col3:
                                    st.metric("Deleted Assets", deleted_count)
                            
                            # Sample assets strategically
                            sampled_assets = sample_assets_strategically(assets, sample_size)
                            st.info(f"🎯 Selected {len(sampled_assets)} assets from different parts of the collection")
                            
                            # Show selected assets
                            with st.expander("🔍 Selected Assets"):
                                for i, asset in enumerate(sampled_assets):
                                    asset_name = asset.get('params', {}).get('name', 'Unknown')
                                    asset_id = asset.get('index', 'Unknown')
                                    asset_url = asset.get('params', {}).get('url', '')[:50]
                                    st.write(f"{i+1}. **{asset_name}** (ID: {asset_id}) - URL: {asset_url}...")
                            
                            # Extract CIDs from selected assets with detailed output
                            with st.expander("🔧 CID Extraction Process", expanded=True):
                                # Capture the extraction output
                                import io
                                import sys
                                
                                # Redirect stdout to capture print statements
                                old_stdout = sys.stdout
                                sys.stdout = buffer = io.StringIO()
                                
                                try:
                                    cids_to_test = extract_cids_from_assets(sampled_assets)
                                finally:
                                    sys.stdout = old_stdout
                                
                                # Display the captured output
                                output = buffer.getvalue()
                                if output:
                                    st.text(output)
                            
                            if cids_to_test:
                                st.success(f"🎯 Extracted {len(cids_to_test)} unique CIDs for testing!")
                                
                                # Show the CIDs that will be tested
                                with st.expander("📋 CIDs to Test"):
                                    for i, cid in enumerate(cids_to_test):
                                        st.code(f"{i+1}. {cid}")
                            else:
                                st.error("❌ No valid CIDs found in selected assets!")
                                st.info("""
                                **Possible reasons:**
                                - Assets don't follow ARC-19, ARC-69, or standard IPFS formats
                                - Assets have HTTP URLs instead of IPFS URLs
                                - Assets are deleted or have malformed metadata
                                - Try increasing the sample size or check different assets
                                """)
                    
                    except Exception as e:
                        st.error(f"❌ Error analyzing wallet: {str(e)}")
                        st.exception(e)  # Show full traceback for debugging
        
        elif test_mode == "📄 File Upload":
            st.markdown("### 📄 File Upload")
            uploaded_file = st.file_uploader(
                "Upload a text file with CIDs (one per line)",
                type=['txt']
            )
            
            if uploaded_file and st.button("🔍 Test CIDs from File"):
                try:
                    content = uploaded_file.read().decode('utf-8')
                    cids_to_test = [cid.strip() for cid in content.split('\n') if cid.strip()]
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
    
    # Run the test if we have CIDs
    if cids_to_test:
        st.markdown("---")
        st.markdown(f"### 🚀 Testing {len(cids_to_test)} CID(s)")
        
        # Smart gateway selection
        selected_gateways = []
        
        # Always include old.web3.storage gateways if enabled
        if include_old_web3:
            selected_gateways.extend(list(tester.old_web3_storage_gateways.keys()))
        
        # Add pinning service gateways
        selected_gateways.extend(list(tester.pinning_service_gateways.keys()))
        
        # Add reliable gateways
        selected_gateways.extend(tester.reliable_gateways[:3])
        
        # Fill remaining slots with other gateways
        remaining_slots = max(0, num_gateways - len(selected_gateways))
        if remaining_slots > 0:
            available_others = [gw for gw in tester.other_public_gateways if gw not in selected_gateways]
            selected_gateways.extend(random.sample(available_others, min(remaining_slots, len(available_others))))
        
        # Limit to requested number
        selected_gateways = selected_gateways[:num_gateways]
        
        st.info(f"🌐 Testing with {len(selected_gateways)} gateways (including old.web3.storage for shutdown analysis)")
        
        with st.expander("🔍 View Selected Gateways"):
            for gw in selected_gateways:
                gateway_name = gw.replace('https://', '').replace('/ipfs/', '')
                
                if gw in tester.old_web3_storage_gateways:
                    badge = "🚨 OLD.WEB3.STORAGE (SHUTTING DOWN)"
                elif gw in tester.pinning_service_gateways:
                    service_name = tester.pinning_service_gateways[gw]
                    badge = f"🔒 {service_name.upper()} SERVICE"
                elif gw in tester.reliable_gateways:
                    badge = "🟢 RELIABLE PUBLIC"
                else:
                    badge = "🌐 PUBLIC ACCESS"
                    
                st.write(f"• {gateway_name} {badge}")
        
        # Run the test
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner("🧪 Running gateway tests..."):
            results = tester.test_multiple_cids_with_progress(
                cids_to_test, 
                selected_gateways, 
                progress_bar,
                status_text
            )
        
        # NEW: Add 4everland API check if API key provided
        if everland_api_key:
            status_text.text("🔍 Checking 4everland via API...")
            everland_results = {}
            
            for cid in cids_to_test:
                is_pinned, status = tester.check_4everland_via_api(cid, everland_api_key)
                everland_results[cid] = {
                    'pinned': is_pinned,
                    'status': status
                }
            
            # Add 4everland results to the main results
            if 'api_services' not in results['risk_analysis']:
                results['risk_analysis']['api_services'] = {}
            
            results['risk_analysis']['api_services']['4everland'] = {
                'results': everland_results,
                'total_pinned': sum(1 for r in everland_results.values() if r['pinned']),
                'total_tested': len(everland_results)
            }
        
        status_text.text("✅ Testing complete!")
        progress_bar.progress(1.0)
        
        # ENHANCED: Shutdown Risk Analysis
        if include_old_web3:
            shutdown_analysis = tester.analyze_shutdown_risk(results['individual_results'])
            
            st.markdown("---")
            st.markdown("## 🚨 OLD.WEB3.STORAGE SHUTDOWN ANALYSIS")
            
            # Shutdown risk metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                critical_count = len(shutdown_analysis['critical_risk'])
                st.metric(
                    "🚨 CRITICAL", 
                    critical_count,
                    help="Only available on old.web3.storage - will be lost when it shuts down"
                )
            
            with col2:
                at_risk_count = len(shutdown_analysis['at_risk'])
                st.metric(
                    "⚠️ AT RISK", 
                    at_risk_count,
                    help="Available elsewhere but currently depends on old.web3.storage"
                )
            
            with col3:
                safe_count = len(shutdown_analysis['safe'])
                st.metric(
                    "✅ SAFE", 
                    safe_count,
                    help="Not dependent on old.web3.storage"
                )
            
            with col4:
                unreachable_count = len(shutdown_analysis['unreachable'])
                st.metric(
                    "⚫ UNREACHABLE", 
                    unreachable_count,
                    help="Not available anywhere"
                )
            
            # Detailed shutdown risk table
            st.markdown("### 🚨 Shutdown Risk Details")
            
            shutdown_data = []
            
            # Process all results for shutdown analysis
            for result in results['individual_results']:
                cid = result['cid']
                shutdown_info = result.get('shutdown_analysis', {})
                old_web3_services = shutdown_info.get('old_web3_services', [])
                other_sources = shutdown_info.get('other_sources', 0)
                
                # Add 4everland info if available
                everland_status = ""
                if everland_api_key and 'api_services' in results['risk_analysis']:
                    everland_data = results['risk_analysis']['api_services']['4everland']['results'].get(cid, {})
                    if everland_data.get('pinned'):
                        everland_status = " + 4everland"
                        other_sources += 1  # Count 4everland as another source
                
                # Determine shutdown risk
                if other_sources == 0 and len(old_web3_services) > 0:
                    shutdown_risk = "🚨 CRITICAL - Will be lost"
                    action_needed = "URGENT: Re-pin immediately"
                elif len(old_web3_services) > 0:
                    shutdown_risk = "⚠️ AT RISK - Currently depends on old.web3.storage"  
                    action_needed = "RECOMMENDED: Verify other sources"
                elif other_sources > 0:
                    shutdown_risk = "✅ SAFE - Not dependent"
                    action_needed = "None"
                else:
                    shutdown_risk = "⚫ UNREACHABLE"
                    action_needed = "Already lost"
                
                shutdown_data.append({
                    'CID': f"{cid[:20]}..." if len(cid) > 20 else cid,
                    'Shutdown Risk': shutdown_risk,
                    'Old.Web3.Storage': ', '.join(old_web3_services) or "Not found",
                    'Other Sources': f"{other_sources} sources{everland_status}",
                    'Action Needed': action_needed
                })
            
            df_shutdown = pd.DataFrame(shutdown_data)
            st.dataframe(df_shutdown, use_container_width=True)
            
            # Urgent warnings
            if critical_count > 0:
                st.error(f"""
                🚨 **URGENT ACTION REQUIRED**
                
                {critical_count} CID(s) are ONLY available on old.web3.storage services!
                
                These will be **completely lost** when old.web3.storage shuts down.
                You must re-pin these CIDs on other services immediately.
                """)
            
            if at_risk_count > 0:
                st.warning(f"""
                ⚠️ **VERIFICATION RECOMMENDED**
                
                {at_risk_count} CID(s) are available on other sources but also found on old.web3.storage.
                
                Verify these are properly stored elsewhere to avoid any dependency on the shutting-down service.
                """)
            
            if safe_count > 0:
                st.success(f"""
                ✅ **{safe_count} CID(s) are SAFE from the shutdown**
                
                These CIDs are not dependent on old.web3.storage services.
                """)
        
        # Enhanced pinning services display (including 4everland)
        st.markdown("---")
        st.markdown("## 🔒 Pinning Services Verification")
        
        # Gateway-based services + API services
        gateway_services = results['summary'].get('pinning_services_tested', [])
        api_services = []
        
        if everland_api_key and 'api_services' in results['risk_analysis']:
            api_services.append('4everland')
        
        total_services = len(gateway_services) + len(api_services)
        if total_services > 0:
            service_cols = st.columns(total_services)
            
            col_index = 0
            
            # Display gateway-based services
            for service_name in gateway_services:
                with service_cols[col_index]:
                    service_stats = results['risk_analysis']['pinning_services'][service_name]
                    success_rate = service_stats['success_rate'] * 100
                    available_count = len(service_stats['available_cids'])
                    
                    st.metric(
                        f"🌐 {service_name}",
                        f"{available_count} CIDs",
                        f"{success_rate:.1f}% available"
                    )
                col_index += 1
            
            # Display API-based services (4everland)
            for service_name in api_services:
                with service_cols[col_index]:
                    if service_name == '4everland':
                        api_data = results['risk_analysis']['api_services']['4everland']
                        pinned_count = api_data['total_pinned']
                        total_count = api_data['total_tested']
                        success_rate = (pinned_count / total_count * 100) if total_count > 0 else 0
                        
                        st.metric(
                            f"🔒 {service_name}",
                            f"{pinned_count} CIDs",
                            f"{success_rate:.1f}% pinned"
                        )
                col_index += 1
        
        # Enhanced detailed results
        st.markdown("### 📋 Detailed Results")
        detailed_data = []
        for result in results['individual_results']:
            cid = result['cid']
            pinning_services = ', '.join(result['pinning_services_available']) or "None"
            
            # CORRECTED risk level calculation
            pinning_count = result['summary']['pinning_service_count']
            old_web3_count = result['summary']['old_web3_storage_count']
            network_available = result['summary']['network_available']
            
            if not network_available:
                risk_level = "⚫ Unreachable"
                risk_detail = "Not found anywhere"
            elif pinning_count == 0 and old_web3_count > 0:
                risk_level = "🔴 Critical Risk"
                risk_detail = "Only on shutting-down services"
            elif pinning_count == 0:
                risk_level = "🔴 High Risk"  
                risk_detail = "No confirmed pinning services"
            elif pinning_count == 1:
                risk_level = "🟡 Medium Risk"
                risk_detail = "Single pinning service"
            else:
                risk_level = "🟢 Low Risk"
                risk_detail = f"{pinning_count} pinning services"
            
            detailed_data.append({
                'CID': f"{cid[:20]}..." if len(cid) > 20 else cid,
                'Risk Level': risk_level,
                'Risk Detail': risk_detail,
                'Pinning Services': pinning_services,
                'Network Available': "✅" if network_available else "❌",
                'Total Gateways': f"{result['summary']['available_count']}/{len(selected_gateways)}"
            })
        
        df = pd.DataFrame(detailed_data)
        st.dataframe(df, use_container_width=True)
        
        # Corrected recommendations
        st.markdown("### 💡 Corrected Risk Analysis")
        
        high_risk_count = results['summary']['high_risk_count']
        medium_risk_count = results['summary']['medium_risk_count']
        
        if high_risk_count > 0:
            st.error(f"""
            🚨 **{high_risk_count} CID(s) are at HIGH RISK!**
            
            These CIDs have no confirmed pinning services. They may be available through public gateways now, 
            but could disappear if the original storing nodes go offline.
            
            **Action Required:** Pin these CIDs on reliable services immediately.
            """)
        
        if medium_risk_count > 0:
            st.warning(f"""
            ⚠️ **{medium_risk_count} CID(s) have MEDIUM RISK**
            
            These CIDs are stored on only one pinning service. While safer than high-risk CIDs,
            they could still be lost if that single service fails.
            
            **Recommendation:** Add redundancy by pinning on additional services.
            """)
        
        # Gateway type breakdown
        st.markdown("### 🔍 Understanding Gateway Types")
        
        st.markdown("""
        **🔒 Pinning Service Gateways:** These guarantee storage
        - Pinata, Infura, Fleek
        - Your content is actively stored and maintained
        
        **🌐 Public Access Gateways:** These only provide access  
        - ipfs.io, cloudflare-ipfs.com, dweb.link
        - Fetch content from wherever it's stored, but don't store it themselves
        
        **🔴 Deprecated Gateways:** These are shutting down
        - nftstorage.link, w3s.link (old.web3.storage)
        - Will stop working soon
        """)
        
        # Export results
        st.markdown("### 💾 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download JSON Report"):
                json_data = json.dumps(results, indent=2)
                st.download_button(
                    label="📄 Download JSON",
                    data=json_data,
                    file_name=f"gateway_risk_report_{int(time.time())}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📊 Download CSV Summary"):
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📄 Download CSV",
                    data=csv_data,
                    file_name=f"gateway_risk_summary_{int(time.time())}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main() 