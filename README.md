# 🚁 AI Lost & Found Drone System

A **Computer Vision system** that detects unattended devices (e.g., laptop, cell phone) using **YOLOv8**, and sends an **email alert with a screenshot**.
## 📸 Email Alert Example
![Email Alert Screenshot](https://github.com/user-attachments/assets/6aee158e-b218-4051-b6b7-44fbda8b8f01)

The system supports two modes:

- 🚁 **Drone-based monitoring (Tello)**
- 💻 **Laptop camera monitoring**

---

## 📂 Project Structure

```bash
lost-found-ai/
│
├── drone_mode.py      # Tello drone + YOLO + email alert
├── laptop_mode.py     # Laptop camera + YOLO + email alert
└── README.md
```

---

## ⚙️ Requirements

Install required packages:

```bash
pip install ultralytics opencv-python djitellopy
```

---

## 🔐 Environment Variables

⚠️ Do NOT hardcode your credentials.

Set your Gmail credentials using environment variables.

### 🪟 Windows (PowerShell)

```powershell
$env:GMAIL_SENDER="your_email@gmail.com"
$env:LOST_FOUND_EMAIL="receiver@example.com"
$env:GMAIL_APP_PASSWORD="your_16_char_app_password"
```

### 🍎 macOS / 🐧 Linux

```bash
export GMAIL_SENDER="your_email@gmail.com"
export LOST_FOUND_EMAIL="receiver@example.com"
export GMAIL_APP_PASSWORD="your_16_char_app_password"
```

---

## 🚁 Run – Drone Mode

Make sure:

- Tello drone is connected
- There is enough flying space
- Battery level is sufficient

Run:

```bash
python drone_mode.py
```

⚠️ The flight path must be customized based on your environment.

---

## 💻 Run – Laptop Camera Mode

```bash
python laptop_mode.py
```

This mode uses your local webcam.

---

## 📩 Detection Logic

If a device (laptop / cell phone) is detected **AND** no person is detected:

- ⚠️ Displays a warning on screen  
- 📧 Sends an email alert  
- 🖼 Attaches a screenshot of the detection  
- ⏳ Uses a cooldown mechanism (4 minutes by default)

---

## ⚠️ Challenges & Limitations

- Limited drone camera resolution  
- Sensitive to lighting conditions  
- Short drone battery life (~10–13 min)  
- No real indoor localization (demo corridor ID)  
- YOLOv8n trade-off between speed and accuracy  
- Detection affected by angle and distance  

---

## 🔮 Future Improvements

- Indoor localization (QR / ArUco / mapping)  
- Database logging system  
- Real-time dashboard  
- Higher resolution drone camera  
