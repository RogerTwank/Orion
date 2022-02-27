#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Run GMAT with a bunch of variations on the initial orbit state
# variations are contained in "params.txt"
# these are substituted into the GMAT_LEM_STATE and written out to state.txt file
# then the state.txt is contatenated to the mission.txt to generate the full GMAT script
# GMAT is invoked with this script
# Result files are copied over to the result directory, with names to indicate which parameter set was used


#get_ipython().run_line_magic('matplotlib', 'inline')
import os
import numpy as np
import subprocess
from demtrack import load_gmat_track, track_analysis, moon_ellipsoid, reference_lla
import pymap3d
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import demtrack
import pandas as pd
import time



#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

GMAT_LEM_STATE = """


Create Spacecraft A16_LM;
GMAT A16_LM.DateFormat = UTCGregorian;
GMAT A16_LM.Epoch = '24 Apr 1972 20:54:12.000';             % from jettison

% Param Order: Index,Latitude,Longitude,RMAG,VMAG,AZI,HFPA

GMAT A16_LM.CoordinateSystem = LunaFixed;
GMAT A16_LM.DisplayStateType = Planetodetic;

GMAT A16_LM.PlanetodeticLAT = {};
GMAT A16_LM.PlanetodeticLON = {};
GMAT A16_LM.PlanetodeticRMAG = {};
GMAT A16_LM.PlanetodeticVMAG = {};
GMAT A16_LM.PlanetodeticAZI = {};
GMAT A16_LM.PlanetodeticHFPA = {};

GMAT A16_LM.DryMass = 2398;
GMAT A16_LM.Cd = 2.2;
GMAT A16_LM.Cr = 1.8;
GMAT A16_LM.DragArea = 5;
GMAT A16_LM.SRPArea = 5;
GMAT A16_LM.NAIFId = -10001001;
GMAT A16_LM.NAIFIdReferenceFrame = -9001001;
GMAT A16_LM.OrbitColor = Red;
GMAT A16_LM.TargetColor = Teal;
GMAT A16_LM.OrbitErrorCovariance = [ 1e+070 0 0 0 0 0 ; 0 1e+070 0 0 0 0 ; 0 0 1e+070 0 0 0 ; 0 0 0 1e+070 0 0 ; 0 0 0 0 1e+070 0 ; 0 0 0 0 0 1e+070 ];
GMAT A16_LM.CdSigma = 1e+070;
GMAT A16_LM.CrSigma = 1e+070;
GMAT A16_LM.Id = 'Eagle';
GMAT A16_LM.Attitude = CoordinateSystemFixed;
GMAT A16_LM.SPADSRPScaleFactor = 1;

"""

# create a new directory for each run like pdtc_long for planetodetic longitude
# script filename reflects the run...like long_-30.script, long_45.script, etc
# result filename also reflects the run...long_-30.csv, etc
# single log in the directory gets appended for each run?

def runSet():

    CWD = 'C:/Users/roger/Desktop/Apollo 10/demtrack/runs'
    GMAT_PATH = 'C:/Users/roger/AppData/Local/GMAT/R2018a/bin/'
    GMAT_OUTPUT_PATH = 'C:/Users/roger/Desktop/GMAToutput/'
    SCRIPT_PATH = 'C:/Users/roger/Desktop/Apollo 10/demtrack/DemTrack/'
    PREFIX = 'A16MonteImpact'
    PREFIX1 = 'A16MontePeri'



    pythonScriptName = SCRIPT_PATH+'RunGMATSequence.py'
    outputFileName = GMAT_OUTPUT_PATH+'FullGroundTrack.csv'
    outputFileName1 = GMAT_OUTPUT_PATH+'perilune.csv'

    timestring = time.strftime("%H%M%S")
    CWD = CWD + '/'+PREFIX+timestring
    os.mkdir(CWD)


    thereIsdata = 1
    pfile = open('params.txt', 'r')
    headers = pfile.readline().strip().split(',')

    while (thereIsdata):
        # read in the next set
        params = pfile.readline().strip().split(',')
        if (params[0]==""):
            thereIsdata = 0
            continue    # KlunKy konstruct


            # patch the state
        print("patching the script with param set {}".format(params[0]))
        patchScript(np.array(params[1:]))

            # Concatenate the state to the mission and copy and rename resulting script
        concatenate()
        scriptName = CWD+'/'+PREFIX+params[0]+'.script'
        #scriptName = CWD+'/'+PREFIX+str(v)+'.script'
        os.rename('gmat.script',scriptName) 
        print("script created...{}".format(scriptName))
        current_dir = os.getcwd()

            # run GMAT with that script
        os.chdir(GMAT_PATH)
        print ("starting GMAT at {}".format(time.strftime("%H %M %S")))
        subprocess.call(['GMAT.exe', '-x', '-m', '-r', scriptName])     # -x exit when finished   -m run minimized, -r run the script at startup

        print ("GMAT finished at {}".format(time.strftime("%H %M %S")))
        time.sleep(4)
        os.chdir(current_dir)

            # copy result files and rename with parameter in filename
        os.rename( outputFileName, CWD+'/'+PREFIX+params[0]+'.csv')
        os.rename( outputFileName1, CWD+'/'+PREFIX1+params[0]+'.csv')

    return CWD



