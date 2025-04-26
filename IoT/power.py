import RPi.GPIO as GPIO
import time
import subprocess  # To run the second script

# GPIO mode set to BCM
GPIO.setmode(GPIO.BCM)

# Disable warnings
GPIO.setwarnings(False)

# Define GPIO pins
TRIG = 23  # Trigger pin for ultrasonic sensor
ECHO = 24  # Echo pin for ultrasonic sensor
LED_PIN = 27  # Pin for the LED

# Set up GPIO pins
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)  # Set the LED pin as an output

# Turn the LED on
GPIO.output(LED_PIN, GPIO.HIGH)

print("Distance Measurement In Progress")

try:
    while True:
        # Ensure TRIG is low
        GPIO.output(TRIG, False)
        print("Waiting For Sensor To Settle")
        time.sleep(2)

        # Trigger ultrasonic pulse
        GPIO.output(TRIG, True)
        time.sleep(0.00001)  # 10 µs pulse
        GPIO.output(TRIG, False)

        # Measure the time for echo to return
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()

        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        # Calculate pulse duration and distance
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # Speed of sound: 34300 cm/s ÷ 2
        distance = round(distance, 2)

        print(f"Distance: {distance} cm")

        # Check if the distance is less than 45 cm
        if distance < 45:
            print("Distance is less than 45 cm. Stopping the script.")
            break  # Exit the loop if the distance is less than 45 cm

        # Wait for 1 second before the next measurement
        time.sleep(1)

except KeyboardInterrupt:
    print("Measurement stopped by User")
finally:
    GPIO.cleanup()  # Clean up GPIO pins

# Run the second script (bill2.py) after exiting the loop or script
try:
    print("Running the camera script: bill2.py")
    subprocess.run(["python3", "/home/tecbill/rpi-bookworm-yolov8-main/bill2.py"])
except Exception as e:
    print(f"Failed to run the script: {e}")






