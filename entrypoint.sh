#!/usr/bin/env bash

set -e
echo 'Starting GaelO Pathology Processing'

dicomsdir="/home/gaelo_pathology_processing/storage/dicoms"
### Check for dicom dir, if not found create it using the mkdir ##
[ ! -d "$dicdicomsdiromdir" ] && mkdir -p "$dicomsdir"

dicomsrtssdir="/home/gaelo_pathology_processing/storage/wsi"
### Check for rtss dir, if not found create it using the mkdir ##
[ ! -d "$dicomsrtssdir" ] && mkdir -p "$dicomsrtssdir"

exec "$@"