# -*- coding: utf-8 -*-

import arcpy
from arcpy import env
from arcpy import management as DM
from arcpy import analysis as AN
from arcpy.sa import *
env.overwriteOutput = True

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [RentSuitabilityAnalysis]


class RentSuitabilityAnalysis(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Rent Suitability Analysis"
        self.description = ""
        self.canRunInBackground = False
        
    def EucDistanceAndJoinZonalToTracts(self, location, zones, fieldName):
        """Run the Euclidian Distance, ZonalStatisticsAsTable, and Join Field tools"""
        
        outEucDistance = EucDistance(location)
        zonalTable = "zonalTable.dbf"
        outZonalDistanceFromLocation = ZonalStatisticsAsTable(zones, "OBJECTID", outEucDistance, zonalTable, "NODATA", "MEAN")
        tractsWithZonalDistance = DM.JoinField(zones, "OBJECTID", outZonalDistanceFromLocation, "OBJECTID", ["MEAN"])         
        DM.AlterField(tractsWithZonalDistance, "MEAN", fieldName, fieldName)
        DM.Delete(zonalTable)
        return tractsWithZonalDistance

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        location = arcpy.Parameter(
            displayName = "Location",
            name = "location",
            datatype = "Feature Class",
            parameterType = "Required",
            direction = "Input"
        )
        distanceUnitsLocation = arcpy.Parameter(
            displayName = "Miles from Location",
            name = "distanceUnitsLocation",
            datatype = "Double",
            parameterType = "Required",
            direction = "Input"
        )
        rentTracts = arcpy.Parameter(
            displayName = "Rent Tracts",
            name = "rentTracts",
            datatype = "Feature Class",
            parameterType = "Required",
            direction = "Input"
        )
        rentMax = arcpy.Parameter(
            displayName = "Max Rent",
            name = "rentMax",
            datatype = "Double",
            parameterType = "Required",
            direction = "Input"
        )
        transitPoints = arcpy.Parameter(
            displayName = "Transit Points",
            name = "transitPoints",
            datatype = "Feature Class",
            parameterType = "Optional",
            direction = "Input"
            )
        transitSQL = arcpy.Parameter(
            displayName = "Subset Transit Feature Class w/SQL",
            name = "transitSQL",
            datatype = "SQL Expression",
            parameterType = "Optional",
            direction = "Input"
        )
        transitSQL.parameterDependencies = [transitPoints.name]
        
        distanceUnitsTransit = arcpy.Parameter(
            displayName = "Distance Units from Transit",
            name = "distanceUnitsTransit",
            datatype = "Double",
            parameterType = "Required",
            direction = "Input"
        )
        
        outputPath = arcpy.Parameter(
            displayName = "Output",
            name = "outputPath",
            datatype = "Feature Class",
            parameterType = "Required",
            direction = "Output"
        )

        params = [location, distanceUnitsLocation, rentTracts, rentMax, transitPoints, transitSQL, distanceUnitsTransit, outputPath]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return        

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.AddMessage("Starting Rent Suitability Analysis...\n")
        location = parameters[0].valueAsText
        milesFromLocation = parameters[1].valueAsText
        rentTracts = parameters[2].valueAsText
        rentMax = parameters[3].valueAsText
        transitPoints = parameters[4].valueAsText
        transitSQL = parameters[5].valueAsText
        milesFromTransit = parameters[6].valueAsText
        outputPath = parameters[7].valueAsText
        
        toolExt = arcpy.Describe(rentTracts).extent
        env.extent = toolExt
        arcpy.CheckOutExtension("Spatial")
        
        # locSR = arcpy.Describe(location).spatialReference
                
        tractFieldNames = [f.name for f in arcpy.ListFields(rentTracts)]
        fieldsToDelete = ["MilesFromLoc", "MilesFromTransit"]
        
        for f in fieldsToDelete:
            if f in tractFieldNames:
                 rentTracts = DM.DeleteField(rentTracts, f)
                 
        tractsWithDistance = self.EucDistanceAndJoinZonalToTracts(location, rentTracts, "MilesFromLoc")
                
        transitSelection = DM.SelectLayerByAttribute(transitPoints, 'SUBSET_SELECTION', transitSQL)
        tractsWithDistance2 = self.EucDistanceAndJoinZonalToTracts(transitSelection, tractsWithDistance, "MilesFromTransit") 
       
        with arcpy.da.UpdateCursor(tractsWithDistance2, ["MilesFromLoc", "MilesFromTransit"]) as cur:
            for row in cur:
                if row[0] is not None:
                    row[0] = row[0]/1609
                if row[1] is not None:
                    row[1] = row[1]/1609
                cur.updateRow(row)
        del cur
        
        outFieldNames = [f.name for f in arcpy.ListFields(tractsWithDistance2)]
        for f in outFieldNames:
            if "MEAN_" in f:
                DM.DeleteField(tractsWithDistance2, f)        
                
        outSelectionSQL = f'"estimate" > 600 AND "estimate" <= {rentMax} AND "MilesFromLoc" <= {milesFromLocation} AND "MilesFromTransit" <= {milesFromTransit}'
        rentTractsSelection = DM.SelectLayerByAttribute(tractsWithDistance2, 'SUBSET_SELECTION', outSelectionSQL)
        DM.CopyFeatures(rentTractsSelection, outputPath)
        arcpy.AddMessage("Done!")

