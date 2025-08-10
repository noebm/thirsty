import argparse

import gpxpy
import rich.console
import rich.progress

import thirsty.core

console = rich.console.Console()


def main():
    default = next(iter(thirsty.core.AMENITIES))

    parser = argparse.ArgumentParser(description="Add water POI to a GPX trace.")

    parser.add_argument("input", help="input GPX trace")

    parser.add_argument("output", help="output GPX trace", type=argparse.FileType("w"))

    parser.add_argument(
        "-d", "--distance", type=float, default=100, help="search distance around trace"
    )

    parser.add_argument(
        "--html",
        action="store_true",
        help="generate HTML interactive map to <output>.html",
    )

    parser.add_argument(
        "-p",
        "--poi-type",
        action="append",
        choices=thirsty.core.AMENITIES.keys(),
        default=None,
        help=f"set which type of amenities to consider (default: {default}",
    )

    args = parser.parse_args()

    if args.input.startswith("http"):
        input = thirsty.core.download_gpx(args.input)
    else:
        input = open(args.input, "rb")  # noqa: SIM115

    if args.poi_type is None:
        args.poi_type = [default]

    console.print(f"Selected amenities: {args.poi_type}")

    gpx = gpxpy.parse(input)
    bounds = thirsty.core.get_bounds(gpx)
    pois = thirsty.core.query_overpass(bounds, args.poi_type)
    pois = thirsty.core.filter_pois_near_track(gpx, pois, max_distance_m=args.distance)
    gpx = thirsty.core.add_waypoints_to_gpx(gpx, pois)

    if args.html:
        map = thirsty.core.display_gpx_on_map(gpx, pois)
        map.save(args.output.name + ".html")

    gpx = thirsty.core.sanitize_gpx_text(gpx.to_xml())

    args.output.write(gpx)

    console.print(f"✅ Added {len(pois)} POI to {args.output.name}")
