import os
import requests
import urllib3

# Potlačenie varovaní o nezabezpečenom HTTPS (keďže vypíname overovanie)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Skúsime verziu s www, ktorá máva častejšie platný certifikát
URL = "https://huty96.eu"
HEADERS = {
    "X-NAWS-Key": os.getenv("X_NAWS_KEY"),
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def run():
    try:
        # 1. Volanie tvojho API (verify=False ignoruje chybu certifikátu)
        resp = requests.get(URL, headers=HEADERS, verify=False, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        measurements = []
        devices = data.get("body", {}).get("devices", [])
        
        targets = {
            "05:00:00:0a:f9:4a": ("sum_rain_24", "mm"),
            "06:00:00:07:0f:ee": ("GustStrength", "km/h"),
            "70:ee:50:73:e6:1e": ("Temperature", "°C"),
            "02:00:00:73:d1:2e": ("Temperature", "°C"),
            "03:00:00:0d:87:4c": ("Temperature", "°C"),
            "02:00:00:20:f7:70": ("Temperature", "°C")
        }

        for d in devices:
            m_id = d.get("_id")
            dash = d.get("dashboard_data", {})
            if m_id in targets:
                data_type, unit = targets[m_id]
                val = dash.get(data_type)
                if val is not None:
                    measurements.append({
                        "module_id": m_id,
                        "data_type": data_type,
                        "value": float(val),
                        "unit": unit
                    })

        # 2. Odoslanie do Supabase
        if measurements:
            supa_url = f"{os.getenv('SUPABASE_URL')}/rest/v1/netatmo_measurements"
            supa_headers = {
                "apikey": os.getenv("SUPABASE_KEY"),
                "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
                "Content-Type": "application/json"
            }
            res = requests.post(supa_url, json=measurements, headers=supa_headers)
            res.raise_for_status()
            print(f"Uložené: {len(measurements)} hodnôt.")
        else:
            print("V API sa nenašli žiadne dáta pre definované moduly.")
            
    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    run()
