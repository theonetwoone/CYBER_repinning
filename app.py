import streamlit as st
import pandas as pd
import json
import utils

def ensure_dataframe_dtypes(df):
    """Ensure DataFrame has proper string dtypes to prevent pandas warnings."""
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    df = df.copy()
    
    # Fill NaN/None values with empty strings
    df = df.fillna("")
    
    # Convert all object columns to string to prevent dtype conflicts
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype == 'float64':
            df[col] = df[col].astype('string')
    
    # Specifically ensure these columns are string type
    string_columns = ['asset_id', 'asset_name', 'asset_url', 'metadata_cid', 'image_cid', 'status', 'repin_cid', 'error_message']
    for col in string_columns:
        if col in df.columns:
            # Force conversion to string, handling any edge cases
            df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else "")
            df[col] = df[col].astype('string')
    
    return df

def inject_custom_css():
    """Inject custom CSS for cyber skulls aesthetic."""
    st.markdown("""
        <style>
            /* 1. FONT IMPORT & GLOBAL APPLICATION */
            @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

            html, body, [class*="st-"], [class*="css-"] {
                font-family: 'VT323', monospace;
                font-size: 18px;
            }

            /* 2. COMPONENT STYLING */

            /* Buttons */
            .stButton > button {
                border: 2px solid #00FF41;
                background-color: transparent;
                color: #00FF41;
                padding: 10px 24px;
                border-radius: 0px;
                transition: all 0.2s ease-in-out;
                font-family: 'VT323', monospace;
                font-size: 18px;
                text-transform: uppercase;
            }
            .stButton > button:hover {
                border-color: #FFFFFF;
                color: #000000;
                background-color: #00FF41;
            }
            .stButton > button:active {
                background-color: #00b32d;
            }
            
            /* Dataframe/Table Header */
            .dataframe th {
                background-color: #00FF41 !important;
                color: #000000 !important;
                font-size: 20px;
            }

            /* Sidebar */
            .css-1d391kg {
                background-color: #0D1117;
            }

            /* Error Messages */
            .st-emotion-cache-1tud4wn {
                 border: 2px solid #FF4747;
            }

            /* Text inputs */
            .stTextInput > div > div > input {
                border: 1px solid #00FF41;
                background-color: #0D1117;
                color: #E0E0E0;
                font-family: 'VT323', monospace;
                font-size: 16px;
            }

            /* Select boxes */
            .stSelectbox > div > div > select {
                border: 1px solid #00FF41;
                background-color: #0D1117;
                color: #E0E0E0;
                font-family: 'VT323', monospace;
                font-size: 16px;
            }

            /* Headers */
            .main-header {
                color: #00FF41;
                font-family: 'VT323', monospace;
                font-size: 36px;
                text-align: center;
                margin-bottom: 20px;
            }

            .section-header {
                color: #00FF41;
                font-family: 'VT323', monospace;
                font-size: 24px;
                margin: 20px 0 10px 0;
            }

        </style>
    """, unsafe_allow_html=True)

