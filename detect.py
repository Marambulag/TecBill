import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import csv
import os
from datetime import datetime


def initialize_camera():
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 480) 
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()
    return picam2

def load_model_and_classes(model_path, class_file_path):
    model = YOLO(model_path)
    with open(class_file_path, "r") as file:
        class_list = file.read().splitlines()
    return model, class_list


def process_frame(model, frame):
    frame = cv2.flip(frame, -1)
    results = model.predict(frame, stream=False)
    if results and results[0].boxes:
        return results[0].boxes.data
    return None


def update_class_count(detections, class_list, class_count):
    for detection in detections:
        class_index = int(detection[5])
        class_name = class_list[class_index]
        if class_name in class_count:
            class_count[class_name] += 1
        else:
            class_count[class_name] = 1


def save_class_counts_to_csv(class_count, output_file):
    print(f"Attempting to save CSV at {output_file}...")  
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Class Name', 'Count'])  
        for class_name, count in class_count.items():
            writer.writerow([class_name, count])
    print(f"CSV saved successfully to {output_file}.")


def generate_csv_filename(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)  
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(directory, f"class_counts_{timestamp}.csv")


def main():
  
    print("Initializing camera...")
    picam2 = initialize_camera()
    print("Camera initialized.")

    model, class_list = load_model_and_classes('best.pt', 'coco1.txt')
    print("Model and classes loaded.")

 
    csv_directory = "detections_csv"
    output_file = generate_csv_filename(csv_directory) 


    class_count = {}

    try:
        while True:
            
            print("Capturing frame...")
            frame = picam2.capture_array()

          
            detections = process_frame(model, frame)
            print(f"Detections: {detections}")

           
            if detections is not None:
                print("Updating class counts...")
                update_class_count(detections, class_list, class_count)
                print(f"Current class count: {class_count}")

          
            if detections is not None:
                for detection in detections:
                    x1, y1, x2, y2, _, class_index = map(int, detection[:6])
                    class_name = class_list[class_index]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

          
            cv2.imshow("Camera", frame)

         
            if cv2.waitKey(1) == ord('q'):
                break
    finally:
      
        print(f"Final class count: {class_count}") 
        save_class_counts_to_csv(class_count, output_file)

       
        picam2.close()
        cv2.destroyAllWindows()
        print("Camera and windows closed.")

if __name__ == "__main__":
    main()
