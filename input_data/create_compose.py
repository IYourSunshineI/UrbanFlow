import csv
import yaml

CSV_FILE = "cameras.csv"
COMPOSE_FILE = "docker-compose.yml"
IMAGE_NAME = "speed-camera-sim"

# Configuration for the containers
# Allows the container to talk to machine via 'host.docker.internal'
EXTRA_HOSTS = ["host.docker.internal:host-gateway"]


def generate_compose_file():
    # Basic Compose structure
    compose_data = {
        "name": "urban_flow_cameras",
        "version": "3.8",
        "services": {}
    }

    print(f"--- Reading {CSV_FILE} ---")

    with open(CSV_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        first_service = True
        for row in reader:
            street_name = row['street_name']
            street_id = row['street_id']
            speed_limit = row['speed_limit_kph']
            lanes = row['lanes']

            # Create a clean service name (e.g., cam_vie_001)
            service_name = f"cam_{street_id.lower().replace('-', '_')}"

            # Define the service for this specific camera
            service = {
                "image": IMAGE_NAME,
                "container_name": service_name,
                "restart": "unless-stopped",
                "extra_hosts": EXTRA_HOSTS,
                # Pass arguments to the python script inside the container
                "command": [
                    "--name", street_name,
                    "--id", street_id,
                    "--interval", "10.0",  # Slower interval to save resources
                    "--limit", speed_limit,
                    "--position", "1",  # Single camera at position 1 (can be changed when adding average speed)
                    "--lanes", lanes
                ]
            }

            # Only define build in the first service to prevent concurrent build failures
            if first_service:
                service["build"] = "."
                first_service = False

            # Add to the services dictionary
            compose_data["services"][service_name] = service

    # Write the YAML file
    print(f"--- Writing {COMPOSE_FILE} ---")
    with open(COMPOSE_FILE, 'w') as outfile:
        yaml.dump(compose_data, outfile, default_flow_style=False, sort_keys=False, encoding='utf-8')

    print(f"Done! Defined {len(compose_data['services'])} cameras.")
    print("Run 'docker-compose up -d --build' to build image and start them all.")


if __name__ == "__main__":
    generate_compose_file()