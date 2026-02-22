from ultralytics import YOLO
import cv2
import time
import smtplib
from email.message import EmailMessage
import os
import random

# -------------------------
# Settings
# -------------------------
SENDER_EMAIL = os.getenv("GMAIL_SENDER", "lamaalarfajj@gmail.com")
LOST_FOUND_EMAIL = "lama.rf53847@gmail.com"

# Set this as an Environment Variable named GMAIL_APP_PASSWORD
# PowerShell example:
# $env:GMAIL_APP_PASSWORD="your_16_char_app_password"
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

COOLDOWN_SECONDS = 4 * 60  # 4 minutes
DEVICE_CLASSES = {"cell phone", "laptop"}  # YOLO class names

# -------------------------
# Load YOLO
# -------------------------
model = YOLO("yolov8n.pt")

# -------------------------
# Email helper
# -------------------------
def send_email(found_item: str, corridor_num: int, image_frame):
    if not APP_PASSWORD:
        print("❌ GMAIL_APP_PASSWORD is not set.")
        return False

    image_path = "detected_item.jpg"
    cv2.imwrite(image_path, image_frame)

    msg = EmailMessage()
    msg["Subject"] = "Lost & Found Notification – Unattended Device Detected"
    msg["From"] = SENDER_EMAIL
    msg["To"] = LOST_FOUND_EMAIL

    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

    msg.set_content(
        f"Dear Lost & Found Department,\n\n"
        f"An unattended device has been identified by the monitoring system.\n\n"
        f"Detection Details:\n"
        f"- Item Type: {found_item}\n"
        f"- Location: Corridor {corridor_num}\n"
        f"- Detection Time: {current_time}\n\n"
        f"Please review the attached image for verification and proceed accordingly.\n\n"
        f"Sincerely,\n"
        f"AI Monitoring System"
    )

    with open(image_path, "rb") as img:
        msg.add_attachment(
            img.read(),
            maintype="image",
            subtype="jpeg",
            filename="detected_item.jpg"
        )

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)

        print(f"✅ Email sent: {found_item} | Corridor {corridor_num}")
        return True

    except Exception as e:
        print("❌ Email sending failed:", e)
        return False

# -------------------------
# Camera
# -------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("❌ Unable to open camera.")

last_email_time = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, verbose=False)
        annotated = results[0].plot()

        labels = []
        if results[0].boxes is not None:
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                labels.append(results[0].names[cls_id])

        found_person = "person" in labels
        found_devices = [obj for obj in labels if obj in DEVICE_CLASSES]
        found_device = len(found_devices) > 0

        now = time.time()
        cooldown_left = int(max(0, COOLDOWN_SECONDS - (now - last_email_time)))

        if found_device and not found_person:
            cv2.putText(
                annotated,
                "⚠️ Unattended Device Detected",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )

            if (now - last_email_time) >= COOLDOWN_SECONDS:
                item_name = found_devices[0]
                fake_corridor = random.randint(1, 20)
                sent = send_email(item_name, fake_corridor, annotated)
                if sent:
                    last_email_time = now
            else:
                cv2.putText(
                    annotated,
                    f"Email cooldown: {cooldown_left}s",
                    (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2,
                )

        cv2.imshow("YOLO Laptop Camera Scan", annotated)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    pass

cap.release()
cv2.destroyAllWindows()