from djitellopy import Tello
from ultralytics import YOLO
import cv2
import time
import smtplib
from email.message import EmailMessage
import os
import random


# -------------------------
# Settings (CUSTOMIZE ME)
# -------------------------

# NOTE: Do NOT hardcode real emails in public repos.
SENDER_EMAIL = os.getenv("GMAIL_SENDER", "your_sender@gmail.com")
LOST_FOUND_EMAIL = os.getenv("LOST_FOUND_EMAIL", "receiver@example.com")

# Gmail App Password as env var
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

COOLDOWN_SECONDS = 4 * 60  # 4 minutes
DEVICE_CLASSES = {"cell phone", "laptop"}

MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")

# Where to save the screenshot before attaching (customize if needed)
SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", ".")
SCREENSHOT_FILENAME = os.getenv("SCREENSHOT_FILENAME", "detected_item.jpg")


# -------------------------
# Load YOLO
# -------------------------
model = YOLO(MODEL_PATH)


# -------------------------
# Helper: Corridor / Location ID
# -------------------------
def get_corridor_id() -> int:
    """
    CUSTOMIZE THIS.
    Demo only: returns a random corridor number.

    Replace with a real method:
    - env var CORRIDOR_ID
    - route step -> corridor mapping
    - markers (ArUco/AprilTag)
    - indoor localization
    """
    # Example if you want fixed corridor from env:
    # fixed = os.getenv("CORRIDOR_ID")
    # if fixed and fixed.isdigit():
    #     return int(fixed)

    return random.randint(1, 20)


# -------------------------
# Email helper (with screenshot attachment)
# -------------------------
def send_email(found_item: str, corridor_num: int, image_frame) -> bool:
    """
    Sends an email with an attached screenshot (annotated frame).

    image_frame: typically 'annotated' returned from results[0].plot()
    """
    if not APP_PASSWORD:
        print("❌ GMAIL_APP_PASSWORD is not set. Please set it as an environment variable.")
        return False

    # Save screenshot locally
    image_path = os.path.join(SCREENSHOT_DIR, SCREENSHOT_FILENAME)
    try:
        cv2.imwrite(image_path, image_frame)
    except Exception as e:
        print("❌ Failed to save screenshot:", e)
        return False

    msg = EmailMessage()

    # CUSTOMIZE: subject/body
    msg["Subject"] = os.getenv("ALERT_SUBJECT", "Lost & Found Alert")
    msg["From"] = SENDER_EMAIL
    msg["To"] = LOST_FOUND_EMAIL

    body = (
        f'We detected an unattended "{found_item}" in corridor/location "{corridor_num}".\n'
        f"Detected by the drone camera monitoring system.\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"See attached screenshot."
    )
    msg.set_content(body)

    # Attach screenshot
    try:
        with open(image_path, "rb") as img:
            msg.add_attachment(
                img.read(),
                maintype="image",
                subtype="jpeg",
                filename=SCREENSHOT_FILENAME,
            )
    except Exception as e:
        print("❌ Failed to attach screenshot:", e)
        return False

    # Send email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)

        print(f"✅ Email sent: {found_item} | Corridor {corridor_num} | Screenshot attached")
        return True

    except Exception as e:
        print("❌ Email sending failed:", e)
        return False


# -------------------------
# Tello Drone setup
# -------------------------
tello = Tello()
tello.connect()
tello.streamon()


# -------------------------
# Flight path (CUSTOMIZE ME)
# -------------------------
def run_flight_path(drone: Tello) -> None:
    """
    CUSTOMIZE THIS ROUTE.

    Safety notes:
    - Ensure enough space and no obstacles.
    - Consider emergency landing logic and battery checks.
    """
    drone.takeoff()
    time.sleep(2)

    # Example: move forward 100 cm
    drone.move_forward(100)
    time.sleep(1)


run_flight_path(tello)


# -------------------------
# Main loop
# -------------------------
last_email_time = 0

try:
    while True:
        frame = tello.get_frame_read().frame

        results = model.predict(frame, verbose=False)
        annotated = results[0].plot()

        # Extract detected labels
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
                corridor_id = get_corridor_id()

                sent = send_email(item_name, corridor_id, annotated)
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

        cv2.imshow("Tello YOLO Lost & Found", annotated)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

except KeyboardInterrupt:
    pass

finally:
    try:
        tello.land()
    except Exception:
        pass
    tello.streamoff()
    cv2.destroyAllWindows()
