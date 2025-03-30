# zips src folder and uploads it to GCP bucket
#!/bin/bash
# This script zips the src folder and uploads it to a GCP bucket
# Usage: ./zip_function_upload_gcloud.sh
# Check if gsutil is installed
if ! command -v gsutil &> /dev/null
then
    echo "gsutil could not be found. Please install it to use this script."
    exit
fi
# Check if the user is logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null
then
    echo "You are not logged in to gcloud. Please log in to use this script."
    exit
fi
# Check if the user is in the correct project
if ! gcloud config get-value project &> /dev/null
then
    echo "You are not in the correct project. Please set the project to use this script."
    exit
fi
# Check if the src folder exists
if [ ! -d "src" ]; then
    echo "The src folder does not exist. Please create it to use this script."
    exit
fi
# Check if the src folder is empty
if [ -z "$(ls -A src)" ]; then
    echo "The src folder is empty. Please add files to it to use this script."
    exit
fi

cd src && zip -r ../function.zip * && cd ..
gsutil cp function.zip gs://berliner-luft/functions/

# Uncomment the following lines to create a unique zip file name
# and upload it to the GCP bucket with a timestamp
# ZIP_NAME="function_$(date +%s).zip"
# cd src && zip -r "../$ZIP_NAME" * && cd ..
# gsutil cp "../$ZIP_NAME" gs://berliner-luft/functions/