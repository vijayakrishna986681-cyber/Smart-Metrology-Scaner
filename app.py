from datetime import datetime
import os
import time
import random
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from google.genai.errors import ClientError

st.set_page_config(page_title="Smart Legal Metrology Checker", layout="centered")

RULES = {
    "base": ["product", "manufacturer", "marketed by", "quantity", "mrp"],
    "food": ["ingredients", "best before", "use by", "fssai"],
    "cosmetics": ["batch", "expiry", "manufacturing"],
    "electronics": ["model", "warranty", "manufacturer", "voltage"],
    "medicines": ["batch", "expiry", "license", "dosage"]
}

# Sidebar for API Key configuration
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("Enter Gemini API Key:", type="password", help="Enter your Google Gemini API Key")

def detect_category(text: str):
    t = text.lower()
    scores = {
        "food": sum(k in t for k in ["ingredients", "nutrition", "sugar", "salt", "packaged food", "fssai"]),
        "cosmetics": sum(k in t for k in ["cream", "lotion", "shampoo", "soap", "cosmetic", "beauty"]),
        "electronics": sum(k in t for k in ["voltage", "warranty", "model", "charger", "battery", "electronics"]),
        "medicines": sum(k in t for k in ["tablet", "capsule", "syrup", "dosage", "medicine", "pharma"])
    }
    category = max(scores, key=scores.get)
    return category, scores

def gemini_call_with_retry(client, image_bytes, mime_type, max_attempts=3):
    last_err = None
    for attempt in range(max_attempts):
        try:
            return client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    "Analyze this product label image thoroughly. Extract all visible text, declarations, MRP, net quantity, manufacturer details, and category-specific details accurately.",
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
            )
        except Exception as e:
            last_err = e
            msg = str(e)
            if "503" not in msg and "UNAVAILABLE" not in msg and "429" not in msg:
                raise
            time.sleep(2 + random.uniform(0, 1))
    raise last_err

if "count" not in st.session_state:
    st.session_state.count = 0
if "history" not in st.session_state:
    st.session_state.history = []

st.title("⚖️ Smart Legal Metrology Checker")
st.caption("AI-powered compliance verification for packaged commodities under Legal Metrology Rules.")

uploaded = st.camera_input("Take product photo") or st.file_uploader(
    "Or upload product label image",
    type=["jpg", "jpeg", "png"]
)

mode = st.selectbox("Category mode", ["auto", "food", "cosmetics", "electronics", "medicines"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Preview", use_container_width=True)

    if st.button("Run Compliance Check", type="primary"):
        active_api_key = api_key_input
        if not active_api_key:
            try:
                active_api_key = st.secrets["GOOGLE_API_KEY"]
            except Exception:
                pass

        if not active_api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        else:
            st.session_state.count += 1

            try:
                client = genai.Client(api_key=active_api_key)
                image_bytes = uploaded.getvalue()
                mime_type = uploaded.type if getattr(uploaded, "type", None) else "image/jpeg"

                with st.spinner("Analyzing product label against Legal Metrology rules using Gemini 3.6 Flash..."):
                    response = gemini_call_with_retry(client, image_bytes, mime_type)

                extracted_text = response.text or ""
                detected_category, scores = detect_category(extracted_text)
                final_category = detected_category if mode == "auto" else mode

                required_fields = RULES["base"] + RULES.get(final_category, [])
                
                present_fields = []
                missing_fields = []
                t_lower = extracted_text.lower()
                for field in required_fields:
                    if field.lower() in t_lower:
                        present_fields.append(field)
                    else:
                        missing_fields.append(field)

                compliant = len(missing_fields) == 0

                st.subheader("Compliance Analysis Report")
                st.metric("Total Scanned Products", st.session_state.count)
                st.write("**Detected Category:**", detected_category.capitalize())
                st.write("**Active Category Rule Set:**", final_category.capitalize())
                st.markdown(f"**Compliance Status:** `{'PASS ✅' if compliant else 'FAIL ❌'}`")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.success(f"Present Fields: {present_fields}")
                with col_b:
                    st.error(f"Missing Fields: {missing_fields}")

                with st.expander("View Extracted Text from Label"):
                    st.text_area("OCR / Extracted Details", extracted_text, height=200)

                st.session_state.history.append({
                    "category": final_category,
                    "compliant": compliant,
                    "missing": missing_fields,
                    "text": extracted_text[:150]
                })

            except Exception as e:
                st.error(f"Error during analysis: {e}")

    st.markdown("---")
    st.subheader("📋 Live Scan History")
    if not st.session_state.history:
        st.info("No scans performed yet in this session.")
    else:
        for i, item in enumerate(reversed(st.session_state.history), start=1):
            status = 'PASS ✅' if item['compliant'] else 'FAIL ❌'
            st.write(f"{i}. **Category:** {item['category'].capitalize()} | **Status:** {status}")
            if item["missing"]:
                st.write(f"   *Missing:* {', '.join(item['missing'])}")
