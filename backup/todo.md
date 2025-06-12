# TODO.md: Algorand NFT IPFS Repinning Tool (v2 - Full ARC19 Support)

This document outlines all the necessary steps to create a Streamlit-based application for migrating Algorand NFT collections to new IPFS pinning services, with comprehensive support for all ARC19 URL templates.

## Phase 0: Project Setup and Structure

- [x] **1. Create Project Directory Structure:**
  ```
  /algorand-repin-tool/
  |-- app.py             # Main Streamlit application file
  |-- utils.py           # Helper functions for Algorand, ARC19, and Pinning
  |-- requirements.txt   # Python package dependencies
  |-- .streamlit/
  |   |-- secrets.toml   # To store API keys securely
  |-- TODO.md            # This file
  |-- README.md          # User-facing instructions
  ```

- [x] **2. Define `requirements.txt`:**
  Create the file and add the following dependencies.
  ```
  streamlit
  algosdk
  py-ipfs-cid
  pandas
  requests
  ```

- [x] **3. Setup Virtual Environment and Install Dependencies:**
  - Create a Python virtual environment: `python -m venv venv`
  - Activate it: `source venv/bin/activate` (on macOS/Linux) or `.\venv\Scripts\activate` (on Windows)
  - Install packages: `pip install -r requirements.txt`

- [x] **4. Configure Streamlit Secrets:**
  - Create the `.streamlit/secrets.toml` file.
  - Add placeholders for the pinning service API keys. This prevents hardcoding keys in the script.
  ```toml
  # .streamlit/secrets.toml
  [pinning_services]
  filebase_api_key = "YOUR_FILEBASE_KEY_HERE"
  nft_storage_api_key = "YOUR_NFT_STORAGE_KEY_HERE"
  pinata_api_key = "YOUR_PINATA_KEY_HERE"
  infura_api_key = "YOUR_INFURA_KEY_HERE"
  ```

## Phase 1: Core Logic - Data Fetching & Processing (`utils.py`)

- [x] **1. Implement Algorand Asset Fetching:**
  - In `utils.py`, create a function `get_all_creator_assets(creator_address)`.
  - **Inputs:** `creator_address` (string).
  - **Logic:**
    - Initialize the `algosdk.v2client.indexer.IndexerClient`. Use a public indexer like `https://mainnet-idx.algonode.cloud`.
    - Create an empty list `all_assets`.
    - Implement a `while` loop to handle pagination.
    - Call `indexer_client.lookup_account_created_assets(address=creator_address, next_page=next_token)`.
    - Append the `assets` from the response to `all_assets`.
    - Get the `next-token` from the response. If it's `None`, break the loop.
    - Include `try...except` block to handle invalid Algorand addresses or network errors, returning an empty list and an error message.
  - **Returns:** A tuple `(list_of_assets, error_message)`. `error_message` is `None` on success.

