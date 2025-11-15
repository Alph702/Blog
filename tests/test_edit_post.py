import pytest
from playwright.sync_api import Page, expect
import os
import time
import re

def test_edit_post_authorization(page: Page, flask_app_url):
    page.goto(f"{flask_app_url}/edit/1", timeout=300000)
    expect(page).to_have_url(f"{flask_app_url}/login", timeout=300000)

def test_edit_post_form_loads_with_data(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page
    
    page.goto(f"{flask_app_url}/new", timeout=300000)
    test_title = f"Post for Editing {time.time()}"
    test_content = "Original content for the post."
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/new", timeout=300000)

    page.goto(f"{flask_app_url}/", timeout=300000)
    page.locator("a", has_text=test_title).click()
    post_id = page.url.split('/')[-1]

    page.goto(f"{flask_app_url}/edit/{post_id}", timeout=300000)
    expect(page).to_have_title("Edit Post")

    expect(page.locator("input[name='title']")).to_have_value(test_title)
    expect(page.locator("textarea[name='content']")).to_have_value(test_content)

    expect(page.locator("img[alt='Current Post Image']")).not_to_be_visible()
    page.goto(f"{flask_app_url}/delete/{post_id}", timeout=300000)

def test_edit_post_successful_update(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page

    page.goto(f"{flask_app_url}/new", timeout=300000)
    original_title = f"Original Title {time.time()}"
    original_content = "This is the original content."
    page.fill("input[name='title']", original_title)
    page.fill("textarea[name='content']", original_content)
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/new", timeout=300000)

    page.goto(f"{flask_app_url}/", timeout=300000)
    page.locator("a", has_text=original_title).click()
    post_id = page.url.split('/')[-1]

    page.goto(f"{flask_app_url}/edit/{post_id}", timeout=300000)
    expect(page).to_have_title("Edit Post")

    updated_title = f"Updated Title {time.time()}"
    updated_content = "This is the updated content."
    page.fill("input[name='title']", updated_title)
    page.fill("textarea[name='content']", updated_content)
    page.click("button[type='submit']")

    expect(page).to_have_url(f"{flask_app_url}/", timeout=300000)

    expect(page.locator("h1", has_text=updated_title)).to_be_visible()
    page.goto(f"{flask_app_url}/delete/{post_id}", timeout=300000)
def test_edit_post_update_with_new_image(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page

    page.goto(f"{flask_app_url}/new", timeout=300000)
    test_title = f"Post for Image Update {time.time()}"
    test_content = "Content for image update."
    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/new", timeout=300000)

    page.goto(f"{flask_app_url}/", timeout=300000)
    page.locator("a", has_text=test_title).click()
    post_id = page.url.split('/')[-1]

    page.goto(f"{flask_app_url}/edit/{post_id}", timeout=300000)
    expect(page).to_have_title("Edit Post")

    image_path = os.path.join(os.path.dirname(__file__), "test_image_new.png")
    with open(image_path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\xda\xed\xc1\x01\x01\x00\x00\x00\xc2\xa0\xf7Om\x00\x00\x00\x00IEND\xaeB`\x82")

    page.set_input_files("input[name='image']", image_path)
    page.click("button[type='submit']")

    expect(page).to_have_url(f"{flask_app_url}/", timeout=300000)

    page.locator("a", has_text=test_title).click()
    expect(page.locator("img[alt='Post Image']")).to_be_visible(timeout=300000)

    page.goto(f"{flask_app_url}/delete/{post_id}", timeout=300000)
    os.remove(image_path)

def test_edit_post_update_without_changing_image(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page

    page.goto(f"{flask_app_url}/new", timeout=300000)
    test_title = f"Post with Existing Image {time.time()}"
    test_content = "Content for existing image."
    image_path = os.path.join(os.path.dirname(__file__), "test_image_original.png")
    with open(image_path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x00IEND\xaeB`\x82")

    page.fill("input[name='title']", test_title)
    page.fill("textarea[name='content']", test_content)
    page.set_input_files("input[name='image']", image_path)
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/new", timeout=300000)

    page.goto(f"{flask_app_url}/", timeout=300000)
    page.locator("a", has_text=test_title).click()
    post_id = page.url.split('/')[-1]
    original_image_src = page.locator(".image").get_attribute("src")

    page.goto(f"{flask_app_url}/edit/{post_id}", timeout=300000)
    expect(page).to_have_title("Edit Post")

    updated_title = f"Updated Title No Image Change {time.time()}"
    updated_content = "Updated content, image should be same."
    page.fill("input[name='title']", updated_title)
    page.fill("textarea[name='content']", updated_content)
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/", timeout=300000)

    page.locator("a", has_text=updated_title).click()
    expect(page.locator("h1")).to_have_text(updated_title)
    expect(page.locator("p").nth(1)).to_have_text(updated_content)
    expect(page.locator(".image")).to_have_attribute("src", original_image_src)

    page.goto(f"{flask_app_url}/delete/{post_id}", timeout=300000)
    os.remove(image_path)

def test_edit_non_existent_post(admin_logged_in_page: Page, flask_app_url):
    page = admin_logged_in_page
    non_existent_post_id = 999999999

    page.goto(f"{flask_app_url}/edit/{non_existent_post_id}", timeout=300000)
    expect(page.locator(".toast-body")).to_have_text("Post not found.", timeout=300000)
