import re
import base64
import pandas as pd
import requests
import base58
import algosdk.encoding
import multibase
import json
import time

def redact_sensitive_headers(headers):
    """
    Redact sensitive information from headers for safe logging.
    Returns a copy with Authorization headers redacted.
    """
    redacted = {}
    for key, value in headers.items():
        if key.lower() == 'authorization' and isinstance(value, str):
            if value.startswith('Bearer '):
                redacted[key] = 'Bearer [REDACTED]'
            elif value.startswith('Basic '):
                redacted[key] = 'Basic [REDACTED]'
            else:
                redacted[key] = '[REDACTED]'
        else:
            redacted[key] = value
    return redacted

def get_all_creator_assets(creator_address):
    """
    Fetch all assets created by a specific Algorand address using direct API calls.
    Returns: (list_of_assets, error_message)
    """
    try:
        all_assets = []
        next_token = None
        base_url = "https://mainnet-idx.algonode.cloud"
        
        while True:
            # Build URL with pagination
            url = f"{base_url}/v2/accounts/{creator_address}/created-assets?include-all=true"
            if next_token:
                url += f"&next={next_token}"
            
            # Make HTTP request
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                return [], f"HTTP {response.status_code}: {response.text}"
            
            data = response.json()
            
            # Add assets from this page
            if 'assets' in data:
                all_assets.extend(data['assets'])
            
            # Check for next page
            next_token = data.get('next-token')
            if not next_token:
                break
        
        return all_assets, None
        
    except Exception as e:
        return [], f"Error fetching assets: {str(e)}"

def detect_arc_standard(asset_params):
    """
    Detect which ARC standard an asset follows.
    Returns: 'arc19', 'arc69', 'standard_ipfs', or 'unknown'
    """
    url = asset_params.get('url', '')
    metadata_mime_type = asset_params.get('metadata_mime_type', '')
    
    # ARC-19: Uses template-ipfs:// format OR has empty metadata_mime_type with CID in URL
    if url.startswith('template-ipfs://'):
        return 'arc19'
    
    # ARC-19 with missing/empty metadata_mime_type - treat as ARC-19 variant
    print(f"DEBUG: Checking metadata_mime_type: '{metadata_mime_type}', type: {type(metadata_mime_type)}, not metadata_mime_type: {not metadata_mime_type}")
    if not metadata_mime_type and url:
        print(f"DEBUG: metadata_mime_type is falsy and URL exists: '{url[:50] if url else 'None'}...'")
        # Check if URL contains a direct CID or IPFS URL
        if (any(url.startswith(prefix) for prefix in ['Qm', 'bafy', 'bafk', 'bafz']) or 
            url.startswith('ipfs://')):
            print(f"DEBUG: Detected ARC-19 with empty metadata_mime_type: {url[:30]}...")
            return 'arc19'
        else:
            print(f"DEBUG: URL doesn't start with expected CID/IPFS patterns: '{url[:30]}...'")
    else:
        if not url:
            print(f"DEBUG: No URL found")
        if metadata_mime_type:
            print(f"DEBUG: metadata_mime_type is not empty: '{metadata_mime_type}'")
    
    # ARC-69: Has metadata in the 'am-' reserve field and may use standard IPFS URLs
    # Check for ARC-69 metadata field (base64 encoded JSON in reserve)
    reserve = asset_params.get('reserve', '')
    if reserve:
        try:
            # ARC-69 stores metadata as base64 in the reserve field
            decoded = base64.b64decode(reserve + '==')  # Add padding just in case
            metadata = json.loads(decoded.decode('utf-8'))
            if isinstance(metadata, dict) and ('image' in metadata or 'name' in metadata):
                return 'arc69'
        except:
            pass
    
    # Standard IPFS URL - check if it contains a valid CID pattern
    if url.startswith('ipfs://'):
        return 'standard_ipfs'
    
    # Special case: Check if there's a CID-like string in the URL but missing metadata_mime_type
    # This handles cases where assets have CIDs in URL field but might be malformed
    if url and len(url) > 20:  # Basic check for CID-like content
        # Check for common CID patterns (Qm... or bafy...)
        if any(url.startswith(prefix) for prefix in ['Qm', 'bafy', 'bafk', 'bafz']):
            print(f"DEBUG: Found CID-like pattern in URL but no standard prefix: {url[:30]}...")
            return 'potential_cid'
    
    return 'unknown'

def extract_cid_from_asset(asset):
    """
    Extract CID from an Algorand asset supporting ARC-19, ARC-69, and standard IPFS URLs.
    Returns: CID string or None
    """
    try:
        if 'params' not in asset:
            return None
            
        asset_params = asset['params']
        arc_standard = detect_arc_standard(asset_params)
        
        asset_id = asset.get('index', 'Unknown')
        metadata_mime_type = asset_params.get('metadata_mime_type', '')
        print(f"DEBUG: Asset {asset_id} detected as {arc_standard}")
        if arc_standard == 'arc19' and not metadata_mime_type:
            print(f"DEBUG: Asset {asset_id} is ARC-19 with empty metadata_mime_type - will use fallback logic")
        
        if arc_standard == 'arc19':
            print(f"DEBUG: Calling extract_arc19_cid for asset {asset_id}")
            result = extract_arc19_cid(asset_params)
            print(f"DEBUG: extract_arc19_cid returned: {result}")
            return result
        elif arc_standard == 'arc69':
            return extract_arc69_cid(asset_params)
        elif arc_standard == 'standard_ipfs':
            return extract_standard_ipfs_cid(asset_params)
        elif arc_standard == 'potential_cid':
            return extract_potential_cid(asset_params)
        
        print(f"DEBUG: No matching ARC standard for asset {asset_id}, arc_standard: {arc_standard}")
        return None
        
    except Exception as e:
        print(f"DEBUG: General error extracting CID: {e}")
        return None

def extract_arc19_cid(asset_params):
    """Extract CID from ARC-19 template URL."""
    try:
        url = asset_params.get('url', '')
        if not url:
            print(f"DEBUG ARC19: ❌ No URL found in asset params")
            return None
            
        print(f"DEBUG ARC19: Parsing URL: {url}")
        metadata_mime_type = asset_params.get('metadata_mime_type', '')
        print(f"DEBUG ARC19: metadata_mime_type = '{metadata_mime_type}' (empty: {not metadata_mime_type})")
        
        # First, try to parse as ARC19 template format (regardless of metadata_mime_type)
        # Parse ARC19 template format
        pattern = re.compile(r"template-ipfs://\{ipfscid:(?P<version>\d+):(?P<codec>[\w-]+):(?P<field>\w+):(?P<hash_type>[\w-]+)\}")
        match = pattern.match(url)
        
        if not match:
            print(f"DEBUG ARC19: ❌ URL does not match ARC19 template pattern")
            print(f"DEBUG ARC19: Expected format: template-ipfs://{{ipfscid:version:codec:field:hash_type}}")
            
            # Fallback: check if it's a direct CID or IPFS URL (only if metadata_mime_type is missing)
            if not metadata_mime_type:
                print(f"DEBUG ARC19: 🔄 Fallback for missing metadata_mime_type: checking for direct CID")
                
                if any(url.startswith(prefix) for prefix in ['Qm', 'bafy', 'bafk', 'bafz']):
                    print(f"DEBUG ARC19: ✅ Fallback: Found direct CID in URL: {url}")
                    return url.strip()
                elif url.startswith('ipfs://'):
                    cid_part = url.replace('ipfs://', '').split('#')[0].split('/')[0]
                    print(f"DEBUG ARC19: ✅ Fallback: Found IPFS CID in URL: {cid_part}")
                    return cid_part
                elif url and len(url) > 10:
                    # More aggressive fallback - check if it could be any kind of CID
                    url_clean = url.strip()
                    print(f"DEBUG ARC19: 🔍 Fallback: Checking if URL could be a CID: '{url_clean}'")
                    
                    # Check if it looks like a base58 CID (Qm...) or base32 CID (bafy...)
                    if (url_clean.startswith('Qm') and len(url_clean) >= 46) or \
                       (url_clean.startswith(('bafy', 'bafk', 'bafz', 'bafr')) and len(url_clean) >= 50):
                        print(f"DEBUG ARC19: ✅ Fallback: URL appears to be a direct CID: {url_clean}")
                        return url_clean
                    else:
                        print(f"DEBUG ARC19: ❌ Fallback: URL doesn't appear to be a direct CID")
                else:
                    print(f"DEBUG ARC19: ❌ Fallback: URL is too short or empty for CID: '{url}'")
            
            return None
        
        # Extract template parameters
        params = match.groupdict()
        field_to_get = params['field']  # 'reserve', 'manager', 'freezer', or 'clawback'
        cid_version = int(params['version'])
        cid_codec = params['codec']
        hash_type = params['hash_type']
        
        print(f"DEBUG ARC19: Template params - version: {cid_version}, codec: {cid_codec}, field: {field_to_get}, hash: {hash_type}")
        
        # Print all available asset parameters for debugging
        available_fields = list(asset_params.keys())
        print(f"DEBUG ARC19: Available asset fields: {available_fields}")
        
        # Get address from the correct field
        address_to_decode = asset_params.get(field_to_get)
        if not address_to_decode:
            print(f"DEBUG ARC19: ❌ Field '{field_to_get}' not found in asset params")
            print(f"DEBUG ARC19: Available fields: {[k for k in asset_params.keys() if k in ['reserve', 'manager', 'freezer', 'clawback']]}")
            
            # Check if the field exists but is empty
            if field_to_get in asset_params:
                print(f"DEBUG ARC19: Field '{field_to_get}' exists but is empty/None")
            
            return None
        
        print(f"DEBUG ARC19: Field: {field_to_get}, Address: {address_to_decode}")
        
        # Additional validation for address format
        if len(address_to_decode) < 10:
            print(f"DEBUG ARC19: ❌ Address too short: {len(address_to_decode)} characters")
            return None
        
        # Decode using algosdk
        try:
            decoded_address = algosdk.encoding.decode_address(address_to_decode)
            print(f"DEBUG ARC19: ✅ Successfully decoded address using algosdk")
            print(f"DEBUG ARC19: Decoded address bytes: {decoded_address.hex()}")
            
            # Construct CID based on version
            if cid_version == 1:
                codec_map = {'raw': 0x55, 'dag-pb': 0x70, 'dag-cbor': 0x71}
                codec_byte = codec_map.get(cid_codec, 0x55)
                
                if hash_type == 'sha2-256':
                    multihash = bytes([0x12, 0x20]) + decoded_address
                else:
                    multihash = bytes([0x12, 0x20]) + decoded_address
                
                cid_bytes = bytes([0x01, codec_byte]) + multihash
                cid_str = multibase.encode('base32', cid_bytes).decode('ascii')
                print(f"DEBUG ARC19: ✅ Final CIDv1: {cid_str}")
                return cid_str
            else:
                cid_str = base58.b58encode(decoded_address).decode('ascii')
                print(f"DEBUG ARC19: ✅ Final CIDv0: {cid_str}")
                return cid_str
                
        except Exception as decode_error:
            print(f"DEBUG ARC19: ⚠️ algosdk decode failed: {decode_error}")
            print(f"DEBUG ARC19: Trying fallback base32 decode method...")
            
            # Fallback method with better error handling
            try:
                # Algorand addresses are base32 encoded, try direct base32 decode
                padded_address = address_to_decode.upper()
                # Add padding if needed
                while len(padded_address) % 8 != 0:
                    padded_address += '='
                
                decoded_bytes = base64.b32decode(padded_address)
                print(f"DEBUG ARC19: ✅ Fallback decode successful: {len(decoded_bytes)} bytes")
                
                if cid_version == 1:
                    codec_map = {'raw': 0x55, 'dag-pb': 0x70, 'dag-cbor': 0x71}
                    codec_byte = codec_map.get(cid_codec, 0x55)
                    
                    # Use appropriate hash for CIDv1
                    if hash_type == 'sha2-256':
                        multihash = bytes([0x12, 0x20]) + decoded_bytes
                    else:
                        multihash = bytes([0x12, 0x20]) + decoded_bytes
                    
                    cid_bytes = bytes([0x01, codec_byte]) + multihash
                    cid_str = multibase.encode('base32', cid_bytes).decode('ascii')
                    print(f"DEBUG ARC19: ✅ Fallback CIDv1: {cid_str}")
                    return cid_str
                else:
                    cid_str = base58.b58encode(decoded_bytes).decode('ascii')
                    print(f"DEBUG ARC19: ✅ Fallback CIDv0: {cid_str}")
                    return cid_str
                    
            except Exception as fallback_error:
                print(f"DEBUG ARC19: ❌ Fallback decode also failed: {fallback_error}")
                print(f"DEBUG ARC19: Address length: {len(address_to_decode)}")
                print(f"DEBUG ARC19: Address characters: {[c for c in address_to_decode[:10]]}")
                return None
        
    except Exception as e:
        print(f"DEBUG ARC19: ❌ General error: {e}")
        import traceback
        print(f"DEBUG ARC19: Full traceback: {traceback.format_exc()}")
        return None

