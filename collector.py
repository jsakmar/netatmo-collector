import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

# ---------------------------
# 🕒 TIME CONVERSION (UTC → Bratislava)
# ---------------------------
def to_bratislava_time(ts):
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=ZoneInfo("UTC")) \
        .astimezone(ZoneInfo("Europe/Bratislava")) \
        .isoformat()


# ---------------------------
# 📦 PARSE DEVICES
# ---------------------------
def extract_devices(data):
    devices = []

    for device in data.get("devices", []):
        devices.append({
            "device_id": device.get("_id"),
            "station_name": device.get("station_name"),
            "location": device.get("place")
        })

    return devices


# ---------------------------
# 🔧 PARSE MEASUREMENTS
# ---------------------------
def parse_netatmo(data):
    rows = []

    for device in data.get("devices", []):
        device_id = device.get("_id")

        # MAIN STATION
        dashboard = device.get("dashboard_data", {})
        if dashboard:
            rows.append({
                "time": to_bratislava_time(dashboard.get("time_utc")),
                "device_id": device_id,
                "module_name": "main",
                "module_type": device.get("type"),

                "temperature": dashboard.get("Temperature"),
                "humidity": dashboard.get("Humidity"),
                "co2": dashboard.get("CO2"),
                "pressure": dashboard.get("Pressure"),
                "noise": dashboard.get("Noise"),

                "rain": None,
                "rain_1h": None,
                "rain_24h": None,

                "wind_strength": None,
                "wind_angle": None,
                "gust_strength": None
            })

        # MODULES (rain, wind, outdoor...)
        for module in device.get("modules", []):
            dash = module.get("dashboard_data", {})
            if not dash:
                continue

            rows.append({
                "time": to_bratislava_time(dash.get("time_utc")),
                "device_id": device_id,
                "module_name": module.get("module_name"),
                "module_type": module.get("type"),

                "temperature": dash.get("Temperature"),
                "humidity": dash.get("Humidity"),
                "co2": dash.get("CO2"),
                "pressure": dash.get("Pressure"),
                "noise": dash.get("Noise"),

                # 🌧 Rain
                "rain": dash.get("Rain"),
                "rain_1h": dash.get("sum_rain_1"),
                "rain_24h": dash.get("sum_rain_24"),

                # 🌬 Wind
                "wind_strength": dash.get("WindStrength"),
                "wind_angle": dash.get("WindAngle"),
                "gust_strength": dash.get("GustStrength"),
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

    try:
        print("🔐 Authenticating...")

        auth = requests.post(
            "https://api.netatmo.com/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": rtk,
                "client_id": cid,
                "client_secret": csc
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )

        token_data = auth.json()

        if "access_token" not in token_data:
            print(f"❌ Auth error: {token_data}")
            return

        access_token = token_data["access_token"]
        print("✅ Token OK")

        # ---------------------------
        # 📊 FETCH DATA
        # ---------------------------
        print("📡 Fetching data...")

        res = requests.get(
            "https://api.netatmo.com/api/getstationsdata",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15
        )

        if res.status_code != 200:
            print(f"❌ Data error: {res.text}")
            return

        payload = res.json().get("body", {})
        print("✅ Data OK")

        # ---------------------------
        # 📦 PARSE
        # ---------------------------
        devices = extract_devices(payload)
        rows = parse_netatmo(payload)

        print(f"Devices: {len(devices)}")
        print(f"Measurements: {len(rows)}")

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

        # ---------------------------
        # 🏠 INSERT DEVICES
        # ---------------------------
        device_url = f"{supabase_url}/rest/v1/netatmo_devices"

        if devices:
            d_res = requests.post(device_url, json=devices, headers=headers)
            print(f"Devices insert: {d_res.status_code}")

        # ---------------------------
        # 📊 INSERT MEASUREMENTS
        # ---------------------------
        data_url = f"{supabase_url}/rest/v1/netatmo_measurements"

        if rows:
            m_res = requests.post(data_url, json=rows, headers=headers)
            print(f"Measurements insert: {m_res.status_code}")

            if m_res.status_code >= 300:
                print(m_res.text)
            else:
                print("✅ SUCCESS: Data inserted!")

    except Exception as e:
        print(f"❌ SYSTEM ERROR: {e}")


if __name__ == "__main__":
    run()
