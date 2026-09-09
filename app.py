import streamlit as st
import pandas as pd
from datetime import datetime
import os
import google.generativeai as genai
from PIL import Image
import json

# Page Configuration
st.set_page_config(
    page_title="Smart Legal Metrology Inspector Portal",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS for Professional UI & Color-coded indicators
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
DB_FILE = "legal_metrology_gemini_logs.csv"
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
    st.title("🔍 Real Gemini AI Compliance Engine (2011 Rules)")
    st.write("Capture or upload product label. Google Gemini AI will analyze the image, detect category, extract details, and enforce rules.")

    # API Key Input
    gemini_api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

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
            img_display = Image.open(image_data)
            st.image(img_display, caption="Selected Product Label", use_container_width=True)

    with col_analysis:
        st.subheader("📋 Rule Verification Panel")
        run_check = st.button("Run Real Gemini AI Compliance Check")

        if run_check:
            if not gemini_api_key:
                st.error("Please enter your Google Gemini API Key in the sidebar!")
            elif image_data is None:
                st.warning("Please capture or upload a product label image first!")
            else:
                try:
                    genai.configure(api_key=gemini_api_key)
                    # Using Gemini 1.5 Flash for fast and accurate multimodal extraction
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    img = Image.open(image_data)
                    
                    prompt = """
                    You are an expert Legal Metrology Inspector enforcing the Legal Metrology (Packaged Commodities) Rules, 2011.
                    Analyze the given product label image carefully and return a JSON response with the following keys:
                    1. "detected_category": Classify the product into one of these: "Food & Groceries (FSSAI)", "Medicines & Drugs", "Cosmetics & Beauty", "Electronics & Appliances", "General Commodities / Textiles".
                    2. "rule_checklist": A dictionary where each key is a statutory rule requirement name, and the value is a list containing two elements: [boolean (true if present/valid, false if missing/invalid), string (extracted detail or reason for failure)].
                    
                    For example, check for:
                    - Common Name of Commodity
                    - Manufacturer / Packer Name & Address
                    - Net Quantity (Weight/Volume)
                    - MRP (Inclusive of all taxes)
                    - Expiry / Best Before / Use By / Validity
                    - Category specific marks (e.g., FSSAI License Number/Logo for Food, Batch/Mfg date for Cosmetics/Medicines, BIS mark for Electronics).
                    
                    Return ONLY valid JSON format without any markdown formatting blocks like ```json.
                    """
                    
                    with st.spinner("Connecting with Google Gemini AI to analyze label and check statutory rules..."):
                        response = model.generate_content([prompt, img])
                        clean_text = response.text.replace("```json", "").replace("```", "").strip()
                        ai_result = json.loads(clean_text)
                    
                    detected_category = ai_result.get("detected_category", "General Commodities / Textiles")
                    rule_checklist = ai_result.get("rule_checklist", {})
                    
                    violations = [rule for rule, (status, _) in rule_checklist.items() if not status]
                    verdict = "PASS" if len(violations) == 0 else "FAIL"

                    # Display Category Badge
                    st.markdown("---")
                    st.markdown(f"""
                    <div class="category-badge">
                        🤖 Real Gemini AI Detected Category: <u>{detected_category}</u>
                    </div>
                    """, unsafe_allow_html=True)

                    # Display Color-Coded Checklist
                    st.subheader("🎯 Statutory Rule Verification Checklist:")
                    for rule_name, val_list in rule_checklist.items():
                        is_present = val_list[0]
                        details = val_list[1]
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
                            <p>All mandatory declarations under Legal Metrology Rules, 2011 are verified by Gemini AI.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="fail-card">
                            <h3>❌ NON-COMPLIANT (FAIL)</h3>
                            <p>Violations identified! Marked in red above by Gemini AI OCR.</p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Save to Local Database Log
                    new_log = {
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Inspector_ID": st.session_state.inspector_name,
                        "Detected_Category": detected_category,
                        "Verdict": verdict,
                        "Summary_Details": f"Checked {len(rule_checklist)} rules via Gemini AI",
                        "Violations": " | ".join(violations) if violations else "None"
                    }
                    df_db = pd.read_csv(DB_FILE)
                    df_db = pd.concat([df_db, pd.DataFrame([new_log])], ignore_index=True)
                    df_db.to_csv(DB_FILE, index=False)

                except Exception as e:
                    st.error(f"Error communicating with Gemini API: {e}")
                    
