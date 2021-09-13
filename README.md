# `simple-dipole-aimd`

Simple parser to allow for storing atoms objects into an ASE database for parsing their dipole moments.

# Usage

In each AIMD trajectory directory, create a folder called `details.yaml`. This file should contain the following information:
1. `state`: The state of the system. Examples: slab, co2, etc.
2. `run_number`: The run number of the aimd assuming that several restarts are usually done.
