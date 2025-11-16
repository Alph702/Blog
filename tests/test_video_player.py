import os
import re
import time

import pytest
from playwright.sync_api import Page, expect


def validate_test_video_file():
    """Validates MP4 file for testing."""
    source_filepath = "tests/assets/test_video.mp4"
    print(f"Current working directory: {os.getcwd()}")
    print(f"Checking for test video at: {os.path.abspath(source_filepath)}")
    if not os.path.exists(source_filepath):
        raise FileNotFoundError(
            f"Test video file not found at {source_filepath}. Please ensure it exists."
        )

    return source_filepath


@pytest.fixture(scope="function")
def post_with_processed_video(admin_logged_in_page: Page, flask_app_url):
    """
    Fixture to create a post with a video and wait for it to be processed.
    Yields the URL of the post.
    """
    page = admin_logged_in_page
    page.goto(f"{flask_app_url}/new", timeout=600000)

    test_title = f"Video Player Test Post {time.time()}"
    video_path = validate_test_video_file()

    # Create post
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", "Video player test content.")
    page.set_input_files("input[name='video']", video_path)
    page.click("button[type='submit']")

    # Go to homepage to find the post link
    page.goto(f"{flask_app_url}/", timeout=600000)
    post_locator = page.locator(f".post:has-text('{test_title}')")
    expect(post_locator).to_be_visible(timeout=600000)
    post_link = post_locator.locator("a.post-button").first
    post_url = f"{flask_app_url}{post_link.get_attribute('href')}"
    post_id = post_url.split("/")[-1]

    # Poll for video processing
    processing_complete = False
    for i in range(120):  # Poll for up to 2 minutes
        page.goto(post_url, timeout=600000)
        player = page.locator(".video-player")
        status = player.get_attribute("data-status")
        if status == "processed":
            processing_complete = True
            break
        print(f"Polling video status... Current: {status} (Attempt {i + 1}/120)")
        time.sleep(1)

    if not processing_complete:
        pytest.fail("Video processing did not complete within the timeout period.")

    yield post_url

    # Cleanup
    page.goto(f"{flask_app_url}/delete/{post_id}", timeout=600000)


def test_video_player_volume_and_mute(page: Page, post_with_processed_video: str):
    """
    Tests the volume slider and mute button functionality.
    """
    page.goto(post_with_processed_video, timeout=600000)
    video_container = page.locator(".video-container")
    video_player = video_container.locator("video.video-player")
    mute_btn = video_container.locator(".mute-btn")
    volume_icon = mute_btn.locator("img.volume-icon")
    volume_slider = video_container.locator(".volume-slider")

    # 1. Test Mute
    expect(video_player).not_to_have_js_property("muted", True)
    expect(volume_icon).to_have_attribute("src", "/static/svg/volume-up.svg")

    mute_btn.click()

    expect(video_player).to_have_js_property("muted", True)
    expect(volume_icon).to_have_attribute("src", "/static/svg/volume-mute.svg")

    # 2. Test Unmute
    mute_btn.click()

    expect(video_player).not_to_have_js_property("muted", True)
    expect(volume_icon).to_have_attribute("src", "/static/svg/volume-up.svg")

    # 3. Test Volume Slider
    initial_volume = float(video_player.evaluate("player => player.volume"))
    assert initial_volume > 0.9  # Should be close to 1

    # Set volume to 50%
    volume_slider.evaluate(
        "slider => { slider.value = 50; slider.dispatchEvent(new Event('input')); }"
    )
    expect(video_player).to_have_js_property("volume", 0.5)
    expect(volume_icon).to_have_attribute("src", "/static/svg/volume-up.svg")

    # Set volume to 0%
    volume_slider.evaluate(
        "slider => { slider.value = 0; slider.dispatchEvent(new Event('input')); }"
    )
    expect(video_player).to_have_js_property("muted", True)
    expect(volume_icon).to_have_attribute("src", "/static/svg/volume-mute.svg")


def test_video_player_fullscreen(page: Page, post_with_processed_video: str):
    """
    Tests the fullscreen button functionality.
    Note: True fullscreen state is hard to test programmatically.
    This test checks if the button and classes are updated correctly.
    """
    page.goto(post_with_processed_video, timeout=600000)
    video_container = page.locator(".video-container")
    fullscreen_btn = video_container.locator(".fullscreen-btn")
    fullscreen_icon = fullscreen_btn.locator("img.fullscreen-icon")

    expect(fullscreen_icon).to_have_attribute("src", "/static/svg/fullscreen.svg")
    expect(video_container).not_to_have_class(re.compile(r"\bfullscreen\b"))

    # This will not actually make the browser window fullscreen in headless mode,
    # but we can check if the button icon and class change as expected.
    fullscreen_btn.click()

    expect(fullscreen_icon).to_have_attribute("src", "/static/svg/fullscreen-exit.svg")
    expect(video_container).to_have_class(re.compile(r"\bfullscreen\b"))
