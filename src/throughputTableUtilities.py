import csv
import numpy as np
from scipy.interpolate import griddata
import math


# returns table of strings, (min, max) for number of onD, (min, max) for number of bur
def readTable(filename):
    throughput = {}
    onD = set()
    bur = set()
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:
            dictTemp = {}
            for i in row:
                if i != "ond":
                    if int(row[i]) != -1:
                        dictTemp[i] = row[i]
                        bur.add(int(i))
            throughput[row["ond"]] = dictTemp
            onD.add(int(row["ond"]))
        return throughput, (min(onD), max(onD)), (min(bur), max(bur))


# convert dict to arr to help with the data type conversion for interpolation function griddata
# returns 3 lists for x, y and z respectively
def convertDictToArr(throughput):
    x = []
    y = []
    z = []
    for keyonD in throughput.keys():
        for keyBur in throughput[keyonD].keys():
            x.append(int(keyonD))
            y.append(int(keyBur))
            z.append(int(throughput[keyonD][keyBur]))
    return x, y, z


# Implementation of Linear Interpolation using Python3 code
def interpolation(grid_X, grid_Y, grid_Z, interpolate_x):
    grid_Z = np.asarray(grid_Z)
    points = np.vstack((grid_X, grid_Y)).T
    p = griddata(points, grid_Z, interpolate_x, method='linear')
    return p


# Fill up table using linear interpolation
def fillUpThroughputTable(table, onDlim, burlim):
    # Find out which cells are missing
    onDAll = list(range(onDlim[0], onDlim[1] + 1))
    burAll = list(range(burlim[0], burlim[1] + 1))
    interpolate_val = []
    for i in onDAll:
        for j in burAll:
            if str(i) not in table.keys():
                interpolate_val.append([i, j])
            elif str(j) not in table[str(i)].keys():
                interpolate_val.append([i, j])

    # Interpolate for the missing cells
    x, y, z = convertDictToArr(table)
    interpolate_x = np.array(interpolate_val)
    results = interpolation(x, y, z, interpolate_x)

    # Add all the results back to the dict
    for i in range(0, len(interpolate_val)):
        if str(interpolate_val[i][0]) not in table.keys():
            table[str(interpolate_val[i][0])] = {}
        table[str(interpolate_val[i][0])][str(interpolate_val[i][1])] = results[i]

'''
    Determines the number of burstable instances required to achieve a given throughput given the number of regular instances.

    Parameters:
    - table (dict): A lookup table where keys represent the number of on-demand instances (`onD`), 
      and values are dictionaries mapping burstable instance counts to throughput values.
    - onD (int): The number of on-demand instances currently in use.
    - throughput (float): The desired throughput to achieve.
    - min (int): The minimum number of burstable instances to start the search from.

    Returns:
    - int: The optimal number of burstable instances (`b`) to achieve the desired throughput.
           If no suitable number is found, the maximum possible value from the table is returned.
'''
def findNumberOfBurstable(table, onD, throughput, min):
    burstable = table[str(onD)]
    currentthroughput = math.inf
    b = -1
    i = min
    list(burstable.keys())
    m = int(max(burstable.keys(), key=lambda x: int(x)))
   
    while i <= m:
        if str(i) not in burstable.keys():
            i += 1
            continue
        if math.isnan(float(burstable[str(i)])) is False:
            if throughput <= float(burstable[str(i)]) < currentthroughput:
                b = int(i)
                currentthroughput = float(burstable[str(i)])
                break
        i += 1
    if b == -1:
        b = m
    return b
