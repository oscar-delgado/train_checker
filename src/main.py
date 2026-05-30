from datetime import date

from providers.iryo import run as iryo_run
from providers.ouigo import run as ouigo_run
from providers.renfe import run as renfe_run

MAX_TRAINS = 3
outbound_date = date(2026, 6, 10)
inbound_date = date(2026, 6, 14)

iryo_trains = iryo_run(outbound_date, inbound_date)
ouigo_trains = ouigo_run(outbound_date, inbound_date)
renfe_trains = renfe_run(outbound_date, inbound_date)

all_outbound = [
    *iryo_trains["outbound"],
    *ouigo_trains["outbound"],
    *renfe_trains["outbound"],
]
all_inbound = [
    *iryo_trains["inbound"],
    *ouigo_trains["inbound"],
    *renfe_trains["inbound"],
]

ordered_out = sorted(all_outbound, key=lambda x: x.price)
ordered_in = sorted(all_inbound, key=lambda x: x.price)

print("- Outbound")
for t in ordered_out[:MAX_TRAINS]:
    print(t)
print("- Inbound")
for t in ordered_in[:MAX_TRAINS]:
    print(t)
