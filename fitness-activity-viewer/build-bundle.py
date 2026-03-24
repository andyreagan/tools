#!/usr/bin/env python3
"""
Build bundled/offline versions of the activity viewer.

This script takes the CDN-based HTML files and creates bundled versions
with all dependencies inlined.
"""

import re
from pathlib import Path


def bundle_html(input_file: str, output_file: str, chart_lib: str):
    """Bundle an HTML file with all dependencies inlined."""

    print(f"\nBundling {input_file} -> {output_file}")

    # Read the source HTML
    with open(input_file, 'r') as f:
        html = f.read()

    # Read the library files
    libs_dir = Path('libs')

    leaflet_css = (libs_dir / 'leaflet.css').read_text()
    leaflet_js = (libs_dir / 'leaflet.js').read_text()
    js_yaml = (libs_dir / 'js-yaml.js').read_text()
    fit_sdk = (libs_dir / 'fitsdk.js').read_text()

    if chart_lib == 'chartjs':
        chart_js = (libs_dir / 'chart.js').read_text()
    else:  # d3
        chart_js = (libs_dir / 'd3.js').read_text()

    # Helper function to safely replace - escapes backslashes in replacement
    def safe_replace(pattern, replacement_template, content_var):
        # Use a lambda to avoid interpreting backslashes in the content
        return re.sub(pattern, lambda m: replacement_template.format(content=content_var), html)

    # Replace Leaflet CSS link with inline style
    leaflet_css_pattern = r'<link rel="stylesheet" href="https://unpkg\.com/leaflet@[\d\.]+/dist/leaflet\.css"\s*/>'
    html = re.sub(leaflet_css_pattern, lambda m: f'<style>/* Leaflet CSS */\n{leaflet_css}\n</style>', html)

    # Replace script tags with inline scripts
    # Leaflet
    leaflet_js_pattern = r'<script src="https://unpkg\.com/leaflet@[\d\.]+/dist/leaflet\.js"></script>'
    html = re.sub(leaflet_js_pattern, lambda m: f'<script>/* Leaflet.js */\n{leaflet_js}\n</script>', html)

    # Chart.js or D3.js
    if chart_lib == 'chartjs':
        chart_pattern = r'<script src="https://cdn\.jsdelivr\.net/npm/chart\.js@[\d\.]+/dist/chart\.umd\.min\.js"></script>'
        html = re.sub(chart_pattern, lambda m: f'<script>/* Chart.js */\n{chart_js}\n</script>', html)
    else:
        d3_pattern = r'<script src="https://d3js\.org/d3\.v7\.min\.js"></script>'
        html = re.sub(d3_pattern, lambda m: f'<script>/* D3.js */\n{chart_js}\n</script>', html)

    # js-yaml
    yaml_pattern = r'<script src="https://cdn\.jsdelivr\.net/npm/js-yaml@[\d\.]+/dist/js-yaml\.min\.js"></script>'
    html = re.sub(yaml_pattern, lambda m: f'<script>/* js-yaml */\n{js_yaml}\n</script>', html)

    # Garmin FIT SDK (ES Module) - bundled inline with blob URL
    # Match the entire ES module script block
    fit_pattern = r'<!-- FIT SDK as ES Module[^>]*>\s*<script type="module">\s*import[^<]+from[^;]+;\s*//[^<]+\s*window\.FitDecoder[^<]+\s*window\.FitStream[^<]+\s*</script>'

    # Create inline module using blob URL to load the bundled FIT SDK
    def create_fit_replacement(match):
        # Escape backticks and ${} in the fit_sdk content for template literal
        escaped_sdk = fit_sdk.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        return f'''<!-- FIT SDK as ES Module - bundled inline -->
    <script type="module">
        /* @garmin/fitsdk bundled by jsDelivr */
        const fitSdkCode = `{escaped_sdk}`;
        const blob = new Blob([fitSdkCode], {{ type: 'text/javascript' }});
        const url = URL.createObjectURL(blob);
        const module = await import(url);
        URL.revokeObjectURL(url);
        // Expose to window
        window.FitDecoder = module.Decoder;
        window.FitStream = module.Stream;
        // Dispatch custom event to signal FIT SDK is ready
        window.dispatchEvent(new Event('fitsdk-ready'));
    </script>'''

    html = re.sub(fit_pattern, create_fit_replacement, html, flags=re.DOTALL)

    # Add a comment at the top indicating this is a bundled version
    html = re.sub(
        r'(<!DOCTYPE html>)',
        r'\1\n<!-- BUNDLED VERSION: All JavaScript/CSS dependencies inlined.\n     Note: Map tiles still load from OpenStreetMap servers (requires internet for maps).\n     Charts, stats, and data processing work fully offline. -->',
        html
    )

    # Write the bundled HTML
    with open(output_file, 'w') as f:
        f.write(html)

    # Get file size
    size_kb = Path(output_file).stat().st_size / 1024
    print(f"  Created: {output_file} ({size_kb:.1f} KB)")


def main():
    # Check that libs directory exists
    if not Path('libs').exists():
        print("Error: libs/ directory not found!")
        print("Run ./build-offline.sh first to download dependencies.")
        return

    # Ensure dist directory exists
    Path('dist').mkdir(exist_ok=True)

    print("Building bundled/offline versions...")

    # Bundle Chart.js version
    bundle_html('src/single-page-chartjs.html', 'dist/single-page-chartjs-bundled.html', 'chartjs')

    # Bundle D3.js version
    bundle_html('src/single-page-d3.html', 'dist/single-page-d3-bundled.html', 'd3')

    print("\n✅ Bundled versions created in dist/!")
    print("\nFiles created:")
    print("  - dist/single-page-chartjs-bundled.html (Chart.js bundled)")
    print("  - dist/single-page-d3-bundled.html (D3.js bundled)")
    print("\nSource files:")
    print("  - src/single-page-chartjs.html (Chart.js source)")
    print("  - src/single-page-d3.html (D3.js source)")
    print("\nNote: All JavaScript/CSS is bundled, but map tiles still load from")
    print("      OpenStreetMap servers (internet required for maps).")
    print("      Charts, stats, and data processing work fully offline.")


if __name__ == '__main__':
    main()
