import serial
import cv2
import threading
import tkinter as tk
from handlers import init_globals, arduino_listener, update_frame, create_placeholder

# ===== KẾT NỐI ARDUINO & CAMERA =====
arduino = serial.Serial('COM3', 9600)
API_URL = "http://127.0.0.1:8000/scan-plate/"
cam_in = cv2.VideoCapture(0)
cam_out = cv2.VideoCapture(1)

# ===== TẠO GIAO DIỆN =====
root = tk.Tk()
root.title("BÃI ĐỖ XE THÔNG MINH")
root.configure(bg="#f0f4f7")

# ===== TIÊU ĐỀ =====
title_label = tk.Label(
    root, text="BÃI ĐỖ XE THÔNG MINH",
    font=("Arial", 20, "bold"), bg="#00aaff", fg="white", pady=12
)
title_label.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

# ===== ẢNH MẶC ĐỊNH =====
placeholder_img = create_placeholder()

# ===== CAMERA VÀO =====
frame_in = tk.LabelFrame(root, text="CAMERA VÀO", font=("Arial", 12, "bold"), padx=10, pady=10, bg="white")
frame_in.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
label_cam_in = tk.Label(frame_in, image=placeholder_img, bg="white")
label_cam_in.pack()

# ===== CAMERA RA =====
frame_out = tk.LabelFrame(root, text="CAMERA RA", font=("Arial", 12, "bold"), padx=10, pady=10, bg="white")
frame_out.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
label_cam_out = tk.Label(frame_out, image=placeholder_img, bg="white")
label_cam_out.pack()


# ===== ẢNH CHỤP XE VÀO =====
label_captured_in = tk.Label(root, image=placeholder_img, bg="white", bd=2, relief="groove")
label_captured_in.grid(row=2, column=0, pady=5)

# ===== ẢNH CHỤP XE RA =====
label_captured_out = tk.Label(root, image=placeholder_img, bg="white", bd=2, relief="groove")
label_captured_out.grid(row=2, column=1, pady=5)

# ===== BIỂN SỐ XE VÀO =====
plate_text_in = tk.StringVar()
plate_label_in = tk.Label(root, textvariable=plate_text_in, font=("Arial", 14, "bold"), fg="green", bg="#e8f5e9", relief="groove")
plate_label_in.grid(row=3, column=0, pady=5, padx=5, sticky="nsew")

# ===== BIỂN SỐ XE RA =====
plate_text_out = tk.StringVar()
plate_label_out = tk.Label(root, textvariable=plate_text_out, font=("Arial", 14, "bold"), fg="red", bg="#ffebee", relief="groove")
plate_label_out.grid(row=3, column=1, pady=5, padx=5,  sticky="nsew")

# ===== TRUYỀN BIẾN CHO handlers.py =====
init_globals(
    arduino=arduino,
    API_URL=API_URL, cam_in=cam_in, cam_out=cam_out,
    label_captured_in=label_captured_in, label_captured_out=label_captured_out,
    label_cam_in=label_cam_in, label_cam_out=label_cam_out,
    plate_text_in=plate_text_in, plate_text_out=plate_text_out, root=root
)

# ===== CHẠY THREAD & CẬP NHẬT CAMERA =====
threading.Thread(target=arduino_listener, daemon=True).start()
update_frame()

# ===== TÙY CHỈNH KÍCH THƯỚC CỘT =====
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=0)

root.geometry("1000x720")
root.mainloop()

# ===== GIẢI PHÓNG CAMERA =====
cam_in.release()
cam_out.release()
