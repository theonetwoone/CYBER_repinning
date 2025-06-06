

# STYLING.MD: Cyber Skulls Interface Protocol

This document outlines the official styling, branding, and voice guidelines for the Cyber Skulls Repinning Tool. All UI/UX elements must adhere to these protocols to maintain brand integrity.

## 1. Core Philosophy & Aesthetic

-   **Concept:** Retro "hacker" terminal, CLI (Command-Line Interface), tech-noir.
-   **Feeling:** Functional, high-tech, urgent, and slightly dystopian. The user is an operative running a critical protocol.
-   **Inspiration:** 1980s-90s computer terminals, cyberpunk media, and the provided `image.png` (green, glowing skull).

## 2. Color Palette

The palette is minimalist and high-contrast, designed to mimic a classic monochrome monitor.

| Role                     | Hex Code  | Notes                                   |
| ------------------------ | :-------: | --------------------------------------- |
| **Primary / Accent** | `#00FF41` | "Radioactive" Green. Used for highlights, borders, buttons, and important text. |
| **Background** | `#000000` | Pure Black. The main canvas of the application. |
| **Secondary Background** | `#0D1117` | A dark charcoal/off-black. Used for sidebars or container backgrounds to create subtle depth. |
| **Primary Text** | `#E0E0E0` | A slightly off-white/light grey. Easy to read on a black background without being too harsh. |
| **Success State** | `#00FF41` | The primary accent color also serves as the success indicator. |
| **Error / Warning State**| `#FF4747` | A stark, alerting red for error messages and failed statuses. |

## 3. Typography

-   **Primary Font:** `VT323`
-   **Source:** Google Fonts
-   **Fallback:** `monospace`
-   **Weight:** `400` (Regular)
-   **Size:** `18px` base size to enhance the terminal feel. Headings can be larger.

The font should be applied globally to all text within the application for a consistent look.

## 4. Component Styling

### 4.1 Buttons

-   **Default State:** Transparent background, 2px solid green border, green text. No rounded corners.
-   **Hover State:** Green background, white or brighter green border, black text. This provides clear interactive feedback.
-   **Padding:** Generous padding to create a larger click target.

### 4.2 DataFrames & Tables

-   **Header:** Black text on a solid green background.
-   **Cell Text:** Standard primary text color (`#E0E0E0`).
-   **Grid Lines:** A dark, subtle grey (`#2a2a2a`) to avoid visual noise.

### 4.3 Text Input & Selectors

-   **Border:** 1px solid green border.
-   **Background:** Black or secondary background color (`#0D1117`).
-   **Text:** Primary text color (`#E0E0E0`).

### 4.4 Containers & Layout

-   **Main Area:** Pure black background (`#000000`).
-   **Sidebar:** Secondary background color (`#0D1117`) to visually separate it from the main content area.
-   **Dividers:** Use `st.divider()`, which will inherit a subtle color from the theme.
-   **Headers:** Use brackets and capitalization for a distinct, programmatic look (e.g., `[ SECTION_HEADER ]`).

## 5. Tone & Voice

The language used throughout the app should be concise, technical, and thematic.

-   **Buttons:** Use action-oriented, capitalized commands: `> SCAN FOR ASSETS`, `> EXECUTE REPIN PROTOCOL`, `> DOWNLOAD DATA LOGS`.
-   **Labels & Titles:** Use underscores instead of spaces, all caps: `CREATOR_WALLET`, `PINNING_SERVICE`, `MIGRATION_STATUS`.
-   **Instructions:** Keep them brief and direct, as if from a system manual: `INPUT TARGET WALLET ADDRESS.`, `SELECT PINNING SERVICE FROM LIST.`.
-   **Feedback:** Use technical-sounding status updates: `STATUS: STANDING BY...`, `ACQUIRING ASSET DATA...`, `SIGNAL DECRYPTION COMPLETE.`, `ERROR: CONNECTION TIMED OUT.`.

## 6. Implementation Snippets

### 6.1 Streamlit `config.toml`

This file sets the base theme. Place it in `.streamlit/config.toml`.

```toml
# .streamlit/config.toml

[theme]
primaryColor="#00FF41"
backgroundColor="#000000"
secondaryBackgroundColor="#0D1117"
textColor="#E0E0E0"
font="monospace"
```

### 6.2 Custom CSS Injection

Use this in your main Python app file (`protocol_app.py`) to apply the specific font and advanced component styles.

```python
import streamlit as st

def inject_custom_css():
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
            }
            .stButton > button:hover {
                border-color: #FFFFFF;
                color: #000000;
                background-color: #00FF41;
            }
            .stButton > button:active {
                background-color: #00b32d; /* A slightly darker green for click feedback */
            }
            
            /* Dataframe/Table Header */
            .dataframe th {
                background-color: #00FF41;
                color: #000000;
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

        </style>
    """, unsafe_allow_html=True)

# --- In your main app function ---
# inject_custom_css()
# st.title("[ CYBER SKULLS // REPINNING PROTOCOL ]")
# ... rest of your app
```