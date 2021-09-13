"""Get all the folders with details.yaml and store the atoms object in the database."""
from ase.db import connect
import click
import glob
from dipole_parser import StoreAtomsinASEdb

@click.command()
@click.option('--dbname', default='test.db')
def store_to_database(dbname):
    """Finds all the folders of arbitrary depth which contain details.yaml."""
    all_paths = glob.glob('*/details.yaml', recursive=True)
    for paths in all_paths:
        foldernames = paths.replace('details.yaml', '')
        for foldername in foldernames:
            method = StoreAtomsinASEdb(dbname=dbname, foldernames=foldername)
            method.validate_inputs()
            method.store_to_database()

