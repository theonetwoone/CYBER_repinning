#!/usr/bin/env python3
"""
Safe Testing Script for Robust ARC-19 Collection Processing

This script allows you to safely test the improved processing logic
with comprehensive error handling and recovery mechanisms.
"""

import json
import time
from datetime import datetime
from utils import (
    get_all_creator_assets, 
    process_arc19_collection_robust, 
    recover_failed_assets,
    create_collection_dataframe
)

def safe_test_robust_processing(creator_address, test_mode="small_sample"):
    """
    Safely test the robust processing with different test modes.
    
    Args:
        creator_address: The Algorand creator address
        test_mode: "small_sample" (10 assets), "medium_sample" (100 assets), 
                   "large_sample" (500 assets), or "full_collection"
    """
    print(f"🧪 SAFE TESTING MODE: {test_mode}")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Fetch all assets first
    print(f"🔍 Fetching assets for creator: {creator_address}")
    all_assets, error = get_all_creator_assets(creator_address)
    
    if error:
        print(f"❌ Error fetching assets: {error}")
        return None
    
    print(f"📊 Total assets found: {len(all_assets)}")
    
    # Select test subset based on mode
    if test_mode == "small_sample":
        test_assets = all_assets[:10]
        print(f"🔬 Testing with small sample: {len(test_assets)} assets")
    elif test_mode == "medium_sample":
        test_assets = all_assets[:100]
        print(f"🔬 Testing with medium sample: {len(test_assets)} assets")
    elif test_mode == "large_sample":
        test_assets = all_assets[:500]
        print(f"🔬 Testing with large sample: {len(test_assets)} assets")
    elif test_mode == "full_collection":
        test_assets = all_assets
        print(f"🔬 Testing with full collection: {len(test_assets)} assets")
    else:
        print(f"❌ Unknown test mode: {test_mode}")
        return None
    
    # Create progress callback
    def progress_callback(current, total, results):
        if current % 25 == 0 or current == total:
            print(f"📈 PROGRESS: {current}/{total} ({(current/total)*100:.1f}%) - "
                  f"Success: {results['success_count']}, Failed: {results['failure_count']}")
    
    # Run robust processing
    start_time = time.time()
    
    print(f"\n🚀 Starting robust processing of {len(test_assets)} assets...")
    results = process_arc19_collection_robust(test_assets, progress_callback)
    
    processing_time = time.time() - start_time
    
    # Print detailed results
    print(f"\n📊 PROCESSING RESULTS:")
    print(f"   ⏱️  Processing time: {processing_time:.2f} seconds")
    print(f"   📈 Success rate: {results['processing_summary']['success_rate']:.1f}%")
    print(f"   💾 Cache hit rate: {results['processing_summary']['cache_hit_rate']:.1f}%")
    print(f"   📁 Directory efficiency: {results['processing_summary']['directory_efficiency']:.1f}%")
    print(f"   🔢 Unique metadata CIDs: {results['processing_summary']['unique_metadata_cids']}")
    print(f"   🖼️  Unique image CIDs: {results['processing_summary']['unique_image_cids']}")
    
    # Show error breakdown
    if results['errors_by_type']:
        print(f"\n❌ ERROR BREAKDOWN:")
        for error_type, count in results['errors_by_type'].items():
            print(f"   {error_type}: {count}")
    
    # Attempt recovery if there are failures
    if results['failed_assets']:
        print(f"\n🔄 ATTEMPTING RECOVERY for {len(results['failed_assets'])} failed assets...")
        recovery_start = time.time()
        recovery_results = recover_failed_assets(results['failed_assets'], max_retries=2)
        recovery_time = time.time() - recovery_start
        
        print(f"   ⏱️  Recovery time: {recovery_time:.2f} seconds")
        print(f"   ✅ Recovered: {recovery_results['recovery_count']}")
        print(f"   ❌ Permanent failures: {recovery_results['permanent_failures']}")
        
        # Update final success rate
        total_successful = results['success_count'] + recovery_results['recovery_count']
        final_success_rate = (total_successful / len(test_assets)) * 100
        print(f"   🎯 Final success rate: {final_success_rate:.1f}%")
    
    # Save detailed results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"test_results_{test_mode}_{timestamp}.json"
    
    # Prepare serializable results
    serializable_results = {
        'test_mode': test_mode,
        'timestamp': timestamp,
        'creator_address': creator_address,
        'total_assets_tested': len(test_assets),
        'processing_time': processing_time,
        'success_count': results['success_count'],
        'failure_count': results['failure_count'],
        'timeout_count': results['timeout_count'],
        'cache_hits': results['cache_hits'],
        'unique_metadata_cids': len(results['unique_metadata_cids']),
        'unique_image_cids': len(results['unique_image_cids']),
        'success_rate': results['processing_summary']['success_rate'],
        'cache_hit_rate': results['processing_summary']['cache_hit_rate'],
        'directory_efficiency': results['processing_summary']['directory_efficiency'],
        'errors_by_type': results['errors_by_type'],
        'failed_assets': results['failed_assets'][:10],  # Save first 10 failures for analysis
        'sample_successful_assets': [a for a in results['processed_assets'] if a['success']][:10]
    }
    
    # Add recovery results if they exist
    if 'recovery_results' in locals():
        serializable_results['recovery_count'] = recovery_results['recovery_count']
        serializable_results['permanent_failures'] = recovery_results['permanent_failures']
        serializable_results['final_success_rate'] = final_success_rate
        serializable_results['recovery_time'] = recovery_time
    
    with open(results_file, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Return results for further analysis
    return {
        'results': results,
        'recovery_results': recovery_results if 'recovery_results' in locals() else None,
        'test_file': results_file
    }

def compare_with_legacy_processing(creator_address, sample_size=50):
    """
    Compare the new robust processing with the legacy method on a small sample.
    """
    print(f"⚖️  COMPARISON TEST: Robust vs Legacy Processing")
    
    # Fetch assets
    all_assets, error = get_all_creator_assets(creator_address)
    if error:
        print(f"❌ Error fetching assets: {error}")
        return
    
    test_assets = all_assets[:sample_size]
    print(f"🔬 Testing {sample_size} assets with both methods")
    
    # Test legacy method (existing create_collection_dataframe)
    print(f"\n1️⃣ Testing LEGACY method...")
    legacy_start = time.time()
    legacy_df = create_collection_dataframe(test_assets)
    legacy_time = time.time() - legacy_start
    
    legacy_success = len(legacy_df[legacy_df['image_cid'] != ''])
    legacy_failed = len(legacy_df[legacy_df['image_cid'] == ''])
    
    print(f"   ⏱️  Legacy time: {legacy_time:.2f} seconds")
    print(f"   ✅ Legacy success: {legacy_success}/{sample_size}")
    print(f"   ❌ Legacy failed: {legacy_failed}/{sample_size}")
    
    # Test robust method
    print(f"\n2️⃣ Testing ROBUST method...")
    robust_start = time.time()
    robust_results = process_arc19_collection_robust(test_assets)
    robust_time = time.time() - robust_start
    
    print(f"   ⏱️  Robust time: {robust_time:.2f} seconds")
    print(f"   ✅ Robust success: {robust_results['success_count']}/{sample_size}")
    print(f"   ❌ Robust failed: {robust_results['failure_count']}/{sample_size}")
    
    # Comparison
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"   🚀 Speed improvement: {((legacy_time - robust_time) / legacy_time * 100):.1f}%")
    print(f"   📈 Success rate - Legacy: {(legacy_success/sample_size)*100:.1f}%, Robust: {robust_results['processing_summary']['success_rate']:.1f}%")
    print(f"   💾 Cache hits: {robust_results['cache_hits']}")
    print(f"   🔄 Retry attempts: {robust_results['timeout_count']}")

