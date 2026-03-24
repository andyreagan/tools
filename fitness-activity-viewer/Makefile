.PHONY: all build test clean deps help

# Default target
all: build

# Help target
help:
	@echo "Plain Text Fitness - Build Targets"
	@echo ""
	@echo "  make deps     - Download JavaScript dependencies to libs/"
	@echo "  make build    - Build bundled HTML files in dist/"
	@echo "  make test     - Run all tests with pytest"
	@echo "  make all      - Build everything (deps + build)"
	@echo "  make clean    - Remove libs/ and dist/ directories"
	@echo ""

# Download dependencies from CDN to libs/
deps:
	@echo "Creating libs/ directory..."
	@mkdir -p libs
	@echo "Downloading dependencies..."
	@echo "  - Leaflet.js..."
	@curl -sL https://unpkg.com/leaflet@1.9.4/dist/leaflet.js -o libs/leaflet.js
	@echo "  - Leaflet CSS..."
	@curl -sL https://unpkg.com/leaflet@1.9.4/dist/leaflet.css -o libs/leaflet.css
	@echo "  - Chart.js..."
	@curl -sL https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js -o libs/chart.js
	@echo "  - D3.js..."
	@curl -sL https://d3js.org/d3.v7.min.js -o libs/d3.js
	@echo "  - js-yaml..."
	@curl -sL https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js -o libs/js-yaml.js
	@echo "  - @garmin/fitsdk..."
	@curl -sL "https://cdn.jsdelivr.net/npm/@garmin/fitsdk@21.171.0/+esm" -o libs/fitsdk.js
	@echo ""
	@echo "✅ Dependencies downloaded to libs/"
	@echo ""

# Build bundled HTML files
build: deps
	@echo "Building bundled HTML files..."
	@python3 build-bundle.py

# Run tests
test:
	@echo "Running tests..."
	@uv run pytest test -v

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf libs/
	@rm -rf dist/
	@rm -rf __pycache__/
	@rm -rf test/__pycache__/
	@rm -rf .pytest_cache/
	@echo "✅ Clean complete"
