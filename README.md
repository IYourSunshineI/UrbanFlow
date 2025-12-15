# UrbanFlow

## Mock Data Generation
Each traffic camera is simulated by `camera_sim.py` script. This script generates mock data
as a traffic camera, including vehicle counts and average speeds. 
The generated data is sent to a specified server endpoint at regular intervals.

It can be configured with the following parameters:
- `--name`: A name of the street that it simulates.
- `--id`: An identifier of the street.
- `--interval`: Time interval (in seconds) between data generations.
- `--limit`: The speed limit of that street.
- `--position`: The camera position order, more cameras can be on a street if they measure avg speed.
- `--lanes`: Number of lanes on the street.

The data that get sent look like this:
```json
{
  "street_name": "Südosttangente (A23)",
  "street_id": "VIE-001",
  "camera_id": "CAM-VIE-001-01",
  "timestamp": "2025-12-15T14:36:04.272179",
  "license_plate": "OZ 638IS",
  "speed_kph": 80.9,
  "speed_limit": 80,
  "lane_id": 1,
  "vehicle_type": "Bus",
  "ocr_confidence": 0.91,
  "is_violation": true
}
```

To run the camera simulation, use the following command:
```bash
docker compose up -d
```

It will start multiple camera simulations as defined in the `docker-compose.yml` file.
The number of cameras and their configurations can be adjusted in the compose file.
The streets are generated with `streetgen.py` script and the output is saved in `cameras.csv`.
