import os
import requests
from datetime import datetime

# ---------------------------
# 🔧 PARSER (Netatmo → rows)
# ---------------------------
def parse_netatmo(data):
    rows = []

    devices = data.get("devices", [])

    for device in devices:
        device_id = device.get("_id")
        station_name = device.get("station_name")

        dashboard = device.get("dashboard_data", {})
        if dashboard:
            rows.append({
                "time": datetime.fromtimestamp(dashboard.get("time_utc")).isoformat(),
                "device_id": device_id,
                "module_name": "main",
                "temperature": dashboard.get("Temperature"),
                "humidity": dashboard.get("Humidity"),
                "co2": dashboard.get("CO2"),
                "pressure": dashboard.get("Pressure"),
                "noise": dashboard.get("Noise")
            })

        # modules (outdoor, rain, wind...)
        for module in device.get("modules", []):
            dash = module.get("dashboard_data", {})

            if not dash:
                continue

            rows.append({
                "time": datetime.fromtimestamp(dash.get("time_utc")).isoformat(),
                "device_id": device_id,
                "module_name": module.get("module_name"),
                "temperature": dash.get("Temperature"),
                "humidity": dash.get("Humidity"),
                "co2": dash.get("CO2"),
                "pressure": dash.get("Pressure"),
                "noise": dash.get("Noise")
            })

    return rows


# ---------------------------
# 🚀 MAIN
# ---------------------------
def run():
    cid = os.getenv("NETATMO_CLIENT_ID", "").strip()
    csc = os.getenv("NETATMO_CLIENT_SECRET", "").strip()
    rtk = os.getenv("NETATMO_REFRESH_TOKEN", "").strip()

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = os.getenv("SUPABASE_KEY", "").strip()

    if not supabase_url:
        print("❌ SUPABASE_URL missing!")
        return

    auth_url = "https://api.netatmo.com/oauth2/token"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": rtk,
        "client_id": cid,
        "client_secret": csc
    }

    try:
        print(f"DEBUG: Auth for ID: {cid[:6]}...")

        r = requests.post(
            auth_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )

        print(f"Auth Status: {r.status_code}")
        token_data = r.json()

        if "access_token" not in token_data:
            print(f"❌ Auth error: {token_data}")
            return

        access_token = token_data["access_token"]
        print("✅ Token OK")

        # ---------------------------
        # 📊 FETCH DATA
        # ---------------------------
        data_url = "https://api.netatmo.com/api/getstationsdata"

        d = requests.get(
            data_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15
        )

        print(f"Data status: {d.status_code}")

        if d.status_code != 200:
            print(f"❌ Data error: {d.text}")
            return

        full_payload = d.json().get("body", {})
        print("✅ Data OK")

        # ---------------------------
        # 🔧 PARSE
        # ---------------------------
        rows = parse_netatmo(full_payload)

        if not rows:
            print("⚠️ No data parsed")
            return

        print(f"Parsed rows: {len(rows)}")

        # ---------------------------
        # 📦 INSERT INTO SUPABASE
        # ---------------------------
        supa_url = f"{supabase_url}/rest/v1/netatmo_measurements"

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        res = requests.post(
            supa_url,
            json=rows,
            headers=headers
        )

        print(f"Supabase status: {res.status_code}")

        if res.status_code >= 300:
            print(f"❌ Supabase error: {res.text}")
        else:
            print("✅ SUCCESS: Data inserted!")

    except Exception as e:
        print(f"❌ SYSTEM ERROR: {e}")


if __name__ == "__main__":
    run()
