# Patrol for Oil (Supervisor)

Server side application for the patrolling framework addressed in Entre Mares.

# How to install

1. Download releases of [PyGnome 1.0.0](https://github.com/NOAA-ORR-ERD/PyGnome) and [Oil Library 1.1.3](https://github.com/NOAA-ORR-ERD/OilLibrary), unzip and place them in a folder. Do not install it yet, in this repository an unified requirements file is provided.

2. Create a python 3.8 environment, in this tutorial we are using [Miniconda 3](https://docs.conda.io/en/latest/miniconda.html):

`$ conda create -n gnome python=3.8`

3. Add the conda-forge channel to acquire some libraries:

`conda config --add channels conda-forge`

4. With the gnome environment created, activate it:

`$ conda activate gnome`

5. Install dependencies from requirements file provided in this repository:

`$ conda install --file requirements.txt`

6. If a library could not be installed, install manually, as for today, pynucos need to be manually installed:

`$ conda install pynucos`

7. Install the Oil Library, go to the respective folder and run (it may take a while):

`$ python setup install`

8. Install PyGnome, got to the respective folder, there will have a *"py_gnome"* folder, inside it, run:

`$ python setup develop`

9. With that all is set up for running the server

# Running the Supervisor

In the repository folder, run *run_server.sh* in Linux or *run_server.bat* in Windows. The API interface will be up at "http://localhost:5000" and the web application at "http://localhost:5000/index"