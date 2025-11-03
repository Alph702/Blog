import pytest
from playwright.sync_api import Page, expect
import os
import time
import re
import shutil

def create_test_video_file(filename="test_video.mp4"):
    """Copies a small, dummy MP4 file for testing from tmp/uploads."""
    source_filepath = os.path.join("tmp", "uploads", "video.mp4")
    destination_filepath = os.path.join(os.path.dirname(__file__), filename)

    if not os.path.exists(source_filepath):
        raise FileNotFoundError(f"Test video file not found at {source_filepath}. Please ensure it exists.")
    
    shutil.copy(source_filepath, destination_filepath)
    return destination_filepath

def test_create_post_with_video(admin_logged_in_page: Page, flask_app_url):
    """
    Tests creating a post with a video, verifying processing, and cleanup.
    """
    page = admin_logged_in_page
    page.goto(f"{flask_app_url}/new")
    expect(page).to_have_title("New Post")

    test_title = f"Test Post with Video {time.time()}"
    test_content = "This post has a video that should be processed."
    video_path = create_test_video_file()

    # 1. Create the post with a video
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.set_input_files("input[name='video']", video_path)
    page.click("button[type='submit']")

    # Expect to be on the same page with a success message
    expect(page).to_have_url(f"{flask_app_url}/new")
    expect(page.locator(".toast-success")).to_be_visible()

    # 2. Verify the post and initial video state on the homepage
    page.goto(f"{flask_app_url}/")
    post_locator = page.locator(f".post:has-text('{test_title}')")
    expect(post_locator).to_be_visible()

    video_player = post_locator.locator(".video-js")
    # expect(video_player).to_be_visible()
    
    # The video is processing, so it should have the original mp4 url
    initial_video_url = video_player.get_attribute("data-url")
    assert initial_video_url, "Video player should have a data-url attribute"
    assert "upload" in initial_video_url

    # 3. Poll and wait for the video to be processed
    post_link = post_locator.locator("a.post-button").first
    post_url = f"{flask_app_url}{post_link.get_attribute('href')}"
    
    processing_complete = False
    for i in range(120): # Poll for up to 120 seconds
        page.goto(post_url)
        player_on_post_page = page.locator(".video-js")
        status = player_on_post_page.get_attribute("data-status")
        if status == "processed":
            processing_complete = True
            break
        time.sleep(1)
        print(f"Polling video status... Current: {status} (Attempt {i+1}/120)")
        if page.url != post_url:
            print(f"Redirected to {page.url}, navigating back to {post_url}")
            page.goto(post_url)

    assert processing_complete, "Video processing did not complete within the timeout period."

    # 4. Verify the final state on the post page
    page.goto(post_url)
    final_player = page.locator(".video-js")
    expect(final_player).to_have_attribute("data-status", "processed")
    
    processed_video_url = final_player.get_attribute("data-url")
    assert processed_video_url, "Processed video player should have a data-url"
    assert ".m3u8" in processed_video_url, "Processed video URL should be an HLS playlist"
    assert processed_video_url != initial_video_url, "Video URL should have changed after processing"

    # 5. Cleanup
    post_id = post_url.split('/')[-1]
    page.goto(f"{flask_app_url}/delete/{post_id}")
    expect(page.locator(f".post:has-text('{test_title}')")).not_to_be_visible()
    
    # Clean up the dummy video file
    if os.path.exists(video_path):
        os.remove(video_path)