- [x] **2. Implement Full ARC19 CID Extraction (Revised):**
  - In `utils.py`, create a function `extract_cid_from_asset(asset)`.
  - **Inputs:** `asset` (a single asset dictionary from the Algorand Indexer response).
  - **Logic:**
    - **a. Check for URL:** Verify that `asset['params']['url']` exists and is a string. If not, return `None`.
    - **b. Parse the ARC19 Template String:**
      - Use the `re` (regular expression) library to parse the URL.
      - The pattern must capture the variable parts of the ARC19 template: `version`, `codec`, `field`, and `hash_type`.
      - Define the regex pattern:
        ```python
        import re
        pattern = re.compile(r"template-ipfs://{ipfscid:(?P<version>\d+):(?P<codec>\w+):(?P<field>\w+):(?P<hash_type>[\w-]+)}")
        match = pattern.match(asset['params']['url'])
        ```
      - If `match` is `None`, it's not a valid ARC19 URL; return `None`.
    - **c. Extract Template Parameters:**
      - If a match is found, extract the groups:
        ```python
        params = match.groupdict()
        field_to_get = params['field'] # This will be 'reserve', 'manager', 'freezer', or 'clawback'
        cid_version = int(params['version']) # e.g., 1
        cid_codec = params['codec'] # e.g., 'raw'
        hash_type = params['hash_type'] # e.g., 'sha2-256'
        ```
    - **d. Get Address from the Correct Field:**
      - Check if the `field_to_get` exists in `asset['params']`. The valid fields are `reserve`, `manager`, `freezer`, `clawback`.
      - Retrieve the address string: `address_to_decode = asset['params'].get(field_to_get)`.
      - If `address_to_decode` is `None`, return `None` (asset is malformed).
    - **e. Decode the Address:**
      - The address is base32 encoded without padding. It must be padded to a length that is a multiple of 8.
      - `padded_address = address_to_decode + '=' * (-len(address_to_decode) % 8)`
      - Wrap the decoding in a `try...except` block:
        ```python
        try:
            decoded_bytes = base64.b32decode(padded_address)
        except Exception:
            return None # Decoding failed
        ```
    - **f. Reconstruct the CID using Parsed Parameters:**
      - Import `CIDv1`, `codecs`, `multihash` from the `cid` library.
      - Create the multihash object dynamically using the `hash_type` from the template: `mh = multihash.encode(decoded_bytes, hash_type)`.
      - Create the CID object dynamically. Currently `py-ipfs-cid` primarily supports `CIDv1`, so we'll assume `cid_version == 1`.
      - `cid = CIDv1(cid_codec, mh)`.
      - Return the CID as a string: `str(cid)`.
  - **Returns:** CID (string) or `None`.

- [x] **3. Implement Data Structuring:**
  - In `utils.py`, create a function `create_collection_dataframe(assets)`.
  - **Inputs:** `assets` (the list of assets from `get_all_creator_assets`).
  - **Logic:**
    - Initialize an empty list, `processed_data`.
    - Loop through each `asset` in the input list.
    - For each `asset`, call the new, robust `extract_cid_from_asset(asset)` to get the CID.
    - If a CID is returned, create a dictionary with the following structure:
      ```python
      {
          "asset_id": asset['index'],
          "asset_name": asset['params'].get('name'),
          "asset_url": asset['params'].get('url'),
          "cid": cid,
          "status": "pending", # Initial status
          "repin_cid": None,   # To be filled after successful migration
          "error_message": None # To be filled on failure
      }
      ```
    - Append this dictionary to `processed_data`.
    - Use `pandas.DataFrame(processed_data)` to create the DataFrame.
  - **Returns:** A pandas DataFrame.

- [x] **4. Implement CSV/JSON Conversion:**
  - In `utils.py`, create a function `dataframe_to_csv(df)`. It should convert the DataFrame to a CSV string using `df.to_csv(index=False).encode('utf-8')`.
  - In `utils.py`, create a function `dataframe_to_json(df)`. It should convert the DataFrame to a JSON string using `df.to_json(orient='records', indent=4).encode('utf-8')`.

## Phase 2: Core Logic - IPFS Pinning (`utils.py`)

- [x] **1. Create Generic Pinning Wrapper:**
  - In `utils.py`, create a function `pin_cid(service_name, api_key, cid)`.
  - This function will act as a dispatcher. It will use `if/elif/else` to call the correct service-specific function based on `service_name`.

- [x] **2. Implement Filebase Pinning:**
  - In `utils.py`, create `_pin_with_filebase(api_key, cid_to_pin)`.
  - **Endpoint:** `POST https://api.filebase.io/v1/ipfs/pins`
  - **Headers:** `{'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}`
  - **Body:** `{'cid': cid_to_pin}`
  - **Returns:** A tuple `(success: bool, response_json: dict)`.

- [x] **3. Implement NFT.Storage Pinning:**
  - In `utils.py`, create `_pin_with_nft_storage(api_key, cid_to_pin)`.
  - **Endpoint:** `POST https://api.nft.storage/pins`
  - **Headers:** `{'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}`
  - **Body:** `{'cid': cid_to_pin}`
  - **Returns:** A tuple `(success: bool, response_json: dict)`.

