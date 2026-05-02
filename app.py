import io
from typing import List, Tuple, Optional

import cv2
import numpy as np
import streamlit as st
from PIL import Image


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="QR Code Analyzer",
    page_icon="◼",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# -----------------------------
# Monochrome UI
# -----------------------------
st.markdown(
    """
    <style>
        .stApp {
            background: #f4f4f4;
            color: #111111;
        }

        .main-title {
            font-size: 2.1rem;
            font-weight: 800;
            color: #111111;
            margin-bottom: 0.2rem;
        }

        .sub-title {
            font-size: 0.95rem;
            color: #444444;
            margin-bottom: 1.2rem;
        }

        .card {
            background: #ffffff;
            border: 1px solid #d9d9d9;
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            margin-bottom: 16px;
        }

        .label {
            font-size: 0.9rem;
            font-weight: 700;
            color: #222222;
            margin-bottom: 8px;
        }

        .result-box {
            background: #fafafa;
            border: 1px solid #d0d0d0;
            border-radius: 12px;
            padding: 12px 14px;
            margin-top: 10px;
            white-space: pre-wrap;
            word-break: break-word;
            color: #111111;
        }

        .muted {
            color: #666666;
            font-size: 0.9rem;
        }

        .footer {
            color: #777777;
            font-size: 0.85rem;
            text-align: center;
            margin-top: 1rem;
        }

        .stButton > button {
            background: #111111;
            color: #ffffff;
            border-radius: 10px;
            border: 1px solid #111111;
            padding: 0.55rem 1rem;
            font-weight: 600;
        }

        .stButton > button:hover {
            background: #2a2a2a;
            border-color: #2a2a2a;
            color: #ffffff;
        }

        .stDownloadButton > button {
            background: #ffffff;
            color: #111111;
            border-radius: 10px;
            border: 1px solid #111111;
            padding: 0.55rem 1rem;
            font-weight: 600;
        }

        .stDownloadButton > button:hover {
            background: #efefef;
            border-color: #111111;
            color: #111111;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Helpers
# -----------------------------
def pil_to_rgb_array(image: Image.Image) -> np.ndarray:
    """Convert a PIL image to RGB numpy array."""
    if image.mode != "RGB":
        image = image.convert("RGB")
    return np.array(image)


def draw_boxes(image_rgb: np.ndarray, points_list: List[np.ndarray]) -> np.ndarray:
    """Draw QR bounding boxes on image."""
    annotated = image_rgb.copy()

    for points in points_list:
        if points is None:
            continue

        pts = np.array(points, dtype=np.int32)

        # OpenCV may return shape (N, 1, 2) or (N, 2)
        if len(pts.shape) == 3:
            pts = pts.reshape((-1, 2))

        if pts.shape[0] >= 4:
            cv2.polylines(annotated, [pts], isClosed=True, color=(0, 0, 0), thickness=3)

            # Add small marker dots
            for x, y in pts[:4]:
                cv2.circle(annotated, (int(x), int(y)), 5, (0, 0, 0), -1)

    return annotated


def decode_qr_codes(image_rgb: np.ndarray) -> Tuple[List[str], Optional[np.ndarray]]:
    """
    Decode QR codes from an RGB image using OpenCV.

    Returns:
        (decoded_texts, points)
        decoded_texts: list of decoded strings
        points: combined points array if available, else None
    """
    detector = cv2.QRCodeDetector()

    # Try multi-code decode first
    decoded_texts: List[str] = []
    all_points: List[np.ndarray] = []

    try:
        # detectAndDecodeMulti exists in newer OpenCV versions
        retval, decoded_info, points, _ = detector.detectAndDecodeMulti(image_rgb)
        if retval and decoded_info is not None:
            for text in decoded_info:
                if text and text.strip():
                    decoded_texts.append(text.strip())
            if points is not None:
                for p in points:
                    all_points.append(p)
    except Exception:
        # Ignore and fall back to single-code detection
        pass

    if decoded_texts:
        return decoded_texts, np.array(all_points, dtype=object) if all_points else None

    # Fallback to single QR decode
    try:
        text, points, _ = detector.detectAndDecode(image_rgb)
        if text and text.strip():
            decoded_texts = [text.strip()]
            if points is not None:
                all_points.append(points)
            return decoded_texts, np.array(all_points, dtype=object) if all_points else None
    except Exception:
        pass

    return [], None


def make_download_text(decoded_texts: List[str]) -> bytes:
    content = "\n".join(
        [f"QR {i+1}: {text}" for i, text in enumerate(decoded_texts)]
    )
    return content.encode("utf-8")


# -----------------------------
# UI
# -----------------------------
st.markdown('<div class="main-title">QR Code Analyzer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Upload an image or capture a photo and decode QR codes instantly.</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="label">Input</div>', unsafe_allow_html=True)

mode = st.radio(
    "Choose input method",
    ["Upload image", "Capture from camera"],
    horizontal=True,
    label_visibility="collapsed",
)

image: Optional[Image.Image] = None

if mode == "Upload image":
    uploaded_file = st.file_uploader(
        "Upload QR image",
        type=["png", "jpg", "jpeg", "webp", "bmp"],
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
else:
    camera_file = st.camera_input("Take a photo of the QR code")
    if camera_file is not None:
        image = Image.open(camera_file)

st.markdown("</div>", unsafe_allow_html=True)

decoded_texts: List[str] = []
annotated_image = None

if image is not None:
    rgb = pil_to_rgb_array(image)
    decoded_texts, points = decode_qr_codes(rgb)

    if points is not None and len(points) > 0:
        # Draw boxes only if we have coordinates
        try:
            if isinstance(points, np.ndarray):
                pts_list = [p for p in points if p is not None]
            else:
                pts_list = []
            annotated_image = draw_boxes(rgb, pts_list)
        except Exception:
            annotated_image = rgb
    else:
        annotated_image = rgb

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Preview</div>', unsafe_allow_html=True)
    st.image(image, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="label">Decoded Result</div>', unsafe_allow_html=True)

    if decoded_texts:
        st.success(f"Found {len(decoded_texts)} QR code(s).")
        for i, text in enumerate(decoded_texts, start=1):
            st.markdown(f"**QR {i}**")
            st.code(text, language=None)
    else:
        st.warning("No QR code detected in the image.")

    if decoded_texts:
        st.download_button(
            "Download decoded text",
            data=make_download_text(decoded_texts),
            file_name="decoded_qr.txt",
            mime="text/plain",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if annotated_image is not None and decoded_texts:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="label">Annotated Image</div>', unsafe_allow_html=True)
        st.image(annotated_image, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("Upload an image or capture a photo to start scanning.")

st.markdown(
    '<div class="footer">Built with Streamlit + OpenCV</div>',
    unsafe_allow_html=True
)
