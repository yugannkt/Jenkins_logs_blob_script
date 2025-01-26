import requests
import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import logging
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def fetch_build_log(job_name, build_url, auth):
    """Fetch the log for a specific build."""
    try:
        with requests.get(build_url, auth=auth, timeout=30) as response:
            response.raise_for_status()
            logging.info(f"Fetched log for {job_name} from {build_url}")
            return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching log for {job_name}: {e}")
        return None
def get_jenkins_logs(jenkins_url, user, api_token):
    """Fetch all Jenkins job build logs in parallel."""
    try:
        logging.info("Fetching Jenkins job list...")
        with requests.get(f"{jenkins_url}/api/json", auth=(user, api_token), timeout=30) as response:
            response.raise_for_status()
            jobs = response.json().get('jobs', [])
        logs = {}
        with ThreadPoolExecutor(max_workers=10) as executor:  # Limit the number of concurrent threads
            future_to_log = {}
            for job in jobs:
                job_name = job['name']
                logging.info(f"Fetching builds for job: {job_name}")
                with requests.get(f"{job['url']}api/json", auth=(user, api_token), timeout=30) as job_response:
                    job_response.raise_for_status()
                    builds = job_response.json().get('builds', [])
                for build in builds:
                    build_number = build['number']
                    build_url = f"{build['url']}consoleText"
                    # Submit the fetch task to the executor
                    future = executor.submit(fetch_build_log, job_name, build_url, (user, api_token))
                    future_to_log[future] = (job_name, build_number)
            # Collect results as they complete
            for future in as_completed(future_to_log):
                job_name, build_number = future_to_log[future]
                try:
                    log_content = future.result()
                    if log_content:
                        logs[f"{job_name}_{build_number}"] = log_content
                except Exception as e:
                    logging.error(f"Error processing log for {job_name}, build {build_number}: {e}")
        return logs
    except Exception as e:
        logging.error(f"Error fetching Jenkins logs: {e}")
        raise
def upload_logs_to_azure(blob_service_client, container_name, logs):
    """Upload logs to Azure Blob Storage with timestamps."""
    try:
        logging.info("Uploading logs to Azure Blob Storage...")
        container_client = blob_service_client.get_container_client(container_name)
        # Check if the container exists, if not, create it
        try:
            container_client.get_container_properties()
            logging.info(f"Container '{container_name}' already exists.")
        except Exception:
            logging.info(f"Creating container: {container_name}")
            container_client.create_container()
        for log_name, log_content in logs.items():
           # Get the current UTC date (without time)
            utc_time = datetime.utcnow()
            # Format the UTC timestamp to include only the date (year-month-day)
            timestamp_utc = utc_time.strftime('%Y-%m-%d')
            blob_name = f"{log_name}_{timestamp_utc}.txt"
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            logging.info(f"Uploading log: {blob_name}")
            blob_client.upload_blob(log_content, overwrite=True)
    except Exception as e:
        logging.error(f"Error uploading logs to Azure: {e}")
        raise
if __name__ == "__main__":
    # Jenkins configuration (hardcoded values)
    JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080/")  # Default to a placeholder if not set
    JENKINS_USER = os.getenv("JENKINS_USER", "user")
    JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN", "add_token")
    # Azure Blob Storage configuration (use environment variables)
    AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING", "ADD_Key")
    AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "jenkins-build-logs")
    try:
        # Get Jenkins logs and list jobs
        logs = get_jenkins_logs(JENKINS_URL, JENKINS_USER, JENKINS_API_TOKEN)
        # Connect to Azure Blob Storage
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        # Upload logs to Azure Blob Storage
        upload_logs_to_azure(blob_service_client, AZURE_CONTAINER_NAME, logs)
        logging.info("All logs have been successfully uploaded.")
    except Exception as e:
        logging.error(f"Script failed: {e}")