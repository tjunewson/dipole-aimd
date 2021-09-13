"""Get all the folders with details.yaml and store the atoms object in the database."""
from ase.db import connect
import click
import glob
from dipole_parser.parser_dipole import StoreAtomsinASEdb
import click

@click.command()
@click.option('--dbname', default='test.db')
def store_to_database(dbname):
    """Finds all the folders of arbitrary depth which contain details.yaml."""
    all_paths = glob.glob('**/details.yaml', recursive=True)
    for paths in all_paths:
        foldername = paths.replace('details.yaml', '')
        method = StoreAtomsinASEdb(dbname=dbname, foldername=foldername)
        method.validate_inputs()
        method.store_attributes()

