#!/bin/bash
set -e

lumina project create demo_project --path ./demo_project
lumina data add sample examples/sample_data.csv --project demo_project
lumina project open demo_project
