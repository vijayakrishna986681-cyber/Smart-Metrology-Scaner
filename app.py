from datetime import datetime
import os
from google import genai
from google.genai import types
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
from streamlit_mic_recorder import mic_recorder

st.set_page_config(
    page_title="AI Smart Legal Metrology Scanner", page_icon="🛡️", layout="wide"
)

st.title("🛡️ AI-Powered Smart Legal Metrology Compliance Checker")
st.markdown(
    "### SIH 2026 - Gemini Vision AI Powered Rule Validation System"
)

if "history" not in st.session_state:
  st.session_state["history"] = []

# Sidebar for API Key & Controls
st.sidebar.header("⚙️ AI & Voice Panel")

# Gemini API Key Input (రేపు డెమోకి మీ కీ ఇక్కడ ఇవ్వొచ్చు)
api_key_input = st.sidebar.text_input(
    "Enter Gemini API Key:", type="password", help="Enter your Google Gemini API key here"
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; text-align: center; border: 1px dashed #4f46e5;">
        <span style="font-size: 24px;">🎙️</span><br>
        <b style="color: #333;">Voice Assistant</b>
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

if audio_data:
  st.sidebar.success("Audio captured successfully!")

st.markdown("---")

# Camera Power Control Switch
camera_mode = st.radio(
    "📷 Camera Power Control:", ["Turn On Camera", "Turn Off Camera"], index=0
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
  col_img1, col_img2 = st.columns([1, 2])
  with col_img1:
    st.image(active_image, caption="Scanned Product Label", width="stretch")

  with col_img2:
    if not api_key_input:
      st.error("⚠️ దయచేసి సైడ్‌బార్‌లో మీ Gemini API Key ని ఎంటర్ చేయండి!")
    else:
      with st.spinner("🤖 Gemini AI is analyzing the product label & legal compliance..."):
        try:
          # Initialize Gemini Client
          client = genai.Client(api_key=api_key_input)
          
          image_pil = Image.open(active_image)

          prompt = """
          You are an expert Legal Metrology Compliance Inspector (Packaged Commodities Rules, 2011 in India).
          Analyze the given product label image carefully.
          
          1. Detect the product category strictly from one of these: 
             - "Electronics / Gadgets (Mobiles, Buds)"
             - "Cosmetics / Personal Care"
             - "Food & Bakery Item"
             - "Textiles / Garments (Shirts)"
             - "Medicine / Pharmaceutical"
             - "General Product"
          
          2. Check for the mandatory declarations based on the category:
             - For Electronics: MRP, Net Quantity, Country of Origin, Customer Care / Importer details.
             - For Cosmetics: MRP, Net Quantity, Manufacturing Date, Maker/Manufacturer Details.
             - For Food: MRP, Net Quantity, Expiry / Best Before / Use By, FSSAI & Ingredients.
             - For Textiles: MRP, Size/Dimensions, Month & Year of Mfg, Packer Details.
             - For Medicine: MRP, Batch Number, Manufacturing Date, Expiry Date / Use Before.
          
          Provide the output in a clean format:
          Category: [Detected Category]
          Rule 1 Name: [Name] | Status: [PASS or FAIL]
          Rule 2 Name: [Name] | Status: [PASS or FAIL]
          Rule 3 Name: [Name] | Status: [PASS or FAIL]
          Rule 4 Name: [Name] | Status: [PASS or FAIL]
          Summary: [Short explanation of findings]
          """

          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=[image_pil, prompt]
          )
          
          ai_analysis = response.text
          
          st.success("✅ AI Analysis Completed Successfully!")
          st.markdown(ai_analysis)

        except Exception as e:
          st.error(f"Error communicating with Gemini AI: {e}")

st.markdown("---")
st.subheader("📈 Live Scan History")
total_scans = len(st.session_state["history"])
st.metric(label="📊 Total Scans", value=total_scans)
