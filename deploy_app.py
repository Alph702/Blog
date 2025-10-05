import subprocess
import os
import sys
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command, cwd=None):
    """Helper function to run shell commands."""
    logging.info(f"Executing command: {' '.join(command)}")
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
        logging.info(f"STDOUT:
{result.stdout}")
        if result.stderr:
            logging.warning(f"STDERR:
{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with exit code {e.returncode}")
        logging.error(f"STDOUT:
{e.stdout}")
        logging.error(f"STDERR:
{e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Command not found: {command[0]}. Make sure it's in your PATH.")
        return False

def deploy():
    repo_dir = os.path.abspath(os.path.dirname(__file__))
    logging.info(f"Starting deployment in directory: {repo_dir}")

    # 1. Pull latest changes from GitHub
    logging.info("Pulling latest changes from GitHub...")
    if not run_command(['git', 'pull', 'origin', 'main'], cwd=repo_dir):
        logging.error("Failed to pull latest changes. Aborting deployment.")
        return False

    # 2. Install/update Python dependencies
    logging.info("Installing/updating Python dependencies...")
    # Ensure pip is run from the correct environment if a virtual environment is active
    pip_executable = [sys.executable, '-m', 'pip']
    if not run_command(pip_executable + ['install', '-r', 'requirements.txt'], cwd=repo_dir):
        logging.error("Failed to install dependencies. Aborting deployment.")
        return False

    logging.info("Deployment script finished. Application restart is required.")
    return True

if __name__ == '__main__':
    if deploy():
        logging.info("Deployment successful. Please ensure your application is restarted by your process manager.")
    else:
        logging.error("Deployment failed.")
