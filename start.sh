#!/bin/sh
set -e

# Start nginx (daemonises itself); it listens on 8501 and proxies to Streamlit.
nginx

# Become PID 1 so Docker signals reach Streamlit cleanly.
exec streamlit run main.py \
    --server.port=8502 \
    --server.address=127.0.0.1 \
    --server.headless=true
