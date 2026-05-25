import requests


url = "https://api.iryo.eu/b2c/availability/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:151.0) Gecko/20100101 Firefox/151.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES",
    "Content-Type": "application/json;charset=utf-8",
    "Ocp-Apim-Subscription-Key": "7c9b9b1ea0fe4f0c9d1739fcbf8b5438",
    "Request-Channel": "WEB",
    "X-Pwa-Sessid": "4ae78bf1-ca71-4e3a-92b9-4374d48b6b48",
    "x-client-version": "1.104.2",
    "x-request-id": "75b2e675-afd2-48bc-8cf0-62852a5f515a",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "No-Authorization": "",
    "Referer": "https://iryo.eu/",
}
payload = {"cfgToken":"H4sIAAAAAAAA/52QUUvDMBSF/0ueG0nTNO36NqWgOLHMgsgQSdNk1rUuJh0opf/dG8ukMkQQ8nDOycl3LxmQaLcoQ5d3NOYoQLKpwVVUgrbyGfR9fg5a6863iqfiGpx7k+Cu1g+3YPqmU64XnYGIEsoxiTGNy5BlcOL0LKQ85AlNPF69/2jxX1vO+glFyciNnyc1yjYDjPLbGQdR0/cg/ca6RZkWrVMBqo37eEVZbw9gnIFyCLTj/RgcCS+nhOnNKSCaAD6Zv9fqm2BVtd/v/r3JjHQwWytq9SeKzlGP0JYOvseLWk7CWEgGtFytJn+xzpdl7vUIw1onamN8Yfe1xKJKBGcpx1XMBGYRYzhNSYgJoUynyaJSNELj+AlP7UslLAIAAA==.kL05b3c/73KnCy8QG5ZbLotu0dU6gY67DnjuIsn5zuM=","currency":"EUR","passengers":[{"id":"passenger_1","type":"AD"}],"travels":[{"origin":"60000","destination":"71801","direction":"outbound","departure":"2026-05-27"},{"origin":"71801","destination":"60000","direction":"inbound","departure":"2026-05-30"}]}
response = requests.post(url, json=payload, headers=headers)

data: dict = response.json()["data"]
travels = data.get("offer", {}).get("travels", {})

for travel in travels:
    print()
    print(travel["direction"])
    for route in travel.get("routes", []):
        main_leg = route.get("legs")[0]
        dep_time = main_leg["departure_station"]["departure_timestamp"]

        price = min([item["price"] for item in route["selected_bundles"] if item["price"] > 0])
        print(f"{dep_time}: {price} ({main_leg['service_name']})")
