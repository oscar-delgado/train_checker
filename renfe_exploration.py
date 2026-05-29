import re
import demjson3
import requests
import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:151.0) Gecko/20100101 Firefox/151.0",
    "Accept": "*/*",
    "Accept-Language": "en,es-ES;q=0.9,ca;q=0.8",
    "Content-Type": "text/plain",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Origin": "https://venta.renfe.com",
    "Referer": "https://venta.renfe.com/vol/buscarTrenEnlaces.do",
}


def get_response_data(text: str) -> dict:
    pattern = r"handle(?:Exception|Callback)\([^,]+,[^,]+,(.*?)\);"
    match = re.compile(pattern, re.DOTALL).search(text)
    obj_text = match.group(1)

    return demjson3.decode(obj_text)


CHARMAP = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ*$"


def tokenify(number):
    number = int(number)
    out = []

    while number > 0:
        out.append(CHARMAP[number & 0x3F])
        number //= 64

    return "".join(out)


def generate_page_id():
    return tokenify(int(time.time() * 1000)) + "-" + tokenify(random.random() * 1e16)


# LOGIN

login_url = "https://venta.renfe.com/vol/dwr/call/plaincall/__System.generateId.dwr"
login_body = """
callCount=1
c0-scriptName=__System
c0-methodName=generateId
c0-id=0
batchId=1
instanceId=0
page=%2Fvol%2FbuscarTrenEnlaces.do
scriptSessionId=
windowName=
"""
response = requests.post(login_url, data=login_body, headers=HEADERS)
if not response.ok:
    raise RuntimeError("Login not valid")

# CHECK SESSION

script_session_id = f"{get_response_data(response.text)}/{generate_page_id()}"
check_url = (
    "https://venta.renfe.com/vol/dwr/call/plaincall/sesionManager.checkSession.dwr"
)
check_body = f"""
callCount=1
windowName=
c0-scriptName=sesionManager
c0-methodName=checkSession
c0-id=0
batchId=0
instanceId=0
page=%2Fvol%2FbuscarTrenEnlaces.do
scriptSessionId={script_session_id}
"""
response = requests.post(check_url, data=check_body, headers=HEADERS)
if not response.ok:
    raise RuntimeError("Not checked")

# UPDATE SESSION OBJECT

update_url = "https://venta.renfe.com/vol/dwr/call/plaincall/buyEnlacesManager.actualizaObjetosSesion.dwr"
update_body = f"""
callCount=1
windowName=
c0-scriptName=buyEnlacesManager
c0-methodName=actualizaObjetosSesion
c0-id=0
c0-e1=string:_YZlP
c0-e2=string:
c0-param0=array:[reference:c0-e1,reference:c0-e2]
batchId=1
instanceId=0
page=%2Fvol%2FbuscarTrenEnlaces.do%3Fc%3D_YZlP
scriptSessionId={script_session_id}
"""
response = requests.post(update_url, data=update_body, headers=HEADERS)
if not response.ok:
    raise RuntimeError("Not updated")

data = get_response_data(response.text)
# ['appl', 'cause', 'cdgoError', 'isIda', 'javaClassName', 'localizedMessage', 'message', 'msgError', 'parametros', 'plaza', 'stackTrace', 'suppressed', 'tramo']
print(data["message"])

exit()
# GET TRAINS

url = "https://venta.renfe.com/vol/dwr/call/plaincall/trainEnlacesManager.getTrainsList.dwr"
headers = {
    **HEADERS,
    "Akamai-Key": "MADRI, BARCE, 30/05/2026, 30/05/2026, IV, , 1, 0, 0, 0, 0, 0, 0, 0, , , , ,",
}
payload = (
    """
callCount=1
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
page=%2Fvol%2FbuscarTrenEnlaces.do%3Fc%3D_YZlP
"""
    + f"scriptSessionId={script_session_id}"
)

response = requests.post(url, headers=headers, data=payload)

if not response.ok:
    raise RuntimeError("Error getting trains")

data = get_response_data(response.text)
print(data.keys())