def extract_arc69_cid(asset_params):
    """Extract CID from ARC-69 metadata in reserve field."""
    try:
        reserve = asset_params.get('reserve', '')
        if not reserve:
            return None
        
        # Decode base64 metadata
        import base64
        decoded = base64.b64decode(reserve + '==')  # Add padding
        metadata = json.loads(decoded.decode('utf-8'))
        
        # Extract image URL from metadata
        image_url = metadata.get('image', '')
        if image_url.startswith('ipfs://'):
            cid_part = image_url.replace('ipfs://', '').split('#')[0].split('/')[0]
            print(f"DEBUG ARC69: Extracted CID from metadata: {cid_part}")
            return cid_part
            
        return None
        
    except Exception as e:
        print(f"DEBUG ARC69: Error extracting from metadata: {e}")
        return None

def extract_standard_ipfs_cid(asset_params):
    """Extract CID from standard IPFS URL."""
    try:
        url = asset_params.get('url', '')
        if not url or not url.startswith('ipfs://'):
            return None
        
        # Extract CID from standard IPFS URL
        cid_part = url.replace('ipfs://', '').split('#')[0].split('/')[0]
        print(f"DEBUG IPFS: Extracted CID: {cid_part}")
        return cid_part
        
    except Exception as e:
        print(f"DEBUG IPFS: Error: {e}")
        return None

def extract_potential_cid(asset_params):
    """Extract CID from URL that appears to contain a raw CID."""
    try:
        url = asset_params.get('url', '')
        if not url:
            return None
        
        # Check if URL itself looks like a CID
        cid_candidate = url.strip()
        
        # Basic CID validation - check length and starting pattern
        if len(cid_candidate) > 10 and any(cid_candidate.startswith(prefix) for prefix in ['Qm', 'bafy', 'bafk', 'bafz']):
            print(f"DEBUG POTENTIAL_CID: Found raw CID in URL field: {cid_candidate}")
            print(f"DEBUG POTENTIAL_CID: Note - this asset may be missing metadata_mime_type or have non-standard format")
            return cid_candidate
        
        return None
        
    except Exception as e:
        print(f"DEBUG POTENTIAL_CID: Error: {e}")
        return None

def fetch_metadata_and_extract_image_cid(metadata_cid):
    """
    Fetch metadata JSON from IPFS and extract image CID.
    Returns: (image_cid, metadata_json) or (None, None) if failed
    """
    # Common IPFS gateways to try - reduced list for faster failure
    gateways = [
        "https://ipfs.io/ipfs/",
        "https://gateway.ipfs.io/ipfs/",
        "https://cloudflare-ipfs.com/ipfs/"
    ]
    
    for i, gateway in enumerate(gateways):
        try:
            url = f"{gateway}{metadata_cid}"
            # Reduced timeout to 8 seconds to prevent long hangs
            response = requests.get(url, timeout=8)
            
            if response.status_code == 200:
                metadata = response.json()
                
                # Extract media CID - prioritize animation_url for videos, then fallback to image
                animation_url = metadata.get('animation_url', '')
                image_url = metadata.get('image', '')
                
                # Check for animation_url first (videos, GIFs, etc.)
                if animation_url and animation_url.startswith('ipfs://'):
                    media_cid = animation_url.replace('ipfs://', '').split('#')[0].split('/')[0]
                    print(f"✅ METADATA: Found animation CID: {media_cid} (from animation_url)")
                    return media_cid, metadata
                
                # Fallback to image field
                elif image_url and image_url.startswith('ipfs://'):
                    media_cid = image_url.replace('ipfs://', '').split('#')[0].split('/')[0]
                    print(f"✅ METADATA: Found image CID: {media_cid} (from image)")
                    return media_cid, metadata
                
                else:
                    print(f"⚠️ METADATA: No IPFS media found - animation_url: {animation_url}, image: {image_url}")
                    return None, metadata
                    
        except Exception as e:
            print(f"❌ METADATA: Failed to fetch from {gateway} (attempt {i+1}/3): {e}")
            # Don't continue trying all gateways if we hit too many errors
            if i >= 1:  # Only try first 2 gateways to fail faster
                break
            continue
    
    print(f"❌ METADATA: Could not fetch metadata for CID: {metadata_cid}")
    return None, None

def create_collection_dataframe(assets, existing_df=None):
    """
    Create a structured DataFrame from the list of assets.
    Supports mixed ARC-19, ARC-69, and standard IPFS assets.
    """
    processed_data = []
    
    # Create lookup dict from existing data if provided
    existing_lookup = {}
    if existing_df is not None and not existing_df.empty:
        for _, row in existing_df.iterrows():
            existing_lookup[row['asset_id']] = {
                'status': row['status'],
                'repin_cid': row.get('repin_cid'),
                'error_message': row.get('error_message')
            }
    
    # Tracking variables for debugging
    total_assets = len(assets)
    deleted_assets = 0
    no_cid_assets = 0
    processed_assets = 0
    failed_assets = 0
    
    print(f"🔧 DEBUG: Starting to process {total_assets} assets...")
    
    for i, asset in enumerate(assets):
        try:
            # Progress indicator for large collections
            if i % 100 == 0 and i > 0:
                print(f"🔧 DEBUG: Processed {i}/{total_assets} assets ({(i/total_assets)*100:.1f}%)...")
            
            # Skip deleted assets
            if asset.get('deleted', False):
                deleted_assets += 1
                asset_id = asset.get('index', 'Unknown')
                asset_name = asset.get('params', {}).get('name', 'Unknown')
                print(f"🔧 DEBUG: ❌ Skipping deleted asset {asset_id} ({asset_name})")
                continue
                
            asset_params = asset.get('params', {})
            arc_standard = detect_arc_standard(asset_params)
            metadata_cid = extract_cid_from_asset(asset)
            
            if metadata_cid:  # Only include assets with valid CIDs
                processed_assets += 1
                asset_id = str(asset['index'])
                asset_name = asset_params.get('name', 'Unknown')
                asset_url = asset_params.get('url', '')
                
                # Handle image CID extraction based on ARC standard
                image_cid = None
                
                if arc_standard == 'arc19':
                    # Check if this ARC-19 asset has metadata_mime_type
                    metadata_mime_type = asset_params.get('metadata_mime_type', '')
                    if not metadata_mime_type:
                        # Missing metadata_mime_type - treat as ARC-69 style (CID is the image CID)
                        image_cid = metadata_cid
                        print(f"🔍 ARC-19 (missing metadata_mime_type): Using extracted CID as image CID for asset {asset_id}: {image_cid}")
                    else:
                        # Standard ARC-19: fetch metadata to get image CID with timeout protection
                        print(f"🔍 ARC-19: Fetching metadata for asset {asset_id} ({asset_name}): {metadata_cid}")
                        try:
                            image_cid, metadata = fetch_metadata_and_extract_image_cid(metadata_cid)
                        except Exception as metadata_error:
                            print(f"⚠️ ARC-19: Failed to fetch metadata for {asset_id}: {metadata_error}")
                            image_cid = None  # Continue processing without image CID
                elif arc_standard == 'arc69':
                    # For ARC-69, image CID is already extracted from metadata
                    image_cid = metadata_cid  # In ARC-69, the metadata CID IS the image CID
                    print(f"🔍 ARC-69: Using metadata CID as image CID for asset {asset_id}: {image_cid}")
                elif arc_standard == 'standard_ipfs':
                    # For standard IPFS, the URL directly points to the image
                    image_cid = metadata_cid  # The extracted CID is the image CID
                    print(f"🔍 Standard IPFS: Using URL CID as image CID for asset {asset_id}: {image_cid}")
                
                # Check if we have existing status for this asset
                if asset_id in existing_lookup:
                    existing_data = existing_lookup[asset_id]
                    data_row = {
                        "asset_id": asset_id,
                        "asset_name": asset_name,
                        "asset_url": asset_url,
                        "arc_standard": arc_standard,  # NEW: Track ARC standard
                        "metadata_cid": metadata_cid,
                        "image_cid": image_cid if image_cid else "",
                        "status": existing_data['status'],
                        "repin_cid": existing_data['repin_cid'] if existing_data['repin_cid'] else "",
                        "error_message": existing_data['error_message'] if existing_data['error_message'] else ""
                    }
                else:
                    # New asset or first run
                    data_row = {
                        "asset_id": asset_id,
                        "asset_name": asset_name,
                        "asset_url": asset_url,
                        "arc_standard": arc_standard,  # NEW: Track ARC standard
                        "metadata_cid": metadata_cid,
                        "image_cid": image_cid if image_cid else "",
                        "status": "pending",
                        "repin_cid": "",
                        "error_message": ""
                    }
                processed_data.append(data_row)
            else:
                # Asset has no valid CID
                no_cid_assets += 1
                asset_id = asset.get('index', 'Unknown')
                asset_name = asset_params.get('name', 'Unknown')
                asset_url = asset_params.get('url', '')
                reserve = asset_params.get('reserve', '')
                print(f"🔧 DEBUG: ❌ No CID extracted for asset {asset_id} ({asset_name})")
                print(f"    URL: {asset_url[:50] if asset_url else 'None'}...")
                print(f"    Reserve: {'Present' if reserve else 'None'}")
                print(f"    ARC Standard: {arc_standard}")
                
                # Provide more detailed diagnostics for different ARC standards
                if arc_standard == 'arc19':
                    metadata_mime_type = asset_params.get('metadata_mime_type', '')
                    print(f"    🔍 ARC19 Diagnosis: metadata_mime_type = {'Present' if metadata_mime_type else 'MISSING'}")
                    
                    if asset_url and asset_url.startswith('template-ipfs://'):
                        # Check if URL pattern is correct but field is missing
                        import re
                        pattern = re.compile(r"template-ipfs://\{ipfscid:(?P<version>\d+):(?P<codec>\w+):(?P<field>\w+):(?P<hash_type>[\w-]+)\}")
                        match = pattern.match(asset_url)
                        if match:
                            params = match.groupdict()
                            field_needed = params['field']
                            field_value = asset_params.get(field_needed)
                            if not field_value:
                                print(f"    🔍 ARC19 Diagnosis: URL template requires field '{field_needed}' but it's missing or empty")
                                print(f"    🔍 Available address fields: {[k for k in asset_params.keys() if k in ['reserve', 'manager', 'freezer', 'clawback']]}")
                            else:
                                print(f"    🔍 ARC19 Diagnosis: Field '{field_needed}' present but CID extraction failed (possibly invalid address format)")
                        else:
                            print(f"    🔍 ARC19 Diagnosis: URL doesn't match expected template pattern")
                    elif any(asset_url.startswith(prefix) for prefix in ['Qm', 'bafy', 'bafk', 'bafz']) or asset_url.startswith('ipfs://'):
                        print(f"    🔍 ARC19 Diagnosis: URL contains direct CID but extraction failed")
                        if not metadata_mime_type:
                            print(f"    💡 Expected: Missing metadata_mime_type should trigger fallback to treat as image CID")
                    else:
                        print(f"    🔍 ARC19 Diagnosis: Missing or invalid template-ipfs:// URL")
                elif arc_standard == 'arc69':
                    if reserve:
                        print(f"    🔍 ARC69 Diagnosis: Reserve field present but couldn't decode/parse metadata")
                    else:
                        print(f"    🔍 ARC69 Diagnosis: Missing reserve field required for ARC69")
                elif arc_standard == 'standard_ipfs':
                    print(f"    🔍 IPFS Diagnosis: URL should start with 'ipfs://' but extraction failed")
                elif arc_standard == 'potential_cid':
                    print(f"    🔍 POTENTIAL_CID Diagnosis: URL contains CID-like pattern but extraction failed")
                    print(f"    💡 Note: This might be the case mentioned 'cid was presented under url but missing metadata_mime_type'")
                elif arc_standard == 'unknown':
                    print(f"    🔍 General Diagnosis: Asset doesn't match any known ARC standard pattern")
                    if asset_url:
                        if asset_url.startswith('http'):
                            print(f"    💡 Suggestion: Asset uses HTTP URL - not compatible with IPFS pinning")
                        elif not any(asset_url.startswith(prefix) for prefix in ['template-ipfs://', 'ipfs://']):
                            print(f"    💡 Suggestion: URL format not recognized as ARC19, ARC69, or standard IPFS")
                
        except Exception as e:
            # Handle any unexpected errors during asset processing
            failed_assets += 1
            asset_id = asset.get('index', 'Unknown')
            asset_name = asset.get('params', {}).get('name', 'Unknown')
            print(f"🔧 DEBUG: ❌ Error processing asset {asset_id} ({asset_name}): {e}")
            continue
    
    # Print processing summary
    print(f"🔧 DEBUG: Asset processing complete!")
    print(f"    📊 Total assets found: {total_assets}")
    print(f"    🗑️ Deleted assets skipped: {deleted_assets}")
    print(f"    ❌ No CID extracted: {no_cid_assets}")
    print(f"    ⚠️ Processing errors: {failed_assets}")
    print(f"    ✅ Successfully processed: {processed_assets}")
    print(f"    📋 Final DataFrame size: {processed_assets} rows")
    
    df = pd.DataFrame(processed_data)
    
    # Explicitly set dtypes to prevent future warnings
    if not df.empty:
        df = df.astype({
            'asset_id': 'string',
            'asset_name': 'string', 
            'asset_url': 'string',
            'arc_standard': 'string',  # NEW: ARC standard column
            'metadata_cid': 'string',
            'image_cid': 'string',
            'status': 'string',
            'repin_cid': 'string',
            'error_message': 'string'
        })
    
    return df

