
import math
import requests

HEADERS = {
    "User-Agent": "DriveMap-Student-Project/1.0"
}


def find_location(place):
    """장소 이름을 실제 위도와 경도로 변환"""

    url = "https://nominatim.openstreetmap.org/search"

    response = requests.get(
        url,
        params={
            "q": place,
            "format": "json",
            "limit": 1,
            "countrycodes": "kr"
        },
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    if not data:
        return None

    return [
        float(data[0]["lat"]),
        float(data[0]["lon"])
    ]


def get_route(start, end):
    """실제 도로를 따라 경로 검색"""

    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{start[1]},{start[0]};{end[1]},{end[0]}"
    )

    response = requests.get(
        url,
        params={
            "overview": "full",
            "geometries": "geojson"
        },
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok":
        return None

    route = data["routes"][0]

    return {
        "coordinates": route["geometry"]["coordinates"],
        "distance": route["distance"],
        "duration": route["duration"]
    }


def distance_between(a, b):
    """두 GPS 좌표 사이 거리 계산"""

    radius = 6371000

    lat1 = math.radians(a[0])
    lat2 = math.radians(b[0])

    dlat = math.radians(b[0] - a[0])
    dlon = math.radians(b[1] - a[1])

    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return radius * 2 * math.asin(
        math.sqrt(value)
    )


def get_car_position(coordinates, progress):
    """누적 주행 거리에 해당하는 자동차 위치 계산"""

    traveled = 0

    for i in range(len(coordinates) - 1):

        a = [
            coordinates[i][1],
            coordinates[i][0]
        ]

        b = [
            coordinates[i + 1][1],
            coordinates[i + 1][0]
        ]

        segment = distance_between(a, b)

        if traveled + segment >= progress:

            ratio = (
                (progress - traveled) / segment
                if segment > 0 else 0
            )

            lat = a[0] + (b[0] - a[0]) * ratio
            lon = a[1] + (b[1] - a[1]) * ratio

            return [lat, lon]

        traveled += segment

    return [
        coordinates[-1][1],
        coordinates[-1][0]
    ]


def get_passed_route(coordinates, progress):
    """자동차가 지나온 도로 좌표 반환"""

    result = []

    traveled = 0

    for i in range(len(coordinates) - 1):

        a = [
            coordinates[i][1],
            coordinates[i][0]
        ]

        b = [
            coordinates[i + 1][1],
            coordinates[i + 1][0]
        ]

        segment = distance_between(a, b)

        if traveled + segment <= progress:
            result.append(a)
            traveled += segment

        else:
            break

    result.append(
        get_car_position(coordinates, progress)
    )

    return result
