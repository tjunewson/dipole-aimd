"""Parse the energy from an AIMD calculation stored in an ASE database."""
import json
from dataclasses import dataclass
from ase.db import connect
from collections import defaultdict
import numpy as np

def cumulative_average(quantity):
    """Return the cumulative average of quantity."""
    return np.cumsum(quantity) / np.arange(1, len(quantity) + 1)

@dataclass
class ParseEnergy:
    """Parses the ASE database for the dipole moment.
    Inputs
    ------
    ase_db_file: str
        The path to the ASE database file.
    output_file: str
        The path to the output json file.
    """
    ase_db_file: str
    output_file: str

    def __post_init__(self):
        self.energy = defaultdict(list)
        self._energy = defaultdict(list)
        self.parse_energy()
        self.store_energy()
    
    def get_ase_database(self):
        """Read the ASE database and yield the dipole moment."""
        with connect(self.ase_db_file) as handle:
            for row in handle.select():
                # Consider only the dipole moment along the z-axis
                if row.get('energy') is not None:
                    yield row.energy, row.run_number, row.timestep, row.state

    def parse_energy(self):
        """Store the energy and the structure in a dict of lists in sorted order of sampling."""
        for energy, run_number, timestep, state in self.get_ase_database():
            self._energy[state].append(np.array([run_number, timestep, energy]))
    
    def store_energy(self):
        """Store the energy from the collected data."""
        # Sort the energy based on the sampling for each structure
        for structure, energy_data in self._energy.items():
            energy_data = np.array(energy_data)
            sorted_index = np.lexsort((energy_data[:, 0], energy_data[:, 1]))
            self.energy[structure].append(energy_data[sorted_index]) 

        # Store the quantities for later use
        self.avg_energy = defaultdict(list)

        # Find the cumulative average of the energy
        for structure, data in self.energy.items():
            _, _, energy = np.array(data).T
            energy_average = cumulative_average(energy)
            time_in_ps = np.arange(0, len(energy_average), 1) * 0.001
            self.avg_energy[structure] = [time_in_ps.tolist(), energy_average.tolist()]

        # Save the file as a json
        with open(self.output_file, 'w') as handle:
            json.dump(self.avg_energy, handle)
