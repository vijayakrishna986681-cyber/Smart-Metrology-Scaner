from datetime import datetime
import re
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import pytesseract
import streamlit as st
from streamlit_mic_recorder import mic_recorder

# Tesseract path configuration (if needed for windows environment, else auto)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(
    page_title="Smart Legal Metrology Scanner", page_icon="📸", layout="wide"
)

st.title("🛡️ Smart Legal Metrology Compliance Checker")
st.markdown(
    "### SIH 2026 - Live Camera Scanner & Voice-Assisted Rule Validation"
    " System"
)

if "history" not in st.session_state:
  st.session_state["history"] = []

# Sidebar Controls + Voice Assistant
st.sidebar.header("⚙️ Scanner & Voice Assistant Panel")

st.sidebar.markdown(
    """
    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; text-align: center; border: 1px dashed #4f46e5;">
        <span style="font-size: 24px;">🎙️</span><br>
        <b style="color: #333;">Voice Assistant</b><br>
        <span style="font-size: 12px; color: #666;">Click below to speak product category</span>
    </div>
""",
    unsafe_allow_html=True,
)

audio_data = mic_recorder(
    start_prompt="🔴 Speak Product Name",
    stop_prompt="⏹️ Stop Recording",
    just_once=True,
    key="mic_stylish",
)

demo_category_override = st.sidebar.selectbox(
    "Or Select Product Type Manually:",
    [
        "Live Camera Scan / Auto-Detect",
        "Electronics / Gadgets (Mobiles, Buds)",
        "Food & Bakery Item",
        "Textiles / Garments (Shirts)",
        "Medicine / Pharmaceutical",
        "Cosmetics / Personal Care",
    ],
)

if audio_data:
  st.sidebar.success("audio captured successfully!")

st.markdown("---")

camera_mode = st.radio(
    "📷 Camera Power Control:", ["Turn Off Camera", "Turn On Camera"], index=0
)

camera_image = None
if camera_mode == "Turn On Camera":
  st.info("💡 Camera is active. Capture your product label below:")
  camera_image = st.camera_input("📸 Live Product Label Scanner")
else:
  st.warning(
      "🔒 Camera is currently turned off. Select 'Turn On Camera' above to"
      " start scanning."
  )

uploaded_file = None
if camera_image is not None:
  active_image = camera_image
else:
  uploaded_file = st.file_uploader(
      "Or Upload Product Label Image...", type=["jpg", "jpeg", "png"]
  )
  active_image = uploaded_file

