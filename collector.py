import os
import requests

def run():
    # Načítanie premenných
    client_id = os.getenv("NETATMO_CLIENT_ID")
    client_secret = os.getenv("NETATMO_CLIENT_SECRET")
    refresh_token = os.getenv("NETATMO_REFRESH_TOKEN")

    print(f"DEBUG: Skúšam autentifikáciu pre Client ID: {client_id[:5]}***")

    try:
        # 1. Pokus o získanie Access Tokenu
        auth_url = "https://netatmo.com"
        auth_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        
        auth_resp = requests.post(auth_url, data=auth_data)
        
        if auth_resp.status_code != 200:
            print(f"CHYBA AUTENTIFIKÁCIE ({auth_resp.status_code}):")
            print(auth_resp.text) # Tu uvidíme skutočný dôvod
            return

        token_json = auth_resp.json()
        access_token = token_json.get("access_token")
        print("DEBUG: Access Token úspešne získaný.")

        # 2. Pokus o získanie dát
        api_url = "https://netatmo.com"
        headers = {"Authorization": f"Bearer {access_token}"}
        data_resp = requests.get(api_url, headers=headers)

        if data_resp.status_code != 200:
            print(f"CHYBA NETATMO API ({data_resp.status_code}):")
            print(data_resp.text)
            return

        full_payload = data_resp.json().get("body", {})

        # 3. Zápis do Supabase
        supa_url = f"{os.getenv('SUPABASE_URL')}/rest/v1/netatmo_raw"
        supa_headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
            "Content-Type": "application/json"
        }
        
        res = requests.post(supa_url, json={"raw_data": full_payload}, headers=supa_headers)
        
        if res.status_code >= 300:
            print(f"CHYBA SUPABASE ({res.status_code}): {res.text}")
        else:
            print("HOTOVO: Dáta boli úspešne uložené do netatmo_raw.")

    except Exception as e:
        print(f"SYSTÉMOVÁ CHYBA: {str(e)}")

if __name__ == "__main__":
    run()
