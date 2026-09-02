import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import time
import random

st.set_page_config(page_title="Smart Legal Metrology Checker", layout="centered")

RULES = {
    "base": ["product", "manufacturer", "quantity", "mrp"],
    "food": ["ingredients", "best before"],
    "cosmetics": ["batch", "expiry"],
    "electronics": ["model", "warranty", "manufacturer"],
    "medicines": ["batch", "expiry", "license"]
}

def detect_category(text: str):
    t = text.lower()
    scores = {
        "food": sum(k in t for k in ["ingredients", "nutrition", "sugar", "salt", "packaged food"]),
        "cosmetics": sum(k in t for k in ["cream", "lotion", "shampoo", "soap", "cosmetic", "beauty"]),
        "electronics": sum(k in t for k in ["voltage", "warranty", "model", "charger", "battery", "electronics"]),
        "medicines": sum(k in t for k in ["tablet", "capsule", "syrup", "dosage", "medicine", "pharma"])
    }
    category = max(scores, key=scores.get)
    return category, scores

def field_check(text: str, required_fields):
    t = text.lower()
    present_fields = [f for f in required_fields if f.lower() in t]
    missing_fields = [f for f in required_fields if f not in present_fields]
    return present_fields, missing_fields

def gemini_call_with_retry(client, image_bytes, mime_type, max_attempts=4):
    last_err = None
    for attempt in range(max_attempts):
        try:
            return client.models.generate_content(
                model="gemini-3.7-flash",
                contents=[
                    "Extract all visible text from this product label. Return only plain text.",
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
            )
        except ClientError as e:
            last_err = e
            msg = str(e)
            if "503" not in msg and "UNAVAILABLE" not in msg and "429" not in msg:
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
    raise last_err

if "count" not in st.session_state:
    st.session_state.count = 0
if "history" not in st.session_state:
    st.session_state.history = []

st.title("Smart Legal Metrology Checker")
st.caption("Capture or upload a product label, then check compliance.")

uploaded = st.camera_input("Take product photo") or st.file_uploader(
    "Upload product image",
    type=["jpg", "jpeg", "png"]
)

mode = st.selectbox("Category mode", ["auto", "food", "cosmetics", "electronics", "medicines"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Preview", use_container_width=True)

    if st.button("Check Compliance"):
        st.session_state.count += 1

        try:
            client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
            image_bytes = uploaded.getvalue()
            mime_type = uploaded.type if getattr(uploaded, "type", None) else "image/jpeg"

            with st.spinner("Analyzing image...", show_time=True):
                response = gemini_call_with_retry(client, image_bytes, mime_type)

            extracted_text = response.text or ""
            detected_category, scores = detect_category(extracted_text)
            final_category = detected_category if mode == "auto" else mode

            required_fields = RULES["base"] + RULES[final_category]
            present_fields, missing_fields = field_check(extracted_text, required_fields)
            compliant = len(missing_fields) == 0

            st.subheader("Result")
            st.write("Scanned products:", st.session_state.count)
            st.write("Detected category:", detected_category)
            st.write("Final category:", final_category)
            st.write("Compliance:", "YES" if compliant else "NO")
            st.write("Present fields:", present_fields)
            st.write("Missing fields:", missing_fields)
            st.text_area("Extracted text", extracted_text, height=250)

            st.session_state.history.append({
                "category": final_category,
                "compliant": compliant,
                "missing": missing_fields,
                "text": extracted_text[:200]
            })

        except Exception as e:
            st.error(f"Something went wrong: {e}")

    st.subheader("Scan History")
    for i, item in enumerate(reversed(st.session_state.history), start=1):
        st.write(f"{i}. {item['category']} - {'YES' if item['compliant'] else 'NO'}")
        if item["missing"]:
            st.write("Missing:", ", ".join(item["missing"]))
