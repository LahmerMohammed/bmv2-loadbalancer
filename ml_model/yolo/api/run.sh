#!/bin/bash

gunicorn --workers=2 --bind=0.0.0.0:8000 --log-level=info main:app
