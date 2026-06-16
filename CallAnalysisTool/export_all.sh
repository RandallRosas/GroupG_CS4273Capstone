#!/bin/bash

echo "Script designed for Git Bash. Other shells may see unexpected behaviors."
echo "This will export selected Docker images and volumes into ./offline_backup/"
echo

read -p "Continue? (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Export canceled."
    exit 1
fi

read -p "Export images? (y/N): " export_images
read -p "Export volumes? (y/N): " export_volumes

start_time=$(date +%s)

mkdir -p offline_backup

echo
echo "=== Starting Export at $(date) ==="
echo

# ----------------------
# Export Images
# ----------------------
if [[ "$export_images" == "y" || "$export_images" == "Y" ]]; then
    echo "=== Exporting Images ==="

    images=(
        callanalysistool-frontend:latest
        callanalysistool-ollama:latest
        callanalysistool-whisper:latest
        callanalysistool-backend:latest
        ubuntu:latest
    )

    for img in "${images[@]}"; do
        if docker image inspect "$img" > /dev/null 2>&1; then
            filename="$(echo "$img" | tr ':' '-')"
            echo "Saving image $img -> $PWD/offline_backup/$filename.tar.gz"
            MSYS_NO_PATHCONV=1 docker save "$img" | gzip > "offline_backup/$filename.tar.gz"
        else
            echo "Skipping image $img (not found)"
        fi
    done
else
    echo "Skipping image export."
fi

echo

# ----------------------
# Export Volumes
# ----------------------
if [[ "$export_volumes" == "y" || "$export_volumes" == "Y" ]]; then
    echo "=== Exporting Volumes ==="

    volumes=(
        callanalysistool_ollama_data
        callanalysistool_whisperx_cache
        callanalysistool_models_data
        callanalysistool_torch_cache
    )

    for vol in "${volumes[@]}"; do
        if docker volume inspect "$vol" > /dev/null 2>&1; then
            echo "Saving volume $vol -> $PWD/offline_backup/$vol.tar.gz"
            MSYS_NO_PATHCONV=1 docker run --rm \
                -v "$vol":/data \
                -v "$PWD/offline_backup":/backup \
                ubuntu \
                tar czf "/backup/$vol.tar.gz" -C /data .
        else
            echo "Skipping volume $vol (not found)"
        fi
    done
else
    echo "Skipping volume export."
fi

echo

end_time=$(date +%s)

echo "=== Export Completed at $(date) ==="
echo
echo "Files written to ./offline_backup/"
echo
read -p "Press Enter to exit. " temp 