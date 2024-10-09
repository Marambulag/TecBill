import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import csv
import os
from datetime import datetime

# Initialize camera with original resolution settings
def initialize_camera():
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 480)  # Restored original resolution
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()
    return picam2

# Load YOLO model and class list
def load_model_and_classes(model_path, class_file_path):
    model = YOLO(model_path)
    with open(class_file_path, "r") as file:
        class_list = file.read().splitlines()
    return model, class_list

# Process frame to get detection results
def process_frame(model, frame):
    frame = cv2.flip(frame, -1)
    results = model.predict(frame, stream=False)
    if results and results[0].boxes:
        return results[0].boxes.data
    return None

# Update class count in the dictionary
def update_class_count(detections, class_list, class_count):
    for detection in detections:
        class_index = int(detection[5])
        class_name = class_list[class_index]
        if class_name in class_count:
            class_count[class_name] += 1
        else:
            class_count[class_name] = 1

# Save class counts to CSV in a specified directory
def save_class_counts_to_csv(class_count, output_file):
    print(f"Attempting to save CSV at {output_file}...")  # Debugging print
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Class Name', 'Count'])  # Header
        for class_name, count in class_count.items():
            writer.writerow([class_name, count])
    print(f"CSV saved successfully to {output_file}.")

# Generate a unique CSV filename using current timestamp inside a directory
def generate_csv_filename(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)  # Create directory if it doesn't exist
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(directory, f"class_counts_{timestamp}.csv")

# Main function to run object detection and save results
def main():
    # Initialize camera and model
    print("Initializing camera...")
    picam2 = initialize_camera()
    print("Camera initialized.")

    model, class_list = load_model_and_classes('best.pt', 'coco1.txt')
    print("Model and classes loaded.")

    # Define the directory for CSV files
    csv_directory = "detections_csv"
    output_file = generate_csv_filename(csv_directory)  # Generate unique CSV filename in the folder

    # Initialize class count dictionary
    class_count = {}

    try:
        while True:
            # Capture frame
            print("Capturing frame...")
            frame = picam2.capture_array()

            # Process frame and get detections
            detections = process_frame(model, frame)
            print(f"Detections: {detections}")

            # Update class count dictionary
            if detections is not None:
                print("Updating class counts...")
                update_class_count(detections, class_list, class_count)
                print(f"Current class count: {class_count}")

            # Draw bounding boxes and labels on the frame
            if detections is not None:
                for detection in detections:
                    x1, y1, x2, y2, _, class_index = map(int, detection[:6])
                    class_name = class_list[class_index]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Display the frame
            cv2.imshow("Camera", frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) == ord('q'):
                break
    finally:
        # Save class counts to CSV when done
        print(f"Final class count: {class_count}")  # Print final class counts for debugging
        save_class_counts_to_csv(class_count, output_file)

        # Cleanup
        picam2.close()
        cv2.destroyAllWindows()
        print("Camera and windows closed.")

if __name__ == "__main__":
    main()
