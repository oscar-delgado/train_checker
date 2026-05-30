import argparse
import json
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_ORIGEN_NAME = "MADRID-PUERTA DE ATOCHA"
DEFAULT_ORIGEN_CODE = "0071,60000,60000"
DEFAULT_DESTINO_NAME = "BARCELONA-SANTS"
DEFAULT_DESTINO_CODE = "0071,71801,71801"
TODAY = "10/06/2026"
TOMORROW = "15/06/2026"

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
        print("  [1/3] Loading renfe.com to warm up session cookies…")
        try:
            page.goto(HOME_URL, wait_until="domcontentloaded", timeout=30_000)
            # Accept cookie banner if present
            try:
                page.click("#onetrust-accept-btn-handler", timeout=5_000)
            except PWTimeout:
                pass  # no banner — fine
            time.sleep(1)
        except PWTimeout:
            print("       Warning: renfe.com load timed out, continuing anyway.")

        # ── Step 2: POST search form via fetch() from inside the page ─────────
        print("  [2/3] Submitting train search…")
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
        print("  [3/3] Waiting for results…")
        try:
            time.sleep(2)
            # Wait for either the results table or a known error element
            page.wait_for_selector("#listaTrenesTBodyIda > *", timeout=10_000)
        except PWTimeout:
            print("       Warning: results selector not found within 10 s.")

        # Handle QueueIT waiting room — if we land there, wait up to 3 min
        for _ in range(36):
            if "queue-it" in page.url or "queueit" in page.url.lower():
                print("       QueueIT waiting room detected, waiting 5 s…")
                time.sleep(5)
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


def _penc(v: str) -> str:
    """Percent-encode a form value (simple version)."""
    from urllib.parse import quote_plus

    return quote_plus(str(v))


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
            departure = _text(times[0])
            arrival = _text(times[1])
            train_type = "AVE"
            prices = [_text(card) for card in row.select(".precio-cards")]
            if not departure:
                continue
            result[direction].append(
                {
                    "train_type": train_type,
                    "departure": departure,
                    "arrival": arrival,
                    "prices": prices,
                }
            )

    return result


def _text(tag) -> str:
    return tag.get_text(separator=" ", strip=True) if tag else ""


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
    ap.add_argument(
        "--ida", default=TODAY, help="Outbound date  DD/MM/YYYY  (default: today)"
    )
    ap.add_argument(
        "--vuelta",
        default=TOMORROW,
        help="Return date    DD/MM/YYYY  (default: tomorrow)",
    )
    ap.add_argument("--adultos", type=int, default=1)
    ap.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        help="Show the browser window (useful for debugging)",
    )
    ap.set_defaults(headless=True)
    return ap.parse_args()


def main() -> None:
    args = build_args()

    print("\nRenfe train search")
    print(f"  {args.origen_name}  →  {args.destino_name}")
    print(f"  Ida: {args.ida}   Vuelta: {args.vuelta}   Adultos: {args.adultos}")
    print()

    html = get_trains_html(
        origen_name=args.origen_name,
        origen_code=args.origen,
        destino_name=args.destino_name,
        destino_code=args.destino,
        fecha_ida=args.ida,
        fecha_vuelta=args.vuelta,
        adultos=args.adultos,
        headless=args.headless,
    )

    print(f"\nResponse size: {len(html):,} characters")
    trains = parse_trains(html)

    # ── Print results ────────────────────────────────────────────────────────
    for direction, entries in trains.items():
        print(direction)
        if entries:
            for t in entries:
                price = min(t["prices"])
                print(f"{t['departure']}: {price} ({t['train_type']})")
        else:
            print("(none parsed)")


if __name__ == "__main__":
    main()
