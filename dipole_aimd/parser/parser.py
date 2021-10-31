"""Get all the folders with details.yaml and store the atoms object in the database."""
from pprint import pprint
from ase.db import connect
import click
import glob
from dipole_aimd.parser.parser_dipole import StoreAtomsinASEdb

@click.command()
@click.option('--dbname', default='test.db')
@click.option('--default', default=None)
@click.option('--consider', default=None)
@click.option('--exclude', default=None)
@click.option('--exact', default=None)
def store_to_database(dbname, default, consider, exclude, exact):
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
        if consider is not None:
            all_paths = glob.glob('*' + consider + '*/**/vasprun.xml', recursive=True)
        elif exact is not None:
            all_paths = glob.glob(exact + '*/**/vasprun.xml', recursive=True)
        else:
            all_paths = glob.glob('**/vasprun.xml', recursive=True)
        for paths in all_paths:
            if exclude not in paths:
                print(paths)
                foldername = paths.replace('vasprun.xml', '')
                try:
                    method = StoreAtomsinASEdb(dbname=dbname, foldername=foldername)
                    method.get_specifics_for_recursive()
                    method.store_attributes()
                except:
                    error_file = dbname.replace('.db', '_error.txt')
                    print('Could not store {}'.format(foldername), file=open(error_file, 'a'))
                    continue
                # If it is successful, store the folder name parsed
                completed_file = dbname.replace('.db', '_completed.txt')
                print(foldername, file=open(completed_file, 'a'))
    elif default == 'all_in_one':
        # This default assumes that the user has all the OUTCARs in one folder
        # and the OUTCAR order is decided by the name of the OUTCAR file. The idea is then
        # to collect all of the files with the name OUTCAR
        print('All in one path chosen.')
        if consider is not None:
            all_paths = glob.glob('*' + consider + '**/OUTCAR*', recursive=True)
        elif exact is not None:
            all_paths = glob.glob('*/' + exact + '**/OUTCAR*', recursive=True)
        else:
            all_paths = glob.glob('**/OUTCAR*', recursive=True)

        for paths in all_paths:
            if exclude is not None:
                if exclude in paths:
                    continue
            foldername = paths
            try:
                method = StoreAtomsinASEdb(dbname=dbname, foldername=foldername)
                method.get_specifics_for_all_in_one()
                method.store_attributes('')
            except:
                error_file = dbname.replace('.db', '_error.txt')
                print('Could not store {}'.format(foldername), file=open(error_file, 'a'))
                continue
            # If it is successful, store the folder name parsed
            completed_file = dbname.replace('.db', '_completed.txt')
            print(foldername, file=open(completed_file, 'a'))
    elif default == 'run_folders':
        # This default assumes that all the outcar files are in folders
        # called run_XYZ where XYZ is the run number.
        print('Run folders path chosen.')
        if consider is not None:
            all_paths = glob.glob('*' + consider + '*/run_**/vasprun.xml', recursive=True)
        elif exact is not None:
            all_paths = glob.glob('*/' + exact + '*/run_**/vasprun.xml*', recursive=True)
        else:
            all_paths = glob.glob('**/run_**/OUTCAR*', recursive=True)
        
        for paths in all_paths:
            if exclude is not None:
                if exclude in paths:
                    continue
            foldername = paths

            try:
                method = StoreAtomsinASEdb(dbname=dbname, foldername=foldername)
                method.get_specifics_for_run_folders()
                method.store_attributes('')
            except:
                error_file = dbname.replace('.db', '_error.txt')
                print('Could not store {}'.format(foldername), file=open(error_file, 'a'))
                continue



