"""Create structures that have random positions of the cation in an AIMD calculation."""

import os
import sys
import numpy as np
import yaml
from dataclasses import dataclass
from ase import atom, build
from ase import constraints
from ase import Atoms
from ase import data
from pathlib import Path
from copy import deepcopy

def get_random_xy_positions(cell, n_atoms):
    """Get random xy positions for the cation."""
    x_chosen = np.random.uniform(0, np.linalg.norm(cell[0]), n_atoms)
    y_chosen = np.random.uniform(0, np.linalg.norm(cell[1]), n_atoms)
    return x_chosen, y_chosen

def check_xy_distance(test_atoms, cutoff_fraction):
    """Check if the xy positions are too close to each other."""
    for i in range(len(test_atoms)):
        for j in range(i+1, len(test_atoms)):
            # required minimum distance is the sum of the covalent radii
            min_cutoff = data.covalent_radii[data.atomic_numbers[test_atoms[i].symbol]] + \
                            data.covalent_radii[data.atomic_numbers[test_atoms[j].symbol]]
            # Reduce the min cutoff by the cutoff fraction
            min_cutoff = min_cutoff * cutoff_fraction
            # if np.linalg.norm(test_atoms.get_positions()[i] - test_atoms.get_positions()[j]) < min_cutoff:
            if test_atoms.get_distance(i,j, mic=True) < min_cutoff:
                return False
    return True

def add_natoms_to_surface(surface, n_atoms, atoms_all, x_chosen, y_chosen, z_chosen):
    """For a given number of atoms, and Atoms extend the original atoms object"""
    for j, n_atom in enumerate(range(n_atoms)):
        atoms_to_extend = atoms_all[j]
        # Standardize the positions
        atoms_to_extend.set_cell([1, 1, 1])
        atoms_to_extend.center()
        atoms_to_extend.set_cell([0, 0, 0])
        atoms_to_extend.rotate('y', np.random.uniform(0, 360), center='COU')
        atoms_to_extend.translate([[x_chosen[j], y_chosen[j], z_chosen]])

        # Rotate the molecule randomly
        surface.extend(atoms_to_extend)

