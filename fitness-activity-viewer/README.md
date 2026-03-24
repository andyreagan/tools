# Plain Text Fitness Activity Viewer

A self-contained, local-first fitness activity viewer that works with .fit and .gpx files. No database, no backend, no server - just a single HTML file, your browser, and your fitness data.

Available in two versions: **Chart.js** (recommended, simpler) and **D3.js** (advanced, more flexible).

## Features

### Core Functionality
- **GPS Activity Viewing**: Load .fit and .gpx files to visualize your runs, rides, and other GPS activities
- **Interactive Map**: OpenStreetMap-based route visualization with distinctive start (green) and finish (red) markers
- **Real-time Charts**: Elevation, heart rate, and pace charts with synchronized hover interaction
- **Chart-to-Map Linking**: Hover over any chart to see a vertical crosshair on all charts and your position on the map
- **Unit Toggle**: Switch between metric (km) and imperial (mi) units on the fly
- **Media Gallery**: Automatically detect photos in a `media/` folder with full-screen gallery viewer
- **Metadata-Only Mode**: Works without GPS data for gym workouts, yoga, etc.

### Display
- Clean, compact Strava/Garmin Connect-inspired interface
- Activity stats: distance, duration, pace, elevation gain, heart rate
- Human-readable metadata in YAML or Org-mode format
- 64x64 photo thumbnails with click-to-expand gallery

## Two Implementations (CDN or Bundled)

This project includes **two implementations** of the activity viewer, each available in both **CDN** and **bundled/offline** versions:

### Chart.js Version (Recommended)
- **CDN version** (`src/single-page-chartjs.html`, ~55KB)
  - Loads libraries from CDN, requires internet connection
  - Smaller file size, faster to load on repeat visits

- **Bundled version** (`dist/single-page-chartjs-bundled.html`, ~830KB)
  - All JavaScript/CSS dependencies inlined
  - **Map tiles still load from OpenStreetMap** (requires internet for maps)
  - Charts, stats, and data parsing work fully offline

### D3.js Version (Advanced)
- **CDN version** (`src/single-page-d3.html`, ~55KB)
  - Loads libraries from CDN, requires internet connection

- **Bundled version** (`dist/single-page-d3-bundled.html`, ~900KB)
  - All JavaScript/CSS dependencies inlined
  - **Map tiles still load from OpenStreetMap** (requires internet for maps)
  - Charts, stats, and data parsing work fully offline

**Why two chart libraries?**
- **Chart.js**: Simpler API, easier to understand, great for most use cases
- **D3.js**: More powerful, fine-grained control, better for custom visualizations

All versions share the same map (Leaflet.js), file parsing, and metadata handling.

## Quick Start

1. **Choose your version and place your activity data in a folder:**
   ```
   my-activity/
   ├── index.html          (symlink to one of:)
   │                       (  dist/single-page-chartjs-bundled.html - recommended, works offline)
   │                       (  src/single-page-chartjs.html - smaller, needs internet)
   │                       (  dist/single-page-d3-bundled.html - D3, works offline)
   │                       (  src/single-page-d3.html - D3, needs internet)
   ├── activity.fit        (optional)
   ├── activity.gpx        (optional)
   ├── metadata.yaml       (optional but recommended)
   └── media/              (optional - photos/videos)
       ├── photo1.jpg
       └── photo2.jpg
   ```

2. **Start a local web server:**
   ```bash
   python3 -m http.server 8000
   ```

3. **Open in browser:**
   ```
   http://localhost:8000/my-activity/
   ```

## Metadata Format (YAML)

```yaml
title: "Morning Run"
date: 2025-11-03
type: "running"
description: |
  Great morning run through the neighborhood.
  Weather was perfect and felt strong throughout.

weather: "Clear, 15°C"
effort: "Easy"
shoes: "Nike Pegasus 40"

tags:
  - morning
  - easy-run
  - neighborhood
```

All fields are optional. You can add any custom fields you want!

## File Structure

```
plain-text-fitness/
├── src/                                    # Source files (edit these)
│   ├── single-page-chartjs.html           # Chart.js version (CDN, ~55KB)
│   └── single-page-d3.html                # D3.js version (CDN, ~55KB)
├── dist/                                   # Built files (auto-generated, committed)
│   ├── single-page-chartjs-bundled.html   # Chart.js bundled (~830KB)
│   └── single-page-d3-bundled.html        # D3.js bundled (~900KB)
├── test/                                   # All test-related files
│   ├── test_activity_viewer.py            # Playwright tests (41 tests)
│   ├── conftest.py                        # Pytest configuration
│   └── test-cases/                        # Test fixtures (sample data)
│       ├── full-activity/                 # Chart.js CDN version
│       ├── bundled/                       # Chart.js bundled version
│       ├── full-activity-d3/              # D3.js CDN version
│       ├── bundled-d3/                    # D3.js bundled version
│       ├── metadata-only/                 # Gym workout (no GPS)
│       └── with-media/                    # GPS data + photos
├── Makefile                               # Build and test automation
├── build-bundle.py                        # Build script (called by Makefile)
└── pyproject.toml                         # Python dependencies and config
```