def main():
    # Page configuration
    st.set_page_config(
        page_title="CYBER SKULLS // REPINNING PROTOCOL", 
        page_icon="💀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject custom CSS
    inject_custom_css()
    
    # Initialize session state
    if 'collection_df' not in st.session_state:
        st.session_state.collection_df = pd.DataFrame()
    if 'migration_results' not in st.session_state:
        st.session_state.migration_results = {}
    
    # Header with logo
    header_col1, header_col2, header_col3 = st.columns([1, 3, 1])
    with header_col1:
        try:
            st.image("logo.png", width=150)
        except FileNotFoundError:
            st.markdown("🏴‍☠️")
    
    with header_col2:
        st.markdown('<h1 class="main-header">[ CYBER SKULLS // REPINNING PROTOCOL ]</h1>', unsafe_allow_html=True)
    
    with header_col3:
        st.markdown("")  # Empty space for balance
    
    # Sidebar - Input UI
    with st.sidebar:
        st.markdown('<h2 class="section-header">[ 1. LOAD_COLLECTION ]</h2>', unsafe_allow_html=True)
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["Manual Entry", "Fetch from Algorand", "Upload wen.tools CSV"],
            help="Choose how to specify your NFT collection"
        )
        
        collection_df = pd.DataFrame()
        
        if input_method == "Manual Entry":
            st.markdown("#### Manual Collection Entry")
            algorand_address = st.text_input(
                "🏠 Creator Address", 
                placeholder="ALGORAND_ADDRESS_HERE",
                help="Enter the Algorand address that created the NFT collection"
            )
            
            if algorand_address:
                if st.button("🔍 Fetch Collection Assets", type="primary"):
                    with st.spinner("🔍 Fetching assets from Algorand network..."):
                        assets, error = utils.get_all_creator_assets(algorand_address)
                        if error:
                            st.error(f"❌ Error: {error}")
                        else:
                            st.success(f"✅ Found {len(assets)} assets")
                            collection_df = utils.create_collection_dataframe(assets, st.session_state.collection_df)
                            st.session_state.collection_df = collection_df
                            
        elif input_method == "Fetch from Algorand":
            st.markdown("#### Direct Algorand Fetch")
            algorand_address = st.text_input(
                "🏠 Creator Address", 
                placeholder="ALGORAND_ADDRESS_HERE",
                help="Enter the Algorand address that created the NFT collection"
            )
            
            if algorand_address:
                if st.button("🔍 Fetch Collection Assets", type="primary"):
                    with st.spinner("🔍 Fetching assets from Algorand network..."):
                        assets, error = utils.get_all_creator_assets(algorand_address)
                        if error:
                            st.error(f"❌ Error: {error}")
                        else:
                            st.success(f"✅ Found {len(assets)} assets")
                            collection_df = utils.create_collection_dataframe(assets, st.session_state.collection_df)
                            st.session_state.collection_df = collection_df
                            
        elif input_method == "Upload wen.tools CSV":
            st.markdown("#### Upload wen.tools CSV")
            st.markdown("""
            **📥 Alternative Fast Method:**
            1. Go to [wen.tools/download-arc19-collection-data](https://www.wen.tools/download-arc19-collection-data)
            2. Enter your collection's asset ID or creator address
            3. Download the CSV file
            4. Upload it below
            
            ⚡ This method is much faster than fetching directly from Algorand!
            """)
            
            uploaded_file = st.file_uploader(
                "Choose CSV file from wen.tools",
                type=['csv'],
                help="Upload the CSV file downloaded from wen.tools"
            )
            
            if uploaded_file is not None:
                # Check if this is the same file we already processed
                file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                last_processed_file = getattr(st.session_state, 'last_processed_csv_file', None)
                
                # Only process if it's a new file or we don't have existing collection data
                if file_id != last_processed_file or st.session_state.collection_df.empty:
                    st.session_state.last_processed_csv_file = file_id
                    print(f"🔧 DEBUG: Processing new CSV file: {file_id}")
                    
                    try:
                        # Read the uploaded file
                        csv_content = uploaded_file.read()
                        
                        # Parse using our new function
                        from utils import parse_wen_tools_csv, analyze_collection_structure
                        result = parse_wen_tools_csv(csv_content)
                        
                        if len(result) == 3:
                            parsed_df, error, collection_info = result
                        else:
                            # Backwards compatibility
                            parsed_df, error = result
                            collection_info = None
                        
                        if error:
                            st.error(f"❌ Error parsing CSV: {error}")
                        else:
                            st.success(f"✅ Successfully parsed {len(parsed_df)} assets from CSV")
                            
                            # Analyze collection structure
                            strategy_type, analysis = analyze_collection_structure(parsed_df)
                            
                            # Show collection analysis
                            if strategy_type == "directory_based":
                                st.info(f"""
                                📁 **Directory-Based Collection Detected**
                                - **Total Assets:** {analysis['total_assets']}
                                - **Unique Base CIDs:** {analysis['unique_base_cids']}
                                - **Largest Directory:** {analysis['largest_directory']} files
                                - **Avg Files/Directory:** {analysis['avg_files_per_directory']:.1f}
                                
                                🎯 **Recommended:** Pin {analysis['unique_base_cids']} base CIDs to cover all {analysis['total_assets']} assets efficiently.
                                """)
                                
                                # Pinning strategy options
                                st.markdown("**🔧 Pinning Strategy:**")
                                pinning_strategy = st.radio(
                                    "Choose pinning approach:",
                                    ["base_cids_only", "individual_files"],
                                    format_func=lambda x: {
                                        "base_cids_only": f"📁 Pin Base CIDs Only ({analysis['unique_base_cids']} pins) - Recommended",
                                        "individual_files": f"📄 Pin Individual Files ({analysis['total_assets']} pins) - Not recommended"
                                    }[x],
                                    help="Base CIDs contain all files in the directory and are more efficient"
                                )
                                
                                if pinning_strategy == "individual_files":
                                    st.warning("⚠️ **Not Recommended:** Pinning individual files is inefficient for directory collections. The base CID already contains all files.")
                                
                            elif strategy_type == "individual_cids":
                                st.info(f"""
                                🔗 **Individual CID Collection**
                                - **Total Assets:** {analysis['total_assets']}
                                - **Unique CIDs:** {analysis['unique_cids']}
                                
                                🎯 **Strategy:** Each asset has its own unique CID - will pin all CIDs.
                                """)
                                pinning_strategy = "individual_cids"
                                
                            else:  # mixed
                                st.warning(f"""
                                🔀 **Mixed Collection Detected**
                                - **Total Assets:** {analysis['total_assets']}
                                - **Unique CIDs:** {analysis['unique_cids']}
                                - **Duplicated CIDs:** {analysis['duplicated_cids']}
                                
                                ⚠️ **Mixed collection with some duplicate CIDs detected.**
                                """)
                                
                                # Pinning strategy options for mixed collections
                                st.markdown("**🔧 Pinning Strategy:**")
                                pinning_strategy = st.radio(
                                    "Choose pinning approach:",
                                    ["unique_only", "all_individual"],
                                    format_func=lambda x: {
                                        "unique_only": f"🎯 Pin Unique CIDs Only ({analysis['unique_cids']} pins) - Recommended",
                                        "all_individual": f"📋 Pin All Individual CIDs ({analysis['total_assets']} pins) - May duplicate work"
                                    }[x],
                                    help="Unique CIDs avoid duplicating pinning work"
                                )
                            
                            # Store strategy in session state
                            st.session_state.pinning_strategy = pinning_strategy
                            
                            # Show top directories/CIDs
                            with st.expander("📊 Collection Structure Analysis"):
                                if 'assets_per_cid' in analysis:
                                    cid_dist = pd.DataFrame(list(analysis['assets_per_cid'].items()), 
                                                          columns=['Base CID', 'Asset Count'])
                                    cid_dist = cid_dist.sort_values('Asset Count', ascending=False)
                                    st.dataframe(cid_dist.head(10), use_container_width=True)
                                
                                # Show sample assets
                                st.markdown("**Sample Assets:**")
                                sample_cols = ['asset_id', 'asset_name', 'image_cid', 'full_ipfs_url']
                                if strategy_type == "directory_based":
                                    sample_cols.append('image_file_path')
                                
                                st.dataframe(
                                    parsed_df[sample_cols].head(5),
                                    use_container_width=True
                                )
                            
                            # IMPORTANT: Preserve existing status if collection already exists
                            if not st.session_state.collection_df.empty:
                                # We have existing data - preserve completion statuses
                                existing_df = st.session_state.collection_df.copy()
                                
                                # Create lookup dict from existing data to preserve statuses
                                existing_status_lookup = {}
                                for _, row in existing_df.iterrows():
                                    existing_status_lookup[row['asset_id']] = {
                                        'status': row['status'],
                                        'repin_cid': row.get('repin_cid', ''),
                                        'error_message': row.get('error_message', '')
                                    }
                                
                                # Update parsed_df with existing statuses where available
                                for idx, row in parsed_df.iterrows():
                                    asset_id = row['asset_id']
                                    if asset_id in existing_status_lookup:
                                        existing_data = existing_status_lookup[asset_id]
                                        parsed_df.at[idx, 'status'] = existing_data['status']
                                        parsed_df.at[idx, 'repin_cid'] = existing_data['repin_cid']
                                        parsed_df.at[idx, 'error_message'] = existing_data['error_message']
                                
                                print(f"🔧 DEBUG: Preserved statuses from existing collection. Completed assets: {len(parsed_df[parsed_df['status'] == 'completed'])}")
                            else:
                                print(f"🔧 DEBUG: Fresh CSV upload, no existing statuses to preserve")
                            
                            st.session_state.collection_df = parsed_df
                            st.session_state.collection_info = collection_info
                            collection_df = parsed_df
                            
                    except Exception as e:
                        st.error(f"❌ Error reading file: {str(e)}")
                else:
                    print(f"🔧 DEBUG: Skipping reprocessing of same CSV file: {file_id}")
                    # File already processed, just show the existing collection info
                    if not st.session_state.collection_df.empty:
                        st.success(f"✅ Using existing collection data ({len(st.session_state.collection_df)} assets)")
                        
                        # Show current status distribution
                        status_counts = st.session_state.collection_df['status'].value_counts()
                        status_info = []
                        for status, count in status_counts.items():
                            status_info.append(f"{status}: {count}")
                        st.info(f"**Current Status:** {', '.join(status_info)}")

        # Use the collection_df from session state if available
        if not collection_df.empty:
            st.session_state.collection_df = collection_df
        elif not st.session_state.collection_df.empty:
            collection_df = st.session_state.collection_df

        # Service Configuration (only show if we have a collection)
        if not st.session_state.collection_df.empty:
            st.markdown("---")
            st.markdown("### 🔧 PINNING SERVICE")
            
            # Service selection with clear categories
            st.markdown("#### ✅ **TESTED & RECOMMENDED**")
            st.success("""
            **🏆 4EVERLAND** - Fully tested and optimized for NFT collections
            - ✅ **Thoroughly tested** with Cyber Skulls collection
            - ✅ **Directory collections** fully supported  
            - ✅ **Comprehensive debugging** and verification
            - ✅ **FREE tier:** 6GB storage + 100GB bandwidth
            - ✅ **$0.08/GB** after free tier (most affordable!)
            """)
            
            recommended_service = st.radio(
                "🏗️ Choose Tested Service:",
                ["4everland (FREE) - RECOMMENDED"],
                help="4everland has been extensively tested with this tool"
            )
            
            st.markdown("#### ⚠️ **EXPERIMENTAL/UNTESTED**")
            st.warning("""
            **⚠️ WARNING:** These services have basic implementation but are **NOT thoroughly tested**
            - May have compatibility issues
            - Limited debugging support  
            - Use at your own risk
            """)
            
            use_experimental = st.checkbox("🧪 Show experimental services", value=False)
            
            if use_experimental:
                experimental_services = [
                    "Pinata (PAID)",
                    "NFT.Storage (FREE)", 
                    "Web3.Storage (FREE)",
                    "Filebase (PAID)",
                    "Infura (PAID)"
                ]
                
                experimental_service = st.selectbox(
                    "⚠️ Choose Experimental Service:",
                    experimental_services,
                    help="These services are untested - use with caution"
                )
                
                selected_service = experimental_service
            else:
                selected_service = recommended_service

            # Service-specific instructions and API key input
            service_name = selected_service.split(" ")[0].lower()
            
            st.markdown("---")
            st.markdown(f"**📋 {selected_service} Setup:**")
            
            # Show warning for experimental services
            if use_experimental and selected_service != "4everland (FREE) - RECOMMENDED":
                st.error(f"""
                ⚠️ **EXPERIMENTAL SERVICE WARNING**
                
                You selected **{selected_service}** which is **NOT thoroughly tested**.
                
                **Known Issues:**
                - May not handle directory collections properly
                - Limited error handling and debugging
                - Pin verification may not work correctly
                
                **Recommended:** Use 4everland for production collections.
                """)
            
            api_key_input = None
            service_instructions = {
                "4everland": {
                    "instruction": "Get your Bearer token from [4everland.org](https://dashboard.4everland.org/) → Bucket → Create IPFS Bucket → API Keys",
                    "placeholder": "4everland_bearer_token_here",
                    "input_type": "single"
                },
                "pinata": {
                    "instruction": "Get your JWT token from [pinata.cloud](https://app.pinata.cloud/) → Account → API Keys → New Key",
                    "placeholder": "JWT_token_here", 
                    "input_type": "single"
                },
                "nft.storage": {
                    "instruction": "Get your API token from [nft.storage](https://nft.storage/) → Account → API Keys",
                    "placeholder": "nft_storage_api_token_here",
                    "input_type": "single"
                },
                "web3.storage": {
                    "instruction": "Get your API token from [web3.storage](https://web3.storage/) → Account → Create API Token",
                    "placeholder": "web3_storage_api_token_here", 
                    "input_type": "single"
                },
                "filebase": {
                    "instruction": "Get your Bearer token from [filebase.com](https://console.filebase.com/) → IPFS Bucket → Pinning Service API → Generate Token",
                    "placeholder": "filebase_bearer_token_here",
                    "input_type": "single"
                },
                "infura": {
                    "instruction": "Get credentials from [infura.io](https://infura.io/) → IPFS → Create Project → Settings",
                    "placeholder": ["project_id_here", "api_secret_here"],
                    "input_type": "double"
                }
            }
            
            if service_name in service_instructions:
                info = service_instructions[service_name]
                st.markdown(info["instruction"])
                
                if info["input_type"] == "single":
                    api_key_input = st.text_input(
                        f"🔑 {selected_service} API Key/Token",
                        type="password",
                        placeholder=info["placeholder"]
                    )
                elif info["input_type"] == "double":
                    col1, col2 = st.columns(2)
                    with col1:
                        project_id = st.text_input(
                            "🆔 Project ID", 
                            type="password",
                            placeholder=info["placeholder"][0]
                        )
                    with col2:
                        api_secret = st.text_input(
                            "🔐 API Secret", 
                            type="password", 
                            placeholder=info["placeholder"][1]
                        )
                    
                    if project_id and api_secret:
                        api_key_input = (project_id, api_secret)

                # Test API Key button
                if api_key_input:
                    if st.button("🧪 Test API Key", type="secondary"):
                        with st.spinner("🧪 Validating API credentials..."):
                            from utils import validate_api_key
                            is_valid, message = validate_api_key(selected_service, api_key_input)
                            if is_valid:
                                st.success(f"✅ API key validated: {message}")
                            else:
                                st.error(f"❌ API key validation failed: {message}")

    # Main content area
    if st.session_state.collection_df.empty:
        # Welcome/instructions when no collection is loaded
        st.markdown("""
        ## 👋 Welcome to the Algorand NFT IPFS Repinning Tool
        
        ### 🎯 What this tool does:
        - **Fetches** your Algorand NFT collection's IPFS metadata and image CIDs
        - **Migrates** them to a reliable IPFS pinning service
        - **Ensures** your NFTs remain accessible forever
        
        ### 🚀 Get started:
        1. Choose an input method in the sidebar (Manual, Algorand fetch, or CSV upload)
        2. Configure your pinning service credentials
        3. Review your collection and estimate storage costs
        4. Start the migration process
        
        ### 💡 Pro tip:
        For large collections or ARC-19 assets, using the **wen.tools CSV upload** method is much faster than fetching directly from Algorand!
        """)
    else:
        # Display collection information
        df = st.session_state.collection_df
        
        # Ensure we always use the latest DataFrame from session state
        if not df.empty:
            # Force reload from session state to catch any updates
            df = st.session_state.collection_df.copy()
        
        # Debug info to help troubleshoot
        st.sidebar.markdown("### 🔧 DEBUG INFO")
        st.sidebar.write(f"DataFrame shape: {df.shape}")
        if not df.empty:
            status_counts = df['status'].value_counts()
            st.sidebar.write("Status distribution:")
            for status, count in status_counts.items():
                st.sidebar.write(f"  {status}: {count}")
        
        # Collection overview - calculate fresh each time using current df
        total_assets = len(df)
        pending = len(df[df['status'] == 'pending'])
        completed = len(df[df['status'] == 'completed'])  
        failed = len(df[df['status'] == 'failed'])
        
        # Check if we need to force refresh metrics after migration
        if hasattr(st.session_state, 'migration_just_completed') and st.session_state.migration_just_completed:
            # Recalculate metrics with fresh data
            fresh_df = st.session_state.collection_df.copy()
            total_assets = len(fresh_df)
            pending = len(fresh_df[fresh_df['status'] == 'pending'])
            completed = len(fresh_df[fresh_df['status'] == 'completed'])  
            failed = len(fresh_df[fresh_df['status'] == 'failed'])
            df = fresh_df  # Update the main df as well

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Assets", total_assets)
        with col2:
            st.metric("⏳ Pending", pending)
        with col3:
            st.metric("✅ Completed", completed)
        with col4:
            st.metric("❌ Failed", failed)

        # Storage estimation
        if st.button("📏 Estimate Storage Requirements", type="secondary"):
            with st.spinner("📏 Analyzing collection size..."):
                from utils import estimate_collection_size
                
                # Get list of CIDs to check (image CIDs for wen.tools uploads, metadata CIDs for others)
                cids_to_check = []
                for _, row in df.iterrows():
                    if row['image_cid']:  # wen.tools CSV format
                        cids_to_check.append(row['image_cid'])
                    elif row['metadata_cid']:  # Direct Algorand fetch format
                        cids_to_check.append(row['metadata_cid'])
                        if row['image_cid']:
                            cids_to_check.append(row['image_cid'])
                
                avg_size, total_size, sample_results = estimate_collection_size(df, sample_count=5)
                
                if total_size > 0:
                    st.success("📏 Storage Analysis Complete!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("📊 Average Asset Size", f"{avg_size} MB")
                    with col2:
                        st.metric("💽 Total Estimated Size", f"{total_size} MB")
                    
                    # Show sample results
                    with st.expander("🔍 Sample Analysis Details"):
                        for result in sample_results:
                            if result['total_size'] > 0:
                                st.write(f"**{result['asset_name']}**: {result['total_size_mb']} MB")
                            else:
                                st.write(f"**{result['asset_name']}**: Could not estimate size")
                else:
                    st.warning("⚠️ Could not estimate storage size. Files may not be accessible via IPFS gateways.")

        # Collection data table
        st.markdown("### 📋 Collection Assets")
        
        # Show different columns based on input method
        if df['image_cid'].notna().any() and df['metadata_cid'].eq('').all():
            # wen.tools CSV format - show image CIDs
            display_columns = ['asset_id', 'asset_name', 'image_cid', 'status']
            column_config = {
                'asset_id': st.column_config.TextColumn('Asset ID', width="medium"),
                'asset_name': st.column_config.TextColumn('Name', width="large"), 
                'image_cid': st.column_config.TextColumn('Image CID', width="large"),
                'status': st.column_config.TextColumn('Status', width="small")
            }
        else:
            # Direct Algorand fetch format - show metadata and image CIDs
            display_columns = ['asset_id', 'asset_name', 'metadata_cid', 'image_cid', 'status']
            column_config = {
                'asset_id': st.column_config.TextColumn('Asset ID', width="small"),
                'asset_name': st.column_config.TextColumn('Name', width="medium"),
                'metadata_cid': st.column_config.TextColumn('Metadata CID', width="large"),
                'image_cid': st.column_config.TextColumn('Image CID', width="large"),
                'status': st.column_config.TextColumn('Status', width="small")
            }
        
        st.dataframe(
            df[display_columns], 
            use_container_width=True,
            column_config=column_config
        )

        # Migration controls (only show if service is configured)
        if 'selected_service' in locals() and 'api_key_input' in locals() and api_key_input:
            st.markdown("---")
            st.markdown("### 🚀 MIGRATION CONTROLS")
            
            # Check if migration is in progress
            migration_in_progress = hasattr(st.session_state, 'migration_progress')
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("▶️ Start Migration", type="primary", disabled=(pending == 0 or migration_in_progress)):
                    migrate_collection(df, selected_service, api_key_input)
            
            with col2:
                if st.button("🔍 Verify Pins", type="secondary", disabled=migration_in_progress):
                    verify_collection_pins(df, selected_service, api_key_input)
            
            with col3:
                if st.button("📥 Download Results", type="secondary"):
                    download_results(df)
            
            with col4:
                if st.button("🔄 Refresh Data", type="secondary"):
                    # Force complete refresh of DataFrame
                    st.session_state.collection_df = st.session_state.collection_df.copy(deep=True)
                    st.rerun()
            
            # Show migration status
            if migration_in_progress:
                st.info("🔄 Migration in progress... Please wait.")
                progress = st.session_state.migration_progress
                st.progress(progress.get('current', 0) / progress.get('total', 1))
                if progress.get('current_asset'):
                    st.write(f"Currently processing: {progress.get('current_asset')}")
            
            # Debug panel - show after migration completed
            if hasattr(st.session_state, 'migration_just_completed') and st.session_state.migration_just_completed:
                st.success("🎉 Migration just completed! Status updated.")
                # Clear the flag after showing
                del st.session_state.migration_just_completed
                # Force DataFrame refresh
                df = st.session_state.collection_df.copy()
            
            # Show enhanced status info
            with st.expander("📊 Migration Status Debug Panel", expanded=False):
                current_time = pd.Timestamp.now().strftime("%H:%M:%S")
                st.write(f"**Last Updated:** {current_time}")
                
                # Show pinning service info
                if 'selected_service' in locals():
                    st.info(f"**Selected Service:** {selected_service}")
                    st.info(f"**API Key Configured:** {'✅ Yes' if api_key_input else '❌ No'}")
                
                # Use fresh DataFrame from session state for debug panel
                debug_df = st.session_state.collection_df.copy()
                
                # Show current counts from fresh DataFrame
                if not debug_df.empty:
                    status_counts = debug_df['status'].value_counts()
                    
                    debug_col1, debug_col2, debug_col3 = st.columns(3)
                    
                    with debug_col1:
                        st.metric("Pending", status_counts.get('pending', 0))
                    
                    with debug_col2:
                        st.metric("Completed", status_counts.get('completed', 0))
                    
                    with debug_col3:
                        st.metric("Failed", status_counts.get('failed', 0))
                    
                    # Show collection structure info
                    from utils import analyze_collection_structure
                    strategy_type, analysis = analyze_collection_structure(debug_df)
                    
                    # 🚀 NEW: Get metadata CID information
                    total_metadata_cids = sum(1 for _, row in debug_df.iterrows() if row.get('metadata_cid', '').strip())
                    metadata_info_str = f", {total_metadata_cids} metadata CIDs" if total_metadata_cids > 0 else ", no metadata CIDs"
                    
                    if strategy_type == "directory_based":
                        st.info(f"📁 **Collection Type:** Directory-based ({analysis.get('unique_base_cids', 0)} base CIDs for {analysis.get('total_assets', 0)} assets{metadata_info_str})")
                    elif strategy_type == "individual_cids":
                        st.info(f"🔗 **Collection Type:** Individual CIDs ({analysis.get('unique_cids', 0)} unique CIDs{metadata_info_str})")
                    elif strategy_type == "mixed":
                        st.info(f"🔀 **Collection Type:** Mixed ({analysis.get('unique_cids', 0)} unique CIDs, {analysis.get('duplicated_cids', 0)} duplicated{metadata_info_str})")
                    
                    # Show sample of latest completed/failed items
                    if 'completed' in status_counts and status_counts['completed'] > 0:
                        completed_assets = debug_df[debug_df['status'] == 'completed'].head(3)
                        st.success("✅ **Latest Completed Assets:**")
                        for _, asset in completed_assets.iterrows():
                            repin_cid = asset.get('repin_cid', 'N/A')
                            if len(repin_cid) > 16:
                                repin_cid_display = repin_cid[:16] + "..."
                            else:
                                repin_cid_display = repin_cid
                            st.write(f"- {asset['asset_name']} → CID: {repin_cid_display}")
                    
                    if 'failed' in status_counts and status_counts['failed'] > 0:
                        failed_assets = debug_df[debug_df['status'] == 'failed'].head(3)
                        st.error("❌ **Latest Failed Assets:**")
                        for _, asset in failed_assets.iterrows():
                            error_msg = asset.get('error_message', 'No error message')
                            if len(error_msg) > 50:
                                error_msg = error_msg[:50] + "..."
                            st.write(f"- {asset['asset_name']} → Error: {error_msg}")
                    
                    # Show unique CIDs info with metadata breakdown
                    unique_image_cids = debug_df['image_cid'].nunique() if 'image_cid' in debug_df.columns else 0
                    unique_metadata_cids = debug_df['metadata_cid'].nunique() if 'metadata_cid' in debug_df.columns else 0
                    
                    cid_summary = f"{len(debug_df)} total assets, {unique_image_cids} unique image CIDs"
                    if total_metadata_cids > 0:
                        cid_summary += f", {unique_metadata_cids} unique metadata CIDs"
                    
                    st.info(f"**Complete NFT Coverage:** {cid_summary}")
                    
                    # Show session state info
                    if hasattr(st.session_state, 'pinning_strategy'):
                        st.info(f"**Pinning Strategy:** {st.session_state.pinning_strategy}")
                    
                    # Show DataFrame comparison for debugging
                    st.text(f"Debug: Main df pending={len(df[df['status'] == 'pending'])}, Debug df pending={len(debug_df[debug_df['status'] == 'pending'])}")
                else:
                    st.warning("No collection data available")

    # Footer with creator information
    st.divider()
    st.markdown("---")
    
    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
    
    with footer_col1:
        st.markdown("")  # Empty space
    
    with footer_col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h3 style="color: #00FF41; font-family: 'VT323', monospace; margin-bottom: 10px;">
                🌐 <a href="https://www.cyberskulls.app" target="_blank" style="color: #00FF41; text-decoration: none;">www.cyberskulls.app</a>
            </h3>
            <div style="background: #0D1117; border: 2px solid #00FF41; border-radius: 10px; padding: 20px; margin: 20px 0;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap;">
                    <img src="https://www.cyberskulls.app/theonetwo.gif" 
                         width="80" height="80" 
                         style="border: 2px solid #00FF41; border-radius: 50%; background: #000;">
                    <div style="text-align: left;">
                        <h4 style="color: #00FF41; font-family: 'VT323', monospace; margin: 0;">
                            [ CREATOR_PROFILE ] [003]
                        </h4>
                        <p style="color: #E0E0E0; font-family: 'VT323', monospace; margin: 5px 0; font-size: 16px;">
                            <span style="color: #00FF41;">● ONLINE</span><br>
                            <strong>[ID: ThΞOneTwo]</strong><br><br>
                            <span style="color: #00FF41;">></span> ALIAS: ThΞOneTwo<br>
                            <span style="color: #00FF41;">></span> REAL_NAME: Markus Jensen<br>
                            <span style="color: #00FF41;">></span> ORIGIN: Denmark<br>
                            <span style="color: #00FF41;">></span> SPECIALIZATION: AI & Graphic Design<br>
                            <span style="color: #00FF41;">></span> MISSION: Creating a project that community members can be proud<br>
                            &nbsp;&nbsp;&nbsp;to be a part of. Combining artistic vision with technological<br>
                            &nbsp;&nbsp;&nbsp;innovation to build something truly unique in the crypto space.
                        </p>
                    </div>
                </div>
            </div>
            <p style="color: #666; font-family: 'VT323', monospace; font-size: 14px; margin-top: 10px;">
                CYBER SKULLS REPINNING PROTOCOL v2.1 // OPTIMIZED FOR 4EVERLAND // CREATED BY ThΞOneTwo
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with footer_col3:
        st.markdown("")  # Empty space

def show_migration_progress():
    """Display migration progress."""
    if hasattr(st.session_state, 'migration_progress'):
        progress = st.session_state.migration_progress
        st.progress(progress.get('current', 0) / progress.get('total', 1))
        st.write(f"Processing {progress.get('current_asset', '')}...")

def migrate_collection(df, service_name, api_key):
    """Execute migration of collection to pinning service. Now handles both metadata and image CIDs."""
    try:
        # Get pending assets with their original indices
        pending_mask = st.session_state.collection_df['status'] == 'pending'
        pending_assets = st.session_state.collection_df[pending_mask].copy()
        
        if pending_assets.empty:
            st.warning("⚠️ No pending assets to migrate.")
            return
        
        # Analyze collection structure to determine pinning strategy
        from utils import analyze_collection_structure, get_cids_to_pin
        strategy_type, analysis = analyze_collection_structure(pending_assets)
        
        # Use user's selected strategy if available, otherwise auto
        user_strategy = getattr(st.session_state, 'pinning_strategy', 'auto')
        
        # Get image CIDs to pin based on user's chosen strategy
        image_cids_to_pin = get_cids_to_pin(pending_assets, strategy=user_strategy)
        
        # 🚀 NEW: Collect metadata CIDs that need to be pinned
        metadata_cids_to_pin = []
        for _, row in pending_assets.iterrows():
            metadata_cid = row.get('metadata_cid', '').strip()
            if metadata_cid and metadata_cid not in metadata_cids_to_pin:
                metadata_cids_to_pin.append(metadata_cid)
        
        # Combine both types of CIDs for total count
        total_unique_cids = len(set(image_cids_to_pin + metadata_cids_to_pin))
        
        print(f"🔧 DEBUG: Collection type: {strategy_type}")
        print(f"🔧 DEBUG: User strategy: {user_strategy}")
        print(f"🔧 DEBUG: Pending assets: {len(pending_assets)}")
        print(f"🔧 DEBUG: Image CIDs to pin: {len(image_cids_to_pin)}")
        print(f"🔧 DEBUG: Metadata CIDs to pin: {len(metadata_cids_to_pin)}")
        print(f"🔧 DEBUG: Total unique CIDs to pin: {total_unique_cids}")
        print(f"🔧 DEBUG: Image CIDs: {image_cids_to_pin[:3]}...")  # Show first 3
        print(f"🔧 DEBUG: Metadata CIDs: {metadata_cids_to_pin[:3]}...")  # Show first 3
        
        st.session_state.migration_progress = {'current': 0, 'total': total_unique_cids}
        
        # Validate API first
        with st.spinner("🧪 Validating API credentials..."):
            from utils import validate_api_key
            is_valid, message = validate_api_key(service_name, api_key)
            if not is_valid:
                st.error(f"❌ API validation failed: {message}")
                if hasattr(st.session_state, 'migration_progress'):
                    del st.session_state.migration_progress
                return
        
        st.success(f"✅ API validated: {message}")
        
        # Show pinning strategy with metadata info
        metadata_info = f" + {len(metadata_cids_to_pin)} metadata CIDs" if metadata_cids_to_pin else ""
        
        if strategy_type == "directory_based":
            if user_strategy == "base_cids_only":
                st.info(f"📁 Directory collection: Pinning {len(image_cids_to_pin)} image base CIDs{metadata_info} to cover {len(pending_assets)} assets (recommended strategy)")
            else:
                st.info(f"📄 Directory collection: Pinning {len(image_cids_to_pin)} individual image files{metadata_info} for {len(pending_assets)} assets (user selected)")
        elif strategy_type == "individual_cids":
            st.info(f"🔗 Individual collection: Pinning {len(image_cids_to_pin)} image CIDs{metadata_info} for {len(pending_assets)} assets")
        elif strategy_type == "mixed":
            if user_strategy == "unique_only":
                st.info(f"🔀 Mixed collection: Pinning {len(image_cids_to_pin)} unique image CIDs{metadata_info} to cover {len(pending_assets)} assets (avoiding duplicates)")
            else:
                st.info(f"🔀 Mixed collection: Pinning all {len(image_cids_to_pin)} image CIDs{metadata_info} for {len(pending_assets)} assets (user selected)")
        else:
            st.info(f"🔄 Collection: Pinning {len(image_cids_to_pin)} image CIDs{metadata_info} for {len(pending_assets)} assets")
        
        # Migration execution - pin both metadata and image CIDs
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        
        pin_results = {}  # Track which CIDs were successfully pinned
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        current_progress = 0
        
        # 🚀 NEW: Pin metadata CIDs first
        if metadata_cids_to_pin:
            st.info(f"📄 Step 1/2: Pinning {len(metadata_cids_to_pin)} metadata CIDs...")
            
            for idx, metadata_cid in enumerate(metadata_cids_to_pin):
                try:
                    current_progress += 1
                    st.session_state.migration_progress['current'] = current_progress
                    st.session_state.migration_progress['current_asset'] = f"Metadata CID {metadata_cid[:16]}..."
                    
                    progress = current_progress / total_unique_cids
                    progress_bar.progress(progress)
                    status_placeholder.info(f"📄 Pinning metadata CID {idx + 1}/{len(metadata_cids_to_pin)}: {metadata_cid[:16]}...")
                    
                    print(f"🔧 DEBUG: Pinning metadata CID {idx + 1}: {metadata_cid}")
                    
                    # Pin the metadata CID
                    from utils import pin_cid
                    success, response = pin_cid(service_name, api_key, metadata_cid)
                    
                    total_requests += 1
                    
                    print(f"🔧 DEBUG: Pin result for metadata {metadata_cid}: success={success}, response={response}")
                    
                    # Store result
                    pin_results[metadata_cid] = {
                        'success': success,
                        'response': response,
                        'type': 'metadata'
                    }
                    
                    if success:
                        successful_requests += 1
                        print(f"🔧 DEBUG: ✅ Metadata CID pinned successfully: {metadata_cid[:16]}...")
                    else:
                        failed_requests += 1
                        print(f"🔧 DEBUG: ❌ Metadata CID pinning failed: {metadata_cid[:16]}... - {response}")
                    
                except Exception as cid_error:
                    print(f"🔧 DEBUG: Exception pinning metadata CID {metadata_cid}: {str(cid_error)}")
                    failed_requests += 1
                    pin_results[metadata_cid] = {
                        'success': False,
                        'response': {'error': f'Pinning error: {str(cid_error)}'},
                        'type': 'metadata'
                    }
        
        # Pin image CIDs
        st.info(f"🖼️ Step {2 if metadata_cids_to_pin else 1}/{2 if metadata_cids_to_pin else 1}: Pinning {len(image_cids_to_pin)} image CIDs...")
        
        for idx, image_cid in enumerate(image_cids_to_pin):
            try:
                current_progress += 1
                st.session_state.migration_progress['current'] = current_progress
                st.session_state.migration_progress['current_asset'] = f"Image CID {image_cid[:16]}..."
                
                progress = current_progress / total_unique_cids
                progress_bar.progress(progress)
                status_placeholder.info(f"🖼️ Pinning image CID {idx + 1}/{len(image_cids_to_pin)}: {image_cid[:16]}...")
                
                print(f"🔧 DEBUG: Pinning image CID {idx + 1}: {image_cid}")
                
                # Pin the image CID
                from utils import pin_cid
                success, response = pin_cid(service_name, api_key, image_cid)
                
                total_requests += 1
                
                print(f"🔧 DEBUG: Pin result for image {image_cid}: success={success}, response={response}")
                
                # Store result
                pin_results[image_cid] = {
                    'success': success,
                    'response': response,
                    'type': 'image'
                }
                
                if success:
                    successful_requests += 1
                    print(f"🔧 DEBUG: ✅ Image CID pinned successfully: {image_cid[:16]}...")
                else:
                    failed_requests += 1
                    print(f"🔧 DEBUG: ❌ Image CID pinning failed: {image_cid[:16]}... - {response}")
                
            except Exception as cid_error:
                print(f"🔧 DEBUG: Exception pinning image CID {image_cid}: {str(cid_error)}")
                failed_requests += 1
                pin_results[image_cid] = {
                    'success': False,
                    'response': {'error': f'Pinning error: {str(cid_error)}'},
                    'type': 'image'
                }
        
        print(f"🔧 DEBUG: Pinning phase complete. Total: {total_requests}, Success: {successful_requests}, Failed: {failed_requests}")
        
        # Now update all assets based on pin results
        assets_updated = 0
        success_count = 0
        failure_count = 0
        
        status_placeholder.info("🔄 Updating asset statuses...")
        print(f"🔧 DEBUG: Starting asset status updates for {len(pending_assets)} assets...")
        
        for original_index, row in pending_assets.iterrows():
            try:
                asset_image_cid = row['image_cid']
                asset_metadata_cid = row.get('metadata_cid', '').strip()
                
                print(f"🔧 DEBUG: Updating asset {row['asset_name']} (index {original_index}), Image CID: {asset_image_cid[:16]}..., Metadata CID: {asset_metadata_cid[:16] if asset_metadata_cid else 'None'}...")
                
                # Check if both image and metadata (if exists) were pinned successfully
                image_pin_result = pin_results.get(asset_image_cid, {'success': False, 'response': {'error': 'Image CID not found in results'}})
                metadata_pin_result = pin_results.get(asset_metadata_cid, {'success': True, 'response': 'No metadata CID'}) if not asset_metadata_cid else pin_results.get(asset_metadata_cid, {'success': False, 'response': {'error': 'Metadata CID not found in results'}})
                
                # Asset is successful only if both required CIDs were pinned
                overall_success = image_pin_result['success'] and metadata_pin_result['success']
                
                if overall_success:
                    st.session_state.collection_df.at[original_index, 'status'] = 'completed'
                    st.session_state.collection_df.at[original_index, 'repin_cid'] = asset_image_cid
                    
                    # Create comprehensive success message
                    success_details = [f"Image CID: {asset_image_cid[:16]}..."]
                    if asset_metadata_cid:
                        success_details.append(f"Metadata CID: {asset_metadata_cid[:16]}...")
                    
                    if strategy_type == "directory_based" and 'image_file_path' in row and row['image_file_path']:
                        success_details.append(f"File: {row['image_file_path']}")
                    
                    st.session_state.collection_df.at[original_index, 'error_message'] = f"Complete NFT pinned ({', '.join(success_details)})"
                    
                    success_count += 1
                    print(f"🔧 DEBUG: ✅ Updated asset {row['asset_name']} to completed")
                else:
                    st.session_state.collection_df.at[original_index, 'status'] = 'failed'
                    
                    # Create detailed error message
                    error_parts = []
                    if not image_pin_result['success']:
                        img_error = image_pin_result['response'].get('error', 'Unknown error') if isinstance(image_pin_result['response'], dict) else str(image_pin_result['response'])
                        error_parts.append(f"Image: {img_error}")
                    if asset_metadata_cid and not metadata_pin_result['success']:
                        meta_error = metadata_pin_result['response'].get('error', 'Unknown error') if isinstance(metadata_pin_result['response'], dict) else str(metadata_pin_result['response'])
                        error_parts.append(f"Metadata: {meta_error}")
                    
                    combined_error = "; ".join(error_parts) if error_parts else "Unknown error"
                    st.session_state.collection_df.at[original_index, 'error_message'] = combined_error
                    failure_count += 1
                    print(f"🔧 DEBUG: ❌ Updated asset {row['asset_name']} to failed: {combined_error}")
                
                assets_updated += 1
                
            except Exception as asset_error:
                print(f"🔧 DEBUG: Exception updating asset {row['asset_name']}: {str(asset_error)}")
                st.session_state.collection_df.at[original_index, 'status'] = 'failed'
                st.session_state.collection_df.at[original_index, 'error_message'] = f'Update error: {str(asset_error)}'
                failure_count += 1
                assets_updated += 1
        
        print(f"🔧 DEBUG: Asset updates complete. Updated: {assets_updated}, Success: {success_count}, Failed: {failure_count}")
        
        # Complete
        progress_bar.progress(1.0)
        
        # Enhanced completion message
        if metadata_cids_to_pin:
            pinned_metadata = sum(1 for cid, result in pin_results.items() if result.get('type') == 'metadata' and result['success'])
            pinned_images = sum(1 for cid, result in pin_results.items() if result.get('type') == 'image' and result['success'])
            status_placeholder.success(f"✅ Complete NFT migration finished! Pinned {pinned_images}/{len(image_cids_to_pin)} image CIDs + {pinned_metadata}/{len(metadata_cids_to_pin)} metadata CIDs. {success_count} assets completed, {failure_count} failed.")
        else:
            if strategy_type == "directory_based":
                pinned_cids = sum(1 for result in pin_results.values() if result['success'])
                status_placeholder.success(f"✅ Migration completed! Pinned {pinned_cids}/{len(image_cids_to_pin)} base CIDs covering {success_count} assets ({failure_count} failed)")
            else:
                status_placeholder.success(f"✅ Migration completed! {success_count} successful, {failure_count} failed")
        
        print(f"🔧 DEBUG: Migration complete. Success: {success_count}, Failures: {failure_count}")
        
        # Important: Force DataFrame to be recognized as changed by creating a deep copy
        print(f"🔧 DEBUG: Forcing DataFrame update in session state...")
        st.session_state.collection_df = st.session_state.collection_df.copy(deep=True)
        
        # Add a flag to indicate migration just completed
        st.session_state.migration_just_completed = True
        
        # Show updated status counts immediately
        total_assets = len(st.session_state.collection_df)
        pending_assets_after = len(st.session_state.collection_df[st.session_state.collection_df['status'] == 'pending'])
        completed_assets_after = len(st.session_state.collection_df[st.session_state.collection_df['status'] == 'completed'])
        failed_assets_after = len(st.session_state.collection_df[st.session_state.collection_df['status'] == 'failed'])
        
        print(f"🔧 DEBUG: Final status counts - Total: {total_assets}, Pending: {pending_assets_after}, Completed: {completed_assets_after}, Failed: {failed_assets_after}")
        
        # Clean up progress tracking
        if hasattr(st.session_state, 'migration_progress'):
            del st.session_state.migration_progress
        
        print(f"🔧 DEBUG: About to rerun...")
        # Rerun to refresh the display
        st.rerun()
        
    except Exception as e:
        print(f"🔧 DEBUG: Major exception in migrate_collection: {str(e)}")
        st.error(f"❌ Migration failed with error: {str(e)}")
        
        # Clean up on error
        if hasattr(st.session_state, 'migration_progress'):
            del st.session_state.migration_progress
            
        # Still try to refresh display
        st.rerun()

def verify_collection_pins(df, service_name, api_key):
    """Verify that pins are actually available on the service."""
    completed_assets = df[df['status'] == 'completed']
    
    if completed_assets.empty:
        st.warning("⚠️ No completed pins to verify.")
        return
    
    with st.spinner("🔍 Verifying pins..."):
        # Collect CIDs to verify
        cids_to_verify = []
        for _, row in completed_assets.iterrows():
            if row.get('repin_cid') and row['repin_cid'] != "":
                cids = [cid.strip() for cid in row['repin_cid'].split(',')]
                cids_to_verify.extend(cids)
        
        if cids_to_verify:
            from utils import verify_pinned_cids
            verified_count, total_count, details = verify_pinned_cids(
                service_name, api_key, cids_to_verify
            )
            
            if verified_count == total_count:
                st.success(f"✅ All pins verified: {verified_count}/{total_count} CIDs")
            elif verified_count > 0:
                st.warning(f"⚠️ Partial verification: {verified_count}/{total_count} CIDs verified")
            else:
                st.error(f"❌ Verification failed: 0/{total_count} CIDs found")
            
            # Show details
            with st.expander("📋 Verification Details"):
                for detail in details:
                    status_icon = "✅" if detail['is_pinned'] else "❌"
                    st.write(f"{status_icon} {detail['cid'][:16]}... - {detail['status']}")
        else:
            st.warning("⚠️ No CIDs found to verify.")

def download_results(df):
    """Provide download buttons for results."""
    col1, col2 = st.columns(2)
    
    with col1:
        from utils import dataframe_to_csv
        csv_data = dataframe_to_csv(df)
        st.download_button(
            "📊 Download CSV",
            data=csv_data,
            file_name="nft_repinning_results.csv",
            mime="text/csv"
        )
    
    with col2:
        from utils import dataframe_to_json
        json_data = dataframe_to_json(df)
        st.download_button(
            "📄 Download JSON",
            data=json_data,
            file_name="nft_repinning_results.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main() 