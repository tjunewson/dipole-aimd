"""Get all the folders with details.yaml and store the atoms object in the database."""
from ase.db import connect
import click
import glob
from dipole_parser.parser_dipole import StoreAtomsinASEdb
import click

@click.command()
@click.option('--dbname', default='test.db')
@click.option('--defaults', default=None)
def store_to_database(dbname, default):
    """Finds all the folders of arbitrary depth which contain details.yaml."""
    if default is None:
        # If no defaults are given, use the values from the details.yaml file
        all_paths = glob.glob('**/details.yaml', recursive=True)
        for paths in all_paths:
            foldername = paths.replace('details.yaml', '')
            method = StoreAtomsinASEdb(dbname=dbname, foldername=foldername)
            method.get_specifics()
            method.validate_inputs()
            method.store_attributes()
    elif default == 'recursive':
        # This default assumes that the user has a set of recursive folders
        # where restarts are stored in folders are increases in depth. 
        # Find all the directories that have a vasprun.xml file.
        print('Recursive path chosen.')
        all_paths = glob.glob('**/vasprun.xml', recursive=True)
        print(f'Found paths: {all_paths}')
        for paths in all_paths:
            foldername = paths.replace('vasprun.xml', '')
            method = StoreAtomsinASEdb(dbname=dbname, foldername=foldername)
            method.get_specifics_for_recursive()
            method.store_attributes()

