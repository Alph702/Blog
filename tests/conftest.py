import pytest
from playwright.sync_api import Page, expect, sync_playwright
import os
import subprocess
import time
import requests
from dotenv import load_dotenv

load_dotenv()


# Define the base URL for the Flask app
BASE_URL = "http://127.0.0.1:8080"

# Fixture to start and stop the Flask application
@pytest.fixture(scope="session")
def flask_app_url():
    # Set environment variables for admin credentials
    env = os.environ.copy()
    env["ADMIN_USERNAME"] = os.getenv('ADMIN_USERNAME')
    env["ADMIN_PASSWORD"] = os.getenv('ADMIN_PASSWORD')
    env["SUPABASE_URL"] = os.getenv('SUPABASE_URL') # Assuming local Supabase for testing
    env["SUPABASE_KEY"] = (
    os.getenv('SUPABASE_SERVICE_ROLE_KEY') or
    os.getenv('SUPERBASE_SERVICE_ROLE_KEY') or
    os.getenv('SUPERBASE_ANON_KEY') or
    os.getenv('SUPABASE_ANON_KEY')
)
    # Start the Flask app in a separate process
    # Use 'start /b python app.py' on Windows to run in background
    # For Linux/macOS, use 'python app.py &'
    if os.name == 'nt': # Windows
        process = subprocess.Popen(["start", "python", "app.py"], shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else: # Linux/macOS
        process = subprocess.Popen(["python", "app.py"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

    # Wait for the app to start
    for _ in range(20): # Try for up to 10 seconds
        try:
            response = requests.get(BASE_URL)
            if response.status_code == 200:
                print(f"Flask app started at {BASE_URL}")
                break
        except requests.exceptions.ConnectionError:
            print("Waiting for Flask app to start...")
            time.sleep(0.5)
    else:
        raise RuntimeError("Flask app did not start in time.")

    yield BASE_URL

    # Terminate the Flask app process
    if os.name == 'nt': # Windows
        subprocess.run(["taskkill", "/F", "/PID", str(process.pid)], capture_output=True)
    else: # Linux/macOS
        os.killpg(os.getpgid(process.pid), subprocess.signal.SIGTERM)
    print("Flask app stopped.")

# Fixture for Playwright page
@pytest.fixture(scope="function")
def page(flask_app_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        yield page
        browser.close()

# Fixture for admin login
@pytest.fixture(scope="function")
def admin_logged_in_page(page: Page, flask_app_url):
    page.goto('about:blank') # Ensure a clean page state
    page.goto(f"{flask_app_url}/login")
    page.fill("input[name='username']", os.environ["ADMIN_USERNAME"])
    page.fill("input[name='password']", os.environ["ADMIN_PASSWORD"])
    page.click("button[type='submit']")
    expect(page).to_have_url(f"{flask_app_url}/")
    yield page
    # Ensure logout after test
    page.goto(f"{flask_app_url}/logout")
    expect(page).to_have_url(f"{flask_app_url}/")
