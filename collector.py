import os
import requests

def run():
    # .strip() je kritický - odstraňuje neviditeľné znaky
    cid = os.getenv("NETATMO_CLIENT_ID", "").strip()
    csc = os.getenv("NETATMO_CLIENT_SECRET", "").strip()
    rtk = os.getenv("NETATMO_REFRESH_TOKEN", "").strip()

    # Debug dĺžky (skontroluj si to v logu, či to sedí)
    print(f"DEBUG: Client ID dĺžka: {len(cid)}")
    print(f"DEBUG: Client Secret dĺžka: {len(csc)}")

    # 1. Získanie Access Tokenu
    # Netatmo vyžaduje TENTO presný formát hlavičky a dát
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": rtk,
        "client_id": cid,
        "client_secret": csc
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    try:
        r = requests.post("https://netatmo.com", data=payload, headers=headers)
        
        print(f"Auth Status: {r.status_code}")
        
        # Ak stále dostávaš HTML, pozrieme sa na prvých 100 znakov
        print(f"Začiatok odpovede: {r.text[:100]}")

        if r.status_code == 200 and not r.text.strip().startswith("<!DOCTYPE"):
            token_data = r.json()
            access_token = token_data.get("access_token")
            print("ÚSPECH: Token získaný.")

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
                print(f"Chyba pri dátach: {d.text}")
        else:
            print("Netatmo stále vracia HTML namiesto JSONu.")
                
    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    run()
