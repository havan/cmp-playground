#!/bin/env python3

import xml.etree.ElementTree as ET
from collections import defaultdict

from cmp.services.accommodation.v1alpha1 import *
from cmp.types.v1alpha1 import *

import logging
logging.basicConfig(format='%(asctime)s - %(message)s')
#logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logging.info('Starting...')

def strip_ns(tag):
    """
    Removes the namespace from the XML tag.
    """
    return tag.split('}')[-1] if '}' in tag else tag

def xml_to_dict_with_attributes(element):
    """
    Recursively converts an XML element and its children into a Python dictionary,
    including both text and attributes. Repeating elements are stored in lists.
    """
    def convert(child):
        child_dict = {**child.attrib}
        if child.text:
            child_dict['text'] = child.text.strip()
        child_dict.update(xml_to_dict_with_attributes(child))
        return child_dict

    d = defaultdict(list)
    for child in element:
        d[strip_ns(child.tag)].append(convert(child))

    # Convert single-element lists to just the element
    for key in d:
        if len(d[key]) == 1:
            d[key] = d[key][0]

    return dict(d)

def get_room_hotel_code(room):
    return room["BasicPropertyInfo"]["HotelCode"]
def get_room_type_code(room):
    return room["RoomTypes"]["RoomType"]["RoomTypeCode"]
def get_room_price(room):
    return room["RoomRates"]["RoomRate"]["Rates"]["Rate"]["Total"]["AmountAfterTax"]
def get_room_price_currency(room):
    return room["RoomRates"]["RoomRate"]["Rates"]["Rate"]["Total"]["CurrencyCode"]
def get_room_rate_plan(room):
    return room["RoomRates"]["RoomRate"]["Rates"]["Rate"]["ChargeType"]
def get_room_remaining_units(room):
    return int(room["RoomRates"]["RoomRate"]["NumberOfUnits"])

def get_room_timespan_start(room):
    return room["TimeSpan"]["Start"]
def get_room_timespan_end(room):
    return room["TimeSpan"]["End"]
def get_room_travel_period(room):
    start = get_room_timespan_start(room).split("-")
    end = get_room_timespan_end(room).split("-")

    # Travel Period
    tp = TravelPeriod(
            start_date=Date(year=int(start[0]), month=int(start[1]), day=int(start[2])),
            end_date=Date(year=int(end[0]), month=int(end[1]), day=int(end[2])),
        )

    return tp

def get_room_travellers(room):
    guest_age_code = int(room["GuestCounts"]["GuestCount"]["AgeQualifyingCode"])
    guest_count = int(room["GuestCounts"]["GuestCount"]["Count"])

    travellers = []

    for i in range(guest_count):
        traveller = Traveller()
        if guest_age_code == 10:
            # Check this
            traveller.type = TravellerType.TRAVELLER_TYPE_ADULT
        else:
            # Default should probably be adult
            traveller.type = TravellerType.TRAVELLER_TYPE_ADULT
        travellers.append(traveller)

    return travellers

def get_room_guest(room):
    return room["TimeSpan"]["End"]

def get_room_rate_feature(room):
    rate_feature = room["RoomRates"]["RoomRate"]["Features"]["Feature"]["Description"]["Text"]["text"]
    collect_features(rate_feature)
    return rate_feature

def get_rate_rule_from_feature(feature):
    """
    Return RateRule type from a feature id of MTS

    Features: ['BB', 'HB', 'AI', 'RO', 'HB+', 'SC', 'FB', 'AI+', 'FB+']
    """
    if feature in ["BB","BB+"]:
        return RateRule(rate_type = RateRuleType.RATE_RULE_TYPE_NON_REFUNDABLE)
    elif feature in ["HB","HB+"]:
        return RateRule(rate_type = RateRuleType.RATE_RULE_TYPE_FLEXIBLE)
    elif feature in ["SC","SC+"]:
        return RateRule(rate_type = RateRuleType.RATE_RULE_TYPE_FLEXIBLE)
    elif feature in ["AI","AI+"]:
        return RateRule(rate_type = RateRuleType.RATE_RULE_TYPE_RESELLABLE)
    elif feature in ["RO","RO+"]:
        return RateRule(rate_type = RateRuleType.RATE_RULE_TYPE_SEMI_NON_REFUNDABLE)
    elif feature in ["FB","FB+"]:
        return RateRule(rate_type = RateRuleType.RATE_RULE_TYPE_SEMI_NON_REFUNDABLE)
    else:
        return RateRule(rate_type = RateRuleType.RATE_RULE_TYPE_NON_REFUNDABLE)

