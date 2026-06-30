#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python vfp_api/manage.py collectstatic --no-input
python vfp_api/manage.py migrate
