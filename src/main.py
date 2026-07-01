from datetime import date

from fastapi import FastAPI

from providers.iryo import run as iryo_run
from providers.ouigo import run as ouigo_run
from providers.renfe import run as renfe_run


app = FastAPI()


@app.get("/")
def read_root():
    return


@app.get("/trains")
def get_trains(
    outbound: date = date.today(),
    inbound: date = date.today(),
    price_increase: float = 1.2,
):
    iryo_trains = iryo_run(outbound, inbound)
    ouigo_trains = ouigo_run(outbound, inbound)
    renfe_trains = renfe_run(outbound, inbound)

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

    ordered_out = sorted(all_outbound)
    ordered_in = sorted(all_inbound)

    cheapest_outbound = ordered_out[0].price
    cheapest_inbound = ordered_in[0].price

    def filtered(train, cheapest_price, price_increase=price_increase):
        return train.price > cheapest_price * price_increase if train.price else True

    return dict(
        outbound=[
            train for train in ordered_out if not filtered(train, cheapest_outbound)
        ],
        inbound=[
            train for train in ordered_in if not filtered(train, cheapest_inbound)
        ],
    )
