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
        auth_resp.raise_for_status()
        token = auth_resp.json().get("access_token")

        # 2. Stiahnutie kompletnej stanice bez filtrov
        api_url = "https://netatmo.com"
        headers = {"Authorization": f"Bearer {token}"}
        data_resp = requests.get(api_url, headers=headers)
        data_resp.raise_for_status()
        
        # Celý JSON objekt z 'body'
        full_payload = data_resp.json().get("body", {})

        # 3. Zápis do Supabase
        supa_url = f"{os.getenv('SUPABASE_URL')}/rest/v1/netatmo_raw"
        supa_headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json"
        }
        # Uložíme celý JSON do stĺpca raw_data
        res = requests.post(supa_url, json={"raw_data": full_payload}, headers=supa_headers)
        res.raise_for_status()
        
        print("Kompletné dáta úspešne archivované.")

    except Exception as e:
        print(f"Chyba pri zbere: {e}")

if __name__ == "__main__":
    run()
