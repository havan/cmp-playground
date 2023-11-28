import xml.etree.ElementTree as ET
from collections import defaultdict

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

def get_rooms_of_hotel(hotel_code, rooms_list):
    """
    Loops over the given list to find rooms of the hotel.
    """

    hotel_rooms = []

    for room in rooms_list:
        if room["BasicPropertyInfo"]["HotelCode"] == hotel_code:
            hotel_rooms.append(room)

    return hotel_rooms

def print_hotels_info(response_dict):
    """
    Print hotels and rooms counts
    """

    hotels = response_dict["HotelStays"]["HotelStay"]
    all_rooms = response_dict["RoomStays"]["RoomStay"]

    for hotel in hotels:
        hotel_code = hotel["BasicPropertyInfo"]["HotelCode"]
        hotel_name = hotel["BasicPropertyInfo"]["HotelName"]
        hotel_rooms = get_rooms_of_hotel(hotel_code, all_rooms)
        hotel_rooms_count = hotel_rooms.__len__()
        info = f"{hotel_code}: {hotel_name} - Rooms: {hotel_rooms_count}"
        print(info)

xml_file = open("example.xml")
xml_content = xml_file.read()
xml_file.close()

# Parsing the XML file
root = ET.fromstring(xml_content)

# Converting the root element of the XML to a cleaner dictionary
hotel_data_dict_clean = xml_to_dict_with_attributes(root)

print_hotels_info(hotel_data_dict_clean)

