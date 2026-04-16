import os
import requests
import base64

def run():
    cid = os.getenv("NETATMO_CLIENT_ID", "").strip()
    csc = os.getenv("NETATMO_CLIENT_SECRET", "").strip()
    rtk = os.getenv("NETATMO_REFRESH_TOKEN", "").strip()

    # 1. Príprava autentifikácie cez Basic Auth hlavičku
    auth_str = f"{cid}:{csc}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
    
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": rtk
    }

    try:
        print(f"DEBUG: Skúšam Basic Auth s ID: {cid[:5]}...")
        r = requests.post("https://netatmo.com", data=payload, headers=headers)
        
        print(f"Auth Status: {r.status_code}")
        
        # Ak vráti JSON, máme vyhraté
        if r.status_code == 200 and not r.text.strip().startswith("<!DOCTYPE"):
            token_data = r.json()
            access_token = token_data.get("access_token")
            print("ÚSPECH: Token získaný!")

            # 2. Získanie dát
            d = requests.get("https://netatmo.com", 
                             headers={"Authorization": f"Bearer {access_token}"})
            
            if d.status_code == 200:
                full_payload = d.json().get("body", {})
                
                # 3. Zápis do Supabase
                supa_url = f"{os.getenv('SUPABASE_URL')}/rest/v1/netatmo_raw"
                supa_headers = {
                    "apikey": os.getenv("SUPABASE_KEY"),
                    "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
                    "Content-Type": "application/json"
                }
                res = requests.post(supa_url, json={"raw_data": full_payload}, headers=supa_headers)
                if res.status_code < 300:
                    print("VŠETKO OK: Dáta sú v Supabase!")
                else:
                    print(f"Supabase Error: {res.text}")
            else:
                print(f"Data Error: {d.text}")
        else:
            print(f"Odpoveď (prvých 100 znakov): {r.text[:100]}")
            print("CHYBA: Stále HTML alebo iná chyba.")
                
    except Exception as e:
        print(f"Systémová chyba: {e}")

if __name__ == "__main__":
    run()