def dataframe_to_csv(df):
    """Convert DataFrame to CSV bytes."""
    return df.to_csv(index=False).encode('utf-8')

def dataframe_to_json(df):
    """Convert DataFrame to JSON bytes."""
    return df.to_json(orient='records', indent=4).encode('utf-8')

# IPFS Pinning Functions

def validate_api_key(service_name, api_key):
    """
    Validate API key by testing with a dummy CID before bulk operations.
    For Filebase: api_key should be tuple (access_key, secret_key)
    For Infura: api_key should be tuple (project_id, api_secret)  
    For others: api_key should be string
    Returns: (is_valid: bool, error_message: str)
    """
    # Use a well-known test CID that should exist on most gateways
    test_cid = "QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o"  # Small test file
    
    # Clean service name to handle "(FREE)" and "(PAID)" suffixes
    service_name = service_name.split(" ")[0].lower()
    
    try:
        if service_name == "filebase":
            return _validate_filebase(api_key, test_cid)
        elif service_name in ["nft.storage", "web3.storage"]:
            return _validate_protocol_labs_service(service_name, api_key, test_cid)
        elif service_name == "4everland":
            return _validate_4everland(api_key, test_cid)
        elif service_name == "pinata":
            return _validate_pinata(api_key, test_cid)
        elif service_name == "infura":
            return _validate_infura(api_key, test_cid)
        else:
            return False, f"Unsupported service: {service_name}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def _validate_filebase(api_key_tuple, test_cid):
    """Test Filebase Bearer token validity for IPFS Pinning Service API."""
    try:
        # For Filebase IPFS Pinning Service, we expect a Bearer token, not S3 credentials
        if isinstance(api_key_tuple, tuple):
            access_key, secret_key = api_key_tuple
            return False, "Filebase IPFS Pinning requires a Bearer token, not S3 credentials. Generate a Bearer token from your IPFS bucket in the Filebase console."
        
        bearer_token = api_key_tuple
        url = "https://api.filebase.io/v1/ipfs/pins"
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        }
        data = {'cid': test_cid}
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code in [200, 201]:
            return True, "Bearer token valid"
        elif response.status_code == 401:
            return False, "Invalid Bearer token for IPFS Pinning Service"
        elif response.status_code == 409:
            return True, "Bearer token valid (CID already pinned)"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def _validate_protocol_labs_service(service_name, api_key, test_cid):
    """Test NFT.Storage or Web3.Storage API key validity."""
    try:
        if service_name == "nft.storage":
            url = "https://api.nft.storage/pins"
        elif service_name == "web3.storage":
            url = "https://api.web3.storage/pins"
        else:
            return False, f"Unknown Protocol Labs service: {service_name}"
            
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {'cid': test_cid}
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code in [200, 201]:
            return True, "API key valid"
        elif response.status_code == 401:
            return False, "Invalid API key"
        elif response.status_code == 409:
            return True, "API key valid (CID already pinned)"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def _validate_pinata(api_key, test_cid):
    """Test Pinata API key validity."""
    try:
        url = "https://api.pinata.cloud/pinning/pinByHash"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {'hashToPin': test_cid}
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code in [200, 201]:
            return True, "API key valid"
        elif response.status_code == 401:
            return False, "Invalid API key or JWT token"
        elif response.status_code == 409:
            return True, "API key valid (CID already pinned)"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def _validate_infura(api_key_tuple, test_cid):
    """Test Infura API credentials validity."""
    try:
        project_id, api_secret = api_key_tuple
        url = f"https://ipfs.infura.io:5001/api/v0/pin/add?arg={test_cid}"
        
        response = requests.post(url, auth=(project_id, api_secret), timeout=10)
        
        if response.status_code == 200:
            return True, "Credentials valid"
        elif response.status_code == 401:
            return False, "Invalid project ID or API secret"
        elif response.status_code == 409:
            return True, "Credentials valid (CID already pinned)"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def _validate_4everland(api_key, test_cid):
    """Test 4everland API key validity using IPFS Pinning Service API."""
    try:
        url = "https://api.4everland.dev/pins"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {'cid': test_cid}
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code in [200, 201, 202]:
            return True, "API key valid"
        elif response.status_code == 401:
            return False, "Invalid access token"
        elif response.status_code == 409:
            return True, "API key valid (CID already pinned)"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def estimate_collection_size(df, sample_count=3):
    """
    Download sample assets (both metadata and images) to estimate total collection size.
    Returns: (average_size_mb, total_estimated_size_mb, sample_results)
    """
    if df.empty:
        return 0, 0, []
    
    # Select up to sample_count random assets
    sample_assets = df.head(min(sample_count, len(df)))
    sample_results = []
    total_size_bytes = 0
    successful_downloads = 0
    
    # Common IPFS gateways to try
    gateways = [
        "https://ipfs.io/ipfs/",
        "https://gateway.ipfs.io/ipfs/",
        "https://cloudflare-ipfs.com/ipfs/"
    ]
    
    for _, asset in sample_assets.iterrows():
        asset_total_size = 0
        asset_result = {
            'asset_id': asset['asset_id'],
            'asset_name': asset['asset_name'],
            'metadata_cid': asset['metadata_cid'],
            'image_cid': asset.get('image_cid'),
            'metadata_size': 0,
            'image_size': 0,
            'total_size': 0,
            'errors': []
        }
        
        # Get metadata size
        metadata_size = get_cid_size(asset['metadata_cid'], gateways)
        if metadata_size:
            asset_result['metadata_size'] = metadata_size
            asset_total_size += metadata_size
        else:
            asset_result['errors'].append('Could not get metadata size')
        
        # Get image size if available
        if asset.get('image_cid'):
            image_size = get_cid_size(asset['image_cid'], gateways)
            if image_size:
                asset_result['image_size'] = image_size
                asset_total_size += image_size
            else:
                asset_result['errors'].append('Could not get image size')
        
        asset_result['total_size'] = asset_total_size
        asset_result['total_size_mb'] = round(asset_total_size / (1024 * 1024), 2)
        
        if asset_total_size > 0:
            total_size_bytes += asset_total_size
            successful_downloads += 1
        
        sample_results.append(asset_result)
    
    if successful_downloads > 0:
        average_size_bytes = total_size_bytes / successful_downloads
        average_size_mb = average_size_bytes / (1024 * 1024)
        total_estimated_mb = (average_size_mb * len(df))
        
        return round(average_size_mb, 2), round(total_estimated_mb, 2), sample_results
    
    return 0, 0, sample_results

def get_cid_size(cid, gateways):
    """
    Get the size of a CID from IPFS gateways.
    Returns: size in bytes or 0 if failed
    """
    for gateway in gateways:
        try:
            url = f"{gateway}{cid}"
            response = requests.head(url, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                size_bytes = int(response.headers.get('content-length', 0))
                if size_bytes > 0:
                    return size_bytes
                    
        except Exception as e:
            continue
    
    # If HEAD didn't work, try GET with partial download
    for gateway in gateways:
        try:
            url = f"{gateway}{cid}"
            response = requests.get(url, timeout=15, stream=True, 
                                  headers={'Range': 'bytes=0-1023'})  # Download only first 1KB
            
            if response.status_code in [200, 206]:
                # Try to get full size from content-range or estimate
                content_range = response.headers.get('content-range', '')
                if content_range and '/' in content_range:
                    return int(content_range.split('/')[-1])
                else:
                    # Fallback: download more to estimate
                    chunk_size = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        chunk_size += len(chunk)
                        if chunk_size >= 100000:  # Stop after ~100KB
                            break
                    return chunk_size * 10  # Rough estimate
                    
        except Exception as e:
            continue
    
    return 0

def pin_cid(service_name, api_key, cid):
    """
    Generic pinning wrapper that dispatches to specific service functions.
    For Filebase: api_key should be tuple (access_key, secret_key)
    For Infura: api_key should be tuple (project_id, api_secret)
    For others: api_key should be string
    Returns: (success: bool, response_data: dict)
    """
    # Clean service name to handle "(FREE)" and "(PAID)" suffixes
    service_name = service_name.split(" ")[0].lower()
    
    print(f"🔧 DEBUG: Pinning CID {cid[:16]}... to {service_name}")
    
    if service_name == "filebase":
        return _pin_with_filebase(api_key, cid)
    elif service_name in ["nft.storage", "web3.storage"]:
        return _pin_with_protocol_labs_service(service_name, api_key, cid)
    elif service_name == "4everland":
        return _pin_with_4everland(api_key, cid)
    elif service_name == "pinata":
        return _pin_with_pinata(api_key, cid)
    elif service_name == "infura":
        # For Infura, api_key should be a tuple (project_id, api_secret)
        return _pin_with_infura(api_key, cid)
    else:
        print(f"🔧 DEBUG: Unsupported service: {service_name}")
        return False, {"error": f"Unsupported pinning service: {service_name}"}

def _pin_with_filebase(api_key_tuple, cid_to_pin):
    """Pin CID with Filebase IPFS Pinning Service using Bearer token."""
    try:
        # For Filebase IPFS Pinning Service, we expect a Bearer token, not S3 credentials
        if isinstance(api_key_tuple, tuple):
            access_key, secret_key = api_key_tuple
            return False, {"error": "Filebase IPFS Pinning requires a Bearer token, not S3 credentials. Generate a Bearer token from your IPFS bucket in the Filebase console."}
        
        bearer_token = api_key_tuple
        url = "https://api.filebase.io/v1/ipfs/pins"
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        }
        data = {'cid': cid_to_pin}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def _pin_with_protocol_labs_service(service_name, api_key, cid_to_pin):
    """Pin CID with NFT.Storage or Web3.Storage service."""
    try:
        if service_name == "nft.storage":
            url = "https://api.nft.storage/pins"
        elif service_name == "web3.storage":
            url = "https://api.web3.storage/pins"
        else:
            return False, {"error": f"Unknown Protocol Labs service: {service_name}"}
            
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {'cid': cid_to_pin}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def _pin_with_pinata(api_key, cid_to_pin):
    """Pin CID with Pinata service."""
    try:
        url = "https://api.pinata.cloud/pinning/pinByHash"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {'hashToPin': cid_to_pin}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def _pin_with_4everland(api_key, cid_to_pin):
    """Pin CID with 4everland service."""
    try:
        print(f"🔧 DEBUG 4everland: Starting pin request for {cid_to_pin[:16]}...")
        
        url = "https://api.4everland.dev/pins"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {'cid': cid_to_pin}
        
        print(f"🔧 DEBUG 4everland: URL: {url}")
        print(f"🔧 DEBUG 4everland: Headers: {redact_sensitive_headers(headers)}")
        print(f"🔧 DEBUG 4everland: Data: {data}")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"🔧 DEBUG 4everland: Response status: {response.status_code}")
        print(f"🔧 DEBUG 4everland: Response text: {response.text}")
        
        if response.status_code in [200, 201, 202]:
            response_json = response.json()
            print(f"🔧 DEBUG 4everland: Success! Response JSON: {response_json}")
            return True, response_json
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            print(f"🔧 DEBUG 4everland: Error: {error_msg}")
            return False, {"error": error_msg}
            
    except Exception as e:
        error_msg = str(e)
        print(f"🔧 DEBUG 4everland: Exception: {error_msg}")
        return False, {"error": error_msg}

