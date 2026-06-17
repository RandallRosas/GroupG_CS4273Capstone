# Offline Deployment Setup Guide

This guide explains how to import prebuilt Docker images and volumes,
then start the application in offline mode.

The offline artifact for this project is:

- Docker images
- Named Docker volumes containing cached AI models

The application is not fully offline from images alone.

------------------------------------------------------------------------

## Prerequisites

-   Docker Desktop installed and running
-   The project directory containing:
    -   `backend/data/`
        -   Contains the question list `EMSQA.csv`
    -   `offline_backup/`
        -   Contains all exported images (`callanalysistool-*-latest.tar.gz`)
        -   Contains all exported volumes (`callanalysistool_*.tar.gz`)
-   `.env`
-   `import_all.sh`
    -   `docker-compose.yml`
- **No other source code required**

Path on server as of writing:\
C:/ou_transfer/

------------------------------------------------------------------------

## Step 1 - Import Docker Images

1.  Navigate to the main project directory.

2.  Open **Git Bash** in that directory.\
    The import script may not work correctly in other shells.

3.  Run:

    ``` bash
    ./import_all.sh
    # Or, if that doesn't work
    sh import_all.sh
    ```

4.  When prompted, choose to install **IMAGES ONLY**.

Do not install volumes yet. Volume restore depends on the `ubuntu` image
being present.

------------------------------------------------------------------------

## Step 2 - Import Docker Volumes

1.  Close Git Bash completely.

2.  Reopen Git Bash in the same directory.

3.  Run:

    ``` bash
    ./import_all.sh
    # Or, if that doesn't work
    sh import_all.sh
    ```

4.  When prompted, choose to install **VOLUMES ONLY**.

------------------------------------------------------------------------

## Step 3 - Verify Images and Volumes

In Docker Desktop:

-   Confirm all required images are present.
-   Confirm all required volumes are present and non-empty.

------------------------------------------------------------------------

## Step 4 - Configure Environment

1.  Open `.env`.
2.  Ensure these values are correct:
    -   `HF_HUB_OFFLINE=1`
    -   `TRANSFORMERS_OFFLINE=1`
    -   `OLLAMA_MODEL=llama3.1:8b`

The Compose file already uses the correct fixed Docker volume names:

-   `callanalysistool_ollama_data`
-   `callanalysistool_whisperx_cache`
-   `callanalysistool_models_data`
-   `callanalysistool_torch_cache`

------------------------------------------------------------------------

## Step 5 - Start the Application

1.  Open the terminal inside Docker Desktop.

2.  Navigate to the directory containing `docker-compose.yml`.

3.  Run:

    ``` bash
    docker compose up
    ```

The containers should attach to the imported images and model-cache
volumes, and then start the application.

------------------------------------------------------------------------

## Accessing the Web Application

Open a browser and go to:

http://localhost:3000

The application should now be running fully offline.

*- Luke Chey, 3/27/26*
