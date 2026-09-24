"""
locations.py
Real Delhi NCR localities used as monitoring points.
Coordinates are the actual public geographic coordinates of these areas.
'zone_type' is our own classification (used only by the transparent
rule-based source-attribution estimate) -- it is NOT a measured value.
"""

LOCATIONS = [
    {
        "id": "anand_vihar",
        "name": "Anand Vihar, Delhi",
        "lat": 28.6469,
        "lon": 77.3152,
        "zone_type": "traffic_heavy",   # major ISBT bus terminal + traffic corridor
    },
    {
        "id": "ito",
        "name": "ITO, Delhi",
        "lat": 28.6289,
        "lon": 77.2405,
        "zone_type": "traffic_heavy",   # one of the busiest traffic intersections
    },
    {
        "id": "rk_puram",
        "name": "RK Puram, Delhi",
        "lat": 28.5636,
        "lon": 77.1855,
        "zone_type": "residential",
    },
    {
        "id": "punjabi_bagh",
        "name": "Punjabi Bagh, Delhi",
        "lat": 28.6692,
        "lon": 77.1174,
        "zone_type": "residential",
    },
    {
        "id": "okhla",
        "name": "Okhla Phase 2, Delhi",
        "lat": 28.5307,
        "lon": 77.2731,
        "zone_type": "industrial",
    },
    {
        "id": "rohini",
        "name": "Rohini, Delhi",
        "lat": 28.7041,
        "lon": 77.1025,
        "zone_type": "residential",
    },
    {
        "id": "lodhi_road",
        "name": "Lodhi Road, Delhi",
        "lat": 28.5918,
        "lon": 77.2273,
        "zone_type": "green_zone",       # large park cover nearby
    },
    {
        "id": "gurugram_sec51",
        "name": "Sector 51, Gurugram",
        "lat": 28.4478,
        "lon": 77.0722,
        "zone_type": "mixed",
    },
    {
        "id": "noida_sec62",
        "name": "Sector 62, Noida",
        "lat": 28.6280,
        "lon": 77.3649,
        "zone_type": "mixed",
    },
    {
        "id": "faridabad",
        "name": "Faridabad NIT",
        "lat": 28.4089,
        "lon": 77.3178,
        "zone_type": "industrial",
    },
    {
        "id": "mandir_marg",
        "name": "Mandir Marg, Delhi",
        "lat": 28.6367,
        "lon": 77.2007,
        "zone_type": "traffic_heavy",
    },
    {
        "id": "dwarka_sec8",
        "name": "Dwarka Sector 8, Delhi",
        "lat": 28.5706,
        "lon": 77.0716,
        "zone_type": "residential",
    },
    {
        "id": "narela",
        "name": "Narela, Delhi",
        "lat": 28.8553,
        "lon": 77.0916,
        "zone_type": "industrial",
    },
    {
        "id": "jahangirpuri",
        "name": "Jahangirpuri, Delhi",
        "lat": 28.7277,
        "lon": 77.1642,
        "zone_type": "mixed",
    },
    {
        "id": "ashok_vihar",
        "name": "Ashok Vihar, Delhi",
        "lat": 28.6960,
        "lon": 77.1815,
        "zone_type": "residential",
    },
    {
        "id": "shadipur",
        "name": "Shadipur, Delhi",
        "lat": 28.6514,
        "lon": 77.1587,
        "zone_type": "traffic_heavy",
    },
    {
        "id": "najafgarh",
        "name": "Najafgarh, Delhi",
        "lat": 28.6091,
        "lon": 76.9793,
        "zone_type": "residential",
    },
    {
        "id": "gurugram_vikas_sadan",
        "name": "Vikas Sadan, Gurugram",
        "lat": 28.4601,
        "lon": 77.0269,
        "zone_type": "mixed",
    },
    {
        "id": "noida_sec125",
        "name": "Sector 125, Noida",
        "lat": 28.5445,
        "lon": 77.3260,
        "zone_type": "residential",
    },
    {
        "id": "ghaziabad_vasundhara",
        "name": "Vasundhara, Ghaziabad",
        "lat": 28.6603,
        "lon": 77.3572,
        "zone_type": "mixed",
    },
    {
        "id": "ghaziabad_loni",
        "name": "Loni, Ghaziabad",
        "lat": 28.7515,
        "lon": 77.2897,
        "zone_type": "industrial",
    },
]


def get_location(location_id: str):
    for loc in LOCATIONS:
        if loc["id"] == location_id:
            return loc
    return None