### Development Workflow

1. **Edit source files** in `src/`
2. **Run build** to update `dist/`: `make build`
3. **Run tests**: `make test`

See `make help` for all available targets.

## Testing

### Manual Testing
```bash
python3 -m http.server 8000
# Visit: http://localhost:8000/test/test-cases/test-runner.html
```

### Automated Testing
We have comprehensive Playwright + pytest automated tests with automatic server management:
```bash
# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install browser
uv run playwright install chromium

# Run tests (server starts automatically!)
uv run pytest test_activity_viewer.py -v
```

See `TESTING.md` for complete documentation.

## Use Cases

### GPS Activities
- Running, cycling, hiking with route visualization
- Full stats and charts
- Heart rate, pace, elevation analysis

### Non-GPS Activities
- Gym workouts
- Yoga sessions
- Strength training
- Just use metadata.yaml with title, date, description, and custom fields

### Photo Documentation
- Add photos to any activity in the `media/` folder
- Automatic thumbnail generation and gallery view
- Perfect for scenic runs, race photos, or form checks

## Technology Stack

- **No build step required**: Single HTML files ready to use
- **Client-side processing**: All file parsing and rendering happens in your browser
- **Two deployment options**:
  - **CDN versions**: Small files (~50KB), load libraries from CDN (requires internet)
  - **Bundled versions**: Large files (~450-520KB), JavaScript/CSS inlined (map tiles still need internet)

**Dependencies** (auto-bundled in offline versions):
- Leaflet.js (maps)
- Chart.js or D3.js (charts)
- js-yaml (YAML parsing)
- fit-file-parser (FIT file parsing)

### Library Choices vs. Competitors

We provide **two implementations** - one with Chart.js, one with D3.js. For comparison:

- **Strava**: Uses D3.js v3.3 for charts and Mapbox GL JS (with Leaflet compatibility layer) for maps
- **Garmin Connect**: Uses Highcharts v11.4.1 for charts and Leaflet.js for maps

**Chart.js version** (recommended):
- Lightweight and easy to understand
- Well-documented with simple API
- Perfect for standard fitness visualizations

**D3.js version** (advanced):
- More powerful and flexible
- Fine-grained control for custom visualizations
- Similar to what Strava uses

Both are free and open source with no API keys or accounts required.

## Philosophy

This project follows the "plain text" philosophy:
- Your data is yours: human-readable text files
- No proprietary formats or databases
- No vendor lock-in
- No server or cloud services required (runs locally)
- Easy to version control (git)
- Future-proof: as long as you have a browser, you can view your data

**Partial offline support**: Bundled versions (`dist/single-page-chartjs-bundled.html` and `dist/single-page-d3-bundled.html`) have all JavaScript/CSS inlined. However, map tiles still load from OpenStreetMap servers, so **internet connection is required to view maps**. Charts, stats, and all data processing work offline.

## Building Bundled Versions

The bundled versions in `dist/` are pre-built and included in the repository. To rebuild them after editing source files in `src/`:

```bash
make build
```

This will:
1. Download dependencies from CDN to `libs/`
2. Build bundled HTML files in `dist/`

Available targets:
- `make deps` - Download JavaScript dependencies only
- `make build` - Build bundled HTML files (includes deps)
- `make test` - Run all tests with pytest
- `make clean` - Remove libs/ and dist/ directories
- `make help` - Show all available targets

This will create/update:
- `dist/single-page-chartjs-bundled.html` (Chart.js bundled ~830KB)
- `dist/single-page-d3-bundled.html` (D3.js bundled ~900KB)

## Export from Strava/Garmin

1. **Strava**: Go to activity → More (...) → Export GPX or Export TCX
2. **Garmin Connect**: Activity → Gear icon → Export to GPX or Export Original

Then add a `metadata.yaml` with your notes, shoes, weather, etc.

## Contributing

This project maintains clean separation between source and built files:

### Source Files (edit these)
- `src/single-page-chartjs.html` - Chart.js version with CDN dependencies
- `src/single-page-d3.html` - D3.js version with CDN dependencies

### Build Process
After editing source files, rebuild the bundled versions:
```bash
make build                      # Download dependencies + generate dist/ files
```

This creates:
- `dist/single-page-chartjs-bundled.html` (auto-generated)
- `dist/single-page-d3-bundled.html` (auto-generated)

**Note**: The `dist/` directory IS committed to the repository so users get pre-built files.

### Testing
1. **Automated** (recommended): `make test`
   - 41 tests covering all 4 versions
   - Tests in `test/test_activity_viewer.py`
   - Automatic background server management

2. **Manual**:
   ```bash
   python3 -m http.server 8000
   # Visit: http://localhost:8000/test/test-cases/test-runner.html
   ```

## License

MIT - Do whatever you want with it!
