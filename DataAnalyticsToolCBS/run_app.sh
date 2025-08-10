#!/bin/bash

echo "Starting Test Analytics Dashboard..."
echo ""
echo "Installing required packages..."
pip install -r requirements.txt
echo ""
echo "Launching application..."
streamlit run app.py