import requests


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:151.0) Gecko/20100101 Firefox/151.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES",
    "Content-Type": "application/json;charset=utf-8",
    "Ocp-Apim-Subscription-Key": "7c9b9b1ea0fe4f0c9d1739fcbf8b5438",
    "Request-Channel": "WEB",
    "x-client-version": "1.104.2",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "No-Authorization": "",
    "Referer": "https://iryo.eu/",
}
login_url = "https://api.iryo.eu/b2c/config/sales-channel?lang=es&kcClient=b2c&requestChannel=WEB&uuid="
response = requests.get(login_url, headers=headers)
if not response.ok:
    raise RuntimeError("Login not valid")

login_data = response.json()
if "cfgToken" not in login_data:
    raise RuntimeError("Token not found")

url = "https://api.iryo.eu/b2c/availability/search"
payload = {
    "cfgToken": login_data["cfgToken"],
    "currency": "EUR",
    "passengers": [{"id": "passenger_1", "type": "AD"}],
    "travels": [
        {
            "origin": "60000",
            "destination": "71801",
            "direction": "outbound",
            "departure": "2026-05-30",
        },
        {
            "origin": "71801",
            "destination": "60000",
            "direction": "inbound",
            "departure": "2026-06-02",
        },
    ],
}
response = requests.post(url, json=payload, headers=headers)

data: dict = response.json()["data"]
travels = data.get("offer", {}).get("travels", {})

for travel in travels:
    print(travel["direction"])
    for route in travel.get("routes", []):
        main_leg = route.get("legs")[0]
        dep_time = main_leg["departure_station"]["departure_timestamp"]

        price = min(
            [item["price"] for item in route["selected_bundles"] if item["price"] > 0]
        )
        print(f"{dep_time}: {price} ({main_leg['service_name']})")
