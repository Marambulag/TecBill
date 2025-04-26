import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import pymysql
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import time

# Configuration for the buzzer
BUZZER_PIN = 17

# Setup GPIO for the buzzer
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

buzzer = GPIO.PWM(BUZZER_PIN, 440)  # Initial frequency for PWM

def bell_sound():
    """Produce a bell-style sound."""
    buzzer.start(50)  # 50% duty cycle
    buzzer.ChangeFrequency(1200)  # High tone
    time.sleep(0.15)  # Brief tone
    buzzer.stop()
    time.sleep(0.05)  # Short pause
    buzzer.start(50)
    buzzer.ChangeFrequency(800)  # Low tone
    time.sleep(0.2)  # Slightly longer tone
    buzzer.stop()

# Initialize camera with original resolution settings
def initialize_camera():
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 480)
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

# Initialize the database connection
def initialize_database_connection():
    connection = pymysql.connect(
        host="10.43.127.176",
        user="root",
        password="1234",
        database="autobill",
        cursorclass=pymysql.cursors.DictCursor  # To get results as dictionaries
    )
    return connection

# Add product to active cart and reduce stock in the database
def add_product_to_cart_and_update_stock(connection, product_name):
    with connection.cursor() as cursor:
        # Search for the active cart
        cursor.execute("SELECT ID FROM carrito WHERE estado = 'activo' ORDER BY ID DESC LIMIT 1")
        active_cart = cursor.fetchone()

        if not active_cart:
            print("No active cart found. Ensure a cart with estado='activo' exists.")
            return

        active_cart_id = active_cart['ID']

        # Search for the product in the database
        cursor.execute("SELECT ID, cantidad FROM producto WHERE nombre = %s", (product_name,))
        product = cursor.fetchone()

        if not product:
            print(f"Product '{product_name}' not found in the database.")
            return

        product_id, stock = product['ID'], product['cantidad']

        if stock > 0:
            # Add product to the active cart
            cursor.execute("""
                INSERT INTO carrito_producto (id_carrito, id_producto, cantidad)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE cantidad = cantidad + 1
            """, (active_cart_id, product_id))

            # Reduce product stock
            cursor.execute("UPDATE producto SET cantidad = cantidad - 1 WHERE ID = %s", (product_id,))
            connection.commit()

            print(f"Added '{product_name}' to cart ID {active_cart_id}. Remaining stock: {stock - 1}.")
            
            # Play bell sound
            bell_sound()
        else:
            print(f"Product '{product_name}' is out of stock.")

# Track detections and add products if detected for 3 seconds
def track_and_add_products(detections, class_list, detection_times, db_connection):
    current_time = datetime.now()
    time_threshold = timedelta(seconds=3)  # Require 3 seconds of detection

    for detection in detections:
        class_index = int(detection[5])
        class_name = class_list[class_index]

        # Check if the class is already being tracked
        if class_name not in detection_times:
            # Start tracking with the current timestamp
            detection_times[class_name] = current_time
        else:
            # Check if the object has been detected for the threshold time
            elapsed_time = current_time - detection_times[class_name]
            if elapsed_time >= time_threshold:
                # Add product to the cart
                add_product_to_cart_and_update_stock(db_connection, class_name)
                # Reset the detection timer for this product
                del detection_times[class_name]

    # Cleanup for products no longer detected
    detected_classes = {class_list[int(d[5])] for d in detections}
    for class_name in list(detection_times.keys()):
        if class_name not in detected_classes:
            del detection_times[class_name]

# Main function to run object detection
def main():
    print("Initializing camera...")
    picam2 = initialize_camera()
    print("Camera initialized.")

    model, class_list = load_model_and_classes('best.pt', 'coco1.txt')
    print("Model and classes loaded.")

    db_connection = initialize_database_connection()
    print("Database connection initialized.")

    detection_times = {}

    try:
        while True:
            # Capture frame
            frame = picam2.capture_array()

            # Process frame and get detections
            results = model.predict(frame, stream=False)
            detections = results[0].boxes.data if results and results[0].boxes else []

            # Track and add products
            if detections is not None:
                track_and_add_products(detections, class_list, detection_times, db_connection)

            # Draw bounding boxes and labels
            for detection in detections:
                x1, y1, x2, y2, _, class_index = map(int, detection[:6])
                class_name = class_list[class_index]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Display the frame
            cv2.imshow("Camera", frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) == ord('q'):
                break
    finally:
        # Cleanup
        picam2.close()
        cv2.destroyAllWindows()
        db_connection.close()
        GPIO.cleanup()
        print("Camera, database connection, GPIO, and windows closed.")

if __name__ == "__main__":
    main()





