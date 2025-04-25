import argparse
import math
from io import BytesIO

import gpxpy
import requests

from rich.console import Console
from rich.progress import track


OVERPASS_URL = "http://overpass-api.de/api/interpreter"


console = Console()


def download_gpx(url):
    """
    Download GPX from URL
    """

    console.print(f"⏳ Downloading GPX from {url}")
    # response = requests.get(url)
    # response.raise_for_status()
    # return BytesIO(response.content)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('Content-Length', 0))

    data = BytesIO()

    with Progress() as progress:
        task = progress.add_task("[cyan] Downloading", total=total_size)

        for chunk in response.iter_content(chunk_size=1024):
            data.write(chunk)
            progress.update(task, advance=len(chunk))

    data.seek(0)
    return data

def get_bounds(gpx):
    """
    Return GPX trace bounding box [south, west, north, est]
    """

    min_lat = min(pt.latitude for trk in gpx.tracks for seg in trk.segments for pt in seg.points)
    max_lat = max(pt.latitude for trk in gpx.tracks for seg in trk.segments for pt in seg.points)
    min_lon = min(pt.longitude for trk in gpx.tracks for seg in trk.segments for pt in seg.points)
    max_lon = max(pt.longitude for trk in gpx.tracks for seg in trk.segments for pt in seg.points)
    return min_lat, min_lon, max_lat, max_lon


def query_drinking_water(min_lat, min_lon, max_lat, max_lon):
    """
    Query overpass API for water
    """

    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="drinking_water"]({min_lat},{min_lon},{max_lat},{max_lon});
      node["natural"="spring"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out body;
    """
    response = requests.post(OVERPASS_URL, data=query)
    response.raise_for_status()
    return response.json()["elements"]


def add_waypoints_to_gpx(gpx, pois):
    """
    Add POI to GPX trace
    """

    for poi in pois:
        wpt = gpxpy.gpx.GPXWaypoint()
        wpt.latitude = poi["lat"]
        wpt.longitude = poi["lon"]
        wpt.name = "Eau"
        wpt.description = "Water"
        gpx.waypoints.append(wpt)
    return gpx


def haversine(lat1, lon1, lat2, lon2):
    """
    Return distance in meter between two GPS points
    """

    R = 6371000 # Earth radius in meter
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def filter_pois_near_track(gpx, pois, max_distance_m=100):
    """
    Keep only POI near trace
    """

    points = [pt for trk in gpx.tracks for seg in trk.segments for pt in seg.points]
    nearby_pois = []

    for poi in track(pois, description="Filtering POI"):
        lat, lon = poi["lat"], poi["lon"]
        if any(haversine(lat, lon, pt.latitude, pt.longitude) < max_distance_m for pt in points):
            nearby_pois.append(poi)

    return nearby_pois


def main():
    parser = argparse.ArgumentParser(description="Add water POI to a GPX trace.")

    parser.add_argument("input", help="input GPX trace")

    parser.add_argument("output", help="output GPX trace",
                        type=argparse.FileType("w"))

    parser.add_argument("-d", "--distance", type=float, default=100,
                        help="search distance around trace")

    args = parser.parse_args()

    if args.input.startswith("http"):
        input = download_gpx(args.input)
    else:
        input = open(args.input, "rb")

    gpx = gpxpy.parse(input)
    bounds = get_bounds(gpx)
    pois = query_drinking_water(*bounds)
    pois = filter_pois_near_track(gpx, pois, max_distance_m=args.distance)
    gpx = add_waypoints_to_gpx(gpx, pois)

    args.output.write(gpx.to_xml())

    console.print(f"✅ Added {len(pois)} POI to {args.output.name}")
