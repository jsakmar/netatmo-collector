import os
import requests

def run():
    # Odstránenie bielych znakov
    cid = os.getenv("NETATMO_CLIENT_ID", "").strip()
    csc = os.getenv("NETATMO_CLIENT_SECRET", "").strip()
    rtk = os.getenv("NETATMO_REFRESH_TOKEN", "").strip()

    auth_url = "https://netatmo.com"
    
    # Payload so všetkými údajmi, ako to robí oficiálny generátor
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": rtk,
        "client_id": cid,
        "client_secret": csc
    }

    try:
        print(f"DEBUG: Pokus o autentifikáciu pre ID: {cid[:6]}...")
        
        # Explicitne bez špeciálnych hlavičiek, len čistý POST
        r = requests.post(auth_url, data=payload, timeout=15)
        
        print(f"Auth Status: {r.status_code}")

        # Ak dostaneme HTML, vypíšeme diagnostiku
        if r.text.strip().startswith("<!DOCTYPE"):
            print("CHYBA: Netatmo stále vracia HTML login stránku.")
            print(f"Dĺžka prijatej odpovede: {len(r.text)} znakov")
            return

        # Ak dostaneme JSON
        token_data = r.json()
        if "access_token" not in token_data:
            print(f"CHYBA: JSON neobsahuje access_token. Odpoveď: {token_data}")
            return

        print("ÚSPECH: Access Token získaný.")
        access_token = token_data.get("access_token")

        # 2. Získanie dát zo stanice
        d = requests.get("https://netatmo.com", 
                         headers={"Authorization": f"Bearer {access_token}"},
                         timeout=15)
        
        if d.status_code == 200:
            full_payload = d.json().get("body", {})
            print("Dáta zo stanice stiahnuté.")

            # 3. Zápis do Supabase
            supa_url = f"{os.getenv('SUPABASE_URL')}/rest/v1/netatmo_raw"
            supa_headers = {
                "apikey": os.getenv("SUPABASE_KEY"),
                "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            
            res = requests.post(supa_url, json={"raw_data": full_payload}, headers=supa_headers)
            
            if res.status_code < 300:
                print("VŠETKO OK: Dáta sú úspešne uložené v Supabase!")
            else:
                print(f"Supabase Error ({res.status_code}): {res.text}")
        else:
            print(f"Chyba pri sťahovaní dát ({d.status_code}): {d.text}")
                
    except Exception as e:
        print(f"Systémová chyba: {e}")

if __name__ == "__main__":
    run()