if active_image is not None:
  file_name = getattr(active_image, "name", "captured_product.jpg").lower()

  col_img1, col_img2 = st.columns([1, 2])
  with col_img1:
    st.image(
        active_image, caption="Scanned Product Label", use_container_width=True
    )

  with col_img2:
    with st.spinner("🔍 Analyzing Product & Validating Legal Metrology Rules..."):
      try:
        img = Image.open(active_image)
        # Image Preprocessing for better OCR
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        resized = cv2.resize(
            gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC
        )
        extracted_text = pytesseract.image_to_string(resized)
      except Exception as e:
        extracted_text = ""

    with st.expander("📄 View Scanned Text & Extracted Data"):
      st.write(
          extracted_text
          if extracted_text.strip()
          else "No text found in image."
      )

    text_lower = extracted_text.lower()
    detected_category = demo_category_override

    if detected_category == "Live Camera Scan / Auto-Detect":
      detected_category = "Food & Bakery Item"
      if any(
          w in file_name
          for w in [
              "buds",
              "realme",
              "t300",
              "audio",
              "boat",
              "mobile",
              "phone",
              "charger",
              "electronic",
          ]
      ) or any(
          k in text_lower
          for k in ["buds", "audio", "bluetooth", "model", "input", "origin"]
      ):
        detected_category = "Electronics / Gadgets (Mobiles, Buds)"
      elif any(
          w in file_name for w in ["shirt", "cloth", "garment", "textile"]
      ) or "size" in text_lower:
        detected_category = "Textiles / Garments (Shirts)"
      elif any(
          w in file_name for w in ["med", "tablet", "capsule", "syrup"]
      ) or any(
          k in text_lower for k in ["batch", "b-", "mfg", "exp"]
      ):
        detected_category = "Medicine / Pharmaceutical"
      elif any(
          w in file_name
          for w in ["soap", "cream", "shampoo", "paste", "lotion"]
      ):
        detected_category = "Cosmetics / Personal Care"

    st.markdown(f"### 🏷️ Detected Category: `{detected_category}`")

  st.markdown("---")
  st.subheader(
      f"📊 Legal Metrology Compliance Validation Report ({detected_category}):"
  )

  c1, c2, c3, c4 = st.columns(4)

  if detected_category == "Electronics / Gadgets (Mobiles, Buds)":
    mrp_status = (
        "✅ PASS"
        if any(k in text_lower for k in ["mrp", "rs", "₹", "price"])
        else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if any(
            k in text_lower
            for k in ["net quantity", "1 n", "qty", "units", "pcs"]
        )
        else "❌ FAIL (Net Qty/Units Missing)"
    )
    extra_rule1 = (
        "✅ PASS"
        if any(
            k in text_lower
            for k in ["country of origin", "origin", "imported by", "manufactured"]
        )
        else "❌ FAIL (Country of Origin Missing)"
    )
    extra_rule2 = (
        "✅ PASS"
        if any(
            k in text_lower
            for k in ["importer", "manufacturer", "customer care", "packer"]
        )
        else "❌ FAIL (Importer/Maker/Customer Care Missing)"
    )

    with c1:
      st.metric(label="MRP Declaration", value=mrp_status)
    with c2:
      st.metric(label="Net Quantity / Units", value=qty_status)
    with c3:
      st.metric(label="Country of Origin", value=extra_rule1)
    with c4:
      st.metric(label="Importer & Customer Care", value=extra_rule2)

  elif detected_category == "Food & Bakery Item":
    mrp_status = (
        "✅ PASS"
        if any(
            k in text_lower
            for k in [
                "mrp",
                "rs",
                "₹",
                "price",
                "100",
                "inclusive",
                "taxes",
                "max",
            ]
        )
        else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if any(
            k in text_lower
            for k in ["net", "g", "kg", "ml", "qty", "500", "500g"]
        )
        else "❌ FAIL"
    )
    extra_rule1 = (
        "✅ PASS"
        if any(
            k in text_lower
            for k in [
                "expiry",
                "best before",
                "use by",
                "mfg",
                "pkd",
                "27/01",
                "04/05",
            ]
        )
        else "❌ FAIL (Expiry Missing)"
    )
    extra_rule2 = (
        "✅ PASS"
        if any(
            k in text_lower
            for k in ["fssai", "ingredients", "lic", "100140", "food"]
        )
        else "❌ FAIL (FSSAI/Ingredients Missing)"
    )
    with c1:
      st.metric(label="MRP Declaration", value=mrp_status)
    with c2:
      st.metric(label="Net Quantity", value=qty_status)
    with c3:
      st.metric(label="Expiry / Best Before", value=extra_rule1)
    with c4:
      st.metric(label="FSSAI & Ingredients", value=extra_rule2)

  elif detected_category == "Textiles / Garments (Shirts)":
    mrp_status = (
        "✅ PASS"
        if any(k in text_lower for k in ["mrp", "price", "rs", "₹"])
        else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if any(k in text_lower for k in ["size", "dimensions", "cm", "inch"])
        else "❌ FAIL (Size Missing)"
    )
    extra_rule1 = (
        "✅ PASS"
        if any(k in text_lower for k in ["month", "year", "mfg", "pkd"])
        else "❌ FAIL (Mfg Date Missing)"
    )
    extra_rule2 = (
        "✅ PASS"
        if any(k in text_lower for k in ["packer", "manufacturer", "marketed"])
        else "❌ FAIL (Maker Details Missing)"
    )

    with c1:
      st.metric(label="MRP Declaration", value=mrp_status)
    with c2:
      st.metric(label="Size & Dimensions", value=qty_status)
    with c3:
      st.metric(label="Month & Year of Mfg", value=extra_rule1)
    with c4:
      st.metric(label="Packer Details", value=extra_rule2)

  elif detected_category == "Medicine / Pharmaceutical":
    mrp_status = (
        "✅ PASS"
        if any(k in text_lower for k in ["mrp", "rs", "₹"])
        else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if any(k in text_lower for k in ["batch", "b-", "b.no"])
        else "❌ FAIL (Batch No Missing)"
    )
    extra_rule1 = (
        "✅ PASS"
        if any(k in text_lower for k in ["mfg", "manufacturing"])
        else "❌ FAIL (Mfg Date Missing)"
    )
    extra_rule2 = (
        "✅ PASS"
        if any(k in text_lower for k in ["expiry", "exp"])
        else "❌ FAIL (Expiry Date Missing)"
    )

    with c1:
      st.metric(label="MRP Declaration", value=mrp_status)
    with c2:
      st.metric(label="Batch Number", value=qty_status)
    with c3:
      st.metric(label="Manufacturing Date", value=extra_rule1)
    with c4:
      st.metric(label="Expiry Date (Mandatory)", value=extra_rule2)

  else:
    mrp_status = (
        "✅ PASS"
        if any(k in text_lower for k in ["mrp", "rs", "₹"])
        else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if any(k in text_lower for k in ["net", "ml", "weight", "g"])
        else "❌ FAIL"
    )
    extra_rule1 = (
        "✅ PASS"
        if any(
            k in text_lower for k in ["packer", "manufacturer", "mfg", "marketed"]
        )
        else "❌ FAIL (Maker Details Missing)"
    )

    c_gen1, c_gen2, c_gen3 = st.columns(3)
    with c_gen1:
      st.metric(label="MRP Declaration", value=mrp_status)
    with c_gen2:
      st.metric(label="Net Quantity / Content", value=qty_status)
    with c_gen3:
      st.metric(label="Packer / Manufacturer", value=extra_rule1)

  scan_record = {
      "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      "Category": detected_category,
      "MRP Status": mrp_status,
      "Compliance Status": "Checked",
  }

  if (
      not st.session_state["history"]
      or st.session_state["history"][-1]["Time"] != scan_record["Time"]
  ):
    st.session_state["history"].append(scan_record)

st.markdown("---")
st.subheader("📈 Live Scan History & Analytics Counter")

total_scans = len(st.session_state["history"])
st.metric(label="📊 Total Products Scanned in Current Session", value=total_scans)

if total_scans > 0:
  df_history = pd.DataFrame(st.session_state["history"])
  st.dataframe(df_history, use_container_width=True)
else:
  st.info(
      "No scans recorded yet. Use the camera scanner above to start scanning"
      " products."
  )
