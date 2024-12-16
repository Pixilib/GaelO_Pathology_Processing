#!/bin/sh
gunicorn /home/gaelo_pathology_processing.wsgi --bind 0.0.0.0:8000 --timeout 60 --access-logfile - --error-logfile -