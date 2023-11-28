#!/bin/env python3

from cmp.services.accommodation.v1alpha1 import *
from cmp.types.v1alpha1 import *

header = Header()
header.version.major = 1
header.version.minor = 2
header.version.patch = 3
header.end_user_wallet_address = "X-columbus13lcv2qp3jl8kkz7hm4uwf5scquvsfnx7q370cg"

rs = AccommodationSearchResponse()

rs.header = header

so = SearchOption()
so.property_info.property_name = "AMTSES0SHW"

unit = Unit()
unit.type = UnitType.UNIT_TYPE_ROOM
unit.beds.append(Bed(type=BedType.BED_TYPE_DOUBLE, count=2))

unit.vendor_code = "RMSDDB00A0"

# Rate Plan & Rate Rules
unit.rate_plan = ""
unit.rate_rules.append(RateRule(type = RateRuleType.RATE_RULE_TYPE_NON_REFUNDABLE))
unit.rate_rules.append(RateRule(type = RateRuleType.RATE_RULE_TYPE_NON_REFUNDABLE))

price_detail = PriceDetail()
price_detail.net.currency = Currency.CURRENCY_EUR
price_detail.net.net = 508.17

base_price = PriceDetail()
base_price.net.currency = Currency.CURRENCY_EUR
base_price.net.net = 400.0

price_detail.breakdown.append(PriceDetail(base_price))

unit.price_detail = price_detail

# Extras :: Service Facts
sf1 = ServiceFact()
sf2 = ServiceFact()
sf3 = ServiceFact()
sf4 = ServiceFact()
sf5 = ServiceFact()

sf1.description = "Late Check.out 2h after"
sf2.description = "Bottle of Cava"
sf3.description = "Bottle of Water in the Room"
sf4.description = "Bottle of Red Wine"
sf5.description = "Early Check-in 2h before"

sf1.value = Price(currency=Currency.CURRENCY_EUR, net=81.50)
sf2.value = Price(currency=Currency.CURRENCY_EUR, net=61.13)
sf3.value = Price(currency=Currency.CURRENCY_EUR, net=7.13)
sf4.value = Price(currency=Currency.CURRENCY_EUR, net=36.68)
sf5.value = Price(currency=Currency.CURRENCY_EUR, net=81.50)

# Add extras to the unit
for sf in [sf1, sf2, sf3, sf4, sf5]:
    unit.optional_extras.append(sf)

# Travel Period
tp = TravelPeriod(
        start_date=Date(year=2024, month=11, day=16),
        end_date=Date(year=2024, month=11, day=26),
    )

unit.travel_period = tp

# Travellers
traveller1 = Traveller()
traveller1.age = 30
traveller1.type = TravellerType.TRAVELLER_TYPE_ADULT

unit.travellers.append(traveller1)

traveller2 = Traveller()
traveller2.age = 30
traveller2.type = TravellerType.TRAVELLER_TYPE_ADULT

unit.travellers.append(traveller2)

# Add units to the search option, repeat 68 times (example MTS response)
for i in range(250):
    unit.vendor_code = "APPM00STA5".replace("AP", str(i))
    so.units.append(unit)


# Add search option to the response
rs.options.append(so)

rs_json = rs.to_json()
rs_json_file = open("rs.pb.msg.json", "w")
rs_json_file.write(rs_json)
rs_json_file.close()

#print(rs_json)

print("SIZE:" + str(len(rs.__bytes__())))

# Write message to file
rs_file = open("rs.pb.msg.bin", "wb")
rs_file.write(rs.__bytes__())
rs_file.close()



