import json
import math
import os

# Path ke file JSON
file_path = 'data/sample_data.json'

# Baca file JSON
with open(file_path, 'r') as file:
    data = json.load(file)

# Fungsi untuk menghitung jarak Haversine (dalam km)
def haversine(lat1, lon1, lat2, lon2):
    # Konversi derajat ke radian
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Selisih koordinat
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Rumus Haversine
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    r = 6371  # Radius bumi dalam km
    distance = r * c

    return distance

# Ambil daftar lokasi
locations = data['locations']

# Buat dictionary untuk menyimpan jarak
distance_matrix = {}

# Hitung jarak untuk setiap pasangan lokasi
for i, loc1 in enumerate(locations):
    from_name = loc1['name']
    distance_matrix[from_name] = {}
    
    for j, loc2 in enumerate(locations):
        to_name = loc2['name']
        if from_name == to_name:
            distance_matrix[from_name][to_name] = 0.0
        else:
            dist = haversine(loc1['y'], loc1['x'], loc2['y'], loc2['x'])
            distance_matrix[from_name][to_name] = round(dist, 4)  # Pembulatan 4 digit

# Tampilkan hasil
print("Matriks Jarak (km):")
for from_loc in distance_matrix:
    print(f"\n{from_loc}:")
    for to_loc, dist in distance_matrix[from_loc].items():
        print(f"  -> {to_loc}: {dist} km")

# Simpan ke file JSON (opsional)
output_path = 'results/distance_matrix.json'
with open(output_path, 'w') as outfile:
    json.dump(distance_matrix, outfile, indent=2)

print(f"\nHasil disimpan ke {output_path}")