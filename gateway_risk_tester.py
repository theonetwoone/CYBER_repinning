#!/usr/bin/env python3
"""
IPFS Gateway Risk Tester - Standalone Script
============================================

Tests CID availability across multiple IPFS gateways to assess redundancy risk.
Particularly useful for detecting old.web3.storage dependency risks.

Usage:
    python gateway_risk_tester.py --cids "QmHash1,QmHash2,QmHash3"
    python gateway_risk_tester.py --file cids.txt
    python gateway_risk_tester.py --random-test 10

"""

import requests
import random
import time
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

class IPFSGatewayTester:
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
        """
        Test if a CID is available through a specific IPFS gateway.
        Returns: (is_available, status_message, response_time)
        """
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

    def test_single_cid(self, cid: str, gateways: List[str] = None, timeout: int = 10) -> Dict:
        """Test a single CID across multiple gateways."""
        if gateways is None:
            gateways = self.select_random_gateways()
        
        print(f"\n🔍 Testing CID: {cid}")
        print(f"🌐 Using {len(gateways)} gateways...")
        
        results = {
            'cid': cid,
            'gateway_results': {},
            'summary': {
                'total_gateways': len(gateways),
                'available_count': 0,
                'failed_count': 0,
                'avg_response_time': 0,
                'fastest_gateway': None,
                'fastest_time': float('inf'),
                'high_risk_only': False
            }
        }
        
        # Test each gateway
        for gateway in gateways:
            is_available, status, response_time = self.test_gateway_availability(gateway, cid, timeout)
            
            results['gateway_results'][gateway] = {
                'available': is_available,
                'status': status,
                'response_time': response_time,
                'is_high_risk': gateway in self.high_risk_gateways
            }
            
            if is_available:
                results['summary']['available_count'] += 1
                if response_time < results['summary']['fastest_time']:
                    results['summary']['fastest_time'] = response_time
                    results['summary']['fastest_gateway'] = gateway
            else:
                results['summary']['failed_count'] += 1
            
            print(f"  {gateway:<40} {status} ({response_time:.2f}s)")
        
        # Calculate average response time (only for successful requests)
        successful_times = [r['response_time'] for r in results['gateway_results'].values() if r['available']]
        if successful_times:
            results['summary']['avg_response_time'] = sum(successful_times) / len(successful_times)
        
        # Check if only available on high-risk gateways
        available_gateways = [gw for gw, r in results['gateway_results'].items() if r['available']]
        reliable_available = any(gw in self.reliable_gateways for gw in available_gateways)
        high_risk_available = any(gw in self.high_risk_gateways for gw in available_gateways)
        
        results['summary']['high_risk_only'] = high_risk_available and not reliable_available
        
        return results

    def test_multiple_cids(self, cids: List[str], gateways: List[str] = None, max_workers: int = 5) -> Dict:
        """Test multiple CIDs with concurrent processing."""
        if gateways is None:
            gateways = self.select_random_gateways()
        
        print(f"\n🚀 Starting batch test of {len(cids)} CID(s)")
        print(f"🌐 Using gateways: {', '.join([gw.replace('https://', '').replace('/ipfs/', '') for gw in gateways])}")
        
        all_results = []
        risk_analysis = {
            'high_risk': [],      # Only on shutting-down gateways
            'medium_risk': [],    # Available on few gateways
            'low_risk': [],       # Available on many gateways
            'unreachable': [],    # Not available anywhere
            'gateway_performance': {}
        }
        
        # Initialize gateway performance tracking
        for gateway in gateways:
            risk_analysis['gateway_performance'][gateway] = {
                'success_count': 0,
                'total_tests': 0,
                'avg_response_time': 0,
                'total_response_time': 0
            }
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all CID tests
            future_to_cid = {
                executor.submit(self.test_single_cid, cid, gateways): cid 
                for cid in cids
            }
            
            # Collect results
            for future in as_completed(future_to_cid):
                cid = future_to_cid[future]
                try:
                    result = future.result()
                    all_results.append(result)
                    
                    # Update gateway performance stats
                    for gateway, gw_result in result['gateway_results'].items():
                        stats = risk_analysis['gateway_performance'][gateway]
                        stats['total_tests'] += 1
                        stats['total_response_time'] += gw_result['response_time']
                        if gw_result['available']:
                            stats['success_count'] += 1
                    
                    # Categorize risk level
                    available_count = result['summary']['available_count']
                    high_risk_only = result['summary']['high_risk_only']
                    
                    if available_count == 0:
                        risk_analysis['unreachable'].append(result)
                    elif high_risk_only:
                        risk_analysis['high_risk'].append(result)
                    elif available_count <= 2:
                        risk_analysis['medium_risk'].append(result)
                    else:
                        risk_analysis['low_risk'].append(result)
                        
                except Exception as e:
                    print(f"❌ Error testing CID {cid}: {str(e)}")
        
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

    def print_risk_summary(self, results: Dict):
        """Print a formatted risk analysis summary."""
        summary = results['summary']
        risk_analysis = results['risk_analysis']
        
        print(f"\n" + "="*60)
        print(f"🛡️  IPFS GATEWAY RISK ANALYSIS SUMMARY")  
        print(f"="*60)
        
        print(f"📊 TESTED: {summary['total_cids_tested']} CID(s)")
        print(f"🌐 GATEWAYS: {len(summary['gateways_used'])}")
        
        print(f"\n🚨 RISK LEVELS:")
        print(f"   🔴 HIGH RISK (only on shutting-down gateways): {summary['high_risk_count']}")
        print(f"   🟡 MEDIUM RISK (few gateways available):        {summary['medium_risk_count']}")
        print(f"   🟢 LOW RISK (widely available):                {summary['low_risk_count']}")
        print(f"   ⚫ UNREACHABLE (not found anywhere):           {summary['unreachable_count']}")
        
        # Gateway performance
        print(f"\n📡 GATEWAY PERFORMANCE:")
        performance = risk_analysis['gateway_performance']
        sorted_gateways = sorted(performance.items(), key=lambda x: x[1]['success_rate'], reverse=True)
        
        for gateway, stats in sorted_gateways:
            gateway_name = gateway.replace('https://', '').replace('/ipfs/', '')
            success_rate = stats['success_rate'] * 100
            avg_time = stats['avg_response_time']
            
            status_icon = "🟢" if success_rate >= 80 else "🟡" if success_rate >= 50 else "🔴"
            print(f"   {status_icon} {gateway_name:<30} {success_rate:5.1f}% success, {avg_time:5.2f}s avg")
        
        # Specific high-risk warnings
        if summary['high_risk_count'] > 0:
            print(f"\n⚠️  HIGH RISK CIDS (urgent action needed):")
            for result in risk_analysis['high_risk']:
                print(f"   🔴 {result['cid']} - Only available on shutting-down gateways!")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if summary['high_risk_count'] > 0:
            print(f"   • {summary['high_risk_count']} CID(s) need immediate re-pinning")
        if summary['medium_risk_count'] > 0:
            print(f"   • {summary['medium_risk_count']} CID(s) should be re-pinned for better redundancy")
        if summary['unreachable_count'] > 0:
            print(f"   • {summary['unreachable_count']} CID(s) may be permanently lost")
        if summary['low_risk_count'] == summary['total_cids_tested']:
            print(f"   • ✅ All CIDs have good redundancy!")

