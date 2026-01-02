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
vienna_names = [
    # Highways / Major
    "Südosttangente (A23)", "Donauuferautobahn (A22)", "Ostautobahn (A4)",
    "Westautobahn (A1)", "S1 Wiener Außenring", "Triester Straße",
    "Wagramer Straße", "Prager Straße", "Brünner Straße", "Gürtel (Outer)",
    "Gürtel (Inner)", "Ringstraße", "Franz-Josefs-Kai", "Zweierlinie",
    "Altmannsdorfer Straße", "Grünbergstraße", "Linke Wienzeile", "Rechte Wienzeile",
    "Handelskai", "Donaustadtstraße",
    # City / Residential
    "Mariahilfer Straße", "Kärntner Straße", "Graben", "Rotenturmstraße",
    "Landstraßer Hauptstraße", "Favoritenstraße", "Simmeringer Hauptstraße",
    "Thaliastraße", "Ottakringer Straße", "Hernalser Hauptstraße",
    "Währinger Straße", "Döblinger Hauptstraße", "Heiligenstädter Straße",
    "Nußdorfer Straße", "Alser Straße", "Josefstädter Straße", "Burggasse",
    "Neustiftgasse", "Lerchenfelder Straße", "Gumpendorfer Straße",
    "Margaretenstraße", "Wiedner Hauptstraße", "Ungargasse", "Rennweg",
    "Praterstraße", "Taborstraße", "Wallensteinstraße", "Jägerstraße",
    "Dresdner Straße", "Engerthstraße"
]


def generate_csv():
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Header
        writer.writerow(["street_name", "street_id", "speed_limit_kph", "lanes"])

        for i, name in enumerate(vienna_names):
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

            writer.writerow([name, s_id, limit, lanes])

    print(f"Successfully created '{filename}' with {len(vienna_names)} entries.")


if __name__ == "__main__":
    generate_csv()