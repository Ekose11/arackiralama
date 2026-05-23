#!/usr/bin/env bash
python3 -m gunicorn app:app --bind 0.0.0.0:${PORT:-10000}