def _pin_with_infura(api_key_tuple, cid_to_pin):
    """Pin CID with Infura service."""
    try:
        project_id, api_secret = api_key_tuple
        url = f"https://ipfs.infura.io:5001/api/v0/pin/add?arg={cid_to_pin}"
        
        response = requests.post(url, auth=(project_id, api_secret), timeout=30)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"error": str(e)}

def pin_asset_cids(service_name, api_key, metadata_cid, image_cid=None):
    """
    Pin both metadata and image CIDs for an asset.
    Handles "image_only" assets that don't have metadata CIDs.
    Returns: (success: bool, results: dict)
    """
    results = {
        'metadata': {'success': False, 'response': None},
        'image': {'success': False, 'response': None}
    }
    
    # Handle image-only assets (no metadata CID)
    if not metadata_cid or metadata_cid.strip() == "":
        if image_cid:
            print(f"📌 PINNING: Image-only asset - Image CID: {image_cid}")
            success, response = pin_cid(service_name, api_key, image_cid)
            results['image'] = {'success': success, 'response': response}
            print(f"📌 IMAGE-ONLY RESULT: Success={success}, Response={response}")
            
            return success, {
                'summary': f"Image CID pinned successfully (no metadata)" if success else f"Failed to pin image CID: {response}",
                'results': results,
                'metadata_cid': "",
                'image_cid': image_cid
            }
        else:
            return False, {
                'summary': "No CIDs to pin (missing both metadata and image CIDs)",
                'results': results,
                'metadata_cid': "",
                'image_cid': ""
            }
    
    # Pin metadata CID
    print(f"📌 PINNING: Metadata CID: {metadata_cid}")
    success, response = pin_cid(service_name, api_key, metadata_cid)
    results['metadata'] = {'success': success, 'response': response}
    print(f"📌 METADATA RESULT: Success={success}, Response={response}")
    
    # Pin image CID if present
    if image_cid:
        print(f"📌 PINNING: Image CID: {image_cid}")
        success, response = pin_cid(service_name, api_key, image_cid)
        results['image'] = {'success': success, 'response': response}
        print(f"📌 IMAGE RESULT: Success={success}, Response={response}")
    
    # Determine overall success
    metadata_success = results['metadata']['success']
    image_success = results['image']['success'] if image_cid else True  # No image = success
    
    overall_success = metadata_success and image_success
    
    print(f"📌 OVERALL: Metadata={metadata_success}, Image={image_success}, Overall={overall_success}")
    
    # Create summary
    if overall_success:
        if image_cid:
            summary = f"Both metadata and image CIDs pinned successfully"
        else:
            summary = f"Metadata CID pinned successfully (no image CID)"
    else:
        failures = []
        if not metadata_success:
            failures.append(f"metadata({results['metadata']['response']})")
        if image_cid and not image_success:
            failures.append(f"image({results['image']['response']})")
        summary = f"Failed to pin: {', '.join(failures)}"
    
    return overall_success, {
        'summary': summary,
        'results': results,
        'metadata_cid': metadata_cid,
        'image_cid': image_cid
    }

def verify_pinned_cids(service_name, api_key, cids_to_check):
    """
    Memory-efficient verification for hosted deployment.
    Streams through pins without accumulating in memory.
    Returns: (verified_count, total_count, details, duplicate_report)
    """
    if not cids_to_check:
        return 0, 0, [], None
    
    verified_count = 0
    details = []
    duplicate_report = None
    
    # For 4everland, use memory-efficient streaming verification
    if service_name.split(" ")[0].lower() == "4everland":
        print(f"🔍 VERIFICATION: Streaming verification for {len(cids_to_check)} CIDs (deployment-safe)...")
        verified_count, details, duplicate_report = _stream_verify_cids(api_key, cids_to_check)
    else:
        # For other services, use individual checks
        for cid in cids_to_check:
            is_pinned, status_info = check_pin_status(service_name, api_key, cid)
            details.append({
                'cid': cid,
                'is_pinned': is_pinned,
                'status': status_info
            })
            if is_pinned:
                verified_count += 1
    
    return verified_count, len(cids_to_check), details, duplicate_report

def get_full_duplicate_report_for_cleanup(api_key):
    """
    Generate a comprehensive duplicate report suitable for cleanup operations.
    This is the memory-heavy operation that should only be run when needed.
    """
    print("🔍 DUPLICATE SCAN: Generating comprehensive duplicate report for cleanup...")
    print("⚠️ WARNING: This will fetch ALL pins and may take several minutes for large accounts")
    
    # Use the existing comprehensive duplicate detection
    return _get_4everland_pin_lookup_with_duplicates(api_key)

