from ultralytics import YOLO
import cv2

# Load the YOLO model
model = YOLO("models/best.pt")

# Test Image Path (Change to a sample image)
test_image = "test_image2.jpg"

# Load and process the image
results = model(test_image)

# Print detected objects
print("Detection Results:")
for result in results:
    for box in result.boxes:
        class_name = model.names[int(box.cls[0])]
        confidence = float(box.conf[0])
        print(f"Detected: {class_name}, Confidence: {confidence:.2f}")
