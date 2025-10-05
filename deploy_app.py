import subprocess
import os
import sys
import logging
import time
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command, cwd=None):
    """Helper function to run shell commands."""
    logging.info(f"Executing command: {' '.join(command)}")
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
        # Log trimmed output to avoid extremely long logs while keeping useful info
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if stdout:
            logging.info("STDOUT:\n%s", stdout)
        if stderr:
            logging.warning("STDERR:\n%s", stderr)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with exit code {e.returncode}")
        logging.error("STDOUT:\n%s", (e.stdout or '').strip())
        logging.error("STDERR:\n%s", (e.stderr or '').strip())
        return False
    except FileNotFoundError:
        logging.error(f"Command not found: {command[0]}. Make sure it's in your PATH.")
        logging.error(f"Attempted command: {' '.join(command)}")
        return False


def get_current_branch(cwd=None):
    """Return the current git branch name or None on failure."""
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=cwd, capture_output=True, text=True, check=True)
        branch = result.stdout.strip()
        logging.info(f"Detected current git branch: {branch}")
        return branch
    except Exception as e:
        logging.warning(f"Could not determine current git branch: {e}")
        return None

def deploy():
    repo_dir = os.path.abspath(os.path.dirname(__file__))
    logging.info(f"Starting deployment in directory: {repo_dir}")

    # Determine which branch to pull: CLI/ENV override -> current branch -> 'main'
    branch = os.environ.get('DEPLOY_BRANCH') or get_current_branch(repo_dir) or 'main'
    logging.info(f"Pulling latest changes from GitHub (branch: %s)...", branch)
    if not run_command(['git', 'pull', 'origin', branch], cwd=repo_dir):
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
    parser = argparse.ArgumentParser(description='Simple deploy helper for the Blog project')
    parser.add_argument('--branch', '-b', help='Override branch to pull (env DEPLOY_BRANCH also respected)')
    args = parser.parse_args()

    # If CLI arg provided, set env var so deploy() picks it up
    if args.branch:
        os.environ['DEPLOY_BRANCH'] = args.branch

    success = deploy()
    if success:
        logging.info("Deployment successful. Please ensure your application is restarted by your process manager.")
        sys.exit(0)
    else:
        logging.error("Deployment failed.")
        sys.exit(2)
