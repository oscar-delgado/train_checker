from datetime import date

from providers.iryo import run as iryo_run
from providers.ouigo import run as ouigo_run
from providers.renfe import run as renfe_run

outbound_date = date(2026, 6, 10)
inbound_date = date(2026, 6, 14)

iryo_run(outbound_date, inbound_date)
ouigo_run(outbound_date, inbound_date)
renfe_run(outbound_date, inbound_date)
