import os
import requests

def run():
    # .strip() je dôležitý pre odstránenie neviditeľných znakov
    cid = os.getenv("NETATMO_CLIENT_ID").strip()
    csc = os.getenv("NETATMO_CLIENT_SECRET").strip()
    rtk = os.getenv("NETATMO_REFRESH_TOKEN").strip()

    auth_url = "https://netatmo.com"
    
    try:
        # 1. Získanie Access Tokenu
        # Používame data= namiesto json=, čo Netatmo vyžaduje (form-urlencoded)
        r = requests.post(auth_url, data={
            "grant_type": "refresh_token",
            "refresh_token": rtk,
            "client_id": cid,
            "client_secret": csc
        }, timeout=10)
        
        print(f"Auth Status: {r.status_code}")
        
        # Ak stále dostávaš HTML, vypíšeme len začiatok pre kontrolu
        if r.text.startswith("<!DOCTYPE"):
            print("CHYBA: Stále prichádza HTML. Skontroluj, či Client ID a Secret sedia s obrázkom.")
            return

        token_data = r.json()
        access_token = token_data.get("access_token")

        # 2. Získanie dát
        d = requests.get("https://netatmo.com", 
                         headers={"Authorization": f"Bearer {access_token}"},
                         timeout=10)
        
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
                
    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    run()