def get_room_rate_rule(room):
    return get_rate_rule_from_feature(get_room_rate_feature(room))

def get_rooms_of_hotel(hotel_code, rooms_list):
    """
    Loops over the given list to find rooms of the hotel.
    """

    hotel_rooms = []

    for room in rooms_list:
        if get_room_hotel_code(room) == hotel_code:
            hotel_rooms.append(room)

    return hotel_rooms

def print_rooms_info(rooms_list):
    """
    Print rooms info
    """
    for room in rooms_list:
        room_type_code = get_room_type_code(room)
        room_total_price = get_room_price(room)
        room_total_price_currency = get_room_price_currency(room)
        room_rate_feature = get_room_rate_feature(room)

        info = f"\t - {room_type_code}: \t{room_total_price_currency}{room_total_price} - Feature: {room_rate_feature}"

        print(info)

def get_hotel_code(hotel):
    return hotel["BasicPropertyInfo"]["HotelCode"]
def get_hotel_name(hotel):
    return hotel["BasicPropertyInfo"]["HotelName"]
def get_hotel_code_context(hotel):
    return int(hotel["BasicPropertyInfo"]["HotelCodeContext"])
def get_hotel_area_id(hotel):
    return hotel["BasicPropertyInfo"]["AreaID"]
def get_hotel_image(hotel):
    return hotel["BasicPropertyInfo"]["VendorMessages"]["VendorMessage"]["SubSection"]["Paragraph"]["Image"]["text"]
def get_hotel_stars(hotel):
    try:
        stars = int(hotel["BasicPropertyInfo"]["Award"]["Rating"].split()[0])
    except:
        stars = 0
    return stars
def get_hotel_segmentation_list(hotel):

    segmentation_list = []

    if "Service" in hotel["BasicPropertyInfo"].keys():
        service = hotel["BasicPropertyInfo"]["Service"]
    else:
        # Return empty string if no service element
        return ""

    if isinstance(service, list):
        for segmentation in service:
            segmentation_list.append(segmentation["text"])
    else:
        segmentation_list.append(service["text"])

    return segmentation_list

def get_all_rooms(response_dict):
    return response_dict["RoomStays"]["RoomStay"]
def get_all_hotels(response_dict):
    return response_dict["HotelStays"]["HotelStay"]

features = []
def collect_features(feature):
    """
    Adds feature to a list if it's not seen before and returns the list
    """
    if not feature in features:
        features.append(feature)

def print_hotels_info(response_dict):
    """
    Print hotels and rooms counts
    """

    hotels = get_all_hotels(response_dict)
    all_rooms = get_all_rooms(response_dict)

    total_room_count = all_rooms.__len__()

    total_hotels = len(hotels)

    total_hotel_rooms = 0

    for hotel in hotels:
        hotel_code = get_hotel_code(hotel)
        hotel_name = get_hotel_name(hotel)
        hotel_rooms = get_rooms_of_hotel(hotel_code, all_rooms)
        hotel_rooms_count = hotel_rooms.__len__()

        total_hotel_rooms += hotel_rooms_count

        info = f"{hotel_code}: {hotel_name} - Rooms: {hotel_rooms_count}"

        print(info)
        print_rooms_info(hotel_rooms)

    print(f"Total Hotels: {total_hotels}")
    print(f"Total Rooms: {total_room_count}")
    print(f"Total Hotel Rooms: {total_hotel_rooms}")

def get_header():
    """
    Create a new Header type, populate the fields and return it
    """
    header = Header()
    header.version.major = 1
    header.version.minor = 2
    header.version.patch = 3
    header.end_user_wallet_address = "X-columbus13lcv2qp3jl8kkz7hm4uwf5scquvsfnx7q370cg"
    return header

