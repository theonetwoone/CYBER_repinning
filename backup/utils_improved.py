import time
import requests

def _get_4everland_pin_lookup_improved(api_key):
    """
    Fetch all pins from 4everland and return a lookup dictionary.
    Returns: dict {cid: status} or None if failed
    """
    try:
        url = "https://api.4everland.dev/pins"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Start with first page
        all_results = []
        limit = 1000
        offset = 0
        page_count = 0
        max_pages = 50  # Safety limit - prevent infinite loops
        start_time = time.time()
        
        print(f"DEBUG VERIFICATION: Starting pin fetch with safety limits (max {max_pages} pages, 5min timeout)")
        
        # Handle pagination to get all pins
        while page_count < max_pages:
            page_start_time = time.time()
            
            params = {
                'limit': limit,
                'offset': offset
            }
            
            print(f"DEBUG VERIFICATION: Fetching page {page_count + 1} (offset {offset})...")
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
            except requests.Timeout:
                print(f"DEBUG VERIFICATION: Timeout on page {page_count + 1} - retrying once...")
                try:
                    response = requests.get(url, headers=headers, params=params, timeout=45)
                except requests.Timeout:
                    print(f"DEBUG VERIFICATION: Second timeout on page {page_count + 1} - aborting")
                    break
            
            page_time = time.time() - page_start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                all_results.extend(results)
                page_count += 1
                
                print(f"DEBUG VERIFICATION: Page {page_count} retrieved {len(results)} pins in {page_time:.1f}s (total: {len(all_results)})")
                
                # If we got fewer results than the limit, we've reached the end
                if len(results) < limit:
                    print(f"DEBUG VERIFICATION: Reached end of results (got {len(results)} < {limit})")
                    break
                
                # Safety check for total time
                total_time = time.time() - start_time
                if total_time > 300:  # 5 minutes
                    print(f"DEBUG VERIFICATION: Timeout after {total_time:.1f}s - stopping at {len(all_results)} pins")
                    break
                    
                offset += limit
                
                # Add small delay to be nice to the API
                time.sleep(0.5)
                
            else:
                print(f"DEBUG VERIFICATION: Failed to fetch page {page_count + 1}: HTTP {response.status_code}")
                if response.status_code == 429:  # Rate limited
                    print("DEBUG VERIFICATION: Rate limited - waiting 10 seconds before retry...")
                    time.sleep(10)
                    continue
                else:
                    return None
        
        if page_count >= max_pages:
            print(f"DEBUG VERIFICATION: Hit page limit ({max_pages}) - got {len(all_results)} pins")
        
        total_time = time.time() - start_time
        print(f"DEBUG VERIFICATION: Completed in {total_time:.1f}s - retrieved {len(all_results)} pins across {page_count} pages")
        
        # Create lookup dictionary
        pin_lookup = {}
        for pin in all_results:
            pin_cid = pin.get('pin', {}).get('cid', '')
            status = pin.get('status', 'unknown')
            if pin_cid:
                pin_lookup[pin_cid] = status
        
        print(f"DEBUG VERIFICATION: Created lookup for {len(pin_lookup)} unique pins")
        return pin_lookup
        
    except Exception as e:
        print(f"DEBUG VERIFICATION: Exception fetching pin lookup: {str(e)}")
        return None