@dataclass
class CreateCation:
    """Create structures with cations within a cell of given dimensions."""
    yaml_file: str

    def __post_init__(self):
        """Initialize class."""
        self.yaml_file = os.path.abspath(self.yaml_file)
        # Check if all of the tags are available, and if there
        # is more or less it raises and exception.
        inputs = yaml.safe_load(open(self.yaml_file))

        # get the facet
        self.facet = inputs['facet']
        # get the metal atom
        self.metal_name = inputs['metal_name']
        # get the lattice constants
        self.a = inputs['a']
        # Metal layers
        self.metal_layers = int(inputs['metal_layers'])
        # get the cation
        self.cation = inputs['cation']
        # get the layer that the cation must be in 
        self.layer_of_cation = inputs['layer_of_cation']
        # get the dimensions of the bulk structure
        self.dimensions = inputs['dimensions']
        # get the number of water layers
        self.water_layers = inputs['water_layers']
        # get the number of water atoms per water layer
        self.water_per_layer = inputs['water_per_layer']
        # get the distance between water layers
        self.water_layer_distance = inputs['water_layer_distance']
        # Vacuum based on the slab, important for the dipole correction
        self.vacuum = inputs['vacuum']
        # Choose a cutoff fraction to be lowered from the sum of the covalent radii
        self.cutoff_fraction = inputs['cutoff_fraction']

        # Check if an adsorbate is supplied
        self.adsorbate = inputs.pop('adsorbate', '')

        self.create_surface()
        if self.adsorbate:
            self.add_adsorbate_to_surface()
        self.create_water_and_cation()
        self.create_pre_relaxation_structures()

    def create_surface(self):
        """Create the surface and fix half the layers."""
        # create the bulk structure
        bulk = build.bulk(self.metal_name, 'fcc', a=self.a, cubic=True)

        # create the surface
        miller_indices = [int(a) for a in self.facet]
        surface = build.surface(bulk, indices=miller_indices, layers=self.metal_layers)

        # Repeat the structure
        self.dimensions = [int(a) for a in self.dimensions]
        surface.center(vacuum=self.vacuum, axis=2)
        surface = surface.repeat([self.dimensions[0], self.dimensions[1], 1])

        # fix the bottom half of the surface
        all_z_index = surface.get_positions()[:, 2]
        all_index = np.arange(len(all_z_index))
        mean_z_index = np.mean(all_z_index)
        bottom_z_index = all_index[all_z_index < mean_z_index]

        # Set the tag to 1 for things that we want to fix
        for index_fixed in bottom_z_index:
            surface[index_fixed].tag = 1

        # Store the position of the topmost metal atom 
        self.top_metal_atom = all_index[np.argmax(all_z_index)]

        # Move the surface to the bottom of the cell
        surface.translate([[0, 0, -np.min(all_z_index)]])

        # store the surface
        self.surface = surface
        self._store_highest_positons()

    def constrain_atoms(self):
        """Fix all atoms with a tag of 1"""
        fix_index = [ a for a in range(len(self.surface)) if self.surface[a].tag == 1]
        # create the constraint
        constraint = constraints.FixAtoms(indices=fix_index)
        # add the constraint to the surface
        self.surface.set_constraint(constraint)

    def add_adsorbate_to_surface(self):
        """If an adsorbate is provided, add it to the surface."""
        if self.adsorbate == 'CO2':
            co2_positions = [
                [0.00042955, 10.69278681, 10.02427761 ],
                [0.03581859,  9.53396647, 10.43134496 ],
                [-0.0347786, 11.85195424, 10.43097203 ],
            ]
            co2 = Atoms('CO2', positions=co2_positions)
            height = data.covalent_radii[data.atomic_numbers[self.metal_name]] + 0.75
            # get the position of the topmost metal atom
            position = self.surface.get_positions()[self.top_metal_atom]
            build.add_adsorbate(self.surface, co2, height=height, position = position[0:2])
            for i in range(4):
                self.surface[-i].tag = 1

    def _store_highest_positons(self):
        z_min = self.surface.get_positions()[:, 2].max()
        z_min += data.covalent_radii[data.atomic_numbers[self.metal_name]]
        z_min += self.water_layer_distance
        self.z_min = z_min
        print(f'Lowest possible water structure at z-coordinate {z_min} AA')

    def create_water_and_cation(self):
        """Create water and cation structures that are put on top of the metal surfaces."""

        # Create the water and cation atoms objects
        water = build.molecule('H2O')
        cation = Atoms(self.cation)

        z_min = self.z_min

        # Decide on the z-coordinate of the water positions
        for i, layer in enumerate(np.arange(1, self.water_layers+1, 1)):
            # Find the number of atoms placed in a layer
            n_atoms = self.water_per_layer
            if self.layer_of_cation == layer:
                atoms_all = [deepcopy(water) for n_atom in range(n_atoms-1)]
                atoms_all += [cation]
            else:
                atoms_all = [deepcopy(water) for n_atom in range(n_atoms)]

            # Decide on the z-coordinate of the water
            z_chosen = z_min + i * self.water_layer_distance
            x_chosen, y_chosen = get_random_xy_positions(self.surface.cell, n_atoms)

            # Create a copy of the atoms object to test if the xy positions are too close
            test_atoms = deepcopy(self.surface)

            # Add the atoms to the test_atoms
            add_natoms_to_surface(test_atoms, n_atoms, atoms_all, x_chosen, y_chosen, z_chosen)

            # Check if the xy positions are too close
            iteration = 0
            while not check_xy_distance(test_atoms, cutoff_fraction = self.cutoff_fraction):
                # The atoms are too close to each other, change the angles
                iteration += 1
                print(f'Iteration {iteration}')
                # Try again, with a changed angle
                test_atoms = deepcopy(self.surface)
                add_natoms_to_surface(test_atoms, n_atoms, atoms_all, x_chosen, y_chosen, z_chosen)
                if iteration > 100:
                    # Create a new set of atoms
                    test_atoms = deepcopy(self.surface)
                    x_chosen, y_chosen = get_random_xy_positions(self.surface.cell, n_atoms)
                    add_natoms_to_surface(test_atoms, n_atoms, atoms_all, x_chosen, y_chosen, z_chosen)
                if iteration > 200:
                    # Give up
                    raise Exception('Too many iterations')

            print(f'Chosen z-positions {z_chosen} AA')
            self.surface = test_atoms

    def create_pre_relaxation_structures(self):
        """Create folder structure"""
        self.constrain_atoms()
        index = 1
        no_water = self.water_layers * self.water_per_layer - 1
        if self.adsorbate:
            self.metal_name = self.metal_name + '_' + self.adsorbate
        state_info = self.metal_name + '_' + self.facet + '_' + self.cation + '_' + str(self.dimensions[0]) + 'x' + str(self.dimensions[1]) + '_' + 'cationlayer_' + str(self.layer_of_cation) + '_' + str(no_water) + 'w_' + str(index)

        while os.path.exists(state_info):
            index += 1
            state_info = self.metal_name + '_' + self.facet + '_' + self.cation + '_' + str(self.dimensions[0]) + 'x' + str(self.dimensions[1]) + '_' + 'cationlayer_' + str(self.layer_of_cation) + '_' + str(no_water) + 'w_' + str(index)

        folder = os.path.join(os.getcwd(), state_info, 'pre_relaxation')
        Path(folder).mkdir(parents=True, exist_ok=True)
        self.folder = folder

        # Write the atoms object to that folder
        self.surface.set_pbc([True, True, True])
        self.surface.write(os.path.join(self.folder, 'pre_relaxation.traj'),)