def generate_test_cids(count: int = 5) -> List[str]:
    """Generate some well-known test CIDs for demonstration."""
    known_test_cids = [
        "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",  # README from IPFS
        "QmZULkCELmmk5XNfCgTnCyFgAVxBRBXyDHGGMVoLFLiXEN",  # Hello World
        "QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o",  # Another test file
        "QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc",  # Common test CID
        "QmSrCRJmzE4zE1nAfWPbzVfanKQNBhp7ZWmMnEdkAAUEgh",  # Another common one
        "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi", # CIDv1 example 
        "bafkreifjjcie6lypi6ny7amxnfftagclbuxndqonfipmb64f2km2devei4", # Another CIDv1
    ]
    return random.sample(known_test_cids, min(count, len(known_test_cids)))

def main():
    parser = argparse.ArgumentParser(description="IPFS Gateway Risk Tester")
    parser.add_argument('--cids', type=str, help='Comma-separated list of CIDs to test')
    parser.add_argument('--file', type=str, help='File containing CIDs (one per line)')
    parser.add_argument('--random-test', type=int, help='Test N random well-known CIDs')
    parser.add_argument('--gateways', type=int, default=5, help='Number of random gateways to test (default: 5)')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('--workers', type=int, default=5, help='Max concurrent workers (default: 5)')
    parser.add_argument('--output', type=str, help='Save detailed results to JSON file')
    
    args = parser.parse_args()
    
    tester = IPFSGatewayTester()
    
    # Determine CIDs to test
    cids_to_test = []
    
    if args.cids:
        cids_to_test = [cid.strip() for cid in args.cids.split(',')]
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                cids_to_test = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            return
    elif args.random_test:
        cids_to_test = generate_test_cids(args.random_test)
    else:
        # Default: test a few well-known CIDs
        print("ℹ️  No CIDs specified. Testing 3 random well-known CIDs...")
        cids_to_test = generate_test_cids(3)
    
    if not cids_to_test:
        print("❌ No CIDs to test!")
        return
    
    # Select gateways
    selected_gateways = tester.select_random_gateways(args.gateways)
    
    # Run the test
    results = tester.test_multiple_cids(
        cids_to_test, 
        selected_gateways, 
        max_workers=args.workers
    )
    
    # Print summary
    tester.print_risk_summary(results)
    
    # Save detailed results if requested
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Detailed results saved to: {args.output}")
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")

if __name__ == "__main__":
    main() 