def unit_from_room(room):
    """
    Create a Unit type from room and return it
    """

    unit = Unit()
    unit.type = UnitType.UNIT_TYPE_ROOM

    unit.vendor_code = get_room_type_code(room)

    unit.rate_plan = get_room_rate_plan(room)
    unit.rate_rules.append(get_room_rate_rule(room))

    price_detail = PriceDetail()
    price_detail.net.currency = Currency.CURRENCY_EUR
    price_detail.net.net = 508.17

    # Get copy of the price_detail object as the prices are the same in xml
    base_price = PriceDetail.FromString(price_detail.SerializeToString())

    # Append base price to price detail of Unit
    price_detail.breakdown.append(base_price)
    unit.price_detail = price_detail

    # Travel Period
    tp = get_room_travel_period(room)
    unit.travel_period = tp

    # Travellers - GuestCounts in xml
    unit.travellers.extend(get_room_travellers(room))

    # Remaining units
    unit.remaining_units = get_room_remaining_units(room)

    # We don't have anywhere to put these, so to keep it comparable I put them here
    unit.remarks = 'Type:22,ID:XXXX,ID_Context:XXXX}'

    return unit

def property_info_from_hotel(hotel):

    property = PropertyInfo()

    property.property_name = get_hotel_name(hotel)
    property.city_or_resort = get_hotel_area_id(hotel)

    # Put the hotel code to GIATA ID for now
    property.giata_id = get_hotel_code(hotel)

    property.goal_id = get_hotel_code_context(hotel)

    # Put image to region for now
    property.region = get_hotel_image(hotel)

    # And put the stars into the country type
    property.country = get_hotel_stars(hotel)

    # PropertyInfo don't have service facts for now, use status
    property.status = str(get_hotel_segmentation_list(hotel))

    return property

def get_search_option(hotel, all_rooms):
    """
    Get a hotel and generate a search option with all the rooms of the hotel
    """

    so = SearchOption()

    # Set PropertyInfo
    so.property_info = property_info_from_hotel(hotel)

    # Set Units of the Property
    hotel_code = get_hotel_code(hotel)
    hotel_rooms = get_rooms_of_hotel(hotel_code, all_rooms)

    for room in hotel_rooms:
        so.units.append(unit_from_room(room))

    # Return the search option
    return so

def get_accommodation_search_response(hotel_data_dict):
    """
    Gets the parsed hotel data dict and builds a AccommodationSearchResponse message
    """

    all_hotels = get_all_hotels(hotel_data_dict)
    all_rooms = get_all_rooms(hotel_data_dict)

    accommodation_search_response = AccommodationSearchResponse()
    accommodation_search_response.header = get_header()

    # Search Options
    for hotel in all_hotels:
        # Build the search option for the hotel
        so = get_search_option(hotel, all_rooms)
        # Append the search option to the options list of the response
        accommodation_search_response.options.append(so)

    return accommodation_search_response

def write_message_to_file(message, file_name="pb.msg.bin"):
    """
    Write the message to a file, serializing to binary
    """
    pb_file = open(file_name, "wb")
    msg_bytes = message.SerializeToString()
    pb_file.write(msg_bytes)
    pb_file.close()

### MAIN ###

# TESTS
# print_hotels_info(hotel_data_dict_clean)
# print(f"Features: {features}")

# for room in get_all_rooms(hotel_data_dict_clean)[:1]:
#     unit = unit_from_room(room)
#     print(unit)
#     print()
#     print("BYTES:", unit.SerializeToString())
#     print("LEN:", len(unit.SerializeToString()))

# for hotel in get_all_hotels(hotel_data_dict_clean)[:1]:
#     property = property_info_from_hotel(hotel)
#     print(property)
#     print("BYTES:", property.SerializeToString())
#     print("LEN:", len(property.SerializeToString()))

# Read the example XML file
logging.info("Reading XML File")
xml_file = open("example.xml")
xml_content = xml_file.read()
xml_file.close()
logging.info("Reading XML File Done")

# Parse the XML file
logging.info("Parsing XML")
root = ET.fromstring(xml_content)
logging.info("Parsing XML Done")

# Converting the root element of the XML to a cleaner dictionary
logging.info("Converting XML to Dictionary")
hotel_data_dict_clean = xml_to_dict_with_attributes(root)
logging.info("Converting XML to Dictionary Done")

logging.info("Building AccommodationSearchResponse")
asr = get_accommodation_search_response(hotel_data_dict_clean)
logging.info("Building AccommodationSearchResponse Done")

#print(asr)
file_name = "accommodation_search_response_mts.pb.bin"

logging.info(f"Writing file: {file_name}")
write_message_to_file(asr, file_name)
logging.info("Writing file done")