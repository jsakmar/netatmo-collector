import os
import requests

def run():
    cid = os.getenv("NETATMO_CLIENT_ID", "").strip()
    csc = os.getenv("NETATMO_CLIENT_SECRET", "").strip()
    rtk = os.getenv("NETATMO_REFRESH_TOKEN", "").strip()

    auth_url = "https://api.netatmo.com/oauth2/token"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": rtk,
        "client_id": cid,
        "client_secret": csc
    }

    try:
        print(f"DEBUG: Auth for ID: {cid[:6]}...")

        r = requests.post(auth_url, data=payload, timeout=15)
        print(f"Auth Status: {r.status_code}")

        token_data = r.json()

        if "access_token" not in token_data:
            print(f"CHYBA: {token_data}")
            return

        access_token = token_data["access_token"]
        print("ÚSPECH: Token OK")

        # 🔽 Správny endpoint na dáta
        data_url = "https://api.netatmo.com/api/getstationsdata"

        d = requests.get(
            data_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15
        )

        print(f"Data status: {d.status_code}")

        if d.status_code == 200:
            full_payload = d.json().get("body", {})
            print("Dáta OK")

            # Supabase
            supa_url = f"{os.getenv('SUPABASE_URL')}/rest/v1/netatmo_raw"
            supa_headers = {
                "apikey": os.getenv("SUPABASE_KEY"),
                "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }

            res = requests.post(
                supa_url,
                json={"raw_data": full_payload},
                headers=supa_headers
            )

            print(f"Supabase: {res.status_code}")

        else:
            print(f"Chyba dát: {d.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
