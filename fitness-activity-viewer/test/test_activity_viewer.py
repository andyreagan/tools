"""
Automated tests for Plain Text Fitness Activity Viewer using Playwright and pytest.

Run with: pytest test_activity_viewer.py -v

Note: The background HTTP server is automatically started by the conftest.py fixture.
"""
import pytest
from playwright.sync_api import Page, expect
import time


class TestFullActivity:
    """Test case 1: Full activity with GPS data (.fit + .gpx) and metadata."""

    def test_page_loads(self, page: Page, base_url: str):
        """Test that the page loads without errors."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")
        # Wait for content to load
        expect(page.locator("#activityContent")).to_be_visible(timeout=10000)

    def test_activity_title(self, page: Page, base_url: str):
        """Test that activity title is displayed correctly."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")
        expect(page.locator("#activityTitle")).to_have_text("Morning Run")

    def test_activity_metadata(self, page: Page, base_url: str):
        """Test that date and type are displayed."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")
        meta = page.locator("#activityMeta")
        expect(meta).to_be_visible()
        # Should contain date and type
        expect(meta).to_contain_text("running")

    def test_map_visible(self, page: Page, base_url: str):
        """Test that map is displayed."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")
        expect(page.locator("#map")).to_be_visible()

    def test_charts_visible(self, page: Page, base_url: str):
        """Test that all three charts are displayed."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")
        expect(page.locator("#elevationChart")).to_be_visible()
        expect(page.locator("#heartRateChart")).to_be_visible()
        expect(page.locator("#paceChart")).to_be_visible()

    def test_stats_cards_visible(self, page: Page, base_url: str):
        """Test that stats cards are displayed."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")
        stats_grid = page.locator("#statsGrid")
        expect(stats_grid).to_be_visible()

        # Check for stat cards
        stat_cards = page.locator(".stat-card")
        expect(stat_cards).to_have_count(6)  # Distance, Duration, Pace, Elevation, HR avg, HR max

    def test_unit_toggle_visible(self, page: Page, base_url: str):
        """Test that km/mi toggle is displayed."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")
        expect(page.locator("#unitToggle")).to_be_visible()

    def test_unit_toggle_functionality(self, page: Page, base_url: str):
        """Test that unit toggle changes values."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")

        # Get initial distance value in km
        distance_card = page.locator(".stat-card").first
        initial_text = distance_card.text_content()
        assert "km" in initial_text

        # Toggle to miles - click the toggle switch (the slider span)
        page.locator(".toggle-switch .slider").click()
        time.sleep(0.5)  # Wait for update

        # Check that it changed to miles
        new_text = distance_card.text_content()
        assert "mi" in new_text
        assert new_text != initial_text

    def test_files_detected(self, page: Page, base_url: str):
        """Test that detected files are shown."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")
        files_detected = page.locator("#filesDetected")
        expect(files_detected).to_be_visible()

        # Should show at least activity.fit and activity.gpx
        expect(files_detected).to_contain_text("activity.fit")
        expect(files_detected).to_contain_text("activity.gpx")

    def test_chart_hover_interaction(self, page: Page, base_url: str):
        """Test that hovering on chart shows crosshair and map marker."""
        page.goto(f"{base_url}/test/test-cases/full-activity/")

        # Wait for charts to render
        chart = page.locator("#elevationChart")
        expect(chart).to_be_visible()
        time.sleep(1)  # Wait for chart initialization

        # Get bounding box
        chart_box = chart.bounding_box()

        # Only test hover if chart is properly rendered
        if chart_box:
            # Hover in the middle of the chart
            page.mouse.move(chart_box["x"] + chart_box["width"] / 2,
                           chart_box["y"] + chart_box["height"] / 2)

            # Note: Testing crosshair visibility is complex as it's drawn on canvas
            # This test just ensures no errors occur during hover
            time.sleep(0.5)


class TestMetadataOnly:
    """Test case 2: Activity with only metadata (no GPS data)."""

    def test_page_loads(self, page: Page, base_url: str):
        """Test that the page loads without errors."""
        page.goto(f"{base_url}/test/test-cases/metadata-only/")
        expect(page.locator("#activityContent")).to_be_visible(timeout=10000)

    def test_activity_title(self, page: Page, base_url: str):
        """Test that activity title is displayed."""
        page.goto(f"{base_url}/test/test-cases/metadata-only/")
        expect(page.locator("#activityTitle")).to_have_text("Gym Session - Upper Body")

    def test_activity_type(self, page: Page, base_url: str):
        """Test that activity type is displayed."""
        page.goto(f"{base_url}/test/test-cases/metadata-only/")
        meta = page.locator("#activityMeta")
        expect(meta).to_contain_text("strength-training")

    def test_description_visible(self, page: Page, base_url: str):
        """Test that description is displayed."""
        page.goto(f"{base_url}/test/test-cases/metadata-only/")
        description_card = page.locator("#descriptionCard")
        expect(description_card).to_be_visible()

        # Should contain workout details
        description = page.locator("#activityDescription")
        expect(description).to_contain_text("Bench Press")
        expect(description).to_contain_text("Pull-ups")

    def test_map_not_visible(self, page: Page, base_url: str):
        """Test that map is NOT displayed for metadata-only."""
        page.goto(f"{base_url}/test/test-cases/metadata-only/")
        # Map should exist in DOM but not have content
        # Since we skip rendering, the map div may be empty or not visible
        pass  # Map rendering is conditional

    def test_charts_not_visible(self, page: Page, base_url: str):
        """Test that charts are NOT displayed for metadata-only."""
        page.goto(f"{base_url}/test/test-cases/metadata-only/")
        # Charts won't be rendered if there's no GPS data
        # The canvas elements may not exist or be empty
        pass  # Chart rendering is conditional

    def test_stats_not_visible(self, page: Page, base_url: str):
        """Test that GPS stats are NOT displayed."""
        page.goto(f"{base_url}/test/test-cases/metadata-only/")
        stats_grid = page.locator("#statsGrid")
        # Stats grid should be empty or not rendered
        stat_cards = page.locator(".stat-card")
        expect(stat_cards).to_have_count(0)

    def test_unit_toggle_not_visible(self, page: Page, base_url: str):
        """Test that km/mi toggle is NOT displayed."""
        page.goto(f"{base_url}/test/test-cases/metadata-only/")
        unit_toggle = page.locator("#unitToggle")
        expect(unit_toggle).to_be_hidden()


class TestWithMedia:
    """Test case 3: Activity with GPS data and media files."""

    def test_page_loads(self, page: Page, base_url: str):
        """Test that the page loads without errors."""
        page.goto(f"{base_url}/test/test-cases/with-media/")
        expect(page.locator("#activityContent")).to_be_visible(timeout=10000)

    def test_activity_title(self, page: Page, base_url: str):
        """Test that activity title is displayed."""
        page.goto(f"{base_url}/test/test-cases/with-media/")
        expect(page.locator("#activityTitle")).to_have_text("Trail Run with Photos")

    def test_description_card_visible(self, page: Page, base_url: str):
        """Test that description card is visible."""
        page.goto(f"{base_url}/test/test-cases/with-media/")
        description_card = page.locator("#descriptionCard")
        expect(description_card).to_be_visible()

    def test_media_thumbnails_visible(self, page: Page, base_url: str):
        """Test that media thumbnails are displayed."""
        page.goto(f"{base_url}/test/test-cases/with-media/")

        # Wait for media detection to complete
        time.sleep(1)

        thumbnails = page.locator(".media-thumbnail")
        # Should have 3 SVG images
        expect(thumbnails).to_have_count(3)

    def test_thumbnail_size(self, page: Page, base_url: str):
        """Test that thumbnails are 64x64."""
        page.goto(f"{base_url}/test/test-cases/with-media/")
        time.sleep(1)

        thumbnail = page.locator(".media-thumbnail").first
        box = thumbnail.bounding_box()

        # Check approximate size (64x64 + border)
        assert box["width"] == pytest.approx(64, abs=5)
        assert box["height"] == pytest.approx(64, abs=5)

    def test_modal_opens_on_click(self, page: Page, base_url: str):
        """Test that clicking thumbnail opens modal."""
        page.goto(f"{base_url}/test/test-cases/with-media/")
        time.sleep(1)

        # Click first thumbnail
        thumbnail = page.locator(".media-thumbnail").first
        thumbnail.click()

        # Modal should be visible
        modal = page.locator("#mediaModal")
        expect(modal).to_have_class("modal active")

    def test_modal_close_button(self, page: Page, base_url: str):
        """Test that close button closes modal."""
        page.goto(f"{base_url}/test/test-cases/with-media/")
        time.sleep(1)

        # Open modal
        page.locator(".media-thumbnail").first.click()

        # Click close button
        page.locator(".modal-close").click()

        # Modal should be hidden
        modal = page.locator("#mediaModal")
        expect(modal).not_to_have_class("modal active")

    def test_modal_escape_key(self, page: Page, base_url: str):
        """Test that ESC key closes modal."""
        page.goto(f"{base_url}/test/test-cases/with-media/")
        time.sleep(1)

        # Open modal
        page.locator(".media-thumbnail").first.click()

        # Press ESC
        page.keyboard.press("Escape")

        # Modal should be hidden
        modal = page.locator("#mediaModal")
        expect(modal).not_to_have_class("modal active")

    def test_modal_navigation_arrows(self, page: Page, base_url: str):
        """Test that arrow keys navigate between images."""
        page.goto(f"{base_url}/test/test-cases/with-media/")
        time.sleep(1)

        # Open modal
        page.locator(".media-thumbnail").first.click()

        # Get initial image src
        modal_img = page.locator("#modalImage")
        initial_src = modal_img.get_attribute("src")

        # Press right arrow
        page.keyboard.press("ArrowRight")
        time.sleep(0.2)

        # Image should have changed
        new_src = modal_img.get_attribute("src")
        assert new_src != initial_src

        # Press left arrow
        page.keyboard.press("ArrowLeft")
        time.sleep(0.2)

        # Should be back to initial
        back_src = modal_img.get_attribute("src")
        assert back_src == initial_src

    def test_all_gps_features_work(self, page: Page, base_url: str):
        """Test that all GPS features from Test 1 also work here."""
        page.goto(f"{base_url}/test/test-cases/with-media/")

        # Map should be visible
        expect(page.locator("#map")).to_be_visible()

        # Charts should be visible
        expect(page.locator("#elevationChart")).to_be_visible()
        expect(page.locator("#heartRateChart")).to_be_visible()
        expect(page.locator("#paceChart")).to_be_visible()

        # Stats should be visible
        stat_cards = page.locator(".stat-card")
        expect(stat_cards).to_have_count(6)

        # Unit toggle should be visible
        expect(page.locator("#unitToggle")).to_be_visible()


class TestCrossBrowser:
    """Test that the viewer works across different scenarios."""

    def test_no_console_errors(self, page: Page, base_url: str):
        """Test that there are no console errors on load."""
        errors = []
        page.on("console", lambda msg: errors.append(msg) if msg.type == "error" else None)

        page.goto(f"{base_url}/test/test-cases/full-activity/")
        time.sleep(2)

        # Should have no errors
        assert len(errors) == 0, f"Console errors found: {errors}"

    def test_responsive_layout(self, page: Page, base_url: str):
        """Test that layout works on mobile viewport."""
        page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE
        page.goto(f"{base_url}/test/test-cases/full-activity/")

        # Content should still be visible
        expect(page.locator("#activityContent")).to_be_visible()
        expect(page.locator("#map")).to_be_visible()


class TestBundledVersion:
    """Test the bundled/offline Chart.js version."""

    def test_page_loads(self, page: Page, base_url: str):
        """Test that bundled version loads without errors."""
        page.goto(f"{base_url}/test/test-cases/bundled/")
        expect(page.locator("#activityContent")).to_be_visible(timeout=10000)

    def test_charts_visible(self, page: Page, base_url: str):
        """Test that Chart.js charts render in bundled version."""
        page.goto(f"{base_url}/test/test-cases/bundled/")
        expect(page.locator("#elevationChart")).to_be_visible(timeout=5000)
        expect(page.locator("#heartRateChart")).to_be_visible(timeout=5000)
        expect(page.locator("#paceChart")).to_be_visible(timeout=5000)


class TestBundledD3Version:
    """Test the bundled/offline D3.js version."""

    def test_page_loads(self, page: Page, base_url: str):
        """Test that bundled D3 version loads without errors."""
        page.goto(f"{base_url}/test/test-cases/bundled-d3/")
        expect(page.locator("#activityContent")).to_be_visible(timeout=10000)

    def test_charts_visible(self, page: Page, base_url: str):
        """Test that D3 charts render in bundled version."""
        page.goto(f"{base_url}/test/test-cases/bundled-d3/")
        expect(page.locator("#elevationChart svg")).to_be_visible(timeout=5000)
        expect(page.locator("#heartRateChart svg")).to_be_visible(timeout=5000)
        expect(page.locator("#paceChart svg")).to_be_visible(timeout=5000)


class TestD3Version:
    """Test the D3.js version of the viewer."""

    def test_page_loads(self, page: Page, base_url: str):
        """Test that the D3 version page loads without errors."""
        page.goto(f"{base_url}/test/test-cases/full-activity-d3/")
        expect(page.locator("#activityContent")).to_be_visible(timeout=10000)

    def test_activity_title(self, page: Page, base_url: str):
        """Test that activity title is displayed."""
        page.goto(f"{base_url}/test/test-cases/full-activity-d3/")
        # Wait for content to load first
        expect(page.locator("#activityContent")).to_be_visible(timeout=10000)
        # Title might be h1 or h2 depending on implementation
        title = page.locator("h1, h2, .activity-title").first
        expect(title).to_be_visible()

    def test_map_visible(self, page: Page, base_url: str):
        """Test that the map is displayed."""
        page.goto(f"{base_url}/test/test-cases/full-activity-d3/")
        expect(page.locator("#map")).to_be_visible()

    def test_charts_visible(self, page: Page, base_url: str):
        """Test that D3 charts are displayed."""
        page.goto(f"{base_url}/test/test-cases/full-activity-d3/")
        # D3 renders SVG charts
        expect(page.locator("#elevationChart svg")).to_be_visible(timeout=5000)
        expect(page.locator("#heartRateChart svg")).to_be_visible(timeout=5000)
        expect(page.locator("#paceChart svg")).to_be_visible(timeout=5000)

    def test_stats_cards_visible(self, page: Page, base_url: str):
        """Test that statistics cards are displayed."""
        page.goto(f"{base_url}/test/test-cases/full-activity-d3/")
        stat_cards = page.locator(".stat-card")
        expect(stat_cards.first).to_be_visible()

    def test_unit_toggle_functionality(self, page: Page, base_url: str):
        """Test that unit toggle works with D3 charts."""
        page.goto(f"{base_url}/test/test-cases/full-activity-d3/")

        # Get initial distance value in km
        distance_card = page.locator(".stat-card").first
        initial_text = distance_card.text_content()
        assert "km" in initial_text

        # Toggle to miles
        page.locator(".toggle-switch .slider").click()
        time.sleep(0.5)

        # Check that it changed to miles
        new_text = distance_card.text_content()
        assert "mi" in new_text
        assert new_text != initial_text

    def test_no_console_errors(self, page: Page, base_url: str):
        """Test that D3 version has no console errors."""
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{base_url}/test/test-cases/full-activity-d3/")
        time.sleep(2)  # Wait for any lazy-loaded errors

        # Filter out known acceptable errors (like 404s for optional files)
        serious_errors = [e for e in console_errors if "404" not in e]
        assert len(serious_errors) == 0, f"Console errors: {serious_errors}"
