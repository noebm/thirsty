import io
import math
import re
from typing import Literal, TypedDict

import folium
import gpxpy
import requests
import rich.console
import rich.progress
from gpxpy.geo import haversine_distance

console = rich.console.Console()

# reuse gpxpy location type
type Location = gpxpy.mod_gpx.mod_geo.Location


OVERPASS_URL = "http://overpass-api.de/api/interpreter"

type AmenityType = Literal["water", "point", "tap", "spring", "fountain"]

AMENITIES: dict[AmenityType, str] = {
    "water": "[amenity=drinking_water]",
    "point": "[amenity=water_point][drinking_water=yes]",
    "tap": "[man_made=water_tap][drinking_water=yes]",
    "spring": "[natural=spring][drinking_water=yes]",
    "fountain": "[amenity=fountain][drinking_water=yes]",
}


class Tags(TypedDict):
    amenity: str


class POI(TypedDict):
    lat: float
    lon: float
    tags: Tags


def display_gpx_on_map(points: list[Location], pois: list[POI]):
    """
    Display the GPX route and POIs on a map
    """

    # Create a base map centered around the middle of the GPX track
    track_latitudes = [point.latitude for point in points]
    track_longitudes = [point.longitude for point in points]

    center_lat = sum(track_latitudes) / len(track_latitudes)
    center_lon = sum(track_longitudes) / len(track_longitudes)

    map_center = [center_lat, center_lon]
    folium_map = folium.Map(location=map_center, zoom_start=12)

    track_coords = [(point.latitude, point.longitude) for point in points]
    folium.PolyLine(track_coords, color="blue", weight=2.5, opacity=1).add_to(
        folium_map
    )

    # Plot POIs on the map
    for poi in pois:
        folium.Marker(
            location=[poi["lat"], poi["lon"]],
            popup=folium.Popup(f"{poi['tags']['amenity']}", max_width=300),
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(folium_map)

    return folium_map


def download_gpx(url):
    """
    Download GPX from URL
    """

    console.print(f"⏳ Downloading GPX from {url}")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("Content-Length", 0))

    data = io.BytesIO()

    with rich.progress.Progress() as progress:
        task = progress.add_task("[cyan] Downloading", total=total_size)

        for chunk in response.iter_content(chunk_size=1024):
            data.write(chunk)
            progress.update(task, advance=len(chunk))

    data.seek(0)
    return data


def get_bounds(
    points: list[Location],
) -> tuple[float, float, float, float]:
    """
    Return GPX trace bounding box [south, west, north, est]
    """

    min_lat = min(pt.latitude for pt in points)
    max_lat = max(pt.latitude for pt in points)
    min_lon = min(pt.longitude for pt in points)
    max_lon = max(pt.longitude for pt in points)
    return min_lat, min_lon, max_lat, max_lon


def query_overpass(
    bbox: tuple[float, float, float, float], poi_types: list[AmenityType]
) -> list[POI]:
    """
    Generate an Overpass QL query for potable drinking water POIs.
    """

    south, west, north, east = bbox
    bbox_str = f"({south},{west},{north},{east})"

    query_parts = []
    for poi_type in poi_types:
        tag_filter = AMENITIES[poi_type]
        # for osm_type in ["node", "way", "relation"]:
        #     query_parts.append(f'{osm_type}{tag_filter}{bbox_str};')
        query_parts.append(f"node{tag_filter}{bbox_str};")

    query = "[out:json][timeout:25];(" + "".join(query_parts) + ");out center;"
    response = requests.post(OVERPASS_URL, data=query)
    response.raise_for_status()
    return response.json()["elements"]


def gpx_points(gpx: gpxpy.mod_gpx.GPX, use_route: bool = False) -> list[Location]:

    if use_route:
        if not gpx.routes:
            raise ValueError("GPX data does not contain any routes")

        # FIXME: should this use all routes in sequence?
        return [point for route in gpx.routes for point in route.points]

    if not gpx.tracks:
        raise ValueError("GPX data does not contain any tracks")

    return [
        point
        for track in gpx.tracks
        for segment in track.segments
        for point in segment.points
    ]


def add_waypoints_to_gpx(gpx: gpxpy.mod_gpx.GPX, pois: list[POI]) -> gpxpy.mod_gpx.GPX:
    """
    Add POI to GPX trace
    """

    for poi in pois:
        wpt = gpxpy.mod_gpx.GPXWaypoint()
        wpt.latitude = poi["lat"]
        wpt.longitude = poi["lon"]
        wpt.name = "Water"
        wpt.description = "Water"
        wpt.symbol = "water-drop"
        gpx.waypoints.append(wpt)

    return gpx


def filter_pois_near_track(
    points: list[Location], pois: list[POI], max_distance_m: float = 100
) -> list[POI]:
    """
    Keep only POI near trace
    """

    nearby_pois = []

    for poi in rich.progress.track(pois, description="Filtering POI"):
        lat, lon = poi["lat"], poi["lon"]
        if any(
            haversine_distance(lat, lon, pt.latitude, pt.longitude) < max_distance_m
            for pt in points
        ):
            nearby_pois.append(poi)

    return nearby_pois


def sanitize_gpx_text(data: str) -> str:
    """
    Fix GPX content by replacing unescaped '&' with '&amp;'
    """

    return re.sub(r"&(?!amp;|quot;|lt;|gt;|apos;)", "&amp;", data)
