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
    page_title="AI Smart Legal Metrology Scanner", page_icon="⚖️", layout="wide"
)

st.title("⚖️ AI Smart Legal Metrology Scanner & Voice Assistant")
st.markdown(
    "Automated compliance verification for packaged commodities under Legal Metrology Rules."
)

# Sidebar for API Key and Settings
st.sidebar.header("AI & Voice Panel")
api_key = st.sidebar.text_input(
    "Enter Gemini API Key:", type="password", help="Enter your Google Gemini API Key"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Voice Assistant")
st.sidebar.write(
    "Ask questions about Legal Metrology rules or product compliance:"
)

audio_info = mic_recorder(
    start_prompt="Start Recording",
    stop_prompt="Stop Recording",
    just_once=False,
    key="mic_recorder",
)

# Main Application Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Product Input")
    input_method = st.radio(
        "Select Input Method", ("Upload Label Image", "Live Camera Feed")
    )

    image = None
    if input_method == "Upload Label Image":
        uploaded_file = st.file_uploader(
            "Or Upload Product Label Image...", type=["jpg", "jpeg", "png"]
        )
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(
                image, caption="Scanned Product Label", use_container_width=True
            )
    else:
        st.write("Camera is active below:")
        camera_image = st.camera_input("Capture Product Label")
        if camera_image is not None:
            image = Image.open(camera_image)

with col2:
    st.subheader("Compliance Analysis Report")
    
    if st.button("Run Compliance Check", type="primary"):
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        elif image is None:
            st.error("Please provide a product label image via upload or camera.")
        else:
            try:
                # Initialize Gemini Client
                client = genai.Client(api_key=api_key)
                
                with st.spinner("Analyzing product label against Legal Metrology rules using Gemini..."):
                    prompt = """
                    You are an expert Legal Metrology Inspector. Analyze this product label image carefully and check compliance with the Legal Metrology (Packaged Commodities) Rules.
                    
                    Provide a structured report containing:
                    1. Product Name & Category
                    2. Mandatory Declarations Found (e.g., Generic Name, Net Quantity, Manufacturer Details, MRP, Month/Year of Packing, Consumer Care details).
                    3. Compliance Status (Pass/Fail) with specific observations for each declaration.
                    4. Any violations or missing declarations found.
                    """
                    
                    # Using the standard stable model for google-genai SDK
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[image, prompt]
                    )
                    
                    st.success("Analysis Complete!")
                    st.markdown(response.text)
                    
            except Exception as e:
                # Automatic fallback mechanism if primary model name needs adjustment
                try:
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model='gemini-flash',
                        contents=[image, prompt]
                    )
                    st.success("Analysis Complete!")
                    st.markdown(response.text)
                except Exception as ex:
                    st.error(f"Error communicating with Gemini AI: {ex}")

# Live Scan History Section
st.markdown("---")
st.subheader("📋 Live Scan History")
if "history" not in st.session_state:
    st.session_state.history = []

st.info("Scanned compliance reports will be logged here during your session.")
