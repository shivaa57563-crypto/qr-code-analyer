import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import re
import requests

st.set_page_config(page_title="QR Code Analyzer", layout="centered")

st.title("🔍 QR Code Analyzer")
st.caption("Scan • Decode • Analyze • Try not to get scammed")

# Upload
uploaded_file = st.file_uploader(
    "Upload QR Code Image",
    type=["png", "jpg", "jpeg", "bmp"]
)

# Functions
def detect_type(data):
    if re.match(r'https?://', data):
        return "Website URL"
    elif "upi://" in data.lower():
        return "UPI Payment QR"
    elif "mailto:" in data.lower():
        return "Email QR"
    elif "tel:" in data.lower():
        return "Phone Number QR"
    elif "wifi:" in data.lower():
        return "WiFi Configuration QR"
    else:
        return "Text / Other Data"


def check_safety(data):
    suspicious_words = [
        "free-money",
        "claim-now",
        "urgent-payment",
        "lottery",
        "click-now",
        "verify-account"
    ]

    for word in suspicious_words:
        if word in data.lower():
            return "⚠ Suspicious"

    if re.match(r'https?://', data):
        try:
            response = requests.get(data, timeout=5)
            if response.status_code == 200:
                return "✅ Safe (Website reachable)"
            else:
                return "⚠ Possibly Unsafe (Bad Response)"
        except:
            return "⚠ Possibly Unsafe (Site unreachable)"

    return "✅ Safe"


# Main logic
if uploaded_file:
    image = Image.open(uploaded_file)

    st.image(image, caption="Uploaded QR Code", use_column_width=True)

    if st.button("Analyze QR"):
        decoded_objects = decode(image)

        if not decoded_objects:
            st.warning("No QR Code detected.")
        else:
            st.subheader("📊 Analysis Result")

            for obj in decoded_objects:
                data = obj.data.decode("utf-8")

                st.text_area("Decoded Data", data, height=100)

                qr_type = detect_type(data)
                st.write(f"**Type:** {qr_type}")

                status = check_safety(data)
                st.write(f"**Safety:** {status}")

                st.divider()
