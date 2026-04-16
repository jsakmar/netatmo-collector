import os
import requests

def run():
    try:
        # 1. Získanie Access Tokenu
        auth_url = "https://netatmo.com"
        auth_data = {
            "grant_type": "refresh_token",
            "refresh_token": os.getenv("NETATMO_REFRESH_TOKEN"),
            "client_id": os.getenv("NETATMO_CLIENT_ID"),
            "client_secret": os.getenv("NETATMO_CLIENT_SECRET"),
        }
        
        auth_resp = requests.post(auth_url, data=auth_data)
        if auth_resp.status_code != 200:
            print(f"Chyba autentifikácie: {auth_resp.text}")
            return
            
        access_token = auth_resp.json().get("access_token")

        # 2. Získanie dát
        api_url = "https://netatmo.com"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(api_url, headers=headers)
        
        if resp.status_code != 200:
            print(f"Chyba Netatmo API: {resp.text}")
            return
            
        devices = resp.json().get("body", {}).get("devices", [])

        # Mapovanie: MAC -> (Veličina, Jednotka)
        targets = {
            "05:00:00:0a:f9:4a": ("sum_rain_24", "mm"),
            "06:00:00:07:0f:ee": ("GustStrength", "km/h"),
            "70:ee:50:73:e6:1e": ("Temperature", "°C"),
            "02:00:00:73:d1:2e": ("Temperature", "°C"),
            "03:00:00:0d:87:4c": ("Temperature", "°C"),
            "02:00:00:20:f7:70": ("Temperature", "°C")
        }

        measurements = []

        for d in devices:
            # Hlavná stanica
            m_id = d.get("_id")
            if m_id in targets:
                data_type, unit = targets[m_id]
                val = d.get("dashboard_data", {}).get(data_type)
                if val is not None:
                    measurements.append({"module_id": m_id, "data_type": data_type, "value": float(val), "unit": unit})
            
            # Ostatné moduly
            for m in d.get("modules", []):
                m_id = m.get("_id")
                if m_id in targets:
                    data_type, unit = targets[m_id]
                    val = m.get("dashboard_data", {}).get(data_type)
                    if val is not None:
                        measurements.append({"module_id": m_id, "data_type": data_type, "value": float(val), "unit": unit})

        # 3. Uloženie do Supabase
        if measurements:
            supa_url = f"{os.getenv('SUPABASE_URL')}/rest/v1/netatmo_measurements"
            supa_headers = {
                "apikey": os.getenv("SUPABASE_KEY"),
                "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
                "Content-Type": "application/json"
            }
            res = requests.post(supa_url, json=measurements, headers=supa_headers)
            if res.status_code >= 300:
                print(f"Chyba Supabase: {res.text}")
            else:
                print(f"Úspešne uložené: {len(measurements)} hodnôt.")
        else:
            print("Neboli nájdené žiadne nové dáta pre definované moduly.")

    except Exception as e:
        print(f"Chyba v skripte: {str(e)}")

if __name__ == "__main__":
    run()
