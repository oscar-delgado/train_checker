import argparse
import json
from time import sleep
from datetime import date, datetime, time, timedelta, timezone

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from shared.models import Provider, Train

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_ORIGEN_NAME = "MADRID-PUERTA DE ATOCHA"
DEFAULT_ORIGEN_CODE = "0071,60000,60000"
DEFAULT_DESTINO_NAME = "BARCELONA-SANTS"
DEFAULT_DESTINO_CODE = "0071,71801,71801"

SEARCH_URL = "https://venta.renfe.com/vol/buscarTren.do?Idioma=es&Pais=ES"
HOME_URL = "https://www.renfe.com/es/es"


# ---------------------------------------------------------------------------
# Session bootstrap — visit renfe.com first so the browser receives all
# first-party cookies, then POST the search form.
# ---------------------------------------------------------------------------


def get_trains_html(
    origen_name: str,
    origen_code: str,
    destino_name: str,
    destino_code: str,
    fecha_ida: str,
    fecha_vuelta: str,
    adultos: int = 1,
    headless: bool = True,
) -> str:
    """
    Launches a Chromium browser, warms up the session on renfe.com,
    then POSTs the train-search form and returns the result HTML.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = browser.new_context(
            locale="es-ES",
            timezone_id="Europe/Madrid",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:151.0) "
                "Gecko/20100101 Firefox/151.0"
            ),
            extra_http_headers={
                "Accept-Language": "en,es-ES;q=0.9,ca;q=0.8",
            },
        )
        page = ctx.new_page()

        # ── Step 1: visit renfe.com to get AMCV / OneTrust / f5 cookies ──────
        try:
            page.goto(HOME_URL, wait_until="domcontentloaded", timeout=30_000)
            # Accept cookie banner if present
            try:
                page.click("#onetrust-accept-btn-handler", timeout=5_000)
            except PWTimeout:
                pass  # no banner — fine
            sleep(1)
        except PWTimeout:
            print("       Warning: renfe.com load timed out, continuing anyway.")

        # ── Step 2: POST search form via fetch() from inside the page ─────────
        form_params = {
            "tipoBusqueda": "autocomplete",
            "currenLocation": "menuBusqueda",
            "vengoderenfecom": "SI",
            "desOrigen": origen_name,
            "desDestino": destino_name,
            "cdgoOrigen": origen_code,
            "cdgoDestino": destino_code,
            "idiomaBusqueda": "ES",
            "FechaIdaSel": fecha_ida,
            "FechaVueltaSel": fecha_vuelta,
            "_fechaIdaVisual": fecha_ida,
            "_fechaVueltaVisual": fecha_vuelta,
            "minPriceDeparture": "false",
            "minPriceReturn": "false",
            "adultos_": str(adultos),
            "ninos_": "0",
            "ninosMenores": "0",
            "codPromocional": "",
            "plazaH": "false",
            "sinEnlace": "false",
            "conMascota": "false",
            "conBicicleta": "false",
            "asistencia": "false",
            "franjaHoraI": "",
            "franjaHoraV": "",
            "Idioma": "es",
            "Pais": "ES",
        }

        # Use page.goto with a POST via a temporary form submit (most reliable
        # approach — avoids CORS/fetch complications from the renfe.com origin).
        submit_js = f"""
        (() => {{
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '{SEARCH_URL}';
            const data = {json.dumps(form_params)};
            for (const [k, v] of Object.entries(data)) {{
                const inp = document.createElement('input');
                inp.type  = 'hidden';
                inp.name  = k;
                inp.value = v;
                form.appendChild(inp);
            }}
            document.body.appendChild(form);
            form.submit();
        }})();
        """
        page.evaluate(submit_js)

        # ── Step 3: wait for the results page ────────────────────────────────
        try:
            sleep(2)
            # Wait for either the results table or a known error element
            page.wait_for_selector("#listaTrenesTBodyIda > *", timeout=10_000)
        except PWTimeout:
            print("       Warning: results selector not found within 10 s.")

        # Handle QueueIT waiting room — if we land there, wait up to 3 min
        for _ in range(36):
            if "queue-it" in page.url or "queueit" in page.url.lower():
                print("       QueueIT waiting room detected, waiting 5 s…")
                sleep(5)
                try:
                    page.wait_for_selector(
                        "#tblAva0, .tbl-resultado, .noDisponible",
                        timeout=10_000,
                    )
                    break
                except PWTimeout:
                    continue
            else:
                break

        html = page.content()
        browser.close()
        return html


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def parse_trains(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    result = {"outbound": [], "inbound": []}

    for direction, table_id in [
        ("outbound", "listaTrenesTBodyIda"),
        ("inbound", "listaTrenesTBodyVuelta"),
    ]:
        table = soup.find("div", id=table_id)
        if not table:
            continue
        for row in table.select(".selectedTren"):
            times = row.find_all("h5")
            if len(times) < 2:
                continue
            departure = _time(times[0])
            if not departure:
                continue
            arrival = _time(times[1])
            prices = [_float(card) for card in row.select(".precio-cards")]
            result[direction].append(
                {
                    "departure": departure,
                    "arrival": arrival,
                    "prices": prices,
                }
            )

    return result


def _text(tag) -> str:
    return tag.get_text(separator=" ", strip=True) if tag else ""


def _float(tag) -> float:
    text = _text(tag).replace("€", "").replace(",", ".")
    return float(text)


def _time(tag) -> time:
    text = _text(tag).replace("h", "").replace(" ", "")
    [hour, minute] = text.split(":")
    return time(hour=int(hour), minute=int(minute), tzinfo=timezone(timedelta(hours=2)))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Renfe train search scraper")
    ap.add_argument(
        "--origen",
        default=DEFAULT_ORIGEN_CODE,
        help="Origin station code  (default: Alicante Terminal)",
    )
    ap.add_argument("--origen-name", default=DEFAULT_ORIGEN_NAME)
    ap.add_argument(
        "--destino",
        default=DEFAULT_DESTINO_CODE,
        help="Destination station code  (default: A Coruña)",
    )
    ap.add_argument("--destino-name", default=DEFAULT_DESTINO_NAME)
    return ap.parse_args()


def run(outbound_date: date, inbound_date: date):
    args = build_args()
    html = get_trains_html(
        origen_name=args.origen_name,
        origen_code=args.origen,
        destino_name=args.destino_name,
        destino_code=args.destino,
        fecha_ida=outbound_date.strftime("%d/%m/%Y"),
        fecha_vuelta=inbound_date.strftime("%d/%m/%Y"),
        adultos=1,
        headless=True,
    )
    trains = parse_trains(html)

    result = {"outbound": [], "inbound": []}
    for direction, entries in trains.items():
        if direction not in result:
            continue
        for t in entries:
            price = min(t["prices"]) if t["prices"] else None
            thisbound_date = outbound_date if direction == "outbound" else inbound_date
            dept_time = datetime.combine(thisbound_date, t["departure"])
            arvl_time = datetime.combine(thisbound_date, t["arrival"])
            result[direction].append(
                Train(
                    service_id=None,
                    departure_time=dept_time,
                    arrival_time=arvl_time,
                    price=price,
                    provider=Provider.RENFE,
                )
            )

    return result
