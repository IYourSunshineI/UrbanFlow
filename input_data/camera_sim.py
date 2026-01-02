import time
import datetime
import random
import string
import requests
import argparse
import sys

# Configuration
# SERVER_ENDPOINT = "http://localhost:5000/api/traffic-data"
SERVER_ENDPOINT = "http://host.docker.internal:5000/api/traffic-data"  # Use this when inside Docker
ERROR_RATE = 0.05  # 5% chance of a sensor error

# Traffic Jam Configuration
JAM_PROBABILITY = 0.2   # 10% chance to start a traffic jam if traffic is normal
JAM_DURATION_MIN = 5    # Minimum number of reports the jam lasts
JAM_DURATION_MAX = 15   # Maximum number of reports the jam lasts

def get_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Simulate a speed camera publishing traffic data.")

    # Required arguments
    parser.add_argument("-n", "--name", required=True, type=str, help="The name of the street")
    parser.add_argument("-i", "--id", required=True, type=str, help="The unique ID of the street")

    # Optional arguments
    parser.add_argument("-t", "--interval", type=float, default=2.0,
                        help="Interval between logs in seconds (default: 2.0)")
    parser.add_argument("-l", "--limit", type=int, default=50,
                        help="The speed limit for this street in km/h (default: 50)")
    parser.add_argument("-p", "--position", type=int, default=1,
                        help="The camera position order on the street, if the average speed is being "
                             "measured then the street can have more cameras (default: 1)")
    parser.add_argument("-r", "--lanes", type=int, default=1,
                        help="The number of lanes the street has (default: 1)")

    return parser.parse_args()


def generate_license_plate():
    """Generates a random license plate (e.g., LL 123AA)."""
    city = "".join(random.choices(string.ascii_uppercase, k=2))
    numbers = "".join(random.choices(string.digits, k=3))
    letters = "".join(random.choices(string.ascii_uppercase, k=2))

    return f"{city} {numbers}{letters}"


def generate_vehicle_data(street_name, street_id, speed_limit, lanes, camera_position, is_traffic_jam):
    """
    Generates the vehicle data payload.
    Uses the user-provided speed_limit to determine violations.
    """

    # Determine if we should simulate a sensor glitch (5% chance)
    if random.random() < ERROR_RATE:
        is_error = True
        # 50/50 chance between negative speed or impossible speed
        if random.choice([True, False]):
            # Error Type A: Negative Velocity (e.g., -15 km/h)
            current_speed = round(random.uniform(-50.0, -1.0), 1)
        else:
            # Error Type B: Impossible Velocity (e.g., 800 km/h)
            current_speed = round(random.uniform(300.0, 999.0), 1)

        # Errors usually have low OCR confidence due to blur/glitch
        ocr_confidence = round(random.uniform(0.10, 0.50), 2)

    # 2. Simulate Traffic Jam (Velocity 0 or very slow)
    elif is_traffic_jam:
        # Speed is between 0 and 15% of the limit (e.g., 0-7.5 km/h in a 50 zone)
        max_jam_speed = speed_limit * 0.15
        current_speed = round(random.uniform(0.0, max_jam_speed), 1)
        # Confidence is usually high in slow traffic
        ocr_confidence = round(random.uniform(0.90, 0.99), 2)

    else:
        # Simulate speed: normal distribution around the limit - 5km/h
        base_speed = random.gauss(speed_limit - 5, speed_limit * 0.15)
        current_speed = round(base_speed, 1)
        ocr_confidence = round(random.uniform(0.85, 0.99), 2)

    is_violation = current_speed > speed_limit

    data = {
        "street_name": street_name,
        "street_id": street_id,
        "camera_id": f"CAM-{street_id}-{camera_position:02d}",
        "timestamp": datetime.datetime.now().isoformat(),
        "license_plate": generate_license_plate(),
        "speed_kph": current_speed,
        "speed_limit": speed_limit,
        "lane_id": random.randint(1, lanes),
        "vehicle_type": random.choice(["Car", "Car", "Car", "Truck", "Motorcycle", "Bus"]),
        "ocr_confidence": ocr_confidence,
        "is_violation": is_violation
    }
    return data


def main():
    # 1. Parse Arguments
    args = get_arguments()

    print(f"--- Speed Camera Simulation Started ---")
    print(f"Street: {args.name} (ID: {args.id}) with {args.lanes} lane(s)")
    print(f"Camera Position Order: {args.position}")
    print(f"Speed Limit: {args.limit} km/h")
    print(f"Target: {SERVER_ENDPOINT}")
    print(f"Interval: {args.interval} seconds")
    print("Press CTRL+C to stop.\n")

    # State variable to track persistent traffic jams
    jam_remaining_cycles = 0

    while True:
        try:
            # --- Traffic Jam State Machine ---
            if jam_remaining_cycles > 0:
                # We are currently in a jam
                jam_remaining_cycles -= 1
                is_jammed = True
            else:
                # We are in normal flow, check chance to start a jam
                if random.random() < JAM_PROBABILITY:
                    jam_remaining_cycles = random.randint(JAM_DURATION_MIN, JAM_DURATION_MAX)
                    is_jammed = True
                else:
                    is_jammed = False

            # 2. Generate Data (passing the custom limit)
            vehicle_data = generate_vehicle_data(args.name, args.id, args.limit, args.lanes, args.position, is_jammed)

            # 3. Publish
            try:
                response = requests.post(
                    SERVER_ENDPOINT,
                    json=vehicle_data,
                    timeout=1
                )
                status = f"Sent ({response.status_code})"
            except requests.exceptions.RequestException:
                status = "Failed (Server Offline)"

            # 4. Log
            # Format timestamp to show HH:MM:SS
            time_str = vehicle_data['timestamp'].split('T')[1][:8]

            log_msg = (
                f"[{time_str}] "
                f"Plate: {vehicle_data['license_plate']} | "
                f"Speed: {vehicle_data['speed_kph']:>5} km/h | "
                f"{status}"
            )

            if vehicle_data['is_violation']:
                # Print violations in RED
                print(f"\033[91m{log_msg} [VIOLATION]\033[0m")
            elif is_jammed:
                # YELLOW for Traffic Jams (slow speed)
                print(f"\033[93m{log_msg} [TRAFFIC JAM]\033[0m")
            else:
                print(log_msg)

            time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\nSimulation stopped.")
            sys.exit(0)


if __name__ == "__main__":
    main()