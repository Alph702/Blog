import pytest
from playwright.sync_api import Page, expect
import os
import time
import re
from dotenv import load_dotenv

load_dotenv()
# Assuming BASE_URL is defined in conftest.py
def test_admin_login_logout(page: Page, flask_app_url):
    page.goto(f"{flask_app_url}/login")
    expect(page).to_have_title("Login - Blog")

    # Fill in correct credentials
    page.fill("input[name='username']", os.getenv('ADMIN_USERNAME'))
    page.fill("input[name='password']", os.getenv('ADMIN_PASSWORD'))
    page.click("button[type='submit']")

    # Assert successful login and redirection to home page
    expect(page).to_have_url(f"{flask_app_url}/")
    expect(page.locator("a", has_text="New Post")).to_be_visible()
    expect(page.locator("a", has_text="Logout")).to_be_visible()

    # Perform logout
    page.locator("a", has_text="Logout").click()
    # Assert successful logout and redirection to home page
    expect(page).to_have_url(f"{flask_app_url}/")
    expect(page.locator("a", has_text="Login")).to_be_visible()
    expect(page.locator("a", has_text="New Post")).not_to_be_visible()

def test_admin_login_incorrect_credentials(page: Page, flask_app_url):
    page.goto(f"{flask_app_url}/login")
    expect(page).to_have_title("Login - Blog")

    # Fill in incorrect credentials
    page.fill("input[name='username']", "wronguser")
    page.fill("input[name='password']", "wrongpass")
    page.click("button[type='submit']")

    # Assert error message is displayed and still on login page
    expect(page.locator(".error-message")).to_have_text("Invalid credentials")
    expect(page).to_have_url(f"{flask_app_url}/login")

def test_new_post_authorization(page: Page, flask_app_url):
    page.goto(f"{flask_app_url}/new")
    # Expect redirection to login page
    expect(page).to_have_url(f"{flask_app_url}/login")

def test_delete_post_authorization(page: Page, flask_app_url):
    # Attempt to access delete endpoint directly
    page.goto(f"{flask_app_url}/delete/1") # Assuming post ID 1 might exist
    # Expect redirection to login page
    expect(page).to_have_url(f"{flask_app_url}/login")

def test_admin_inspect_authorization(page: Page, flask_app_url):
    response = page.goto(f"{flask_app_url}/admin/inspect")
    # Expect 403 Forbidden (or redirection to login, depending on Flask's error handling for API endpoints)
    # Since it returns jsonify({'error': 'admin only'}), 403, we expect the text content.
    expect(page.locator("body")).to_have_text("{\"error\":\"admin only\"}")
    assert response.status == 403

def test_create_and_view_post(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page
    page.goto(f"{flask_app_url}/new")
    expect(page).to_have_title("New Post")

    test_title = f"Test Post Title {time.time()}"
    test_content = "This is the content of the test post."

    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.click("button[type='submit']")

    # After submission, it redirects back to /new
    expect(page).to_have_url(f"{flask_app_url}/new")

    # Go to home page to verify the post
    page.goto(f"{flask_app_url}/")
    expect(page.locator("h1", has_text=test_title)).to_be_visible()

    # Click on the post to view it individually
    page.locator("a", has_text=test_title).click()

    # Verify content on the individual post page
    expect(page.locator("h1")).to_have_text(test_title)
    expect(page.locator("p").nth(1)).to_have_text(test_content) # Assuming content is the second <p>

def test_create_post_with_image(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page
    page.goto(f"{flask_app_url}/new")
    expect(page).to_have_title("New Post")

    test_title = f"Test Post with Image {time.time()}"
    test_content = "This post has an image."
    image_path = os.path.join(os.path.dirname(__file__), "test_image.png") # Create a dummy image for testing

    # Create a dummy image file
    with open(image_path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\xda\xed\xc1\x01\x01\x00\x00\x00\xc2\xa0\xf7Om\x00\x00\x00\x00IEND\xaeB`\x82")

    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.set_input_files("input[name='image']", image_path)
    page.click("button[type='submit']")

    expect(page).to_have_url(f"{flask_app_url}/new")

    page.goto(f"{flask_app_url}/")
    expect(page.locator("h1", has_text=test_title)).to_be_visible()

    page.locator("a", has_text=test_title).click()
    expect(page.locator("img[alt='Post Image']")).to_be_visible()

    # Clean up the dummy image
    os.remove(image_path)

def test_duplicate_post_handling(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page
    page.goto(f"{flask_app_url}/new")

    test_title = f"Duplicate Test Post {time.time()}"
    test_content = "This post should only appear once."

    # Create the first post
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/new")

    # Attempt to create a duplicate post
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/new")

    # Go to home page and verify only one post with this title exists
    page.goto(f"{flask_app_url}/")
    # Count occurrences of the title
    post_titles = page.locator(f"h1:has-text(\"{test_title}\")")
    expect(post_titles).to_have_count(1)

def test_delete_post(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page
    page.goto(f"{flask_app_url}/new")

    test_title = f"Post to Delete {time.time()}"
    test_content = "This post will be deleted."

    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/new")

    page.goto(f"{flask_app_url}/")
    expect(page.locator("h1", has_text=test_title)).to_be_visible()

    # Find the delete link for the specific post
    # This assumes the delete link is within the same post div or easily identifiable
    post_locator = page.locator(f".post:has(h1:has-text(\"{test_title}\"))")
    post_locator.locator("a[href^='/delete/']").click()
    # After deletion, the page redirects to home, and the post should be gone
    expect(page).to_have_url(f"{flask_app_url}/")
    expect(page.locator("h1", has_text=test_title)).not_to_be_visible()

def test_remember_me_login_persistence(page: Page, flask_app_url):
    # Login with "remember me"
    page.goto(f"{flask_app_url}/login")
    page.fill("input[name='username']", os.environ["ADMIN_USERNAME"])
    page.fill("input[name='password']", os.environ["ADMIN_PASSWORD"])
    page.check("input[name='remember']") # Check the "Remember Me" checkbox
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/")
    expect(page.locator("a", has_text="New Post")).to_be_visible()

    # Assert admin is still logged in in the same context after navigating away and back
    page.goto(f"{flask_app_url}/")
    expect(page.locator("a", has_text="New Post")).to_be_visible()
    expect(page.locator("a", has_text="Logout")).to_be_visible()

# Test for filtering posts (requires posts with different timestamps)
# This test will be more effective if the database is pre-populated with diverse posts
# For now, we'll just test the UI interaction.
def test_filter_posts_ui(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page
    page.goto(f"{flask_app_url}/")

    # Ensure filter panel is initially hidden and then toggle it
    filter_panel = page.locator("#filterPanel")
    expect(filter_panel).not_to_have_class(re.compile("open"))
    page.click("#toggleFilterBtn")
    expect(filter_panel).to_have_class(re.compile("open"))

    # Select a year (assuming 'any' is always an option and some years exist)
    # This test is more about UI interaction than actual filtering logic without pre-populated data
    page.select_option("#year", "any")
    page.select_option("#month", "any")
    page.select_option("#day", "any")
    page.click("button[type='submit']")
    expect(page).to_have_url(re.compile(f"{flask_app_url}/filter.*year=any.*month=any.*day=any"))

    # Reset filters
    page.screenshot(path="filter_reset_before_click.png")
    page.locator(".filter-reset-btn").wait_for(state="visible", timeout=10000)
    page.evaluate("document.querySelector('.filter-reset-btn').click()")
    page.wait_for_load_state('networkidle')
    page.screenshot(path="filter_reset_after_click.png")
    expect(page).to_have_url(f"{flask_app_url}/")