- [x] **4. Implement Pinata Pinning:**
  - In `utils.py`, create `_pin_with_pinata(api_key, cid_to_pin)`.
  - **Endpoint:** `POST https://api.pinata.cloud/pinning/pinByHash`
  - **Headers:** `{'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}`
  - **Body:** `{'hashToPin': cid_to_pin}`
  - **Returns:** A tuple `(success: bool, response_json: dict)`.

- [x] **5. Implement Infura Pinning:**
  - In `utils.py`, create `_pin_with_infura(api_key_and_secret, cid_to_pin)`.
  - **Note:** Infura uses Basic Auth with Project ID and API Key Secret. The `api_key` parameter here should be a tuple `(project_id, api_secret)`.
  - **Endpoint:** `POST https://ipfs.infura.io:5001/api/v0/pin/add?arg={cid_to_pin}`
  - **Auth:** `auth=(project_id, api_secret)` in the `requests.post` call.
  - **Returns:** A tuple `(success: bool, response_json: dict)`.

## Phase 3: Streamlit UI Implementation (`app.py`)

- [x] **1. Initial Page Setup & State:**
  - Import all necessary libraries and functions.
  - Set page title and layout: `st.set_page_config(page_title="Algorand NFT Repinning Tool", layout="wide")`.
  - Initialize `st.session_state` to hold the data DataFrame.
    ```python
    if 'collection_df' not in st.session_state:
        st.session_state.collection_df = pd.DataFrame()
    ```

- [x] **2. Create Input UI (Sidebar):**
  - Use `st.sidebar` for inputs.
  - `st.sidebar.header("1. Load Collection")`.
  - `st.text_input` for the creator wallet address.
  - `st.button("Fetch Assets from Algorand")`.
  - `st.file_uploader("Or Upload Collection CSV/JSON")`.
  - Implement logic to handle both inputs.

- [x] **3. Create Pinning Configuration UI (Sidebar):**
  - `st.sidebar.header("2. Configure Pinning")`.
  - `st.selectbox` for choosing the pinning service.
  - `st.sidebar.info()` with links to API key documentation.
  - `st.text_input("API Key", type="password")`.

- [x] **4. Create Main Display Area:**
  - `st.title("Collection Migration Status")`.
  - `st.dataframe(st.session_state.collection_df)` to display the live data.

- [x] **5. Implement Migration Logic and Progress UI:**
  - `st.header("3. Run Migration")`.
  - `st.button("Start Migration")`.
  - **Placeholders for progress feedback:**
    ```python
    progress_bar = st.progress(0)
    log_placeholder = st.empty()
    ```
  - **Inside `if st.button("Start Migration"):` block:**
    - Perform validation checks.
    - Get the list of CIDs to migrate (where `status == 'pending'`).
    - **Loop through DataFrame rows:**
      - Update log placeholder with "Attempting to pin...".
      - Call `utils.pin_cid(...)`.
      - **Update the DataFrame in `st.session_state`** based on success or failure.
      - Update log placeholder with result.
      - Update progress bar.
    - Display a final "complete" message.

- [x] **6. Implement Data Download:**
  - `st.header("4. Download Results")`.
  - Create two columns for CSV and JSON download buttons.
  - Use `st.download_button` with data generated by `utils.dataframe_to_csv` and `utils.dataframe_to_json`.

## Phase 4: Final Touches

- [x] **1. Write `README.md`:**
  - Create a user-friendly `README.md`.
  - Explain the purpose and how to run the tool.
  - Detail the `secrets.toml` configuration.
  - Explain how to use the UI.

- [x] **2. Refine Error Handling and User Feedback:**
  - Review all parts of the code. Ensure that `try...except` blocks provide clear, user-facing error messages via `st.error()`.

- [x] **3. Code Cleanup and Commenting:**
  - Add comments to `app.py` and `utils.py` explaining complex logic, especially the revised ARC19 parsing.
  - Ensure code follows PEP 8 standards.

---