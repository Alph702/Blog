import os
import time

from playwright.sync_api import Page, expect


def validate_test_video_file():
    """Validates and returns the path to the test video file."""
    source_filepath = "tests/assets/test_video.mp4"
    print(f"Current working directory: {os.getcwd()}")
    print(f"Checking for test video at: {os.path.abspath(source_filepath)}")
    if not os.path.exists(source_filepath):
        raise FileNotFoundError(
            f"Test video file not found at {source_filepath}. Please ensure it exists."
        )

    return source_filepath


def test_create_post_with_video(admin_logged_in_page: Page, flask_app_url):
    """
    Tests creating a post with a video, verifying processing, and cleanup.
    """
    page = admin_logged_in_page
    page.goto(f"{flask_app_url}/new", timeout=600000)
    expect(page).to_have_title("New Post")

    test_title = f"Test Post with Video {time.time()}"
    test_content = "This post has a video that should be processed."
    video_path = validate_test_video_file()

    # 1. Create the post with a video
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.set_input_files("input[name='video']", video_path)
    page.click("button[type='submit']")

    # Expect to be on the same page with a success message
    expect(page).to_have_url(f"{flask_app_url}/new", timeout=600000)
    expect(page.locator(".toast-success")).to_be_visible(timeout=600000)

    # 2. Verify the post and initial video state on the homepage
    page.goto(f"{flask_app_url}/", timeout=600000)
    post_locator = page.locator(f".post:has-text('{test_title}')")
    expect(post_locator).to_be_visible(timeout=600000)

    video_player = post_locator.locator(".video-player")
    expect(video_player).to_be_visible(timeout=600000)

    initial_video_url = video_player.get_attribute("data-url")
    assert initial_video_url, "Video player should have a data-url attribute"
    assert "upload" in initial_video_url, (
        "Initial video URL should reference the uploaded file"
    )

    # 3. Poll and wait for the video to be processed
    post_link = post_locator.locator("a.post-button").first
    post_url = f"{flask_app_url}{post_link.get_attribute('href')}"
    post_id = post_url.split("/")[-1]

    processing_complete = False
    for i in range(120):  # Poll for up to 120 seconds
        page.goto(post_url, timeout=600000)
        player_on_post_page = page.locator(".video-player")
        status = player_on_post_page.get_attribute("data-status")
        if status == "processed":
            processing_complete = True
            break
        time.sleep(1)
        print(f"Polling video status... Current: {status} (Attempt {i + 1}/120)")

    assert processing_complete, (
        "Video processing did not complete within the timeout period."
    )

    # 4. Verify the final state on the post page
    page.goto(post_url, timeout=600000)
    final_player = page.locator(".video-player")
    expect(final_player).to_have_attribute("data-status", "processed")

    processed_video_url = final_player.get_attribute("data-url")
    assert processed_video_url, "Processed video player should have a data-url"
    assert ".m3u8" in processed_video_url, (
        "Processed video URL should be an HLS playlist"
    )
    assert processed_video_url != initial_video_url, (
        "Video URL should have changed after processing"
    )

    # 5. Cleanup
    page.goto(f"{flask_app_url}/delete/{post_id}", timeout=600000)
    expect(page.locator(f".post:has-text('{test_title}')")).not_to_be_visible(
        timeout=600000
    )


def test_edit_post_to_add_video(admin_logged_in_page: Page, flask_app_url):
    """
    Tests adding a video to a post that initially has none.
    """
    page = admin_logged_in_page

    # 1. Create a post without a video
    test_title = f"Add Video Test {time.time()}"
    page.goto(f"{flask_app_url}/new", timeout=600000)
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", "This post will have a video added.")
    page.click("button[type='submit']")

    page.goto(f"{flask_app_url}/", timeout=600000)
    page.locator("a", has_text=test_title).click()
    post_id = page.url.split("/")[-1]

    # 2. Edit the post to add a video
    page.goto(f"{flask_app_url}/edit/{post_id}", timeout=600000)
    expect(page.locator(".video-player")).not_to_be_visible(
        timeout=600000
    )  # No video initially

    video_path = validate_test_video_file()
    page.set_input_files("input[name='video']", video_path)
    page.click("button[type='submit']")

    # 3. Verify the video was added and poll for processing completion
    expect(page).to_have_url(f"{flask_app_url}/", timeout=600000)
    page.goto(f"{flask_app_url}/post/{post_id}", timeout=600000)

    processing_complete = False
    for i in range(120):  # Poll for up to 120 seconds
        page.goto(f"{flask_app_url}/post/{post_id}", timeout=600000)
        player_on_post_page = page.locator(".video-player")
        status = player_on_post_page.get_attribute("data-status")
        if status == "processed":
            processing_complete = True
            break
        time.sleep(1)
        print(
            f"Polling video status for edit... Current: {status} (Attempt {i + 1}/120)"
        )

    assert processing_complete, (
        "Video processing did not complete within the timeout period after edit."
    )

    page.goto(f"{flask_app_url}/post/{post_id}", timeout=600000)
    final_player = page.locator(".video-player")
    expect(final_player).to_have_attribute("data-status", "processed")

    processed_video_url = final_player.get_attribute("data-url")
    assert processed_video_url, (
        "Processed video player should have a data-url after edit"
    )
    assert ".m3u8" in processed_video_url, (
        "Processed video URL should be an HLS playlist after edit"
    )

    # 4. Cleanup
    page.goto(f"{flask_app_url}/delete/{post_id}", timeout=600000)