def _stream_verify_cids(api_key, cids_to_check):
    """
    Memory-efficient streaming verification with duplicate detection.
    Processes pins page by page without accumulating in memory.
    """
    import gc
    
    # Convert to set for fast O(1) lookup
    cids_set = set(cids_to_check)
    found_cids = {}  # cid -> status
    duplicate_counts = {}  # cid -> count (for duplicate detection)
    
    try:
        url = "https://api.4everland.dev/pins"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        print(f"🔍 VERIFICATION: Starting memory-efficient streaming...")
        
        page_size = 2000
        offset = 0
        pages_processed = 0
        start_time = time.time()
        max_time = 300  # 5 minutes max (increased for large accounts)
        
        # Dynamic page limit based on collection size
        if len(cids_to_check) <= 500:
            max_pages = 50    # Small collections
        elif len(cids_to_check) <= 1000:
            max_pages = 100   # Medium collections  
        elif len(cids_to_check) <= 2500:
            max_pages = 250   # Large collections (like yours)
        else:
            max_pages = 500   # Huge collections
            
        print(f"🔍 VERIFICATION: Using {max_pages} page limit for {len(cids_to_check)} CIDs")
        
        while pages_processed < max_pages and len(found_cids) < len(cids_set):
            # Time safety check
            if time.time() - start_time > max_time:
                print(f"🔍 VERIFICATION: Time limit reached for deployment safety")
                break
            
            params = {
                'limit': page_size,
                'offset': offset
            }
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if not results:
                        print(f"🔍 VERIFICATION: Reached end of pins")
                        break
                    
                    # Process this page immediately (memory efficient!)
                    page_found = 0
                    for pin in results:
                        pin_cid = pin.get('pin', {}).get('cid', '')
                        if pin_cid in cids_set:
                            status = pin.get('status', 'unknown')
                            
                            # Track for verification (first occurrence wins for status)
                            if pin_cid not in found_cids:
                                found_cids[pin_cid] = status
                                page_found += 1
                            
                            # Track for duplicate detection (count all occurrences)
                            if pin_cid not in duplicate_counts:
                                duplicate_counts[pin_cid] = 0
                            duplicate_counts[pin_cid] += 1
                    
                    pages_processed += 1
                    offset += len(results)
                    
                    # Progress update
                    if pages_processed % 10 == 0:
                        print(f"🔍 VERIFICATION: Processed {pages_processed} pages, found {len(found_cids)}/{len(cids_set)} CIDs")
                    
                    # Early exit if we found everything we need
                    if len(found_cids) >= len(cids_set):
                        print(f"🔍 VERIFICATION: Found all CIDs! Stopping early at page {pages_processed}")
                        break
                    
                    # If we got fewer results than requested, we've reached the end
                    if len(results) < page_size:
                        print(f"🔍 VERIFICATION: Reached end at page {pages_processed}")
                        break
                    
                    # Memory cleanup every few pages
                    if pages_processed % 20 == 0:
                        gc.collect()
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                elif response.status_code == 401:
                    print("🔍 VERIFICATION: Authentication failed")
                    break
                elif response.status_code == 429:
                    print("🔍 VERIFICATION: Rate limited, waiting...")
                    time.sleep(2)
                    continue
                else:
                    print(f"🔍 VERIFICATION: API error HTTP {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"🔍 VERIFICATION: Request error: {str(e)[:50]}...")
                break
        
        print(f"🔍 VERIFICATION: Streaming complete - found {len(found_cids)}/{len(cids_set)} CIDs in {pages_processed} pages")
        
        # Check for missing CIDs and do individual lookups if needed
        missing_cids = [cid for cid in cids_to_check if cid not in found_cids]
        
        if missing_cids and pages_processed >= max_pages:
            print(f"🔍 VERIFICATION: Individual lookup for {len(missing_cids)} missing CIDs (hit page limit)...")
            individual_results = _individual_lookup_limited(api_key, missing_cids)
            
            # Merge individual results
            for cid, (is_pinned, status) in individual_results.items():
                if is_pinned:
                    found_cids[cid] = status
        
        # Build results
        verified_count = 0
        details = []
        
        for cid in cids_to_check:
            if cid in found_cids:
                status = found_cids[cid]
                valid_statuses = ['pinned', 'queued', 'pinning', 'processing']
                is_pinned = status in valid_statuses
                
                # Add duplicate info if found
                dup_info = ""
                if cid in duplicate_counts and duplicate_counts[cid] > 1:
                    dup_info = f" (DUPLICATE: {duplicate_counts[cid]} copies!)"
                
                details.append({
                    'cid': cid,
                    'is_pinned': is_pinned,
                    'status': f"Status: {status}{dup_info}"
                })
                if is_pinned:
                    verified_count += 1
            else:
                # Not found anywhere
                details.append({
                    'cid': cid,
                    'is_pinned': False,
                    'status': f"Not found in {pages_processed} pages ({pages_processed * page_size:,} pins) + individual checks"
                })
        
        # Create duplicate report if duplicates found
        duplicate_report = None
        duplicates_found = sum(1 for count in duplicate_counts.values() if count > 1)
        if duplicates_found > 0:
            total_waste = sum(count - 1 for count in duplicate_counts.values() if count > 1)
            print(f"🔍 VERIFICATION: Found {duplicates_found} CIDs with duplicates ({total_waste} unnecessary copies)")
            
            # Create partial duplicate report for the CIDs we checked
            duplicate_report = {
                'total_pins': pages_processed * page_size,  # Approximate
                'unique_cids': len(found_cids),
                'duplicate_cids': duplicates_found,
                'total_duplicates': total_waste,
                'details': {},  # Will need full scan for cleanup details
                'partial': True  # Flag that this is not a complete scan
            }
        
        # Final cleanup
        gc.collect()
        return verified_count, details, duplicate_report
        
    except Exception as e:
        print(f"🔍 VERIFICATION: Streaming failed: {str(e)[:50]}...")
        # Ultra-safe fallback - just check a few individually
        return _safe_individual_fallback(api_key, cids_to_check[:50])

def _individual_lookup_limited(api_key, cids_to_check):
    """
    Limited individual lookup for missing CIDs after streaming.
    More targeted than the full fallback.
    """
    results = {}
    
    # Dynamic individual limit based on number of missing CIDs
    if len(cids_to_check) <= 100:
        max_individual = len(cids_to_check)  # Check all if small
    elif len(cids_to_check) <= 500:
        max_individual = min(len(cids_to_check), 300)  # Most if medium
    else:
        max_individual = min(len(cids_to_check), 500)  # Large limit for big collections
        
    print(f"🔍 VERIFICATION: Individual limit set to {max_individual} for {len(cids_to_check)} missing CIDs")
    
    print(f"🔍 VERIFICATION: Individual checks for {min(len(cids_to_check), max_individual)} CIDs...")
    
    for i, cid in enumerate(cids_to_check[:max_individual]):
        try:
            # Check recent pins for this specific CID
            url = "https://api.4everland.dev/pins"
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get(url, headers=headers, params={'limit': 200}, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                pins = data.get('results', [])
                
                # Look for this specific CID
                for pin in pins:
                    if pin.get('pin', {}).get('cid', '') == cid:
                        status = pin.get('status', 'unknown')
                        valid_statuses = ['pinned', 'queued', 'pinning', 'processing']
                        is_pinned = status in valid_statuses
                        results[cid] = (is_pinned, status)
                        break
                
                # If not found in recent, mark as not found
                if cid not in results:
                    results[cid] = (False, "Not in recent pins")
            else:
                results[cid] = (False, f"API error: HTTP {response.status_code}")
                
        except Exception as e:
            results[cid] = (False, f"Error: {str(e)[:30]}...")
        
        # Rate limiting
        if i % 10 == 0 and i > 0:
            time.sleep(0.5)
    
    # Mark remaining CIDs as not checked due to limits
    for cid in cids_to_check[max_individual:]:
        results[cid] = (False, "Not checked (individual limit reached)")
    
    return results

def _safe_individual_fallback(api_key, cids_to_check):
    """Ultra-safe fallback with strict limits for deployment reliability."""
    verified_count = 0
    details = []
    
    print(f"🔍 VERIFICATION: Safe fallback for {len(cids_to_check)} CIDs")
    
    for i, cid in enumerate(cids_to_check):
        if i >= 50:  # Hard limit for safety
            details.append({
                'cid': cid,
                'is_pinned': False,
                'status': "Not checked (safety limit)"
            })
            continue
            
        try:
            # Simple recent pin check
            url = "https://api.4everland.dev/pins"
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get(url, headers=headers, params={'limit': 100}, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                found = False
                
                for pin in results:
                    if pin.get('pin', {}).get('cid', '') == cid:
                        status = pin.get('status', 'unknown')
                        valid_statuses = ['pinned', 'queued', 'pinning', 'processing']
                        is_pinned = status in valid_statuses
                        details.append({
                            'cid': cid,
                            'is_pinned': is_pinned,
                            'status': f"Status: {status}"
                        })
                        if is_pinned:
                            verified_count += 1
                        found = True
                        break
                
                if not found:
                    details.append({
                        'cid': cid,
                        'is_pinned': False,
                        'status': "Not found in recent pins"
                    })
            else:
                details.append({
                    'cid': cid,
                    'is_pinned': False,
                    'status': f"API error: HTTP {response.status_code}"
                })
                
        except Exception as e:
            details.append({
                'cid': cid,
                'is_pinned': False,
                'status': f"Error: {str(e)[:30]}..."
            })
        
        time.sleep(0.2)  # Rate limiting
    
    return verified_count, details

def check_pin_status(service_name, api_key, cid):
    """
    Check if a specific CID is pinned on the service.
    Returns: (is_pinned: bool, status_info: str)
    """
    service_name = service_name.split(" ")[0].lower()
    
    try:
        if service_name == "4everland":
            return _check_4everland_pin_status(api_key, cid)
        elif service_name == "pinata":
            return _check_pinata_pin_status(api_key, cid)
        elif service_name == "filebase":
            return _check_filebase_pin_status(api_key, cid)
        elif service_name in ["nft.storage", "web3.storage"]:
            return _check_protocol_labs_pin_status(service_name, api_key, cid)
        elif service_name == "infura":
            return _check_infura_pin_status(api_key, cid)
        else:
            return False, f"Pin status check not supported for {service_name}"
    except Exception as e:
        return False, f"Error checking pin status: {str(e)}"

def _get_4everland_pin_lookup(api_key):
    """
    Fetch all pins from 4everland and return both lookup and duplicate info.
    Returns: (pin_lookup_dict, duplicate_report) or (None, None) if failed
    """
    try:
        url = "https://api.4everland.dev/pins"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # First, try to get total count by making a small request
        print("DEBUG VERIFICATION: Getting pin count...")
        test_response = requests.get(url, headers=headers, params={'limit': 1}, timeout=15)
        
        if test_response.status_code != 200:
            print(f"DEBUG VERIFICATION: Failed to get pin count: HTTP {test_response.status_code}")
            return None, None
            
        # Check if the API returns total count information
        test_data = test_response.json()
        print(f"DEBUG VERIFICATION: API response structure: {list(test_data.keys())}")
        
        # Try different page sizes to find the maximum
        page_sizes_to_try = [2000, 1500, 1000]  # Try larger sizes first
        best_page_size = 1000
        
        for size in page_sizes_to_try:
            print(f"DEBUG VERIFICATION: Testing page size {size}...")
            test_resp = requests.get(url, headers=headers, params={'limit': size}, timeout=15)
            if test_resp.status_code == 200:
                best_page_size = size
                print(f"DEBUG VERIFICATION: Page size {size} works!")
                break
            else:
                print(f"DEBUG VERIFICATION: Page size {size} failed: HTTP {test_resp.status_code}")
        
        print(f"DEBUG VERIFICATION: Using page size: {best_page_size}")
        
        # Start fetching all pins
        all_results = []
        limit = best_page_size
        offset = 0
        page_count = 0
        start_time = time.time()
        
        # Remove artificial page limit - let it fetch everything
        while True:
            page_start_time = time.time()
            
            params = {
                'limit': limit,
                'offset': offset
            }
            
            print(f"DEBUG VERIFICATION: Fetching page {page_count + 1} (offset {offset}, expecting up to {limit} pins)...")
            
            response = requests.get(url, headers=headers, params=params, timeout=45)
            page_time = time.time() - page_start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                all_results.extend(results)
                page_count += 1
                
                print(f"DEBUG VERIFICATION: Page {page_count} retrieved {len(results)} pins in {page_time:.1f}s (total: {len(all_results)})")
                
                # If we got fewer results than the limit, we've reached the end
                if len(results) < limit:
                    print(f"DEBUG VERIFICATION: Reached end - got {len(results)} < {limit}")
                    break
                
                # Safety check for total time (increased to 10 minutes)
                total_time = time.time() - start_time
                if total_time > 600:  # 10 minutes
                    print(f"DEBUG VERIFICATION: Time limit reached ({total_time:.1f}s) - stopping at {len(all_results)} pins")
                    break
                    
                offset += limit
                
                # Reduced delay to speed up
                time.sleep(0.2)
                
            elif response.status_code == 429:  # Rate limited
                print("DEBUG VERIFICATION: Rate limited - waiting 10 seconds...")
                time.sleep(10)
                continue
            else:
                print(f"DEBUG VERIFICATION: Failed to fetch page {page_count + 1}: HTTP {response.status_code}")
                return None, None
        
        total_time = time.time() - start_time
        print(f"DEBUG VERIFICATION: Completed in {total_time:.1f}s - retrieved {len(all_results)} pins across {page_count} pages")
        
        # Analyze for duplicates and create lookup
        pin_lookup = {}
        cid_counts = {}
        duplicate_details = {}
        
        for pin in all_results:
            pin_cid = pin.get('pin', {}).get('cid', '')
            status = pin.get('status', 'unknown')
            request_id = pin.get('requestid', 'unknown')
            created = pin.get('created', 'unknown')
            
            if pin_cid:
                # Count occurrences
                if pin_cid not in cid_counts:
                    cid_counts[pin_cid] = 0
                    duplicate_details[pin_cid] = []
                
                cid_counts[pin_cid] += 1
                duplicate_details[pin_cid].append({
                    'request_id': request_id,
                    'status': status,
                    'created': created
                })
                
                # For lookup, prefer 'pinned' status over others
                if pin_cid not in pin_lookup or status == 'pinned':
                    pin_lookup[pin_cid] = status
        
        # Generate duplicate report
        duplicates = {cid: count for cid, count in cid_counts.items() if count > 1}
        
        duplicate_report = {
            'total_pins': len(all_results),
            'unique_cids': len(pin_lookup),
            'duplicate_cids': len(duplicates),
            'total_duplicates': sum(duplicates.values()) - len(duplicates),  # Extra pins beyond first
            'details': {cid: duplicate_details[cid] for cid in duplicates}
        }
        
        if duplicates:
            print(f"🚨 DUPLICATE DETECTION: Found {len(duplicates)} CIDs with duplicates!")
            print(f"   • {duplicate_report['total_duplicates']} unnecessary duplicate pins")
            print(f"   • Potential cost savings from cleanup")
            
            # Show top 5 duplicates
            top_duplicates = sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]
            for cid, count in top_duplicates:
                print(f"   • {cid[:16]}... appears {count} times")
        else:
            print("✅ NO DUPLICATES: All pins are unique")
        
        print(f"DEBUG VERIFICATION: Created lookup for {len(pin_lookup)} unique pins")
        return pin_lookup, duplicate_report
        
    except Exception as e:
        print(f"DEBUG VERIFICATION: Exception fetching pin lookup: {str(e)}")
        return None, None

def _check_4everland_pin_status(api_key, cid):
    """
    Check pin status on 4everland using pin list endpoint.
    Note: The /pins endpoint only returns completed pins, not pending/processing/failed ones.
    """
    try:
        # Use pin list endpoint without status filter to avoid API errors
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
        
        # Handle pagination to get all pins
        while True:
            params = {
                'limit': limit,
                'offset': offset
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                all_results.extend(results)
                page_count += 1
                
                # Debug: Only print for first page to avoid spam
                if offset == 0 and results:
                    print(f"DEBUG VERIFICATION: Retrieved {len(results)} pins on first page")
                    if len(results) == limit:
                        print(f"DEBUG VERIFICATION: Pagination detected - fetching all pages...")
                
                # If we got fewer results than the limit, we've reached the end
                if len(results) < limit:
                    break
                    
                offset += limit
            else:
                print(f"DEBUG VERIFICATION: HTTP {response.status_code}: {response.text}")
                return False, f"HTTP {response.status_code}: {response.text}"
        
        if page_count > 1:
            print(f"DEBUG VERIFICATION: Retrieved {len(all_results)} total pins across {page_count} pages")
        
        # Search for the CID in all results
        for pin in all_results:
            pin_cid = pin.get('pin', {}).get('cid', '')
            if pin_cid == cid:
                status = pin.get('status', 'unknown')
                # Accept pinned, queued, pinning, and processing as valid statuses
                valid_statuses = ['pinned', 'queued', 'pinning', 'processing']
                return status in valid_statuses, f"Status: {status}"
        
        # Important: Not found in /pins doesn't mean it failed - it might be pending/processing
        return False, "Not found in completed pins (may be pending/processing - check https://dashboard.4everland.org/bucket/pinning-service)"
        
    except Exception as e:
        print(f"DEBUG VERIFICATION: Exception: {str(e)}")
        return False, f"Connection error: {str(e)}"

def _check_pinata_pin_status(api_key, cid):
    """Check pin status on Pinata."""
    try:
        url = f"https://api.pinata.cloud/data/pinList?hashContains={cid}"
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rows = data.get('rows', [])
            if rows:
                return True, f"Status: pinned"
            else:
                return False, "Not found in pin list"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def _check_filebase_pin_status(api_key, cid):
    """Check pin status on Filebase."""
    try:
        url = f"https://api.filebase.io/v1/ipfs/pins/{cid}"
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            return status == 'pinned', f"Status: {status}"
        elif response.status_code == 404:
            return False, "Not found - not pinned"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def _check_protocol_labs_pin_status(service_name, api_key, cid):
    """Check pin status on Protocol Labs services."""
    try:
        if service_name == "nft.storage":
            url = f"https://api.nft.storage/pins/{cid}"
        elif service_name == "web3.storage":
            url = f"https://api.web3.storage/pins/{cid}"
        else:
            return False, f"Unknown service: {service_name}"
            
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            return status == 'pinned', f"Status: {status}"
        elif response.status_code == 404:
            return False, "Not found - not pinned"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def _check_infura_pin_status(api_key_tuple, cid):
    """Check pin status on Infura."""
    try:
        project_id, api_secret = api_key_tuple
        url = f"https://ipfs.infura.io:5001/api/v0/pin/ls?arg={cid}"
        
        response = requests.post(url, auth=(project_id, api_secret), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # If the response contains the CID, it's pinned
            keys = data.get('Keys', {})
            return cid in keys, f"Status: {'pinned' if cid in keys else 'not pinned'}"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def test_4everland_status_endpoints(api_key):
    """
    Test different status queries to see what pin statuses 4everland exposes.
    This helps understand if pending/failed pins are stored separately.
    """
    url = "https://api.4everland.dev/pins"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test different status values individually
    test_statuses = [
        'pinned',      # Completed pins
        'pinning',     # Currently being pinned
        'queued',      # Waiting to be pinned
        'failed',      # Failed pins
        'processing',  # Processing pins
        'pending'      # Pending pins
    ]
    
    results = {}
    
    for status in test_statuses:
        try:
            params = {
                'limit': 10,  # Small limit for testing
                'status': status  # Try individual status
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results[status] = {
                    'success': True,
                    'count': len(data.get('results', [])),
                    'sample_statuses': [r.get('status') for r in data.get('results', [])[:3]]
                }
                print(f"✅ STATUS '{status}': Found {results[status]['count']} pins")
            else:
                results[status] = {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                print(f"❌ STATUS '{status}': {results[status]['error']}")
                
        except Exception as e:
            results[status] = {
                'success': False,
                'error': f"Exception: {str(e)}"
            }
            print(f"❌ STATUS '{status}': {results[status]['error']}")
    
    return results

def detect_old_web3_storage_risk(cids_to_check, sample_size=None):
    """
    Lightweight detection to identify CIDs that may be at risk from old.web3.storage unpinning.
    Tests CID availability across multiple IPFS gateways to determine redundancy.
    
    Args:
        cids_to_check: List of CIDs to test
        sample_size: Optional limit for testing (useful for large collections)
    
    Returns:
        dict with risk analysis results
    """
    import random
    
    # Major public IPFS gateways (excluding old.web3.storage)
    public_gateways = [
        "https://ipfs.io/ipfs/",
        "https://gateway.ipfs.io/ipfs/",
        "https://dweb.link/ipfs/",
        "https://cloudflare-ipfs.com/ipfs/",
        "https://cf-ipfs.com/ipfs/",
        "https://gateway.pinata.cloud/ipfs/"
    ]
    
    # old.web3.storage gateways (shutting down)
    old_web3_storage_gateways = [
        "https://nftstorage.link/ipfs/",  # old.web3.storage gateway
        "https://w3s.link/ipfs/"         # old.web3.storage gateway
    ]
    
    # Sample CIDs if needed
    if sample_size and len(cids_to_check) > sample_size:
        cids_to_test = random.sample(cids_to_check, sample_size)
        print(f"🔍 Testing {sample_size} random CIDs out of {len(cids_to_check)} total")
    else:
        cids_to_test = cids_to_check
        print(f"🔍 Testing all {len(cids_to_test)} CIDs")
    
    results = {
        'total_tested': len(cids_to_test),
        'high_risk': [],      # Only available on old.web3.storage
        'medium_risk': [],    # Available on few gateways
        'low_risk': [],       # Available on many gateways
        'unreachable': [],    # Not available anywhere
        'gateway_stats': {}
    }
    
    for i, cid in enumerate(cids_to_test):
        print(f"Testing CID {i+1}/{len(cids_to_test)}: {cid[:16]}...")
        
        gateway_availability = {}
        
        # Test each gateway
        for gateway in public_gateways + old_web3_storage_gateways:
            is_available = _test_gateway_availability(gateway, cid)
            gateway_availability[gateway] = is_available
            
            # Update gateway stats
            if gateway not in results['gateway_stats']:
                results['gateway_stats'][gateway] = {'available': 0, 'total': 0}
            results['gateway_stats'][gateway]['total'] += 1
            if is_available:
                results['gateway_stats'][gateway]['available'] += 1
        
        # Analyze risk level
        public_available = sum(1 for gw in public_gateways if gateway_availability.get(gw, False))
        old_web3_storage_available = sum(1 for gw in old_web3_storage_gateways if gateway_availability.get(gw, False))
        
        cid_info = {
            'cid': cid,
            'public_gateways_available': public_available,
            'old_web3_storage_available': old_web3_storage_available,
            'total_available': public_available + old_web3_storage_available
        }
        
        if public_available == 0 and old_web3_storage_available > 0:
            results['high_risk'].append(cid_info)
        elif public_available == 0:
            results['unreachable'].append(cid_info)
        elif public_available <= 2:
            results['medium_risk'].append(cid_info)
        else:
            results['low_risk'].append(cid_info)
    
    return results

def _test_gateway_availability(gateway_url, cid, timeout=10):
    """
    Test if a CID is available through a specific IPFS gateway.
    Uses HEAD request for lightweight testing.
    """
    try:
        url = f"{gateway_url}{cid}"
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def analyze_old_web3_storage_risk_summary(risk_results):
    """
    Generate a human-readable summary of old.web3.storage risk analysis.
    """
    total = risk_results['total_tested']
    high_risk = len(risk_results['high_risk'])
    medium_risk = len(risk_results['medium_risk'])
    low_risk = len(risk_results['low_risk'])
    unreachable = len(risk_results['unreachable'])
    
    summary = f"""
🔍 OLD.WEB3.STORAGE RISK ANALYSIS RESULTS:

📊 TESTED: {total} CIDs

🚨 HIGH RISK: {high_risk} CIDs ({high_risk/total*100:.1f}%)
   → Only available on old.web3.storage - WILL BE LOST when they unpin

⚠️  MEDIUM RISK: {medium_risk} CIDs ({medium_risk/total*100:.1f}%)
   → Available on few public gateways - Limited redundancy

✅ LOW RISK: {low_risk} CIDs ({low_risk/total*100:.1f}%)
   → Available on multiple public gateways - Well distributed

❌ UNREACHABLE: {unreachable} CIDs ({unreachable/total*100:.1f}%)
   → Not accessible on any tested gateway - Already lost

RECOMMENDATION:
- Immediately repin HIGH RISK CIDs to a reliable service
- Consider repinning MEDIUM RISK CIDs for better redundancy
"""
    
    # Add gateway performance stats
    summary += "\n🌐 GATEWAY AVAILABILITY:\n"
    for gateway, stats in risk_results['gateway_stats'].items():
        percentage = (stats['available'] / stats['total']) * 100 if stats['total'] > 0 else 0
        summary += f"   {gateway}: {stats['available']}/{stats['total']} ({percentage:.1f}%)\n"
    
    return summary 

def parse_wen_tools_csv(csv_content):
    """
    Parse CSV content with improved error handling for boolean NA values.
    Also supports mixed ARC standards.
    """
    try:
        # Read CSV content
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode('utf-8')
        
        from io import StringIO
        # Fix: Add na_filter=False to prevent boolean NA issues
        df_raw = pd.read_csv(StringIO(csv_content), na_filter=False, dtype=str)
        
        if df_raw.empty:
            return None, "CSV file is empty", None
        
        print(f"🔧 DEBUG: CSV columns: {list(df_raw.columns)}")
        print(f"🔧 DEBUG: CSV shape: {df_raw.shape}")
        
        # Detect column mappings with flexible matching
        asset_id_col = None
        name_col = None
        image_cid_col = None
        metadata_cid_col = None
        status_col = None
        
        # Map asset_id column
        for col in df_raw.columns:
            if 'asset_id' in col.lower() or col.lower() == 'id':
                asset_id_col = col
                break
        
        # Map name column  
        for col in df_raw.columns:
            if col.lower() in ['name', 'unit-name', 'unit_name', 'asset_name']:
                name_col = col
                break
        
        # Map image CID column
        for col in df_raw.columns:
            if any(term in col.lower() for term in ['image_ipfs_cid', 'image_cid', 'ipfs_cid', 'cid']):
                image_cid_col = col
                break
        
        # Map metadata CID column (for our app exports)
        for col in df_raw.columns:
            if 'metadata_cid' in col.lower():
                metadata_cid_col = col
                break
        
        # Map status column (for our app exports) 
        for col in df_raw.columns:
            if col.lower() == 'status':
                status_col = col
                break
        
        # Detect CSV format type
        is_our_app_format = bool(metadata_cid_col and status_col)
        csv_format = "Cyber Skulls App Export" if is_our_app_format else "wen.tools or similar"
        
        print(f"🔧 DEBUG: Detected CSV format: {csv_format}")
        print(f"🔧 DEBUG: Detected columns - asset_id: {asset_id_col}, name: {name_col}, image_cid: {image_cid_col}, metadata_cid: {metadata_cid_col}, status: {status_col}")
        
        # Validate required columns
        missing_columns = []
        if not asset_id_col:
            missing_columns.append('asset_id')
        if not name_col:
            missing_columns.append('name (or unit-name)')
        if not image_cid_col:
            missing_columns.append('image_ipfs_cid (or similar)')
        
        if missing_columns:
            return None, f"Missing required columns: {missing_columns}. Available columns: {list(df_raw.columns)}", None
        
        processed_data = []
        base_cid_tracker = {}
        collection_types = set()
        arc_standards_found = set()  # NEW: Track ARC standards
        
        # Tracking variables
        total_csv_rows = len(df_raw)
        skipped_empty_image = 0
        processed_count = 0
        metadata_fetch_failures = 0
        
        if is_our_app_format:
            print(f"🔧 DEBUG: Starting to process {total_csv_rows} CSV rows (Cyber Skulls App format - metadata already present)...")
        else:
            print(f"🔧 DEBUG: Starting to process {total_csv_rows} CSV rows and fetch metadata CIDs from Algorand...")
        
        for idx, row in df_raw.iterrows():
            # Skip rows with empty image_cid - handle string 'nan' and empty strings
            image_url = str(row.get(image_cid_col, '')).strip()
            if not image_url or image_url.lower() in ['nan', 'none', '', 'null']:
                skipped_empty_image += 1
                if skipped_empty_image <= 5:  # Show first 5 examples
                    asset_id = str(row.get(asset_id_col, 'Unknown'))
                    print(f"🔧 DEBUG: ❌ Skipping row {idx+1} (asset {asset_id}) - empty image CID")
                continue
            
            asset_id = str(row[asset_id_col]).strip()
            asset_name = str(row[name_col]).strip() 
            
            print(f"🔧 DEBUG: Processing asset {asset_id} ({asset_name}), image URL: {image_url}")
            
            # Parse IPFS URL to extract CID and file path
            base_cid = ""
            file_path = ""
            full_ipfs_url = ""
            
            if image_url.startswith('ipfs://'):
                full_ipfs_url = image_url
                ipfs_path = image_url.replace('ipfs://', '')
                
                # Handle ARC-19 fragment notation (e.g., "cid#i" or "cid#arc") 
                # This fixes parsing for URLs like "ipfs://bafybei...#i"
                if '#' in ipfs_path:
                    ipfs_path = ipfs_path.split('#')[0]  # Remove fragment like "#i"
                    print(f"🔧 DEBUG: Cleaned fragment from IPFS path: {ipfs_path[:20]}...")
                
                if '/' in ipfs_path:
                    parts = ipfs_path.split('/')
                    base_cid = parts[0]
                    file_path = '/' + '/'.join(parts[1:])
                    collection_types.add('directory_based')
                else:
                    base_cid = ipfs_path
                    file_path = ""
                    collection_types.add('individual_cid')
            else:
                # Handle bare CID with possible fragment
                clean_cid = image_url.split('#')[0] if '#' in image_url else image_url
                base_cid = clean_cid
                file_path = ""
                full_ipfs_url = f"ipfs://{image_url}"
                collection_types.add('individual_cid')
            
            # Handle metadata CID based on CSV format
            metadata_cid = ""
            arc_standard = "unknown"
            existing_status = "pending"
            
            if is_our_app_format:
                # Our app format - metadata already present, no need to fetch from Algorand
                metadata_cid = str(row.get(metadata_cid_col, '')).strip()
                existing_status = str(row.get(status_col, 'pending')).strip()
                arc_standard = "csv_provided"  # Mark as CSV-provided
                arc_standards_found.add(arc_standard)
                print(f"🔧 DEBUG: Using CSV metadata for asset {asset_id}: {metadata_cid[:20] if metadata_cid else 'None'}...")
            else:
                # wen.tools or similar format - need to fetch metadata from Algorand
                try:
                    print(f"🔧 DEBUG: Fetching metadata CID for asset {asset_id}...")
                    from algosdk.v2client import algod
                    
                    algod_address = "https://mainnet-api.algonode.cloud"
                    algod_client = algod.AlgodClient("", algod_address)
                    
                    asset_info = algod_client.asset_info(int(asset_id))
                    asset_params = asset_info.get('params', {})
                    
                    # Detect ARC standard and extract metadata
                    arc_standard = detect_arc_standard(asset_params)
                    arc_standards_found.add(arc_standard)
                    
                    if arc_standard in ['arc19', 'arc69', 'standard_ipfs']:
                        metadata_cid = extract_cid_from_asset({'params': asset_params, 'index': asset_id})
                        if metadata_cid:
                            print(f"🔧 DEBUG: ✅ Found {arc_standard.upper()} metadata CID for {asset_id}: {metadata_cid[:20]}...")
                        else:
                            print(f"🔧 DEBUG: ⚠️ No metadata CID found for {arc_standard.upper()} asset {asset_id}")
                    else:
                        print(f"🔧 DEBUG: ⚠️ Unknown ARC standard for asset {asset_id}")
                        
                except Exception as e:
                    metadata_fetch_failures += 1
                    print(f"🔧 DEBUG: ❌ Error fetching metadata for asset {asset_id}: {str(e)}")
                    metadata_cid = ""
                    arc_standard = "error"
            
            # Improved metadata handling - don't fail assets just because metadata is missing
            if not metadata_cid and arc_standard == "error":
                # If metadata fetch failed but we have a valid image CID, 
                # treat it as a valid asset that can still be pinned
                if base_cid and len(base_cid) > 10:  # Basic CID validation
                    arc_standard = "image_only"  # Mark as image-only asset
                    print(f"🔧 DEBUG: ⚠️ Metadata fetch failed for {asset_id}, but image CID is valid - proceeding as image-only asset")
                    arc_standards_found.add(arc_standard)
            
            print(f"🔧 DEBUG: Parsed - base_cid: {base_cid}, arc_standard: {arc_standard}, metadata_cid: {metadata_cid[:20] if metadata_cid else 'None'}...")
            
            # Track base CID usage for analysis
            if base_cid not in base_cid_tracker:
                base_cid_tracker[base_cid] = []
            base_cid_tracker[base_cid].append({
                'asset_id': asset_id,
                'asset_name': asset_name,
                'file_path': file_path,
                'full_url': full_ipfs_url,
                'metadata_cid': metadata_cid,
                'arc_standard': arc_standard
            })
            
            # Create data row in our internal format
            data_row = {
                "asset_id": asset_id,
                "asset_name": asset_name,
                "asset_url": "",
                "arc_standard": arc_standard,  # Track ARC standard
                "metadata_cid": metadata_cid,
                "image_cid": base_cid,
                "image_file_path": file_path,
                "full_ipfs_url": full_ipfs_url,
                "status": existing_status,  # Use existing status from CSV if available
                "repin_cid": "",
                "error_message": ""
            }
            processed_data.append(data_row)
            processed_count += 1
        
        # Print detailed processing summary
        print(f"🔧 DEBUG: CSV processing complete!")
        print(f"    📊 Total CSV rows: {total_csv_rows}")
        print(f"    ❌ Skipped (empty image CID): {skipped_empty_image}")
        if is_our_app_format:
            print(f"    ⚡ Fast processing (metadata already in CSV): {processed_count}")
        else:
            print(f"    ⚠️ Metadata fetch failures: {metadata_fetch_failures}")
        print(f"    ✅ Successfully processed: {processed_count}")
        print(f"    📋 Final DataFrame size: {processed_count} rows")
        
        # Create DataFrame with proper dtypes
        df = pd.DataFrame(processed_data)
        
        if not df.empty:
            # Fix: Ensure all columns are properly typed as strings
            string_columns = ['asset_id', 'asset_name', 'asset_url', 'arc_standard', 'metadata_cid', 
                            'image_cid', 'image_file_path', 'full_ipfs_url', 'status', 'repin_cid', 'error_message']
            
            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].astype('string')
        
        # Enhanced collection analysis
        unique_base_cids = len(base_cid_tracker)
        total_assets = len(df)
        metadata_cids_found = sum(1 for _, row in df.iterrows() if row['metadata_cid'])
        
        if 'directory_based' in collection_types and unique_base_cids < total_assets:
            collection_type = 'directory_based'
        elif len(collection_types) == 1 and 'individual_cid' in collection_types:
            collection_type = 'individual_cid'
        else:
            collection_type = 'mixed'
        
        collection_info = {
            'total_assets': total_assets,
            'unique_base_cids': unique_base_cids,
            'metadata_cids_found': metadata_cids_found,
            'collection_type': collection_type,
            'collection_types_detected': list(collection_types),
            'arc_standards_found': list(arc_standards_found),
            'is_directory_collection': unique_base_cids < total_assets,
            'base_cid_info': base_cid_tracker,
            'csv_format': csv_format,  # NEW: CSV format type
            'is_our_app_format': is_our_app_format,  # NEW: Flag for our format
            'detected_columns': {
                'asset_id': asset_id_col,
                'name': name_col,
                'image_cid': image_cid_col,
                'metadata_cid': metadata_cid_col,
                'status': status_col
            }
        }
        
        print(f"🔧 DEBUG: Collection analysis - type: {collection_type}, ARC standards: {arc_standards_found}, unique image CIDs: {unique_base_cids}, metadata CIDs found: {metadata_cids_found}, total assets: {total_assets}")
        
        return df, None, collection_info
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"🔧 DEBUG: Full CSV parsing error: {error_details}")
        return None, f"Error parsing CSV: {str(e)}", None

def analyze_collection_structure(df):
    """
    Analyze the collection structure to determine pinning strategy.
    Returns: (strategy, analysis_info)
    """
    if df.empty:
        return "none", {}
    
    # Check if we have file paths (directory-based collection)
    # Only check for file paths if the column exists (from wen.tools CSV uploads)
    has_file_paths = False
    if 'image_file_path' in df.columns:
        has_file_paths = df['image_file_path'].notna().any() and (df['image_file_path'] != '').any()
    
    # Count unique base CIDs vs total assets
    unique_base_cids = df['image_cid'].nunique()
    total_assets = len(df)
    
    if has_file_paths and unique_base_cids < total_assets:
        # Directory-based collection
        cid_groups = df.groupby('image_cid').size().sort_values(ascending=False)
        
        analysis = {
            'type': 'directory_based',
            'total_assets': total_assets,
            'unique_base_cids': unique_base_cids,
            'assets_per_cid': cid_groups.to_dict(),
            'largest_directory': cid_groups.iloc[0] if len(cid_groups) > 0 else 0,
            'avg_files_per_directory': total_assets / unique_base_cids if unique_base_cids > 0 else 0,
            'pinning_strategy_options': {
                'base_cids_only': f'Pin {unique_base_cids} base CIDs (recommended for directories)',
                'individual_files': f'Pin {total_assets} individual file CIDs (not recommended - wasteful)',
                'mixed': 'Let user choose per-CID strategy'
            }
        }
        
        return "directory_based", analysis
    elif unique_base_cids == total_assets:
        # Individual CID collection
        return "individual_cids", {
            'type': 'individual',
            'total_assets': total_assets,
            'unique_cids': unique_base_cids,
            'pinning_strategy_options': {
                'individual_cids': f'Pin {unique_base_cids} unique CIDs (standard approach)'
            }
        }
    else:
        # Mixed or partial duplicates
        cid_groups = df.groupby('image_cid').size().sort_values(ascending=False)
        duplicated_cids = sum(1 for count in cid_groups if count > 1)
        
        return "mixed", {
            'type': 'mixed',
            'total_assets': total_assets,
            'unique_cids': unique_base_cids,
            'duplicated_cids': duplicated_cids,
            'assets_per_cid': cid_groups.to_dict(),
            'pinning_strategy_options': {
                'unique_only': f'Pin {unique_base_cids} unique CIDs (recommended)',
                'all_individual': f'Pin all {total_assets} CIDs (may duplicate work)'
            }
        }

def get_cids_to_pin(df, strategy="auto"):
    """
    Get list of CIDs that need to be pinned based on collection structure and strategy.
    
    Strategies:
    - auto: Automatically choose best strategy
    - base_cids_only: Pin only unique base CIDs  
    - individual_files: Pin each file separately (for directory collections)
    - unique_only: Pin unique CIDs only (for mixed collections)
    - all_individual: Pin every CID even if duplicated
    
    Returns: list of CIDs to pin
    """
    if df.empty:
        return []
    
    strategy_type, analysis = analyze_collection_structure(df)
    
    if strategy == "auto":
        if strategy_type == "directory_based":
            # For directory collections, pin base CIDs only
            return df['image_cid'].unique().tolist()
        elif strategy_type == "individual_cids":
            # For individual collections, pin all CIDs
            return df['image_cid'].tolist()
        else:  # mixed
            # For mixed collections, pin unique CIDs only
            return df['image_cid'].unique().tolist()
    elif strategy == "base_cids_only":
        return df['image_cid'].unique().tolist()
    elif strategy == "individual_files":
        # This would pin each file separately - only useful for very specific cases
        # For directory collections, this creates individual CIDs for each file
        individual_cids = []
        for _, row in df.iterrows():
            # Check if image_file_path column exists and has data
            if 'image_file_path' in df.columns and row['image_file_path']:
                # For files in directories, we'd need to construct individual file CIDs
                # This is complex and not usually needed since the directory CID covers all files
                individual_cids.append(row['image_cid'])  # Fallback to base CID
            else:
                individual_cids.append(row['image_cid'])
        return individual_cids
    elif strategy == "unique_only":
        return df['image_cid'].unique().tolist()
    elif strategy == "all_individual":
        return df['image_cid'].tolist()
    else:
        # Default fallback
        return df['image_cid'].unique().tolist()

def _get_4everland_pin_lookup_with_duplicates(api_key):
    """
    Fetch all pins from 4everland and return both lookup and duplicate info.
    Returns: (pin_lookup_dict, duplicate_report) or (None, None) if failed
    """
    try:
        url = "https://api.4everland.dev/pins"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Fetch all pins (using the improved pagination logic)
        all_results = []
        limit = 2000
        offset = 0
        page_count = 0
        start_time = time.time()
        
        while True:
            params = {'limit': limit, 'offset': offset}
            response = requests.get(url, headers=headers, params=params, timeout=45)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                all_results.extend(results)
                page_count += 1
                
                print(f"DEBUG VERIFICATION: Page {page_count} retrieved {len(results)} pins (total: {len(all_results)})")
                
                if len(results) < limit:
                    break
                offset += limit
                time.sleep(0.2)
            else:
                print(f"DEBUG VERIFICATION: Failed: HTTP {response.status_code}")
                return None, None
        
        print(f"DEBUG VERIFICATION: Retrieved {len(all_results)} total pins")
        
        # Analyze for duplicates and create lookup
        pin_lookup = {}
        cid_counts = {}
        duplicate_details = {}
        
        for pin in all_results:
            pin_cid = pin.get('pin', {}).get('cid', '')
            status = pin.get('status', 'unknown')
            request_id = pin.get('requestid', 'unknown')
            created = pin.get('created', 'unknown')
            
            if pin_cid:
                # Count occurrences
                if pin_cid not in cid_counts:
                    cid_counts[pin_cid] = 0
                    duplicate_details[pin_cid] = []
                
                cid_counts[pin_cid] += 1
                duplicate_details[pin_cid].append({
                    'request_id': request_id,
                    'status': status,
                    'created': created
                })
                
                # For lookup, prefer 'pinned' status over others
                if pin_cid not in pin_lookup or status == 'pinned':
                    pin_lookup[pin_cid] = status
        
        # Generate duplicate report
        duplicates = {cid: count for cid, count in cid_counts.items() if count > 1}
        
        duplicate_report = {
            'total_pins': len(all_results),
            'unique_cids': len(pin_lookup),
            'duplicate_cids': len(duplicates),
            'total_duplicates': sum(duplicates.values()) - len(duplicates),  # Extra pins beyond first
            'details': {cid: duplicate_details[cid] for cid in duplicates}
        }
        
        if duplicates:
            print(f"🚨 DUPLICATE DETECTION: Found {len(duplicates)} CIDs with duplicates!")
            print(f"   • {duplicate_report['total_duplicates']} unnecessary duplicate pins")
            print(f"   • Potential cost savings from cleanup")
            
            # Show top 5 duplicates
            top_duplicates = sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]
            for cid, count in top_duplicates:
                print(f"   • {cid[:16]}... appears {count} times")
        else:
            print("✅ NO DUPLICATES: All pins are unique")
        
        print(f"DEBUG VERIFICATION: Created lookup for {len(pin_lookup)} unique pins")
        return pin_lookup, duplicate_report
        
    except Exception as e:
        print(f"DEBUG VERIFICATION: Exception: {str(e)}")
        return None, None

def verify_pinned_cids_with_duplicate_detection(service_name, api_key, cids_to_check):
    """Enhanced verification with duplicate detection"""
    if not cids_to_check:
        return 0, 0, [], None
    
    verified_count = 0
    details = []
    duplicate_report = None
    
    if service_name.split(" ")[0].lower() == "4everland":
        print(f"DEBUG VERIFICATION: Optimizing 4everland verification for {len(cids_to_check)} CIDs...")
        pin_lookup, duplicate_report = _get_4everland_pin_lookup_with_duplicates(api_key)
        
        if pin_lookup is not None:
            # Check each CID
            for cid in cids_to_check:
                if cid in pin_lookup:
                    status = pin_lookup[cid]
                    valid_statuses = ['pinned', 'queued', 'pinning', 'processing']
                    is_pinned = status in valid_statuses
                    details.append({
                        'cid': cid,
                        'is_pinned': is_pinned,
                        'status': f"Status: {status}"
                    })
                    if is_pinned:
                        verified_count += 1
                else:
                    details.append({
                        'cid': cid,
                        'is_pinned': False,
                        'status': "Not found in completed pins"
                    })
    
    return verified_count, len(cids_to_check), details, duplicate_report

def _delete_4everland_pin(api_key, request_id):
    """
    Delete a specific pin by request ID on 4everland.
    Returns: (success, message)
    """
    try:
        url = f"https://api.4everland.dev/pins/{request_id}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.delete(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return True, "Pin deleted successfully"
        elif response.status_code == 202:
            return True, "Pin deletion accepted (processing asynchronously)"
        elif response.status_code == 404:
            return False, "Pin not found (may already be deleted)"
        elif response.status_code == 403:
            return False, "Permission denied - check API key permissions"
        else:
            return False, f"Failed to delete pin: HTTP {response.status_code}"
            
    except Exception as e:
        return False, f"Exception deleting pin: {str(e)}"

def cleanup_duplicate_pins(api_key, duplicate_report, dry_run=True):
    """
    Clean up duplicate pins, keeping the best copy of each CID.
    
    Args:
        api_key: 4everland API key
        duplicate_report: Report from verification with duplicate details
        dry_run: If True, only simulate deletion without actually deleting
    
    Returns: dict with cleanup results
    """
    if not duplicate_report or duplicate_report['duplicate_cids'] == 0:
        return {
            'success': True,
            'message': 'No duplicates found to clean up',
            'deleted_count': 0,
            'kept_count': 0,
            'savings': 0,
            'details': []
        }
    
    print(f"🧹 DUPLICATE CLEANUP: Starting {'DRY RUN' if dry_run else 'ACTUAL DELETION'}")
    print(f"   • Found {duplicate_report['duplicate_cids']} CIDs with duplicates")
    print(f"   • Total unnecessary duplicates: {duplicate_report['total_duplicates']}")
    
    cleanup_results = {
        'success': True,
        'deleted_count': 0,
        'kept_count': 0,
        'failed_deletions': 0,
        'savings': 0,
        'details': [],
        'errors': []
    }
    
    # Process each CID with duplicates
    for cid, instances in duplicate_report['details'].items():
        if len(instances) <= 1:
            continue  # Skip if not actually duplicated
            
        print(f"\n🔍 Processing CID: {cid[:20]}... ({len(instances)} copies)")
        
        # Sort instances to determine which to keep (priority order):
        # 1. Status 'pinned' over others
        # 2. Newer creation date
        # 3. Lexicographically smaller request_id (for consistency)
        def sort_key(instance):
            status_priority = {'pinned': 0, 'queued': 1, 'pinning': 2, 'processing': 3, 'failed': 4}
            status_score = status_priority.get(instance['status'], 5)
            
            # Parse creation date (newer = lower score)
            try:
                from datetime import datetime
                created_date = datetime.fromisoformat(instance['created'].replace('Z', '+00:00'))
                date_score = -created_date.timestamp()  # Negative so newer is "smaller"
            except:
                date_score = 0
                
            return (status_score, date_score, instance['request_id'])
        
        sorted_instances = sorted(instances, key=sort_key)
        
        # Keep the first (best) instance, delete the rest
        keep_instance = sorted_instances[0]
        delete_instances = sorted_instances[1:]
        
        print(f"   ✅ Keeping: {keep_instance['status']} - {keep_instance['created'][:10]} - ID: {keep_instance['request_id'][:8]}...")
        cleanup_results['kept_count'] += 1
        
        cid_details = {
            'cid': cid,
            'total_instances': len(instances),
            'kept_instance': keep_instance,
            'deleted_instances': [],
            'failed_deletions': []
        }
        
        # Delete the duplicates
        for instance in delete_instances:
            print(f"   🗑️  {'[DRY RUN]' if dry_run else 'Deleting'}: {instance['status']} - {instance['created'][:10]} - ID: {instance['request_id'][:8]}...")
            
            if not dry_run:
                success, message = _delete_4everland_pin(api_key, instance['request_id'])
                
                if success:
                    print(f"      ✅ Deleted successfully")
                    cleanup_results['deleted_count'] += 1
                    cid_details['deleted_instances'].append(instance)
                else:
                    print(f"      ❌ Failed: {message}")
                    cleanup_results['failed_deletions'] += 1
                    cleanup_results['errors'].append(f"Failed to delete {instance['request_id']}: {message}")
                    cid_details['failed_deletions'].append({'instance': instance, 'error': message})
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            else:
                cleanup_results['deleted_count'] += 1
                cid_details['deleted_instances'].append(instance)
        
        cleanup_results['details'].append(cid_details)
    
    # Calculate savings (rough estimate)
    successful_deletions = cleanup_results['deleted_count'] - cleanup_results['failed_deletions']
    cleanup_results['savings'] = successful_deletions * 0.08  # ~$0.08/GB/month estimate
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   • CIDs processed: {len(cleanup_results['details'])}")
    print(f"   • Pins kept: {cleanup_results['kept_count']}")
    print(f"   • Pins {'would be ' if dry_run else ''}deleted: {cleanup_results['deleted_count']}")
    if cleanup_results['failed_deletions'] > 0:
        print(f"   • Failed deletions: {cleanup_results['failed_deletions']}")
    print(f"   • Estimated monthly savings: ${cleanup_results['savings']:.2f}")
    
    return cleanup_results

def verify_cleanup_success(api_key, cleanup_results):
    """
    Verify that cleanup was successful and all unique CIDs still exist.
    Uses memory-safe streaming approach instead of loading all pins.
    Returns: (success, verification_report)
    """
    print(f"\n🔍 VERIFYING CLEANUP SUCCESS...")
    
    # Extract CIDs that should still exist after cleanup
    cids_to_verify = [detail['cid'] for detail in cleanup_results['details']]
    
    if not cids_to_verify:
        print("   ℹ️  No CIDs to verify from cleanup results")
        return True, {'success': True, 'verified_cids': 0, 'missing_cids': 0}
    
    print(f"   • Verifying {len(cids_to_verify)} CIDs still exist after cleanup...")
    
    # Use memory-safe streaming verification
    verified_count, total_cids, details, _ = _stream_verify_cids(api_key, cids_to_verify)
    
    verification_results = {
        'success': verified_count == total_cids,
        'verified_cids': verified_count,
        'missing_cids': total_cids - verified_count,
        'missing_details': [],
        'verified_details': []
    }
    
    # Build detailed results
    for cid in cids_to_verify:
        if cid in details:
            status = details[cid]['status']
            print(f"   ✅ {cid[:20]}... still pinned (status: {status})")
            verification_results['verified_details'].append({
                'cid': cid,
                'current_status': status,
                'kept_instance': next(d['kept_instance']['request_id'] for d in cleanup_results['details'] if d['cid'] == cid)
            })
        else:
            print(f"   ❌ {cid[:20]}... MISSING - cleanup may have failed!")
            verification_results['missing_details'].append({
                'cid': cid,
                'kept_instance': next(d['kept_instance']['request_id'] for d in cleanup_results['details'] if d['cid'] == cid),
                'deleted_count': next(len(d['deleted_instances']) for d in cleanup_results['details'] if d['cid'] == cid)
            })
    
    print(f"\n📋 VERIFICATION RESULTS:")
    print(f"   • Verified CIDs: {verification_results['verified_cids']}")
    print(f"   • Missing CIDs: {verification_results['missing_cids']}")
    
    if verification_results['success']:
        print("   ✅ All CIDs successfully preserved!")
    else:
        print("   ❌ Some CIDs may have been lost during cleanup!")
    
    return verification_results['success'], verification_results