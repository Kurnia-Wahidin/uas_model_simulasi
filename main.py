import json
import math
from typing import List, Dict, Tuple
import itertools

class VRPSolver:
    def __init__(self, data: Dict):
        self.data = data
        self.lokasi = data['lokasi']
        self.gudang = self.lokasi[0]  # Dinas Sosial (Gudang)
        self.listKecamatan = self.lokasi[1:]  # 12 kecamatan
        self.kapasitasTruk = data['kapsitas_truk']
        self.ongkosPerKM = data['ongkos_per_km']
        self.fixed_cost = data['fixed_cost_per_truk']
        
        # kalkulasi jarak, persiapan
        self.matrix_jarak = self._kalkulasi_matrix_jarak()
        
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Kalkulasi jarak dari dua lokasi (dalam km)"""
        R = 6371  # radius bumi (km)
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _kalkulasi_matrix_jarak(self) -> Dict[str, Dict[str, float]]:
        """matrix dari semua lokasi"""
        matrix_jarak = {}
        
        for loc1 in self.lokasi:
            from_name = loc1['name']
            matrix_jarak[from_name] = {}
            
            for loc2 in self.lokasi:
                to_name = loc2['name']
                if from_name == to_name:
                    matrix_jarak[from_name][to_name] = 0.0
                else:
                    dist = self._haversine_distance(
                        loc1['y'], loc1['x'], 
                        loc2['y'], loc2['x']
                    )
                    matrix_jarak[from_name][to_name] = round(dist, 2)
        
        return matrix_jarak
    
    def cek_jarak(self, loc1: str, loc2: str) -> float:
        """Cek jarak dari dua lokasi, berdasar nama"""
        return self.matrix_jarak[loc1][loc2]
    
    def _calculate_savings(self) -> List[Tuple[float, str, str]]:
        """Kalkulasi jarak dipangkas"""
        savings = []
        gudang_name = self.gudang['name']
        
        # Get all nama kecamatan
        namaKecamatan = [c['name'] for c in self.listKecamatan]
        
        for i in range(len(namaKecamatan)):
            for j in range(i+1, len(namaKecamatan)):
                c1 = namaKecamatan[i]
                c2 = namaKecamatan[j]
                
                # Savings formula: S(i,j) = d(depot,i) + d(depot,j) - d(i,j)
                saving = (self.cek_jarak(gudang_name, c1) + 
                         self.cek_jarak(gudang_name, c2) - 
                         self.cek_jarak(c1, c2))
                
                savings.append((saving, c1, c2))
        
        # Sort savings descending
        savings.sort(reverse=True, key=lambda x: x[0])
        
        return savings
    
    def _get_penerima(self, kecamatan: str) -> int:
        """Get penerima manfaat di kecamatan"""
        for kec in self.listKecamatan:
            if kec['name'] == kecamatan:
                return kec.get('penerima', 0)
        return 0
    
    def _get_penerima_di_route(self, route: List[str]) -> int:
        """Hitung total penerima dalam rute"""
        total_penerima = 0
        for lkasi in route:
            if lkasi != self.gudang['name']:  # Skip gudang
                total_penerima += self._get_penerima(lkasi)
        return total_penerima
    
    def clarke_wright_savings(self) -> Dict:
        """Implementasi algoritma Clarke & Wright Savings"""
        nama_gudang = self.gudang['name']
        
        # Step 1: Initialize routes untuk setiap kecamatan
        routes = []
        for kec in self.listKecamatan:
            routes.append({
                'route': [nama_gudang, kec['name'], nama_gudang],
                'penerima': kec['penerima'],
                'external': [kec['name']]  # Kecamatan yang dapat di gabung
            })
        
        # Step 2: Kalkulasi jarak dipangkas (savings)
        savings_list = self._calculate_savings()
        
        # Step 3: gabungkan rute berdasar savings
        for saving, c1, c2 in savings_list:
            route1_idx = -1
            route2_idx = -1
            
            # Cari rute terdiri c1 and c2
            for i, route in enumerate(routes):
                if c1 in route['external']:
                    route1_idx = i
                if c2 in route['external']:
                    route2_idx = i
            
            # Ketemu dan beda
            if route1_idx != -1 and route2_idx != -1 and route1_idx != route2_idx:
                route1 = routes[route1_idx]
                route2 = routes[route2_idx]
                
                # Cek batasan kapasitas truk
                total_paket = route1['penerima'] + route2['penerima']
                if total_paket <= self.kapasitasTruk:
                    # Membuat titik koneksi
                    # If c1 endof route1 dan c2 startof route2
                    route1_end = route1['route'][-2]  # Last kecamatan sebelum kembali gudang
                    route2_start = route2['route'][1]  # First kecamatan setelah dari gudang
                    
                    if route1_end == c1 and route2_start == c2:
                        # Merge route2 ke route1 (hapus gudang di tengah)
                        new_route = route1['route'][:-1] + route2['route'][1:]
                        
                        # Update routes
                        routes[route1_idx] = {
                            'route': new_route,
                            'penerima': total_paket,
                            'external': [c1, c2]  # Kecamatan digabung
                        }
                        
                        # Remove route2
                        routes.pop(route2_idx)
                    
                    elif route1_end == c2 and route2_start == c1:
                        # Koneksi alternatif, dibalik
                        new_route = route1['route'][:-1] + route2['route'][1:]
                        
                        routes[route1_idx] = {
                            'route': new_route,
                            'penerima': total_paket,
                            'external': [c1, c2]
                        }
                        
                        routes.pop(route2_idx)
        
        # Step 4: Format final solution
        solution = []
        total_distance = 0
        
        for i, route_data in enumerate(routes):
            route = route_data['route']
            penerima = route_data['penerima']
            
            # Hitung jarak
            route_distance = 0
            for j in range(len(route) - 1):
                route_distance += self.cek_jarak(route[j], route[j + 1])
            
            total_distance += route_distance
            
            # Total biaya
            route_cost = self.fixed_cost + (route_distance * self.ongkosPerKM)
            
            # Format nama kecamatan
            kecamatan_list = []
            for loc in route[1:-1]:  # Exclude gudang di start dan end
                penerima_val = self._get_penerima(loc)
                kecamatan_list.append(f"{loc} ({penerima_val})")
            
            solution.append({
                'route_id': i + 1,
                'kecamatan': route[1:-1],  # tanpa gudang
                'kecamatan_display': " → ".join(kecamatan_list),
                'penerima': penerima,
                'kapasitas_dipakai': f"{penerima}/{self.kapasitasTruk}",
                'jarak_km': round(route_distance, 2),
                'variable_cost': round(route_distance * self.ongkosPerKM, 2),
                'fixed_cost': self.fixed_cost,
                'total_biaya_route': round(route_cost, 2)
            })
        
        # Hitung total
        total_paket = sum(self._get_penerima(c['name']) for c in self.listKecamatan)
        total_variable_cost = total_distance * self.ongkosPerKM
        total_fixed_cost = len(solution) * self.fixed_cost
        total_cost = total_fixed_cost + total_variable_cost
        
        return {
            'routes': solution,
            'summary': {
                'total_routes': len(solution),
                'total_paket': total_paket,
                'total_jarak_km': round(total_distance, 2),
                'total_variable_cost': round(total_variable_cost, 2),
                'total_fixed_cost': total_fixed_cost,
                'total_cost': round(total_cost, 2),
                'kapasitas_truk': self.kapasitasTruk,
                'ongkos_per_km': self.ongkosPerKM,
                'fixed_cost_per_truk': self.fixed_cost
            }
        }
    
    def print_solution(self, solution: Dict):
        """Print readable solution di terminal"""
        print("=" * 80)
        print("SOLUSI EFISIENSI JARAK PENGIRIMAN DAN BIAYA DISTRIBUSI PAKET BANTUAN SOSIAL")
        print("=" * 80)
        
        # Print depot info
        print(f"\nGUDANG: {self.gudang['name']}")
        print(f"Koordinat: ({self.gudang['y']}, {self.gudang['x']})")
        print(f"Kapasitas Truk: {self.kapasitasTruk} paket")
        print(f"Biaya Tetap per Truk: Rp {self.fixed_cost:,}")
        print(f"Biaya per km: Rp {self.ongkosPerKM:,}")
        
        # Print each route
        print("\n" + "=" * 80)
        print("RUTE DISTRIBUSI:")
        print("=" * 80)
        
        for route in solution['routes']:
            print(f"\nRute {route['route_id']}:")
            print(f"  Kecamatan: {route['kecamatan_display']}")
            print(f"  Jumlah Paket: {route['kapasitas_dipakai']} paket")
            print(f"  Jarak: {route['jarak_km']} km")
            print(f"  Biaya Variabel: Rp {route['variable_cost']:,}")
            print(f"  Biaya Tetap: Rp {route['fixed_cost']:,}")
            print(f"  Total Biaya Rute: Rp {route['total_biaya_route']:,}")
        
        # Print summary
        summary = solution['summary']
        print("\n" + "=" * 80)
        print("RINGKASAN:")
        print("=" * 80)
        print(f"Jumlah Truk: {summary['total_routes']}")
        print(f"Total Paket: {summary['total_paket']}")
        print(f"Total Jarak: {summary['total_jarak_km']} km")
        print(f"Total Biaya Variabel: Rp {summary['total_variable_cost']:,}")
        print(f"Total Biaya Tetap: Rp {summary['total_fixed_cost']:,}")
        print("-" * 80)
        print(f"TOTAL BIAYA DISTRIBUSI: Rp {summary['total_cost']:,}")
        print("=" * 80)
        
        # Efficiency metrics
        avg_utilization = (summary['total_paket'] / 
                          (summary['total_routes'] * self.kapasitasTruk)) * 100
        cost_per_package = summary['total_cost'] / summary['total_paket']
        
        print(f"\nMETRIK EFISIENSI:")
        print(f"Rata-rata Utilisasi Truk: {avg_utilization:.1f}%")
        print(f"Biaya per Paket: Rp {cost_per_package:,.0f}")
        print("=" * 80)

def main():
    # Load data from JSON file
    file_path = 'data/sample_data.json'
    
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        print("Memuat data distribusi paket...")
        print(f"File: {data['judul']}")
        print(f"Deskripsi: {data['deskripsi']}")
        print(f"Jumlah lokasi: {len(data['lokasi'])}")
        print(f"Kapasitas truk: {data['kapsitas_truk']} paket\n")
        
        # Buat solver and solve
        solver = VRPSolver(data)
        solution = solver.clarke_wright_savings()
                
        # Simpan solusi ke JSON file
        output_path = 'results/vrp_solution.json'
        with open(output_path, 'w') as outfile:
            json.dump(solution, outfile, indent=2, default=str)
        
        print(f"\nSolusi disimpan ke: {output_path}")

        # Print solusi
        solver.print_solution(solution)

    except FileNotFoundError as e:
        print(f"Error: File {file_path} tidak ditemukan!")
        print(f"An error occured: {e}")

if __name__ == "__main__":
    main()