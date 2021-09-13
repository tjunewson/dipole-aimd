"""Class to store the atoms into an ASE database."""
from dataclasses import dataclass
import os.path as op
import yaml
from ase import db
from ase.io import read

@dataclass
class StoreAtomsinASEdb:
    dbname: str
    foldername: str

    def __post_init__(self):
        self.specifics = yaml.safeload(op.join(self.foldername, 'details.yaml'))
    
    def validate_inputs(self):
        """Validate that some specific optiosn exit."""
        assert op.exists(self.foldername), f"{self.foldername} does not exist"
        assert op.exists(op.join(self.foldername, 'details.yaml')), f"{op.join(self.foldername, 'details.yaml')} does not exist"
        assert 'run_number' in self.specifics
        assert 'state' in self.specifics
        self.state = self.specifics.pop('state')
        self.run_number = self.specifics.pop('run_number')
        assert not self.specifics, f"{self.specifics} is not empty"

    def store_attributes(self): 
        """Store entry into ASE database based on the specics of the yaml file."""
        # read in the OUTCAR file
        atoms_traj = read(op.join(self.foldername, 'OUTCAR'), ':')
        with db.connect(self.dbname) as database:
            for index, atoms in enumerate(atoms_traj):
                specifics = {'state':self.state, 'run_number':self.run_number,} 
                specifics['timestep'] = index
                database.write(atoms, **specifics) 
