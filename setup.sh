#!/bin/bash

# Create a new conda environment
conda create -n didactic python=3.12 -y

# Activate the environment
source activate didactic

# Install the required packages
pip install -r requirements.txt

echo "Setup complete. To activate the environment, run 'conda activate didactic'."