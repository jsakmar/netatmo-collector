import os
import requests

def run():
    cid = os.getenv("NETATMO_CLIENT_ID").strip()
    csc = os.getenv("NETATMO_CLIENT_SECRET").strip()
    rtk = os.getenv("NETATMO_REFRESH_TOKEN").strip()

    # Logujme dĺžku pre kontrolu (či tam nie sú skryté znaky)
    print(f"DEBUG: Client ID dĺžka: {len(cid)}")
    print(f"DEBUG: Refresh Token dĺžka: {len(rtk)}")

    # 1. Pokus o Token - POZOR na presnú URL
    try:
        r = requests.post("https://netatmo.com", data={
            "grant_type": "refresh_token",
            "refresh_token": rtk,
            "client_id": cid,
            "client_secret": csc
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        
        print(f"Status kód: {r.status_code}")
        
        # Ak vráti HTML (začína to <), je to zle. Musíme dostať { (JSON)
        response_start = r.text[:50]
        print(f"Začiatok odpovede: {response_start}")

        if r.status_code == 200 and not r.text.startswith("<!DOCTYPE"):
            token_data = r.json()
            print("ÚSPECH: Máme JSON s tokenom!")
            # Sem potom vrátime kód pre Supabase
        else:
            print("CHYBA: Netatmo nevrátilo JSON. Pravdepodobne neplatné Client ID alebo Token.")
                
    except Exception as e:
        print(f"Systémová chyba: {e}")

if __name__ == "__main__":
    run()
