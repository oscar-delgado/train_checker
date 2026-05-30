import json
import requests
from datetime import date, datetime

from shared.models import Provider, Train


BASE_API = "https://mdw02.api-es.ouigo.com/api"


def run(outbound_date: date, inbound_date: date) -> dict[str, list[Train]]:
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
        "outbound_date": outbound_date.isoformat(),
        "inbound_date": inbound_date.isoformat(),
        "with_ttt": False,
    }
    response = requests.post(
        f"{BASE_API}/Sale/journeysearch", json=payload, headers=headers
    )

    if not response.ok:
        raise RuntimeError("Not able to get journeysearch data")
    data: dict = response.json()

    result = {"outbound": [], "inbound": []}
    for destination, trains in data.items():
        if destination not in result:
            continue
        for train in trains:
            dep_time_str = train["departure_station"]["departure_timestamp"]
            arr_time_str = train["arrival_station"]["arrival_timestamp"]
            result[destination].append(
                Train(
                    service_id=train["service_name"],
                    departure_time=datetime.fromisoformat(dep_time_str),
                    arrival_time=datetime.fromisoformat(arr_time_str),
                    price=train["price"],
                    provider=Provider.OUIGO,
                )
            )

    return result
