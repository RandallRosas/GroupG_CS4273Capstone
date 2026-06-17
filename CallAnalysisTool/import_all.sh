#!/bin/bash

echo "Script designed for Git Bash. Other shells may see unexpected behaviors."
echo "This will import selected Docker images and volumes from ./offline_backup/"
echo

read -p "Continue? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Import canceled."
    exit 1
fi

read -p "Import images? (y/N): " import_images
read -p "Import volumes? (y/N): " import_volumes

start_time=$(date +%s)

if [[ ! -d "offline_backup" ]]; then
    echo "Error: ./offline_backup directory not found."
    exit 1
fi

echo
echo "=== Starting Import at $(date) ==="
echo

# ----------------------
# Import Images
# ----------------------
if [[ "$import_images" == "y" || "$import_images" == "Y" ]]; then
    echo "=== Importing Images ==="

    image_files=(
        callanalysistool-frontend-latest.tar.gz
        callanalysistool-ollama-latest.tar.gz
        callanalysistool-whisper-latest.tar.gz
        callanalysistool-backend-latest.tar.gz
        ubuntu-latest.tar.gz
    )

    for file in "${image_files[@]}"; do
        path="offline_backup/$file"

        if [[ -f "$path" ]]; then
            echo "Loading image from $path"
            gunzip -c "$path" | docker load
        else
            echo "Skipping $file (not found)"
        fi
    done
else
    echo "Skipping image import."
fi

echo

# ----------------------
# Import Volumes
# ----------------------
if [[ "$import_volumes" == "y" || "$import_volumes" == "Y" ]]; then
    echo "=== Importing Volumes ==="

    volumes=(
        callanalysistool_ollama_data
        callanalysistool_whisperx_cache
        callanalysistool_models_data
        callanalysistool_torch_cache
    )

    for vol in "${volumes[@]}"; do
        archive="offline_backup/$vol.tar.gz"

        if [[ -f "$archive" ]]; then
            # Create volume if it does not exist
            if ! docker volume inspect "$vol" > /dev/null 2>&1; then
                echo "Creating volume $vol"
                docker volume create "$vol"
            fi

            echo "Restoring volume $vol from $archive"

            MSYS_NO_PATHCONV=1 docker run --rm \
                -v "$vol":/data \
                -v "$PWD/offline_backup":/backup \
                ubuntu \
                tar xzf "/backup/$vol.tar.gz" -C /data
        else
            echo "Skipping $vol (archive not found)"
        fi
    done
else
    echo "Skipping volume import."
fi

echo

end_time=$(date +%s)

echo "=== Import Completed at $(date) ==="
echo
echo "Import process finished."
echo
read -p "Press Enter to exit. " temp 