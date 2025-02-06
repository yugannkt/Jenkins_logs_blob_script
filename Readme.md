# Jenkins Logs to Azure Blob Storage with Azure Key Vault

This Python script automates the process of fetching Jenkins build logs and uploading them to Azure Blob Storage and Uses Azure's `BlobServiceClient` for interaction with Azure Blob Storage.

## Features
- **Fetch Jenkins Logs**: Retrieves logs from all Jenkins jobs and builds.
- **Parallel Processing**: Uses `ThreadPoolExecutor` to fetch logs in parallel, enhancing performance.
- **Azure Blob Storage**: Uploads logs to Azure Blob Storage with a timestamped naming convention.

---

## How to Execute the Script

1. **Clone the Repository**:

    ```
    git clone https://github.com/yourusername/jenkins-logs-to-azure.git
    cd jenkins-logs-to-azure
    ```

2. **Set Up Virtual Environment**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate     # On Windows
    ```

3. **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure Environment Variables**:
   
   Set the following environment variables for your specific setup:
   - `JENKINS_URL`: URL to your Jenkins server. 
   - `JENKINS_USER`: Jenkins username.
   - `JENKINS_API_TOKEN`: Jenkins API token.
   - `AZURE_CONNECTION_STRING`: Azure Blob Storage connection string.
   - `AZURE_CONTAINER_NAME`: The Azure Blob container name for storing logs.

5. **Run the Script**:

    ```bash
    python fetch_jenkins_logs.py
    ```

---

## Explanation of Key Functions

### 1. **Fetching Jenkins Logs (`get_jenkins_logs` & `fetch_build_log`)**

- **get_jenkins_logs**: This function retrieves a list of Jenkins jobs using the Jenkins API. For each job, it retrieves build details (e.g., build number and URL) and fetches the build logs in parallel using `ThreadPoolExecutor` to improve performance.
  
- **fetch_build_log**: It fetches the console text (logs) of each build using the URL provided by Jenkins. It also includes retry logic using the `tenacity` library to ensure the script handles transient network issues gracefully.

### 2. **Uploading Logs to Azure Blob Storage (`upload_logs_to_azure`)**

- This function uploads logs to Azure Blob Storage. It checks if the specified container exists and creates it if not. The logs are uploaded with a timestamp format in the filename (`log_name_YYYY-MM-DD.txt`), ensuring the files are organized by date.

---

## Important Libraries Used

- **`requests`**: To interact with Jenkins API and fetch build logs.
- **`azure-storage-blob`**: For uploading logs to Azure Blob Storage.
- **`tenacity`**: To implement retry logic when fetching logs in case of failures.
- **`concurrent.futures`**: To execute tasks (log fetches) concurrently, speeding up the process.

---

## Logging and Error Handling

- **Logging**: The script uses Python's built-in `logging` module to log various stages of execution, including fetching secrets, fetching logs, and uploading them to Azure Blob Storage.
  
- **Error Handling**: Errors in network requests (both Jenkins and Azure) are caught and logged. If the retry attempts for fetching Jenkins logs exceed the set limit, the process is aborted. In case of any error during the upload to Azure Blob Storage, the script halts and logs the issue.

---


