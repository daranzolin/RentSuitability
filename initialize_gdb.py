# -*- coding: utf-8 -*-
"""
Created on Tue May  4 19:18:11 2021

@author: David Ranzolin
"""
import arcpy
import sys, os
from arcpy import env
from arcpy import management as DM
env.workspace = os.path.dirname(sys.argv[0])

projgdb = "projdata.gdb"

if arcpy.Exists(projgdb):
    DM.Delete(projgdb)

DM.CreateFileGDB(env.workspace, projgdb)
print("Created projdata.gdb...\n")

to_transfer = ["sfsuPOINT", "BAdem90.tif", "BA_TransitStops.shp", "ba_1br_rent_estimates.shp"]

for file in to_transfer:
    DM.TransferFiles(file, projgdb)
