#!/bin/bash
cd "$(dirname "$0")"
gcc -o cnhe_sim cnhe_sim.c -Wall -O2
./cnhe_sim
echo "Done"
