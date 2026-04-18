#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export AIRFLOW_HOME="$SCRIPT_DIR"
echo "AIRFLOW_HOME="$SCRIPT_DIR" >> ~/.bashrc
source ~/.bashrc

airflow standalone