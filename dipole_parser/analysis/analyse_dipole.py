"""Plot the dipole moment coming from an AIMD calculation."""
import json
from dataclasses import dataclass
from ase.db import connect
from collections import defaultdict
import numpy as np

def cumulative_average(quantity):
    """Return the cumulative average of quantity."""
    return np.cumsum(quantity) / np.arange(1, len(quantity) + 1)

@dataclass
class ParseDipole:
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
        self.dipole_moment = defaultdict(list)
        self._dipole_moment = defaultdict(list)
        self.parse_dipole_moment()
        self.plot_dipole_moment()
    
    def get_ase_database(self):
        """Read the ASE database and yield the dipole moment."""
        with connect(self.ase_db_file) as handle:
            for row in handle.select():
                # Consider only the dipole moment along the z-axis
                if row.get('dipole') is not None:
                    yield row.dipole[-1], row.run_number, row.timestep, row.state

    def parse_dipole_moment(self):
        """Store the dipole moment and the structure in a dict of lists in sorted order of sampling."""
        for dipole, run_number, timestep, state in self.get_ase_database():
            self._dipole_moment[state].append(np.array([run_number, timestep, dipole]))
    
    def plot_dipole_moment(self):
        """Plot the dipole moment for the different structures in one graph based on ordered sampling."""
        # Sort the dipole moment based on the sampling for each structure
        for structure, dipole_data in self._dipole_moment.items():
            dipole_data = np.array(dipole_data)
            sorted_index = np.lexsort((dipole_data[:, 0], dipole_data[:, 1]))
            self.dipole_moment[structure].append(dipole_data[sorted_index]) 

        # Store the quantities for later use
        self.avg_dipole = defaultdict(list)

        # Find the cumulative average of the dipole moment
        for structure, data in self.dipole_moment.items():
            _, _, dipole = np.array(data).T
            dipole_average = cumulative_average(dipole)
            time_in_ps = np.arange(0, len(dipole_average), 1) * 0.001
            self.avg_dipole[structure] = [time_in_ps.tolist(), dipole_average.tolist()]

        # Save the file as a json
        with open(self.output_file, 'w') as handle:
            json.dump(self.avg_dipole, handle)
