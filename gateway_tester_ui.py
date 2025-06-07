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
        # Comprehensive list of public IPFS gateways
        self.all_gateways = [
            "https://ipfs.io/ipfs/",
            "https://gateway.ipfs.io/ipfs/",
            "https://dweb.link/ipfs/",
            "https://cloudflare-ipfs.com/ipfs/",
            "https://cf-ipfs.com/ipfs/", 
            "https://gateway.pinata.cloud/ipfs/",
            "https://infura-ipfs.io/ipfs/",
            "https://4everland.io/ipfs/",
            "https://nftstorage.link/ipfs/",  # old.web3.storage (shutting down)
            "https://w3s.link/ipfs/",        # old.web3.storage (shutting down)
            "https://ipfs.fleek.co/ipfs/",
            "https://gateway.temporal.cloud/ipfs/",
            "https://hardbin.com/ipfs/",
            "https://gateway.originprotocol.com/ipfs/",
            "https://ipfs.best-practice.se/ipfs/",
            "https://jorropo.net/ipfs/",
            "https://ipfs.joaoleitao.org/ipfs/",
            "https://ipfs.telos.miami/ipfs/",
        ]
        
        # High-risk gateways (shutting down)
        self.high_risk_gateways = [
            "https://nftstorage.link/ipfs/",
            "https://w3s.link/ipfs/"
        ]
        
        # Well-known reliable gateways
        self.reliable_gateways = [
            "https://ipfs.io/ipfs/",
            "https://gateway.ipfs.io/ipfs/",
            "https://cloudflare-ipfs.com/ipfs/",
            "https://gateway.pinata.cloud/ipfs/"
        ]

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
        """Test multiple CIDs with Streamlit progress tracking."""
        total_tests = len(cids) * len(gateways)
        completed_tests = 0
        
        all_results = []
        risk_analysis = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': [],
            'unreachable': [],
            'gateway_performance': {}
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
        
        for i, cid in enumerate(cids):
            status_text.text(f"🔍 Testing CID {i+1}/{len(cids)}: {cid[:20]}...")
            
            cid_result = {
                'cid': cid,
                'gateway_results': {},
                'summary': {
                    'total_gateways': len(gateways),
                    'available_count': 0,
                    'failed_count': 0,
                    'fastest_gateway': None,
                    'fastest_time': float('inf'),
                    'high_risk_only': False
                }
            }
            
            # Test each gateway for this CID
            for gateway in gateways:
                is_available, status, response_time = self.test_gateway_availability(gateway, cid, timeout=8)
                
                cid_result['gateway_results'][gateway] = {
                    'available': is_available,
                    'status': status,
                    'response_time': response_time,
                    'is_high_risk': gateway in self.high_risk_gateways
                }
                
                # Update gateway performance stats
                stats = risk_analysis['gateway_performance'][gateway]
                stats['total_tests'] += 1
                stats['total_response_time'] += response_time
                
                if is_available:
                    cid_result['summary']['available_count'] += 1
                    stats['success_count'] += 1
                    stats['successful_cids'].append(cid)
                    
                    if response_time < cid_result['summary']['fastest_time']:
                        cid_result['summary']['fastest_time'] = response_time
                        cid_result['summary']['fastest_gateway'] = gateway
                else:
                    cid_result['summary']['failed_count'] += 1
                
                completed_tests += 1
                progress_bar.progress(completed_tests / total_tests)
            
            # Categorize risk level
            available_count = cid_result['summary']['available_count']
            available_gateways = [gw for gw, r in cid_result['gateway_results'].items() if r['available']]
            reliable_available = any(gw in self.reliable_gateways for gw in available_gateways)
            high_risk_available = any(gw in self.high_risk_gateways for gw in available_gateways)
            
            cid_result['summary']['high_risk_only'] = high_risk_available and not reliable_available
            
            if available_count == 0:
                risk_analysis['unreachable'].append(cid_result)
            elif cid_result['summary']['high_risk_only']:
                risk_analysis['high_risk'].append(cid_result)
            elif available_count <= 2:
                risk_analysis['medium_risk'].append(cid_result)
            else:
                risk_analysis['low_risk'].append(cid_result)
            
            all_results.append(cid_result)
        
        # Calculate final gateway performance stats
        for gateway, stats in risk_analysis['gateway_performance'].items():
            if stats['total_tests'] > 0:
                stats['success_rate'] = stats['success_count'] / stats['total_tests']
                stats['avg_response_time'] = stats['total_response_time'] / stats['total_tests']
            else:
                stats['success_rate'] = 0
                stats['avg_response_time'] = 0
        
        return {
            'individual_results': all_results,
            'risk_analysis': risk_analysis,
            'summary': {
                'total_cids_tested': len(cids),
                'gateways_used': gateways,
                'high_risk_count': len(risk_analysis['high_risk']),
                'medium_risk_count': len(risk_analysis['medium_risk']),
                'low_risk_count': len(risk_analysis['low_risk']),
                'unreachable_count': len(risk_analysis['unreachable'])
            }
        }