def patchScript(inVal):
    with open("state.txt", 'w') as f:
        f.write(GMAT_LEM_STATE.format(*inVal))



def concatenate():
    filenames = ['state.txt', 'mission.txt']
    with open('gmat.script', 'w') as outfile:
        for fname in filenames:
            with open(fname) as infile:
                outfile.write(infile.read())

def decimate(filepath):
    with open('out.csv', 'w') as outfile:
        i = 0
        with open(filepath) as infile:
            for inLine in infile:
                i = i+1
                if (i%25 == 1):
                    outfile.write(inLine)


def aggregateSet(path):
    #path = 'C:/Users/roger/Desktop/Apollo 10/demtrack/runs/Degree-Order/'

    os.chdir(path)
    columnsToGet = [5]
#    columnsToGet = [3,4]

        # first get a list of all the csv files in the directory
    list = os.listdir(path)
    newlist = []
    for names in list:
        if names.endswith(".csv"):
            newlist.append(names)


        # open each file in the list
    handles = []
    lineout = ""
    for name in newlist:
        handles.append(open(name))
        for c in columnsToGet:
            lineout = lineout + name + str(c) + ','

        # open outfile
    outfile = open('aggregate.txt', 'w')


        # first line is a list of the files and columns
    lineout = lineout.strip() +'\n'
    outfile.write(lineout)

        # read and (for now) discard the first row of each file
    for h in handles:
        firstrow = h.readline().split()

    thereIsdata = 1

    while (thereIsdata):
            # gather desired data from each column in each file
        lineout = ""
        for h in handles:
            fields = h.readline().strip().split(',')
            if (fields[0]==""):
                    thereIsdata = 0
            else:
                for c in columnsToGet:
                    lineout = lineout + fields[c-1] + ', '

        outfile.write(lineout.strip()+'\n')



def findHighLow(filepath):
    low = 1000
    high = 0
    with open(filepath) as infile:
        tossline = infile.readline()
        thereIsdata = 1

        while (thereIsdata):                     
            nextline = infile.readline()
            fields = nextline.strip().split(',')
            if len(fields)>3:
                val = float(fields[4])
                if val > high:
                       high = val
                if val < low:
                       low = val
            else:
                thereIsdata = 0
    return (high,low)


def printHighsLows(path):
    os.chdir(path)

        # first get a list of all the csv files in the directory
    list = os.listdir(path)
    newlist = []
    for names in list:
        if names.endswith(".csv"):
            newlist.append(names)

    for name in newlist:
        apo, peri = findHighLow(name)
        print("File: {}, Apolune: {} km, Perilune {} km".format(name, apo, peri))


def main():

    #timestring = time.strftime("%Y%m%d-%H%M%S")
    #SCRIPT_PATH = "C:/Users/roger/Desktop/Apollo 10/demtrack/DemTrack/gmat.script"
    #concatenate(SCRIPT_PATH, timestring,timestring)


    path = runSet() 

    #aggregateSet(path)

    #decimate(path)
    #printHighsLows(path)

main()