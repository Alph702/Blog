from flask import Flask, request, abort
import subprocess
import hmac
import hashlib
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# IMPORTANT: Set these as environment variables on your server
GITHUB_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET')
REPO_PATH = os.path.abspath(os.path.dirname(__file__)) # Assumes webhook_listener.py is in repo root
DEPLOY_SCRIPT_PATH = os.path.join(REPO_PATH, 'deploy_app.py')
MAIN_APP_SERVICE_NAME = os.environ.get('MAIN_APP_SERVICE_NAME', 'blog_app.service') # Default service name

@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    if request.method == 'POST':
        if not GITHUB_SECRET:
            logging.error("GITHUB_WEBHOOK_SECRET environment variable not set.")
            abort(500, 'Server configuration error: GITHUB_WEBHOOK_SECRET not set.')

        # Verify signature (CRITICAL for security)
        signature = request.headers.get('X-Hub-Signature-256')
        if not signature:
            logging.warning('X-Hub-Signature-256 header missing.')
            abort(400, 'X-Hub-Signature-256 header missing')

        payload_body = request.data
        digest = hmac.new(GITHUB_SECRET.encode('utf-8'), payload_body, hashlib.sha256).hexdigest()
        expected_signature = f'sha256={digest}'

        if not hmac.compare_digest(expected_signature, signature):
            logging.warning('Invalid GitHub webhook signature.')
            abort(401, 'Invalid signature')

        logging.info("GitHub webhook signature verified. Initiating deployment.")
        # Execute the deployment script
        try:
            # Run deploy_app.py
            subprocess.run(['python3', DEPLOY_SCRIPT_PATH], check=True, cwd=REPO_PATH)

            # Restart the main Flask application service
            # This requires the user running the webhook listener to have sudo privileges
            # or for systemd to be configured to allow this without password.
            logging.info(f"Restarting main application service: {MAIN_APP_SERVICE_NAME}")
            subprocess.run(['sudo', 'systemctl', 'restart', MAIN_APP_SERVICE_NAME], check=True)

            logging.info("Deployment and application restart successful.")
            return 'Deployment initiated and app restarted successfully', 200
        except subprocess.CalledProcessError as e:
            logging.error(f'Deployment or restart script failed: {e}')
            return f'Deployment or restart script failed: {e}', 500
        except Exception as e:
            logging.error(f'An unexpected error occurred: {e}')
            return f'An unexpected error occurred: {e}', 500
    abort(400)

if __name__ == '__main__':
    # This part is for local testing or if running directly. In production, use Gunicorn.
    app.run(host='0.0.0.0', port=5001) # Run on a different port than your main app
