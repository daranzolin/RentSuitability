# -*- coding: utf-8 -*-
"""
Created on Tue May  4 19:34:46 2021

@author: David Ranzolin
"""
import arcpy
import sys, os
from arcpy import env
from arcpy import management as DM
env.workspace = os.path.dirname(sys.argv[0])
arcpy.env.overwriteOutput = True

outPoint = "sfsu"

if arcpy.Exists(outPoint):
    DM.Delete(outPoint)

shp_out = DM.CreateFeatureclass(env.workspace, outPoint, "POINT", spatial_reference=4326)

cur = arcpy.da.InsertCursor(shp_out, ["SHAPE@XY"])
sfsu = (-122.4799, 37.7241)
cur.insertRow([sfsu])
del cur

outSR = arcpy.SpatialReference(26943)
DM.Project(env.workspace, "sfsuProjected", outSR)
