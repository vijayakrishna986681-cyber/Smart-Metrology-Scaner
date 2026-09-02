from datetime import datetime
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import pytesseract
import streamlit as st
from streamlit_mic_recorder import mic_recorder  # వాయిస్ రికార్డర్ కోసం

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

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

# Sidebar Controls + Voice Assistant (Stylish Google-Style UI)
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

# Fallback or manual category override
demo_category_override = st.sidebar.selectbox(
    "Or Select Product Type Manually:",
    [
        "Live Camera Scan / Auto-Detect",
        "Cosmetics / Personal Care",
        "Electronics / Gadgets (Mobiles, Buds)",
        "Food & Bakery Item",
        "Textiles / Garments (Shirts)",
        "Medicine / Pharmaceutical",
    ],
)

if audio_data:
  st.sidebar.success("audio captured successfully!")

st.markdown("---")

# Camera Power Control Switch
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


def contains_any(text, keywords):
  return any(k.lower() in text for k in keywords)


if active_image is not None:
  file_name = getattr(active_image, "name", "captured_product.jpg").lower()

  col_img1, col_img2 = st.columns([1, 2])
  with col_img1:
    st.image(active_image, caption="Scanned Product Label", width='stretch')

  extracted_text = ""
  with col_img2:
    with st.spinner("🔍 Analyzing Product & Validating Legal Metrology Rules..."):
      try:
        img = Image.open(active_image).convert("RGB")
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        extracted_text = pytesseract.image_to_string(gray)
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
      # 1. Cosmetics Check First (to prevent face creams from going to medicine)
      if contains_any(
          file_name,
          ["soap", "cream", "shampoo", "paste", "lotion", "oil", "face"],
      ) or contains_any(
          text_lower,
          [
              "face cream",
              "glowderma",
              "net quantity",
              "mfg. date",
              "use before",
              "cosmetics",
              "ingredients:",
              "aqua",
              "glycerin",
              "bright glow",
          ],
      ):
        detected_category = "Cosmetics / Personal Care"

      # 2. Electronics Check
      elif contains_any(
          file_name,
          [
              "buds",
              "realme",
              "t300",
              "audio",
              "boat",
              "mobile",
              "phone",
              "charger",
              "electronic",
          ],
      ) or contains_any(
          text_lower,
          ["realme", "buds", "t300", "bluetooth", "model", "input", "origin"],
      ):
        detected_category = "Electronics / Gadgets (Mobiles, Buds)"

      # 3. Food Check
      elif contains_any(
          file_name, ["nutri", "britannia", "food", "biscuit", "snack"]
      ) or contains_any(text_lower, ["fssai", "best before", "bakery"]):
        detected_category = "Food & Bakery Item"

      # 4. Textiles Check
      elif contains_any(
          file_name, ["shirt", "cloth", "garment", "textile", "pant"]
      ) or contains_any(text_lower, ["size", "dimensions", "wash care"]):
        detected_category = "Textiles / Garments (Shirts)"

      # 5. Medicine Check
      elif contains_any(
          file_name, ["med", "tablet", "capsule", "syrup", "pharma"]
      ) or contains_any(
          text_lower,
          ["batch no", "b.no", "mfg.dt", "exp.dt", "capsules", "tablets"],
      ):
        detected_category = "Medicine / Pharmaceutical"

      else:
        detected_category = "Cosmetics / Personal Care"

    st.markdown(f"### 🏷️ Detected Category: `{detected_category}`")

  st.markdown("---")
  st.subheader(
      f"📊 Legal Metrology Compliance Validation Report ({detected_category}):"
  )

  c1, c2, c3, c4 = st.columns(4)

  mrp_status = "N/A"
  qty_status = "N/A"
  extra_rule1 = "N/A"
  extra_rule2 = "N/A"

  if detected_category == "Cosmetics / Personal Care":
    mrp_status = (
        "✅ PASS" if contains_any(text_lower, ["mrp", "rs", "₹", "price"]) else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if contains_any(text_lower, ["net quantity", "g", "ml", "qty"])
        else "❌ FAIL (Net Quantity Missing)"
    )
    extra_rule1 = (
        "✅ PASS"
        if contains_any(text_lower, ["mfg", "mfg. date", "manufacturing"])
        else "❌ FAIL (Mfg Date Missing)"
    )
    extra_rule2 = (
        "✅ PASS"
        if contains_any(
            text_lower,
            ["marketed by", "manufactured by", "care", "use before"],
        )
        else "❌ FAIL (Maker Details Missing)"
    )

    with c1:
      st.metric("MRP Declaration", mrp_status)
    with c2:
      st.metric("Net Quantity", qty_status)
    with c3:
      st.metric("Manufacturing Date", extra_rule1)
    with c4:
      st.metric("Manufacturer Details", extra_rule2)

  elif detected_category == "Electronics / Gadgets (Mobiles, Buds)":
    mrp_status = (
        "✅ PASS"
        if contains_any(text_lower, ["mrp", "rs", "₹", "price", "12v", "5v"])
        else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if contains_any(text_lower, ["net quantity", "1 n", "qty", "units"])
        else "❌ FAIL (Net Qty/Units Missing)"
    )
    extra_rule1 = (
        "✅ PASS"
        if contains_any(
            text_lower,
            [
                "country of origin",
                "origin",
                "imported by",
                "manufactured",
                "made in",
            ],
        )
        else "❌ FAIL (Country of Origin Missing)"
    )
    extra_rule2 = (
        "✅ PASS"
        if contains_any(
            text_lower,
            ["importer", "manufacturer", "customer care", "packer"],
        )
        else "❌ FAIL (Importer/Maker/Customer Care Missing)"
    )

    with c1:
      st.metric("MRP Declaration", mrp_status)
    with c2:
      st.metric("Net Quantity / Units", qty_status)
    with c3:
      st.metric("Country of Origin", extra_rule1)
    with c4:
      st.metric("Importer & Customer Care", extra_rule2)

  elif detected_category == "Food & Bakery Item":
    mrp_status = (
        "✅ PASS" if contains_any(text_lower, ["mrp", "rs", "₹", "price"]) else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if contains_any(text_lower, ["net", "g", "kg", "ml", "qty"])
        else "❌ FAIL"
    )
    extra_rule1 = (
        "✅ PASS"
        if contains_any(
            text_lower, ["expiry", "best before", "use by", "mfg", "pkd"]
        )
        else "❌ FAIL (Expiry Missing)"
    )
    extra_rule2 = (
        "✅ PASS"
        if contains_any(text_lower, ["fssai", "ingredients", "lic"])
        else "❌ FAIL (FSSAI/Ingredients Missing)"
    )

    with c1:
      st.metric("MRP Declaration", mrp_status)
    with c2:
      st.metric("Net Quantity", qty_status)
    with c3:
      st.metric("Expiry / Best Before", extra_rule1)
    with c4:
      st.metric("FSSAI & Ingredients", extra_rule2)

  elif detected_category == "Textiles / Garments (Shirts)":
    mrp_status = (
        "✅ PASS" if contains_any(text_lower, ["mrp", "price", "rs", "₹"]) else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if contains_any(text_lower, ["size", "dimensions", "cm", "inch"])
        else "❌ FAIL (Size Missing)"
    )
    extra_rule1 = (
        "✅ PASS"
        if contains_any(text_lower, ["month", "year", "mfg", "pkd"])
        else "❌ FAIL (Mfg Date Missing)"
    )
    extra_rule2 = (
        "✅ PASS"
        if contains_any(text_lower, ["packer", "manufacturer", "marketed"])
        else "❌ FAIL (Maker Details Missing)"
    )

    with c1:
      st.metric("MRP Declaration", mrp_status)
    with c2:
      st.metric("Size & Dimensions", qty_status)
    with c3:
      st.metric("Month & Year of Mfg", extra_rule1)
    with c4:
      st.metric("Packer Details", extra_rule2)

  elif detected_category == "Medicine / Pharmaceutical":
    mrp_status = (
        "✅ PASS" if contains_any(text_lower, ["mrp", "rs", "₹"]) else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if contains_any(text_lower, ["batch", "b-", "b.no"])
        else "❌ FAIL (Batch No Missing)"
    )
    extra_rule1 = (
        "✅ PASS"
        if contains_any(text_lower, ["mfg", "manufacturing"])
        else "❌ FAIL (Mfg Date Missing)"
    )
    extra_rule2 = (
        "✅ PASS"
        if contains_any(text_lower, ["expiry", "exp", "use before"])
        else "❌ FAIL (Expiry Date Missing)"
    )

    with c1:
      st.metric("MRP Declaration", mrp_status)
    with c2:
      st.metric("Batch Number", qty_status)
    with c3:
      st.metric("Manufacturing Date", extra_rule1)
    with c4:
      st.metric("Expiry Date (Mandatory)", extra_rule2)

  else:
    mrp_status = (
        "✅ PASS" if contains_any(text_lower, ["mrp", "rs", "₹"]) else "❌ FAIL"
    )
    qty_status = (
        "✅ PASS"
        if contains_any(text_lower, ["net", "ml", "weight", "g"])
        else "❌ FAIL"
    )
    extra_rule1 = (
        "✅ PASS"
        if contains_any(text_lower, ["packer", "manufacturer", "mfg", "marketed"])
        else "❌ FAIL (Maker Details Missing)"
    )

    c_gen1, c_gen2, c_gen3 = st.columns(3)
    with c_gen1:
      st.metric("MRP Declaration", mrp_status)
    with c_gen2:
      st.metric("Net Quantity / Content", qty_status)
    with c_gen3:
      st.metric("Packer / Manufacturer", extra_rule1)

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
  st.dataframe(df_history, width='stretch')
else:
  st.info(
      "No scans recorded yet. Use the camera scanner above to start scanning"
      " products."
  )