def sample_assets_strategically(assets: List[dict], sample_size: int = 5) -> List[dict]:
    """Sample assets from different parts of the collection for diverse testing."""
    if len(assets) <= sample_size:
        return assets
    
    sampled = []
    total = len(assets)
    
    # Take from different segments
    segments = [
        (0, min(5, total)),                    # Beginning
        (total//4, total//4 + 5),             # First quarter 
        (total//2 - 2, total//2 + 3),         # Middle
        (3*total//4, 3*total//4 + 5),         # Third quarter
        (max(0, total-5), total)               # End
    ]
    
    # Sample one from each segment
    for start, end in segments:
        if len(sampled) < sample_size and start < total:
            segment_assets = assets[start:min(end, total)]
            if segment_assets:
                sampled.append(random.choice(segment_assets))
    
    # Fill remaining slots with random samples
    remaining_assets = [a for a in assets if a not in sampled]
    while len(sampled) < sample_size and remaining_assets:
        sampled.append(random.choice(remaining_assets))
        remaining_assets.remove(sampled[-1])
    
    return sampled

def extract_cids_from_assets(assets: List[dict]) -> List[str]:
    """Extract CIDs from assets using the enhanced utils functions."""
    cids = []
    for asset in assets:
        # Try metadata CID first
        metadata_cid = utils.extract_cid_from_asset(asset)
        if metadata_cid:
            cids.append(metadata_cid)
            
            # For ARC-19, also try to get image CID
            asset_params = asset.get('params', {})
            arc_standard = utils.detect_arc_standard(asset_params)
            
            if arc_standard == 'arc19':
                try:
                    image_cid, _ = utils.fetch_metadata_and_extract_image_cid(metadata_cid)
                    if image_cid and image_cid != metadata_cid:
                        cids.append(image_cid)
                except:
                    pass  # If we can't fetch image CID, just use metadata CID
    
    return list(set(cids))  # Remove duplicates

def create_simple_charts(results):
    """Create simple charts using Streamlit's built-in charting."""
    
    # Risk distribution chart
    st.markdown("### 📈 Risk Distribution")
    
    risk_data = {
        'High Risk': results['summary']['high_risk_count'],
        'Medium Risk': results['summary']['medium_risk_count'], 
        'Low Risk': results['summary']['low_risk_count'],
        'Unreachable': results['summary']['unreachable_count']
    }
    
    # Simple bar chart
    st.bar_chart(risk_data)
    
    # Gateway performance chart
    st.markdown("### 🌐 Gateway Performance")
    
    perf_data = results['risk_analysis']['gateway_performance']
    
    # Prepare data for chart
    gateway_chart_data = {}
    for gateway, stats in perf_data.items():
        gateway_name = gateway.replace('https://', '').replace('/ipfs/', '')[:20]  # Shorten names
        gateway_chart_data[gateway_name] = stats['success_rate'] * 100
    
    st.bar_chart(gateway_chart_data)
    
    # Response time chart
    response_time_data = {}
    for gateway, stats in perf_data.items():
        gateway_name = gateway.replace('https://', '').replace('/ipfs/', '')[:20]
        response_time_data[gateway_name] = stats['avg_response_time']
    
    st.markdown("### ⏱️ Average Response Times")
    st.bar_chart(response_time_data)

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
    
    num_gateways = st.sidebar.slider("🌐 Number of gateways to test", 3, 15, 8)
    timeout_seconds = st.sidebar.slider("⏱️ Request timeout (seconds)", 5, 30, 10)
    
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
            
            sample_size = st.slider("Number of random assets to test", 1, 10, 5)
            
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
                            st.success(f"✅ Found {len(assets)} assets in wallet")
                            
                            # Sample assets strategically
                            sampled_assets = sample_assets_strategically(assets, sample_size)
                            st.info(f"🎯 Selected {len(sampled_assets)} assets from different parts of the collection")
                            
                            # Show selected assets
                            with st.expander("🔍 Selected Assets"):
                                for asset in sampled_assets:
                                    asset_name = asset.get('params', {}).get('name', 'Unknown')
                                    asset_id = asset.get('index', 'Unknown')
                                    st.write(f"• **{asset_name}** (ID: {asset_id})")
                            
                            # Extract CIDs from selected assets
                            cids_to_test = extract_cids_from_assets(sampled_assets)
                            
                            if cids_to_test:
                                st.success(f"🎯 Extracted {len(cids_to_test)} unique CIDs for testing")
                            else:
                                st.warning("⚠️ No valid CIDs found in selected assets")
                    
                    except Exception as e:
                        st.error(f"❌ Error analyzing wallet: {str(e)}")
        
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
        
        # Select random gateways
        selected_gateways = tester.select_random_gateways(num_gateways)
        
        st.info(f"🌐 Using {len(selected_gateways)} random gateways")
        with st.expander("🔍 View Selected Gateways"):
            for gw in selected_gateways:
                gateway_name = gw.replace('https://', '').replace('/ipfs/', '')
                is_high_risk = gw in tester.high_risk_gateways
                risk_badge = "🔴 HIGH RISK" if is_high_risk else "🟢 RELIABLE"
                st.write(f"• {gateway_name} {risk_badge}")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Run the test
        with st.spinner("🧪 Running gateway tests..."):
            results = tester.test_multiple_cids_with_progress(
                cids_to_test, 
                selected_gateways, 
                progress_bar,
                status_text
            )
        
        status_text.text("✅ Testing complete!")
        progress_bar.progress(1.0)
        
        # Display results
        st.markdown("---")
        st.markdown("## 📊 Test Results")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🔴 High Risk", 
                results['summary']['high_risk_count'],
                help="Only available on shutting-down gateways"
            )
        
        with col2:
            st.metric(
                "🟡 Medium Risk", 
                results['summary']['medium_risk_count'],
                help="Available on few gateways"
            )
        
        with col3:
            st.metric(
                "🟢 Low Risk", 
                results['summary']['low_risk_count'],
                help="Widely available"
            )
        
        with col4:
            st.metric(
                "⚫ Unreachable", 
                results['summary']['unreachable_count'],
                help="Not found anywhere"
            )
        
        # Create charts based on availability
        if PLOTLY_AVAILABLE:
            create_plotly_charts(results)
        else:
            create_simple_charts(results)
        
        # Detailed results table
        st.markdown("### 📋 Detailed Results")
        
        detailed_data = []
        for result in results['individual_results']:
            cid = result['cid']
            available_count = result['summary']['available_count']
            fastest_gateway = result['summary']['fastest_gateway']
            fastest_time = result['summary']['fastest_time']
            
            # Determine risk level
            if available_count == 0:
                risk_level = "⚫ Unreachable"
            elif result['summary']['high_risk_only']:
                risk_level = "🔴 High Risk"
            elif available_count <= 2:
                risk_level = "🟡 Medium Risk"
            else:
                risk_level = "🟢 Low Risk"
            
            detailed_data.append({
                'CID': f"{cid[:20]}..." if len(cid) > 20 else cid,
                'Risk Level': risk_level,
                'Available On': f"{available_count}/{len(selected_gateways)} gateways",
                'Fastest Gateway': fastest_gateway.replace('https://', '').replace('/ipfs/', '') if fastest_gateway else "N/A",
                'Fastest Time': f"{fastest_time:.2f}s" if fastest_time != float('inf') else "N/A"
            })
        
        df = pd.DataFrame(detailed_data)
        st.dataframe(df, use_container_width=True)
        
        # High-risk CID warnings
        if results['summary']['high_risk_count'] > 0:
            st.markdown("### ⚠️ Urgent Action Required")
            st.error("The following CIDs are only available on shutting-down gateways and need immediate re-pinning:")
            
            for result in results['risk_analysis']['high_risk']:
                cid = result['cid']
                available_gateways = [gw for gw, r in result['gateway_results'].items() if r['available']]
                st.markdown(f"🔴 **{cid}** - Available on: {', '.join([gw.replace('https://', '').replace('/ipfs/', '') for gw in available_gateways])}")
        
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