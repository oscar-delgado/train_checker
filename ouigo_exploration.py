import json
import requests


BASE_API = "https://mdw02.api-es.ouigo.com/api"


# Make login request to get token
url = f"{BASE_API}/Token/login"
payload = {"username": "ouigo.responsive", "password": "SquirelWeb!2020"}
headers = {
    "accept": "application/json",
    "accept-language": "en-GB,en;q=0.7",
    "content-type": "application/json",
    "origin": "https://ventas.ouigo.com",
    "priority": "u=1, i",
    "referer": "https://ventas.ouigo.com/",
    "sec-ch-ua": '"Chromium";v="148", "Brave";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "sec-gpc": "1",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    ),
    "x-app-version": "2.18.2",
}
cookies = {"ouigo_country_lang": json.dumps({"country": "ES", "language": "es"})}
response = requests.post(url=url, headers=headers, cookies=cookies, json=payload)

if not response.ok:
    raise RuntimeError("Login request not successful")
token = response.json()["token"]


# Use token to do journeysearch request
headers = {**headers, "authorization": f"Bearer {token}"}
payload = {
    "origin": "MT1",  # Madrid P. Atocha
    "destination": "7171801",  # Barcelona Sants
    "passengers": [{"discount_cards": [], "disability_type": "NH", "type": "A"}],
    "outbound_date": "2026-06-10",
    "inbound_date": "2026-06-15",
    "with_ttt": False,
}
response = requests.post(
    f"{BASE_API}/Sale/journeysearch", json=payload, headers=headers
)

if not response.ok:
    raise RuntimeError("Not able to get journeysearch data")
data: dict = response.json()


# Explore results
print("\nIda:")
for train in data.get("outbound"):
    dep_time = train["departure_station"]["departure_timestamp"]
    print(f"{dep_time}: {train['price']} ({train['service_name']})")

print("\nVuelta")
for train in data.get("inbound"):
    dep_time = train["departure_station"]["departure_timestamp"]
    print(f"{dep_time}: {train['price']} ({train['service_name']})")
