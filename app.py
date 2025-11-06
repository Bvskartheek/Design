from flask import Flask, request, render_template, redirect, url_for
from ultralytics import YOLO
import os
import uuid
import sqlite3
import cv2
import numpy as np

app = Flask(__name__)

# Set upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load YOLO model
model = YOLO("models/best.pt")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/camera")
def camera():
    return render_template("camera.html")

@app.route("/process_file", methods=["POST"])
def process_file():
    uploaded_file = request.files["file"]
    if uploaded_file.filename:
        unique_filename = f"{uuid.uuid4().hex}_{uploaded_file.filename}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        uploaded_file.save(save_path)
        return process_image(save_path, unique_filename)
    return redirect(url_for("upload"))

@app.route("/process_camera", methods=["POST"])
def process_camera():
    image_data = request.files.get("camera_image")
    if image_data and image_data.filename:
        unique_filename = f"{uuid.uuid4().hex}_camera.jpg"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        image_data.save(save_path)
        return process_image(save_path, unique_filename)
    return redirect(url_for("camera"))

def process_image(image_path, filename):
    results = model(image_path)
    detected_items = {}

    # Process YOLO results
    for result in results:
        for box in result.boxes:
            class_name = model.names[int(box.cls[0])]
            confidence = float(box.conf[0])
            if class_name not in detected_items:
                detected_items[class_name] = {"count": 1, "confidence": confidence}
            else:
                detected_items[class_name]["count"] += 1
                detected_items[class_name]["confidence"] = max(
                    detected_items[class_name]["confidence"], confidence)

    filtered_detections = [
        {"item_name": name, "count": data["count"], "confidence": f"{data['confidence'] * 100:.2f}%"}
        for name, data in detected_items.items()
    ]

    if not detected_items:
        return render_template("result.html", image_filename=filename, detected_items=[], parts=None,
                               recyclable_values=None, recycling_centers=None, reusable_parts=None,
                               resale_donate_areas=None)

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(detected_items))

    # Fetch internal parts
    try:
        cursor.execute(f"""
            SELECT id, item_name, part_name, materials_used, recyclable, reusable, recycling_process
            FROM internal_parts WHERE item_name IN ({placeholders})
        """, list(detected_items.keys()))
        parts = [{"id": row[0], "item_name": row[1], "part_name": row[2], "materials_used": row[3],
                  "recyclable": row[4], "reusable": row[5], "recycling_process": row[6]} for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching internal parts: {e}")
        parts = None

    # Fetch recyclable item values
    try:
        cursor.execute(f"""
            SELECT riv.id, riv.part_name, riv.materials_used, riv.estimated_value
            FROM recyclable_item_value riv
            WHERE riv.part_name IN (
                SELECT ip.part_name FROM internal_parts ip WHERE ip.item_name IN ({placeholders})
            )
        """, list(detected_items.keys()))
        recyclable_values = [{"id": row[0], "part_name": row[1], "materials_used": row[2], "estimated_value": row[3]}
                             for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching recyclable values: {e}")
        recyclable_values = None

    # Fetch recycling centers
    try:
        cursor.execute("SELECT * FROM recycling_centers")
        recycling_centers = [{"location": row[1], "center_name": row[2], "address": row[3], "contact": row[4],
                              "working_hours": row[5], "website": row[6]} for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching recycling centers: {e}")
        recycling_centers = None

    # Fetch reusable parts
    try:
        cursor.execute(f"""
            SELECT rp.id, rp.part_name, rp.reuse_potential, rp.estimated_value
            FROM reusable_parts rp
            WHERE rp.part_name IN (
                SELECT ip.part_name FROM internal_parts ip WHERE ip.item_name IN ({placeholders})
            )
        """, list(detected_items.keys()))
        reusable_parts = [{"id": row[0], "part_name": row[1], "reuse_potential": row[2], "estimated_value": row[3]}
                          for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching reusable parts: {e}")
        reusable_parts = None

    # Fetch resale/donate areas
    try:
        cursor.execute("SELECT * FROM resale_donate_areas")
        resale_donate_areas = [{"location": row[1], "center_name": row[2], "address": row[3], "contact": row[4],
                                 "working_hours": row[5], "website": row[6]} for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching resale/donate areas: {e}")
        resale_donate_areas = None

    conn.close()

    return render_template("result.html", image_filename=filename, detected_items=filtered_detections,
                           parts=parts if parts else None, recyclable_values=recyclable_values,
                           recycling_centers=recycling_centers, reusable_parts=reusable_parts if reusable_parts else None,
                           resale_donate_areas=resale_donate_areas)

if __name__ == "__main__":
    app.run(debug=True)