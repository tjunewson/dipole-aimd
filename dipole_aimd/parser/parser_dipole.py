"""Class to store the atoms into an ASE database."""
from dataclasses import dataclass
import os.path as op
import yaml
from ase import db
from ase.io import read, ParseError

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

    def store_attributes(self, vaspout='vasprun.xml'): 
        """Store entry into ASE database based on the specics of the yaml file."""
        print(f"Storing {self.foldername}")
        if vaspout:
            atoms_traj = read(op.join(self.foldername, vaspout), ':')
        else:
            atoms_traj = read(op.join(self.foldername), ':')
        with db.connect(self.dbname) as database:
            for index, atoms in enumerate(atoms_traj):
                specifics = {'state':self.state, 'run_number':self.run_number,} 
                specifics['timestep'] = index
                specifics['atoms'] = atoms
                database.write(**specifics) 
    
    def get_specifics_for_recursive(self):
        """Get the specifics for the folder if the default is recursive."""
        # Get the specifics from the folder names for the recursive default option
        # The state information comes from the first part of the folder name
        self.state = self.foldername.split('/')[0]
        # The run number is the number of directories there in the folder
        self.run_number = len(self.foldername.split('/')[2:])
        self.specifics = {'state':self.state, 'run_number':self.run_number,}
        print(self.specifics)

    def get_specifics_for_all_in_one(self):
        """Get the specifics for the folder if the default is all in one."""
        # Get the specifics from the folder names for the all in one default option
        # The state information comes from the first part of the folder name
        self.state = self.foldername.split('/')[0]
        # The run number comes from the last part of the OUTCAR name. For example, if the 
        # OUTCAR_1 is in the folder, then the run number is 1. If no number is found, then
        # the run number is 0.
        try:
            self.run_number = int(self.foldername.split('/')[-1].split('_')[-1])
        except ValueError:
            self.run_number = 0
        self.specifics = {'state':self.state, 'run_number':self.run_number,}
        print(self.specifics)
    
    def get_specifics_for_run_folders(self):
        """Get the specifics for the folder where the run folders are."""
        # Get the specifics from the folder names for the run folders default option
        # The state information comes from the first part of the folder name
        self.state = self.foldername.split('/')[0]
        # The run number comes from the last part of the OUTCAR name. For example, if the 
        # OUTCAR_1 is in the folder, then the run number is 1. If no number is found, then
        # the run number is 0.
        self.run_number = int(self.foldername.split('/')[-2].split('_')[-1])
        self.specifics = {'state':self.state, 'run_number':self.run_number,}
        print(self.specifics) 
        