def test_edit_post_to_add_video(admin_logged_in_page: Page, flask_app_url):
    """
    Tests adding a video to a post that initially has none.
    """
    page = admin_logged_in_page
    
    # 1. Create a post without a video
    test_title = f"Add Video Test {time.time()}"
    page.goto(f"{flask_app_url}/new")
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", "This post will have a video added.")
    page.click("button[type='submit']")
    
    page.goto(f"{flask_app_url}/")
    page.locator("a", has_text=test_title).click()
    post_id = page.url.split('/')[-1]

    # 2. Edit the post to add a video
    page.goto(f"{flask_app_url}/edit/{post_id}")
    expect(page.locator(".video-js")).not_to_be_visible() # No video initially
    
    video_path = create_test_video_file("edit_video.mp4")
    page.set_input_files("input[name='video']", video_path)
    page.click("button[type='submit']")

    # 3. Verify the video was added and poll for processing completion
    expect(page).to_have_url(f"{flask_app_url}/")
    page.goto(f"{flask_app_url}/post/{post_id}")
    
    processing_complete = False
    for i in range(120): # Poll for up to 120 seconds
        page.goto(f"{flask_app_url}/post/{post_id}")
        player_on_post_page = page.locator(".video-js")
        status = player_on_post_page.get_attribute("data-status")
        if status == "processed":
            processing_complete = True
            break
        time.sleep(1)
        print(f"Polling video status for edit... Current: {status} (Attempt {i+1}/120)")
        if page.url != f"{flask_app_url}/post/{post_id}":
            print(f"Redirected to {page.url}, navigating back to {flask_app_url}/post/{post_id}")
            page.goto(f"{flask_app_url}/post/{post_id}")

    assert processing_complete, "Video processing did not complete within the timeout period after edit."

    page.goto(f"{flask_app_url}/post/{post_id}")
    final_player = page.locator(".video-js")
    expect(final_player).to_have_attribute("data-status", "processed")
    
    processed_video_url = final_player.get_attribute("data-url")
    assert processed_video_url, "Processed video player should have a data-url after edit"
    assert ".m3u8" in processed_video_url, "Processed video URL should be an HLS playlist after edit"

    # 4. Cleanup
    page.goto(f"{flask_app_url}/delete/{post_id}")
    if os.path.exists(video_path):
        os.remove(video_path)

def test_edit_post_change_video(admin_logged_in_page: Page, flask_app_url):
    """
    Tests changing an existing video in a post.
    """
    page = admin_logged_in_page

    # 1. Create a post with an initial video
    test_title = f"Change Video Test {time.time()}"
    page.goto(f"{flask_app_url}/new")
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", "This post will have its video changed.")
    initial_video_path = create_test_video_file("initial_video.mp4")
    page.set_input_files("input[name='video']", initial_video_path)
    page.click("button[type='submit']")

    # Get post_id and wait for initial video processing
    page.goto(f"{flask_app_url}/")
    post_locator = page.locator(f".post:has-text('{test_title}')")
    post_link = post_locator.locator("a.post-button").first
    post_url = f"{flask_app_url}{post_link.get_attribute('href')}"
    post_id = post_url.split('/')[-1]

    processing_complete = False
    for i in range(120): # Poll for up to 120 seconds
        page.goto(post_url)
        player_on_post_page = page.locator(".video-js")
        status = player_on_post_page.get_attribute("data-status")
        if status == "processed":
            processing_complete = True
            break
        time.sleep(1)
        print(f"Polling initial video status... Current: {status} (Attempt {i+1}/120)")
    assert processing_complete, "Initial video processing did not complete within the timeout period."

    # Get initial video URL to compare later
    page.goto(post_url)
    initial_video_player = page.locator(".video-js")
    old_video_url = initial_video_player.get_attribute("data-url")
    assert old_video_url, "Initial video player should have a data-url"

    # 2. Edit the post to change the video
    page.goto(f"{flask_app_url}/edit/{post_id}")
    new_video_path = create_test_video_file("new_video.mp4")
    page.set_input_files("input[name='video']", new_video_path)
    page.click("button[type='submit']")

    # 3. Verify the video was changed and poll for new video processing completion
    expect(page).to_have_url(f"{flask_app_url}/")
    page.goto(post_url)

    processing_complete = False
    for i in range(120): # Poll for up to 120 seconds
        page.goto(post_url)
        player_on_post_page = page.locator(".video-js")
        status = player_on_post_page.get_attribute("data-status")
        if status == "processed":
            processing_complete = True
            break
        time.sleep(1)
        print(f"Polling new video status... Current: {status} (Attempt {i+1}/120)")
        if page.url != post_url:
            print(f"Redirected to {page.url}, navigating back to {post_url}")
            page.goto(post_url)
    assert processing_complete, "New video processing did not complete within the timeout period."

    page.goto(post_url)
    final_video_player = page.locator(".video-js")
    expect(final_video_player).to_have_attribute("data-status", "processed")
    new_video_url = final_video_player.get_attribute("data-url")
    assert new_video_url, "New video player should have a data-url"
    assert ".m3u8" in new_video_url, "New video URL should be an HLS playlist"
    assert new_video_url != old_video_url, "Video URL should have changed to the new video"

    # 4. Cleanup
    page.goto(f"{flask_app_url}/delete/{post_id}")
    if os.path.exists(initial_video_path):
        os.remove(initial_video_path)
    if os.path.exists(new_video_path):
        os.remove(new_video_path)