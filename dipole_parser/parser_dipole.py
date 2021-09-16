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
        pass

    def get_specifics(self):
        self.specifics = yaml.safe_load(open(op.join(self.foldername, 'details.yaml'), 'r'))
        # Print out the specifics of the yaml file
        print(self.specifics)
    
    def validate_inputs(self):
        """Validate that some specific optiosn exit."""
        assert op.exists(self.foldername), f"{self.foldername} does not exist"
        assert op.exists(op.join(self.foldername, 'details.yaml')), f"{op.join(self.foldername, 'details.yaml')} does not exist"
        assert op.exists(op.join(self.foldername, 'vasprun.xml')), f"{op.join(self.foldername, 'vasprun.xml')} does not exist" 
        assert 'run_number' in self.specifics
        assert 'state' in self.specifics
        self.state = self.specifics.pop('state')
        self.run_number = self.specifics.pop('run_number')
        assert not self.specifics, f"{self.specifics} is not empty"

    def store_attributes(self): 
        """Store entry into ASE database based on the specics of the yaml file."""
        # read in the OUTCAR file
        atoms_traj = read(op.join(self.foldername, 'vasprun.xml'), ':')
        with db.connect(self.dbname) as database:
            for index, atoms in enumerate(atoms_traj):
                specifics = {'state':self.state, 'run_number':self.run_number,} 
                specifics['timestep'] = index
                specifics['atoms'] = atoms
                database.write(**specifics) 
    
    def get_specifics_for_recursive(self):
        # Get the specifics from the folder names for the recursive default option
        # The state information comes from the first part of the folder name
        self.state = self.foldername.split('/')[1]
        # The run number is the number of directories there in the folder
        self.run_number = len(self.foldername.split('/')[2:])
        self.specifics = {'state':self.state, 'run_number':self.run_number,}
        print(self.specifics)
