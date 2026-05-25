import re
import demjson3
import requests

url = "https://venta.renfe.com/vol/dwr/call/plaincall/trainEnlacesManager.getTrainsList.dwr"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:151.0) "
        "Gecko/20100101 Firefox/151.0"
    ),
    "Accept": "*/*",
    "Accept-Language": "en,es-ES;q=0.9,ca;q=0.8",
    "Content-Type": "text/plain",
    "Origin": "https://venta.renfe.com",
    "Referer": "https://venta.renfe.com/vol/buscarTrenEnlaces.do?c=_Lids",
    "Akamai-Key": "MADRI, BARCE, 26/05/2026, 27/05/2026, IV, , 1, 0, 0, 0, 0, 0, 0, 0, , , , ,",
}

cookies = {}

payload = """callCount=1
windowName=
c0-scriptName=trainEnlacesManager
c0-methodName=getTrainsList
c0-id=0
c0-e1=string:false
c0-e2=string:false
c0-e3=string:false
c0-e4=string:
c0-e5=string:
c0-e6=string:
c0-e7=string:
c0-e8=string:25%2F05%2F2026
c0-e9=string:26%2F05%2F2026
c0-e10=string:1
c0-e11=string:0
c0-e12=string:0
c0-e13=string:IV
c0-e14=string:
c0-e15=string:false
c0-e16=string:false
c0-e17=string:MADRI
c0-e18=string:BARCE
c0-e19=string:
c0-param0=Object_Object:{atendo:reference:c0-e1, sinEnlace:reference:c0-e2, plazaH:reference:c0-e3, tipoFranjaI:reference:c0-e4, tipoFranjaV:reference:c0-e5, horaFranjaIda:reference:c0-e6, horaFranjaVuelta:reference:c0-e7, fechaSalida:reference:c0-e8, fechaVuelta:reference:c0-e9, adultos:reference:c0-e10, ninos:reference:c0-e11, ninosMenores:reference:c0-e12, trayecto:reference:c0-e13, idaVuelta:reference:c0-e14, conMascota:reference:c0-e15, conBicicleta:reference:c0-e16, origen:reference:c0-e17, destino:reference:c0-e18, codPromo:reference:c0-e19}
batchId=2
instanceId=0
page=%2Fvol%2FbuscarTrenEnlaces.do%3Fc%3D_Lids
scriptSessionId=d6yocUc3sSt97$qMkmocT8QfuVp/A82huVp-XaoR1B2Z7
"""

response = requests.post(
    url,
    headers=headers,
    cookies=cookies,
    data=payload,
)

if not response.ok:
    raise RuntimeError("Error getting trains")

pattern = r'handle(?:Exception|Data)\([^,]+,[^,]+,(\{.*?\})\);'
match = re.compile(pattern, re.DOTALL).search(response.text)
obj_text = match.group(1)

data: dict = demjson3.decode(obj_text)
print(data.keys())
