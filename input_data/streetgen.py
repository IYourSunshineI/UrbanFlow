import csv
import random

# File name
filename = "cameras.csv"

# Configuration for realistic Vienna data
street_types = [
    {"type": "Highway", "limit": 130, "lanes": [3, 4], "prefix": "A"},  # Autobahn
    {"type": "Urban Highway", "limit": 80, "lanes": [2, 3], "prefix": "A"},  # Stadtautobahn
    {"type": "Major Road", "limit": 50, "lanes": [2, 3], "prefix": "B"},  # Bundesstraße
    {"type": "Street", "limit": 50, "lanes": [1, 2], "prefix": ""},  # Standard street
    {"type": "Residential", "limit": 30, "lanes": [1], "prefix": ""}  # Zone 30
]

# List of real street names in Vienna
vienna_names = {
    # Highways / Major
    "Südosttangente (A23)": [48.193010199999996,16.416310799999998],
    "Donauuferautobahn (A22)": [48.2511784,16.372324499999998],
    "Ostautobahn (A4)": [48.1806906,16.451268],
    "Westautobahn (A1)": [48.2033901,16.2173247],
    "S1 Wiener Außenring": [48.1251319,16.398042999999998],
    "Triester Straße": [48.1423602,16.3298931],
    "Wagramer Straße": [48.2726164,16.4695428],
    "Prager Straße": [48.285799,16.3840888],
    "Brünner Straße": [48.3065053,16.425827599999998],
    "Gürtel": [48.2363472,16.3616113],
    "Schottenring": [48.214481899999996,16.3636321],
    "Franz-Josefs-Kai": [48.2162794,16.3726104],
    "Obere Donaustraße": [48.218365399999996,16.3725798],
    "Altmannsdorfer Straße": [48.1685071,16.3157928],
    "Grünbergstraße": [48.178978699999995,16.316680299999998],
    "Linke Wienzeile": [48.1876296,16.337139],
    "Rechte Wienzeile": [48.198788699999994,16.364421399999998],
    "Handelskai": [48.2320201,16.3970081],
    "Donaustadtstraße": [48.238087799999995,16.4402105],
    # City / Residential
    "Mariahilfer Straße": [48.1998864,16.354417599999998],
    "Kärntner Straße": [48.206005,16.3713883],
    "Graben": [48.2083656,16.370203699999998],
    "Rotenturmstraße": [48.2103007,16.374451],
    "Landstraßer Hauptstraße": [48.1866531,16.3971817],
    "Favoritenstraße": [48.187708799999996,16.3732872],
    "Simmeringer Hauptstraße": [48.1607205,16.4307348],
    "Thaliastraße": [48.212064899999994,16.315657299999998],
    "Ottakringer Straße": [48.2140947,16.3308238],
    "Hernalser Hauptstraße": [48.224751499999996,16.312213],
    "Währinger Straße": [48.2254936,16.3470135],
    "Döblinger Hauptstraße": [48.237327,16.353954899999998],
    "Heiligenstädter Straße": [48.2678838,16.3631948],
    "Nußdorfer Straße": [48.2282398,16.3547419],
    "Alser Straße": [48.2148411,16.3523851],
    "Josefstädter Straße": [48.2098988,16.3472604],
    "Burggasse": [48.2048123,16.3574435],
    "Neustiftgasse": [48.205501299999995,16.3481958],
    "Lerchenfelder Straße": [48.207991299999996,16.3413812],
    "Gumpendorfer Straße": [48.1933742,16.3493717],
    "Margaretenstraße": [48.188998899999994,16.354637999999998],
    "Wiedner Hauptstraße": [48.182420699999994,16.3593845],
    "Ungargasse": [48.2038106,16.385464499999998],
    "Rennweg": [48.1906307,16.39705],
    "Praterstraße": [48.2169445,16.3885392],
    "Taborstraße": [48.229406399999995,16.394228],
    "Wallensteinstraße": [48.229073299999996,16.3691091],
    "Jägerstraße": [48.238530399999995,16.370884],
    "Dresdner Straße": [48.2372439,16.3801081],
    "Engerthstraße": [48.2393996,16.385704999999998]
}

def generate_csv():
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Header
        writer.writerow(["street_name", "street_id", "speed_limit_kph", "lanes", "latitude", "longitude"])
        
        # Iterate over the dictionary items
        for i, (name, manual_coords) in enumerate(vienna_names.items()):
            # Assign characteristics based on street name clues or random assignment
            if "(A" in name or "S1" in name:
                # Highways
                profile = street_types[0] if "A1" in name or "S1" in name else street_types[1]
            elif "Gürtel" in name or "Triester" in name or "Kai" in name:
                # Major roads
                profile = street_types[2]
            elif "gasse" in name or "Graben" in name:
                # Smaller streets often 30 or 50
                profile = random.choice([street_types[3], street_types[4]])
            else:
                # Default standard streets
                profile = street_types[3]

            # Generate ID (e.g., VIE-001)
            s_id = f"VIE-{str(i + 1).zfill(3)}"

            lanes = random.choice(profile["lanes"])
            limit = profile["limit"]

            lat, lon = manual_coords

            writer.writerow([name, s_id, limit, lanes, lat, lon])

    print(f"Successfully created '{filename}' with {len(vienna_names)} entries.")


if __name__ == "__main__":
    generate_csv()