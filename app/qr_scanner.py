import cv2
import numpy as np


def extract_qr_text_from_bytes(image_bytes: bytes) -> str | None:
    if not image_bytes:
        return None

    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return None

        detector = cv2.QRCodeDetector()
        data, _bbox, _ = detector.detectAndDecode(image)
        return data if data else None
    except Exception:
        return None
