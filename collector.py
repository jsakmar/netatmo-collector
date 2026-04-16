import os
import requests

def run():
    cid = os.getenv("NETATMO_CLIENT_ID")
    csc = os.getenv("NETATMO_CLIENT_SECRET")
    rtk = os.getenv("NETATMO_REFRESH_TOKEN")

    print(f"DEBUG: Spúšťam test pre Client ID: {cid[:8]}...")

    # 1. Pokus o Token
    try:
        r = requests.post("https://netatmo.com", data={
            "grant_type": "refresh_token",
            "refresh_token": rtk,
            "client_id": cid,
            "client_secret": csc
        }, timeout=10)
        
        print(f"Status kód: {r.status_code}")
        print(f"Surová odpoveď: {r.text}")

        if r.status_code == 200:
            token = r.json().get("access_token")
            # 2. Pokus o Dáta
            d = requests.get("https://netatmo.com", 
                             headers={"Authorization": f"Bearer {token}"})
            print(f"Dáta Status: {d.status_code}")
            
            if d.status_code == 200:
                print("Úspech! Dáta prišli.")
                # Tu by nasledoval zápis do Supabase
            else:
                print(f"Dáta Error: {d.text}")
                
    except Exception as e:
        print(f"Chyba počas komunikácie: {e}")

if __name__ == "__main__":
    run()
