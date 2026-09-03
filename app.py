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

# Sidebar for API Key configuration (Optional fallback if secrets are not set)
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("Enter Gemini API Key (Optional):", type="password", help="If left empty, app will use default multi-keys from secrets")

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

def gemini_call_with_fallback(image_bytes, mime_type, manual_key):
    """
    ఒకటికి మించి API కీలను హ్యాండిల్ చేయడానికి మరియు 429 కోటా ఎర్రర్ వస్తే 
    ఆటోమేటిక్‌గా వేరే కీకి మళ్లేలా రాసిన ఫాల్‌బ్యాక్ ఫంక్షన్.
    """
    # 1. యూజర్ మ్యాన్యువల్‌గా ఇస్తే అది ముందు తీసుకుంటుంది
    api_keys_list = []
    if manual_key:
        api_keys_list.append(manual_key)
    
    # 2. స్ట్రీమ్‌లిట్ సీక్రెట్స్ నుండి మల్టీ కీలను యాడ్ చేయడం
    try:
        if "API_KEYS" in st.secrets:
            for k in st.secrets["API_KEYS"]:
                if k not in api_keys_list:
                    api_keys_list.append(k)
        elif "GOOGLE_API_KEY" in st.secrets:
            if st.secrets["GOOGLE_API_KEY"] not in api_keys_list:
                api_keys_list.append(st.secrets["GOOGLE_API_KEY"])
    except Exception:
        pass

    if not api_keys_list:
        raise Exception("దశలవారీగా ఉపయోగించడానికి ఎలాంటి API కీలు కనుగొనబడలేదు. దయచేసి secrets లేదా sidebar లో ఎంటర్ చేయండి.")

    last_err = None
    # 3. ప్రతి కీని లూప్ ద్వారా చెక్ చేస్తూ పోతుంది
    for api_key in api_keys_list:
        for attempt in range(2): # ప్రతి కీకి 2 ప్రయత్నాలు
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[
                        "Analyze this product label image thoroughly. Extract all visible text, declarations, MRP, net quantity, manufacturer details, and category-specific details accurately.",
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    ],
                )
                return response # సక్సెస్ అయితే రెస్పాన్స్ రిటర్న్ చేస్తుంది
            except Exception as e:
                last_err = e
                msg = str(e)
                # కోటా లిమిట్ (429) లేదా సర్వర్ బిజీ ఉంటే తర్వాతి కీకి వెళ్తుంది
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "503" in msg or "UNAVAILABLE" in msg:
                    time.sleep(1)
                    break # తర్వాతి కీకి స్విచ్ అవుతుంది
                else:
                    raise e # వేరే ఎర్రర్ వస్తే ఇక్కడే ఆగిపోతుంది

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
        st.session_state.count += 1

        try:
            image_bytes = uploaded.getvalue()
            mime_type = uploaded.type if getattr(uploaded, "type", None) else "image/jpeg"

            with st.spinner("Analyzing product label against Legal Metrology rules using Gemini 3.6 Flash..."):
                # ఫాల్‌బ్యాక్ ఫంక్షన్‌ని కాల్ చేయడం
                response = gemini_call_with_fallback(image_bytes, mime_type, api_key_input)

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
