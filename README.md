# dp1-coloring

This is the CSCE-668 Final Course Project.

Choice of paper: Locally-Iterative Distributed (∆ + 1)-Coloring below
Szegedy-Vishwanathan Barrier, and Applications to
Self-Stabilization and to Restricted-Bandwidth Models

Authors: Yifan Liu, Yahui Sun, Shibo Wang

## Usage

### Requirements
The program runs with python 3.6. Create a virtual environment
and install the requirements listed in requirements.txt (including
DistAlgo).

### Run
We've written two versions of our algorithms. One in DistAlgo,
located in src_da/SyncAGReduction.da. To run this file, type

```
python -m da src_da/SyncAGReduction.da
```

The other version, AGColoring_mps.py, is written in pure python. 
To run this file, type 

```
python AGColoring_mps.py
```

You can adjust the number of nodes in the main function of 
these two files (e.g. ```n=10```).

The program will draw the final coloring in browser.