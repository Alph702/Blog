import pytest
from playwright.sync_api import Page, expect
import os
import time
import re
import math

def create_test_post_with_image(page: Page, flask_app_url: str):
    """Helper function to create a post with an image."""
    page.goto(f"{flask_app_url}/new")
    
    test_title = f"Test Post with Image {time.time()}"
    test_content = "This post has an image for viewer testing."
    
    image = os.path.join(os.path.dirname(__file__), "test_viewer_image.png")

    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.set_input_files("input[name='image']", image)
    page.click("button[type='submit']")
    
    page.goto(f"{flask_app_url}/")
    page.locator("h1", has_text=test_title).click()
    post_id = page.url.split('/')[-1]
    page.goto(f"{flask_app_url}/")

    return test_title, post_id

def test_image_viewer_on_homepage(admin_logged_in_page: Page, flask_app_url: str):
    """Test that the image viewer opens on the homepage."""
    page = admin_logged_in_page
    test_title, post_id = create_test_post_with_image(page, flask_app_url)

    # Find the post and click the image
    post_locator = page.locator(f".post:has(h1:has-text(\"{test_title}\"))")
    image_locator = post_locator.locator("img")
    expect(image_locator).to_be_visible()
    image_locator.click()

    # Check if the viewer is visible
    viewer = page.locator(".viewer-container")
    expect(viewer).to_be_visible()
    expect(viewer).to_have_class(re.compile(r"viewer-in"))

    page.goto(f"{flask_app_url}/delete/{post_id}")

def test_image_viewer_on_post_page(admin_logged_in_page: Page, flask_app_url: str):
    """Test that the image viewer opens on the post page."""
    page = admin_logged_in_page
    test_title, post_id = create_test_post_with_image(page, flask_app_url)

    # Navigate to the post page
    page.locator(f"a:has-text(\"{test_title}\")").click()

    # Click the image on the post page
    image_locator = page.locator(".gallery img")
    expect(image_locator).to_be_visible()
    image_locator.click()

    # Check if the viewer is visible
    viewer = page.locator(".viewer-container")
    expect(viewer).to_be_visible()
    expect(viewer).to_have_class(re.compile(r"viewer-in"))

    page.goto(f"{flask_app_url}/delete/{post_id}")

def test_image_viewer_zoom_scroll(admin_logged_in_page: Page, flask_app_url: str):
    """Test zoom functionality even when toolbar is disabled, using bounding box measurement."""
    page = admin_logged_in_page
    test_title, post_id = create_test_post_with_image(page, flask_app_url)

    # Go to post page
    page.locator(f"a:has-text('{test_title}')").click()

    # Open image viewer
    image_locator = page.locator(".gallery img")
    image_locator.click()
    expect(page.locator(".viewer-container")).to_be_visible()

    # Select visible image inside the viewer
    viewer_image = page.locator(".viewer-canvas img, .viewer-image, .viewer-move img").first
    expect(viewer_image).to_be_visible()

    # Get initial bounding box size
    box_before = viewer_image.bounding_box()
    print(f"Before zoom: {box_before}")

    # Simulate zoom gesture (scroll or pinch gesture)
    viewer_image.dispatch_event("wheel", {"deltaY": -300, "ctrlKey": True})
    page.wait_for_timeout(1000)

    # Measure after zoom
    box_after = viewer_image.bounding_box()
    print(f"After zoom: {box_after}")

    # Check that dimensions increased (zoomed in)
    assert box_after and box_before, "Bounding boxes could not be measured"
    area_before = box_before["width"] * box_before["height"]
    area_after = box_after["width"] * box_after["height"]

    zoom_ratio = area_after / area_before if area_before > 0 else 0
    print(f"Zoom ratio: {zoom_ratio:.2f}")

    assert zoom_ratio > 1.1, f"Zoom failed — area ratio {zoom_ratio:.2f}"

    # Cleanup
    page.goto(f"{flask_app_url}/delete/{post_id}")