if __name__ == "__main__":
    # Example usage - replace with your creator address
    CREATOR_ADDRESS = "CV3ZM4KVJS4CRMXEVMABNIHP3LCQAJJEYMYXF3NNBYJUW7C4CTVD7PUEOY"
    
    print("🧪 SAFE TESTING SUITE")
    print("=" * 50)
    
    # Run progressive tests
    print("\n1️⃣ Small sample test (10 assets)")
    small_results = safe_test_robust_processing(CREATOR_ADDRESS, "small_sample")
    
    if small_results and small_results['results']['processing_summary']['success_rate'] > 70:
        print("\n2️⃣ Medium sample test (100 assets)")
        medium_results = safe_test_robust_processing(CREATOR_ADDRESS, "medium_sample")
        
        if medium_results and medium_results['results']['processing_summary']['success_rate'] > 70:
            print("\n3️⃣ Comparison test")
            compare_with_legacy_processing(CREATOR_ADDRESS, 50)
            
            # Only proceed to full test if everything looks good
            user_input = input("\n❓ Results look good. Proceed with full collection? (y/N): ")
            if user_input.lower() == 'y':
                print("\n4️⃣ Full collection test")
                full_results = safe_test_robust_processing(CREATOR_ADDRESS, "full_collection")
            else:
                print("✅ Safe testing complete. Review results before full deployment.")
        else:
            print("⚠️ Medium test had issues. Please review before proceeding.")
    else:
        print("⚠️ Small test had issues. Please review configuration before proceeding.") 