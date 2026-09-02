import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
import json
import re

st.set_page_config(page_title="Smart Legal Metrology Checker", layout="centered")

RULES = {
    "base": ["product name", "manufacturer", "net quantity", "mfg date or import date", "mrp"],
    "food": ["ingredients", "best before"],
    "cosmetics": ["batch no", "expiry date"],
    "electronics": ["model number", "manufacturer details"],
    "medicines": ["batch no", "expiry date", "license no"]
}

def detect_category(text):
    t = text.lower()
    scores = {
        "food": sum(k in t for k in ["ingredients", "nutrition", "sugar", "salt", "packaged food"]),
        "cosmetics": sum(k in t for k in ["cream", "lotion", "shampoo", "soap", "cosmetic"]),
        "electronics": sum(k in t for k in ["voltage", "warranty", "model", "charger", "electronics"]),
        "medicines": sum(k in t for k in ["tablet", "capsule", "syrup", "dosage", "medicine"])
    }
    return max(scores, key=scores.get), scores

def field_present(text, keywords):
    t = text.lower()
    return any(k in t for k in keywords)

if "count" not in st.session_state:
    st.session_state.count = 0
if "history" not in st.session_state:
    st.session_state.history = []

st.title("Smart Legal Metrology Checker")
st.caption("Capture product label and check mandatory declarations")

uploaded = st.camera_input("Take product photo") or st.file_uploader("Upload product image", type=["jpg", "jpeg", "png"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Preview", use_container_width=True)

    manual_category = st.selectbox("Select category", ["auto", "food", "cosmetics", "electronics", "medicines"])

    if st.button("Check Compliance"):
        st.session_state.count += 1

        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
        image_bytes = uploaded.getvalue()

        prompt = """
        Read the product label carefully.
        Return ONLY plain text with all visible label text.
        Do not explain.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            ]
        )

        extracted_text = response.text or ""
        detected_category, scores = detect_category(extracted_text)

        final_category = detected_category if manual_category == "auto" else manual_category
        required = RULES["base"] + RULES[final_category]

        present = [f for f in required if field_present(extracted_text, [f])]
        missing = [f for f in required if f not in present]
        compliant = len(missing) == 0

        result = {
            "category": final_category,
            "detected_text": extracted_text,
            "present_fields": present,
            "missing_fields": missing,
            "compliant": compliant
        }

        st.subheader("Result")
        st.write("Scanned products:", st.session_state.count)
        st.write("Detected category:", final_category)
        st.write("Compliance:", "YES" if compliant else "NO")
        st.write("Present fields:", present)
        st.write("Missing fields:", missing)
        st.text_area("Extracted text", extracted_text, height=250)

        st.session_state.history.append(result)

    st.subheader("Scan History")
    for i, item in enumerate(reversed(st.session_state.history), start=1):
        st.write(f"{i}. {item['category']} - {'YES' if item['compliant'] else 'NO'}")
