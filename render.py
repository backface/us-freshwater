#!/usr/bin/python

import gdal, ogr, osr
from PIL import Image, ImageDraw, ImageFont
import math
import sys
  
primary_color = (0, 0, 255, 255)
width = 8196
custom_extend = (-122, 18, -60, 50)


def main():
  if len(sys.argv) > 1:
    infile = sys.argv[1]
    outfile  = sys.argv[2]
  else:
    infile = 'input.osm'
    outfile = 'output.png'

  gdal.SetConfigOption('OGR_INTERLEAVED_READING', 'YES')
  osm = ogr.Open(infile)

  nLayerCount = osm.GetLayerCount()
  thereIsDataInLayer = True

  sourceRef = osm.GetLayer(0).GetSpatialRef()
  targetRef = osr.SpatialReference()
  targetRef.ImportFromEPSG(102003)
  transform = osr.CoordinateTransformation(sourceRef, targetRef)

  Xmin, Xmax, Ymin, Ymax = osm.GetLayer(0).GetExtent()
  print("orig extents:", Xmin, Ymin, Xmax, Ymax)

  if custom_extend:
    Xmin, Ymin, Xmax, Ymax = custom_extend
    print("custom extents:", Xmin, Ymin, Xmax, Ymax)
    
  minPoint = ogr.Geometry(ogr.wkbLineString)
  minPoint.AddPoint(Xmin, Ymin)
  minPoint.Transform(transform)
  maxPoint = ogr.Geometry(ogr.wkbLineString)
  maxPoint.AddPoint(Xmax, Ymax)
  maxPoint.Transform(transform)

  Xmin, Ymin, Xmax, Ymax = (minPoint.GetX(), minPoint.GetY(), maxPoint.GetX(), maxPoint.GetY() )
  print("target extents:", Xmin, Ymin, Xmax, Ymax)

  pixel_size = 100 # meter per pixel
  pixel_size = abs(Xmax - Xmin) / width
  target_Width = int(abs(Xmax - Xmin) / pixel_size)
  target_Height = int(abs(Ymax - Ymin) / pixel_size)

  print ("width: {0:.2f} km".format(abs(Xmax - Xmin)/1000))
  print ("height: {0:.2f} km".format(abs(Ymax - Ymin)/1000))
  print ("target width: {} px ".format(target_Width))
  print ("target height: {} px".format(target_Height))

  image = Image.new('RGBA', (target_Width, target_Height), "white")
  draw = ImageDraw.Draw(image)
  counter = 0
  
  def linestring(points, color="black", width=1):
    for i in range(1, len(points)):
      draw.line( [ points[i-1], points[i]], fill=color, width=width )    

  while thereIsDataInLayer:

    thereIsDataInLayer = False

    for iLayer in range(nLayerCount):

      lyr=osm.GetLayer(iLayer)
      feature = lyr.GetNextFeature()
      
      while (feature is not None):

        thereIsDataInLayer = True
        geom = feature.GetGeometryRef()            
        counter += 1
        print("\r ... processing feature {} ... ".format(counter),end="")
        
        # we ignore points
        if geom.GetGeometryName() == "POINT":  
          pass
      
        # Linestring are for ways
        elif geom.GetGeometryName() == "LINESTRING":
          geom.Transform(transform)
          points = list(map(lambda p: ((p[0]- Xmin) / pixel_size, (Ymax - p[1]) / pixel_size), geom.GetPoints()))
           
          
          # this is for rivers and streams
          if feature.GetFieldIndex("waterway"):
            if feature.GetField(feature.GetFieldIndex("waterway")) == "river":
              linestring(points, primary_color, 1)
            elif feature.GetField(feature.GetFieldIndex("waterway")) == "riverbank":
              linestring(points, primary_color, 3)
            elif feature.GetField(feature.GetFieldIndex("waterway")) == "canal":
              linestring(points, primary_color, 1)
            elif feature.GetField(feature.GetFieldIndex("waterway")) == "stream":
              pass
           
          # this if for roads  
          #if feature.GetFieldIndex("highway"):
          #  if feature.GetField(feature.GetFieldIndex("highway")) == "motorway":
          #    linestring(points, primary_color, 4)
          #  elif feature.GetField(feature.GetFieldIndex("highway")) == "primary":
          #    linestring(points, primary_color, 3)
          #  elif feature.GetField(feature.GetFieldIndex("highway")) == "secondary":
          #    linestring(points, primary_color, 2)
          #  elif feature.GetField(feature.GetFieldIndex("highway")):
          #    linestring(points, primary_color, 1)
              
          #if feature.GetFieldIndex("railway"):
          #    linestring(points, primary_color, 1)
          #    
          #if feature.GetFieldIndex("pipepline"):
          #    linestring(points, primary_color, 1)              
  
        # Polygons? Haven't seen them yet.
        elif geom.GetGeometryName() == "POLYGON":
          pass
      
        # multipolygons are for lakes and stuff 
        elif geom.GetGeometryName() == "MULTIPOLYGON":
          geom.Transform(transform)
          for i in range(0, geom.GetGeometryCount()):
            g = geom.GetGeometryRef(i)
            for j in range(0, g.GetGeometryCount()):        
              ring = g.GetGeometryRef(j)  
              if ring.GetPoints():
                points =  list(map(lambda p: ((p[0]- Xmin) / pixel_size, (Ymax - p[1]) / pixel_size),  ring.GetPoints()))
                draw.polygon(points, fill=primary_color, outline=primary_color) 
                linestring(points, primary_color, 2)              
              else:
                print("MULTIPOLYGON inner", ring.GetGeometryCount(), ring.GetGeometryName())

                 
        # Everything else is not necessary. I guess these are relations.
        # We just draw everthing over, so it makes important ways stronger
        
        elif geom.GetGeometryName() == "MULTILINESTRING":
          geom.Transform(transform)
          for j in range(0, geom.GetGeometryCount()):        
            ring = geom.GetGeometryRef(j)  
            if ring.GetPoints():
              points =  list(map(lambda p: ((p[0]- Xmin) / pixel_size, (Ymax - p[1]) / pixel_size),  ring.GetPoints()))
              if len(points) > 1:
                linestring(points, primary_color, 2)              
            else:
              print("MULTILINESTRINGr inner", ring.GetGeometryCount(), ring.GetGeometryName())
              
        elif geom.GetGeometryName() == "GEOMETRYCOLLECTION":
          geom.Transform(transform)
          for j in range(0, geom.GetGeometryCount()):          
            ring = geom.GetGeometryRef(j)  
            
            if ring.GetGeometryName() == "POINT":  
              #ignore points again
              pass
            
            elif ring.GetGeometryName() == "LINESTRING":
              if ring.GetPoints():
                points =  list(map(lambda p: ((p[0]- Xmin) / pixel_size, (Ymax - p[1]) / pixel_size),  ring.GetPoints()))
                if len(points) > 1:
                  linestring(points, primary_color, 2)              
              else:
                print("MULTILINESTRINGr inner", ring.GetGeometryCount(), ring.GetGeometryName())
                
            elif ring.GetGeometryName() == "POLYGON":        
              for i in range(0, geom.GetGeometryCount()):
                g = geom.GetGeometryRef(i)
                for j in range(0, g.GetGeometryCount()):        
                  ring = g.GetGeometryRef(j)  
                  if ring.GetPoints():
                    points =  list(map(lambda p: ((p[0]- Xmin) / pixel_size, (Ymax - p[1]) / pixel_size),  ring.GetPoints()))
                    draw.polygon(points, fill=primary_color, outline=primary_color) 
                    linestring(points, primary_color, 3)              
                  else:
                    print("MULTIPOLYGON inner", ring.GetGeometryCount(), ring.GetGeometryName())
            else:
              #something else? what am I?
              print(ring.GetGeometryName())
                
        else:
          pass
          print("ohter geom", geom)
          
        #The destroy method is necessary for interleaved reading
        feature.Destroy()
        feature = lyr.GetNextFeature()

        # save intermediate results for debugging
        if counter % 1000000 == 0:
          image.save(outfile)

  # destroy and save
  print("")
  osm.Destroy()
  image.save(outfile)


if __name__ == "__main__":
    main()
