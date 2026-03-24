# Test Cases for Plain Text Fitness Viewer

This directory contains test cases for different scenarios of the activity viewer.

## Test Scenarios

### 1. `full-activity/`
**Tests:** Complete activity with GPS data and metadata
- ✓ activity.fit (FIT file with GPS data)
- ✓ activity.gpx (GPX file with GPS data)
- ✓ metadata.yaml (Activity metadata)

**Expected behavior:**
- Should load GPS route and display on map
- Should show start (green) and finish (red) markers
- Should render elevation, heart rate, and pace charts
- Should show stats: distance, duration, pace, elevation gain, heart rate
- Hovering over charts should show crosshair on all charts and marker on map
- km/mi toggle should convert all units

### 2. `metadata-only/`
**Tests:** Activity without GPS data (gym workout)
- ✓ metadata.yaml (Activity metadata only)

**Expected behavior:**
- Should load and display activity title, date, type, description
- Should NOT show map, charts, or GPS-based stats
- Should NOT show km/mi toggle
- Description should display workout details

### 3. `with-media/`
**Tests:** Activity with GPS data and photos
- ✓ activity.fit (FIT file with GPS data)
- ✓ activity.gpx (GPX file with GPS data)
- ✓ metadata.yaml (Activity metadata)
- ✓ media/ directory with sample images

**Expected behavior:**
- All features from `full-activity`
- Should detect and display 64x64 thumbnails of images
- Clicking thumbnail should open full-screen gallery
- Gallery should support:
  - Arrow key navigation (← →)
  - ESC to close
  - Click prev/next buttons
  - Images scale to fit screen

## Running Tests

### Manual Testing
1. Start a local web server from the project root:
   ```bash
   python3 -m http.server 8000
   ```

2. Visit each test case:
   - http://localhost:8000/test-cases/full-activity/
   - http://localhost:8000/test-cases/metadata-only/
   - http://localhost:8000/test-cases/with-media/

### Automated Testing
Run the automated test suite:
```bash
npm test
```

## File Structure

Each test case uses a symlink to the main viewer:
```
test-cases/
├── full-activity/
│   ├── index.html -> ../../single-page-local.html
│   ├── activity.fit
│   ├── activity.gpx
│   └── metadata.yaml
├── metadata-only/
│   ├── index.html -> ../../single-page-local.html
│   └── metadata.yaml
└── with-media/
    ├── index.html -> ../../single-page-local.html
    ├── activity.fit
    ├── activity.gpx
    ├── metadata.yaml
    └── media/
        ├── photo1.svg
        ├── photo2.svg
        └── photo3.svg
```

This ensures there's only one copy of the source code.
