<p align="center">
<img src="logo.png" alt="Thirsty Logo" width="200"/>
</p>

# Thirsty

Add hydration points to your GPX tracks automatically 🚴‍♂️💧

<p align="center">
<a href="https://www.paypal.com/donate/?business=TJAXC3T4WD66L&no_recurring=0&currency_code=EUR" target="_blank">
<img src="https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge" alt="Donate with PayPal"/>
</a>
</p>

Thirsty is a Python tool that enhances your GPX files by adding Points of Interest (POIs), particularly drinking water points, to your cycling or running routes. It integrates with the Overpass API to query OpenStreetMap for relevant points along your route and adds them to the GPX file. Ideal for long-distance cycling events, ultra races, or any activity where hydration points matter!

## Features

- **Query Overpass API**: Fetch drinking water POIs from OpenStreetMap.
- **Bounding Box Filtering**: Filter POIs around a defined area to match your GPX route.
- **Distance-based Filtering**: Ensures POIs are within a defined proximity of your GPX track.
- **Supports GPX from URL and Local Files**: Easily work with GPX files from your device or download them from a URL.
- **In-Memory Handling**: No need for temporary files; everything is handled in memory for speed.
- **Progress Bar**: Monitor download and processing progress with the `rich` module.

## ⚙️ Installation

Clone this repository and set up a virtual environment:

```bash
git clone https://github.com/jsleroy/thirsty
cd thirsty
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
pip install .
```

## Usage

### Download GPX from URL and Add POIs

This example shows how to download a GPX file from a URL, add drinking water POIs to the route, and save the modified GPX to an output file.

```bash
thirsty https://example.com/yourfile.gpx output.gpx --distance 150
```

- **URL or Local GPX**: Supports both local files and downloading from a URL.
- **Distance**: Optionally specify the maximum distance (in meters) from the track for POIs (default: 100 meters).

### Local GPX File Usage

You can also process a local GPX file:

```bash
thirsty input.gpx output.gpx --distance 150
```

### Features in Detail

#### 1. Bounding Box Filtering
- Queries the Overpass API for drinking water POIs within the bounding box of the GPX file's route.

#### 2. Distance-based Filtering
- Filters POIs that are within a specified distance from the GPX track. This ensures that only nearby POIs are added to the GPX file.

#### 3. In-Memory File Handling
- Both downloaded and local GPX files are handled entirely in memory, eliminating the need for temporary files and speeding up the process.

#### 4. Progress Bar
- During the download process, the script shows a progress bar (using the `rich` library) so you can track the download status in real-time.

## ️ Development

### Requirements

- Python 3.7+
- `requests`: For HTTP requests to Overpass API and downloading GPX files.
- `gpxpy`: For reading and writing GPX files.
- `rich`: For the progress bar and rich text output.

### Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Running the CLI

You can run the script directly from the command line. Make sure to provide the appropriate input parameters (either a local file or a URL) and specify the output file:

```bash
thirsty input.gpx output.gpx --distance 150
```

## Contributing

1. Fork this repository and create a new branch.
2. Make your changes and commit them.
3. Push your changes to your fork.
4. Create a Pull Request with a detailed description of your changes.

## License

This project is licensed under the [GNU GPL v3 License](LICENSE).
