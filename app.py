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

# Custom CSS for Professional UI, Cards, and Color-coded indicators
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stButton>button { width: 100%; background-color: #1e3d59; color: white; font-weight: bold; border-radius: 6px; }
    .stButton>button:hover { background-color: #17b978; color: white; }
    .pass-card { padding: 15px; background-color: #d4edda; border-left: 6px solid #28a745; color: #155724; border-radius: 4px; margin-bottom: 10px; }
    .fail-card { padding: 15px; background-color: #f8d7da; border-left: 6px solid #dc3545; color: #721c24; border-radius: 4px; margin-bottom: 10px; }
    .category-badge { padding: 10px; background-color: #cce5ff; border-left: 6px solid #004085; color: #004085; border-radius: 4px; font-weight: bold; margin-bottom: 15px; }
    .item-pass { padding: 8px 12px; background-color: #d4edda; color: #155724; border-radius: 4px; margin-bottom: 5px; border-left: 4px solid #28a745; font-weight: 500; }
    .item-fail { padding: 8px 12px; background-color: #f8d7da; color: #721c24; border-radius: 4px; margin-bottom: 5px; border-left: 4px solid #dc3545; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# Authentication State Management
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "inspector_name" not in st.session_state:
    st.session_state.inspector_name = ""

# Secure Local Database File for Inspection Logs
DB_FILE = "legal_metrology_complete_logs.csv"
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["Timestamp", "Inspector_ID", "Detected_Category", "Verdict", "Summary_Details", "Violations"])
    df_init.to_csv(DB_FILE, index=False)

# ----------------- 1. OFFICIAL LOGIN & SECURITY PORTAL -----------------
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #1e3d59;'>⚖️ Legal Metrology Smart Inspector</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #6c757d;'>Government Enforcement Portal (Packaged Commodities Rules, 2011)</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔒 Official Inspector Login")
            inspector_id = st.text_input("Inspector ID (e.g., LMI_HYD_402)")
            password = st.text_input("Secure Password", type="password")
            login_btn = st.form_submit_button("Access Portal")
            
            if login_btn:
                if inspector_id and password == "sih2026":
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
    st.title("🔍 Ultimate Compliance Engine (2011 Rules & Multi-Category)")
    st.write("Capture or upload product label via Camera/File. AI will auto-detect category, handle synonyms, and show green/red statutory validation.")

    col_img, col_analysis = st.columns([1, 1])

    with col_img:
        st.subheader("📸 Capture / Upload Label")
        upload_choice = st.radio("Choose Input Method", ["Use Phone Camera", "Upload Image File"])
        
        image_data = None
        if upload_choice == "Use Phone Camera":
            image_data = st.camera_input("Take a photo of the product label")
        else:
            image_data = st.file_uploader("Upload Label Image", type=["jpg", "jpeg", "png"])

        if image_data is not None:
            st.image(image_data, caption="Selected Product Label", use_container_width=True)

    with col_analysis:
        st.subheader("📋 Compliance & Rule Verification Panel")
        
        # Optional manual override option just in case
        override_category = st.selectbox(
            "Select/Confirm Category (Auto-detected by default)", 
            ["Auto-Detect via AI", "Food & Groceries (FSSAI)", "Medicines & Drugs", "Cosmetics & Beauty", "Electronics & Appliances", "General Commodities / Textiles"]
        )
        
        run_check = st.button("Run AI Scan & Color-Coded Verification")

        if run_check:
            if image_data is None:
                st.warning("Please capture or upload a product label image first!")
            else:
                with st.spinner("AI parsing label, normalizing synonyms, and enforcing category rules..."):
                    
                    # Determine category (simulated auto-detection or manual selection)
                    if override_category == "Auto-Detect via AI":
                        detected_category = "Food & Groceries (FSSAI)" # Default AI match example
                    else:
                        detected_category = override_category

                    # Rule checklists based on category
                    if "Food" in detected_category:
                        rule_checklist = {
                            "Common Name of Commodity [Rule 6]": (True, "Wheat Flour (Aashirvaad)"),
                            "Manufacturer / Packer Name & Address [Rule 6]": (True, "ITC Ltd., Kolkata - 700001"),
                            "Net Quantity (Weight/Volume) [Rule 14]": (True, "1 kg (When packed)"),
                            "MRP (Inclusive of all taxes) [Rule 18]": (True, "₹58.00"),
                            "Expiry / Best Before / Use By": (True, "Best Before 4 months (Synonym matched)"),
                            "FSSAI License Number / Logo (Mandatory)": (False, "Missing / Not Visible on Label!")
                        }
                    elif "Medicines" in detected_category:
                        rule_checklist = {
                            "Brand / Generic Name": (True, "Paracetamol Tablets IP 500mg"),
                            "Composition / Active Ingredients": (True, "Each tablet contains Paracetamol IP 500mg"),
                            "Manufacturer Name & Address": (True, "Sun Pharma Ltd., Mumbai"),
                            "Batch Number": (True, "BT2026X9"),
                            "Manufacturing & Expiry Dates": (True, "Mfg: 01/2026, Exp: 12/2028"),
                            "Manufacturing License Number": (False, "Mfg License Number is missing or unreadable!")
                        }
                    elif "Cosmetics" in detected_category:
                        rule_checklist = {
                            "Product Name & Description": (True, "Herbal Neem Face Wash"),
                            "Manufacturer / Packer Address": (True, "Himalaya Wellness, Bengaluru"),
                            "Net Quantity (Volume)": (True, "100 ml"),
                            "MRP (Inclusive of taxes)": (True, "₹180.00"),
                            "Batch Number & Mfg Date": (True, "Batch #BN2409"),
                            "Expiry / Use Before Date": (False, "Expiry / Use Before Date is missing!")
                        }
                    elif "Electronics" in detected_category:
                        rule_checklist = {
                            "Product Name & Model Number": (True, "Smart LED Bulb 9W"),
                            "Manufacturer / Importer Address": (True, "Syska LED, Pune"),
                            "Electrical Ratings (Voltage/Wattage)": (True, "230V AC, 50Hz, 9W"),
                            "MRP (Inclusive of taxes)": (True, "₹450.00"),
                            "BIS Standard Mark (Mandatory)": (False, "BIS Safety Standard Mark is missing!"),
                            "Warranty Period Details": (True, "1 Year Replacement Warranty")
                        }
                    else: # General Commodities / Clothes
                        rule_checklist = {
                            "Common / Generic Name [Rule 6]": (True, "Men's Cotton Casual Shirt"),
                            "Manufacturer / Seller Info [Rule 6]": (True, "Raymonds Apparel Ltd."),
                            "Size / Dimensions [Rule 13]": (True, "Size: 40 (L)"),
                            "Net Quantity [Rule 14]": (True, "1 Unit"),
                            "MRP (Inclusive of taxes) [Rule 18]": (True, "₹1,499.00"),
                            "Wash Care Instructions": (True, "Machine wash cold")
                        }

                    violations = [rule for rule, (status, _) in rule_checklist.items() if not status]
                    verdict = "PASS" if len(violations) == 0 else "FAIL"

                    # Display Category Badge
                    st.markdown("---")
                    st.markdown(f"""
                    <div class="category-badge">
                        🤖 Active Category Verified: <u>{detected_category}</u>
                    </div>
                    """, unsafe_allow_html=True)

                    # Display Color-Coded Checklist
                    st.subheader("🎯 Statutory Rule Verification Checklist (2011 Act):")
                    for rule_name, (is_present, details) in rule_checklist.items():
                        if is_present:
                            st.markdown(f"""
                            <div class="item-pass">
                                ✅ <b>{rule_name}:</b> {details}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="item-fail">
                                ❌ <b>{rule_name}:</b> {details}
                            </div>
                            """, unsafe_allow_html=True)

                    # Display Final Verdict Card
                    st.markdown("---")
                    st.subheader("⚖️ Final Inspection Verdict:")
                    
                    if verdict == "PASS":
                        st.markdown("""
                        <div class="pass-card">
                            <h3>✅ COMPLIANT (PASS)</h3>
                            <p>All mandatory declarations under Legal Metrology Rules, 2011 are verified and present.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="fail-card">
                            <h3>❌ NON-COMPLIANT (FAIL)</h3>
                            <p>Violations identified! Marked in red above against statutory rules.</p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Save to Local Database Log
                    new_log = {
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Inspector_ID": st.session_state.inspector_name,
                        "Detected_Category": detected_category,
                        "Verdict": verdict,
                        "Summary_Details": f"Checked {len(rule_checklist)} rules",
                        "Violations": " | ".join(violations) if violations else "None"
                    }
                    df_db = pd.read_csv(DB_FILE)
                    df_db = pd.concat([df_db, pd.DataFrame([new_log])], ignore_index=True)
                    df_db.to_csv(DB_FILE, index=False)
                    
