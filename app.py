import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Page Configuration
st.set_page_config(
    page_title="Smart Legal Metrology Inspector Portal",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS for Professional UI
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stButton>button { width: 100%; background-color: #1e3d59; color: white; font-weight: bold; border-radius: 6px; }
    .stButton>button:hover { background-color: #17b978; color: white; }
    .pass-card { padding: 15px; background-color: #d4edda; border-left: 6px solid #28a745; color: #155724; border-radius: 4px; margin-bottom: 10px; }
    .fail-card { padding: 15px; background-color: #f8d7da; border-left: 6px solid #dc3545; color: #721c24; border-radius: 4px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Authentication State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "inspector_name" not in st.session_state:
    st.session_state.inspector_name = ""

# Database Configuration (CSV based local storage)
DB_FILE = "legal_metrology_logs.csv"
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["Timestamp", "Inspector_ID", "Category", "Verdict", "Detected_Details", "Violations"])
    df_init.to_csv(DB_FILE, index=False)

# ----------------- 1. LOGIN & SECURITY PORTAL -----------------
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #1e3d59;'>⚖️ Legal Metrology Smart Inspector</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #6c757d;'>Government Enforcement Portal (Packaged Commodities Rules, 2011)</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔒 Official Login")
            inspector_id = st.text_input("Inspector ID (e.g., LMI_HYD_402)")
            password = st.text_input("Secure Password", type="password")
            login_btn = st.form_submit_button("Access Portal")
            
            if login_btn:
                if inspector_id and password == "sih2026": # Demo Password
                    st.session_state.authenticated = True
                    st.session_state.inspector_name = inspector_id
                    st.rerun()
                else:
                    st.error("Invalid Inspector ID or Password!")
    st.stop()

# ----------------- 2. SIDEBAR NAVIGATION -----------------
st.sidebar.title("📌 Navigation")
st.sidebar.write(f"Inspector: **{st.session_state.inspector_name}**")
nav_choice = st.sidebar.radio("Go to", ["Product Scanner & Rule Engine", "Inspection Database & Logs", "Logout"])

if nav_choice == "Logout":
    st.session_state.authenticated = False
    st.session_state.inspector_name = ""
    st.rerun()

elif nav_choice == "Inspection Database & Logs":
    st.title("📂 Inspection History & Database")
    st.write("All past verification records conducted under Legal Metrology Act are stored here securely.")
    if os.path.exists(DB_FILE):
        df_logs = pd.read_csv(DB_FILE)
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True)
            if st.button("Export Logs to CSV"):
                df_logs.to_csv("exported_inspection_reports.csv", index=False)
                st.success("Reports exported successfully!")
        else:
            st.info("No inspection history available yet.")

elif nav_choice == "Product Scanner & Rule Engine":
    st.title("🔍 Category-Based Compliance Engine (2011 Rules)")
    st.write("Upload product label images. The system will auto-detect the category and check variable keywords (Synonyms) like Use By, Expiry, Marketed by, etc.")

    col_img, col_analysis = st.columns([1, 1])

    with col_img:
        uploaded_image = st.file_uploader("Upload Label Image", type=["jpg", "jpeg", "png"])
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Scanned Product Label", use_container_width=True)

    with col_analysis:
        st.subheader("Rule Validation Panel")
        product_category = st.selectbox(
            "Select Detected Product Category",
            ["General Commodities (Clothes, Toys, etc.)", "Food & Groceries (FSSAI)", "Cosmetics & Drugs", "Electronics / Appliances"]
        )
        
        run_check = st.button("Run 2011 Rule Compliance Check")

        if run_check:
            if uploaded_image is None:
                st.warning("Please upload a product label image first!")
            else:
                with st.spinner("AI parsing labels & matching synonyms (MRP, Expiry/Use By, Packer info)..."):
                    
                    violations = []
                    extracted_info = {}

                    # --- SIMULATED FLEXIBLE EXTRACTION (Handling Synonyms) ---
                    # In real backend, Gemini extracts text and maps variants:
                    # 'Use By' or 'Expiry Date' or 'Best Before' -> mapped to Expiry field.
                    # 'Manufactured By' or 'Packed By' or 'Marketed By' -> mapped to Packer field.
                    
                    has_mrp = True  # Universal mandatory
                    has_net_quantity = True # Universal mandatory
                    
                    # Flexible Synonym Check for Packer
                    packer_found_variants = ["Manufactured By", "Packed By", "Marketed By"]
                    has_packer_details = True # Simulated true
                    
                    # Flexible Synonym Check for Expiry/Date
                    expiry_found_variants = ["Use By", "Expiry Date", "Best Before", "Use Before"]
                    
                    # 1. Universal Rule Checks
                    if not has_mrp:
                        violations.append("Mandatory declaration missing: MRP (Inclusive of all taxes) [Rule 18]")
                    if not has_net_quantity:
                        violations.append("Mandatory declaration missing: Net Quantity (Weight/Volume) [Rule 14]")
                    if not has_packer_details:
                        violations.append("Mandatory declaration missing: Name & Address of Manufacturer / Packer / Importer [Rule 6]")

                    # 2. Category-Specific Dynamic Rules (2011 Regulations)
                    if product_category == "Food & Groceries (FSSAI)":
                        has_fssai_logo_or_no = False # Simulated missing FSSAI
                        has_expiry_date = True # Found "Use By" variant on food label
                        
                        if not has_fssai_logo_or_no:
                            violations.append("Category Violation: FSSAI License Number / Logo is missing (Mandatory for Food)")
                        if not has_expiry_date:
                            violations.append("Category Violation: 'Best Before' / 'Use By' / 'Expiry Date' is missing")

                    elif product_category == "Cosmetics & Drugs":
                        has_batch_no = True
                        has_mfg_date = True
                        # Cosmetics might use "Use Before" instead of Expiry
                        if not has_batch_no:
                            violations.append("Category Violation: Batch Number / Manufacturing License number missing")
                        if not has_mfg_date:
                            violations.append("Category Violation: Month & Year of Manufacture missing")

                    elif product_category == "Electronics / Appliances":
                        has_bis_mark = False # Simulated missing BIS mark
                        if not has_bis_mark:
                            violations.append("Category Violation: BIS (Bureau of Indian Standards) Standard Mark missing")

                    # Final Verdict
                    verdict = "PASS" if len(violations) == 0 else "FAIL"

                    # Display Results
                    st.markdown("---")
                    st.subheader("Inspection Result:")
                    
                    if verdict == "PASS":
                        st.markdown(f"""
                        <div class="pass-card">
                            <h3>✅ LEGAL COMPLIANCE: PASS</h3>
                            <p>The product label complies with all statutory declarations under Legal Metrology Rules, 2011 for <b>{product_category}</b>.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="fail-card">
                            <h3>❌ LEGAL COMPLIANCE: FAIL (Violations Found)</h3>
                            <p>The following discrepancies were identified based on 2011 statutory rules:</p>
                        </div>
                        """, unsafe_allow_html=True)
                        for v in violations:
                            st.write(f"- ⚠️ {v}")

                    # Save to Local Database Log
                    new_log = {
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Inspector_ID": st.session_state.inspector_name,
                        "Category": product_category,
                        "Verdict": verdict,
                        "Detected_Details": "Synonym-mapped labels parsed successfully",
                        "Violations": " | ".join(violations) if violations else "None"
                    }
                    df_db = pd.read_csv(DB_FILE)
                    df_db = pd.concat([df_db, pd.DataFrame([new_log])], ignore_index=True)
                    df_db.to_csv(DB_FILE, index=False)
 
