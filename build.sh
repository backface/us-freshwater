#!/bin/sh

INPUT=us-latest.osm.pbf
TARGET=us-freshwater

#downoad 
#wget -c http://download.geofabrik.de/north-america/$INPUT

echo "filter osm file"
#filter with osmium (FASTEST)
#osmium tags-filter $INPUT \
#  wr/waterway=river,stream,canal,riverbank,tidal_channel \
#  wr/water=river,lake,pond,reservoir,oxbow,lagoon,stream_pool,canal \
#  wr/landuse=reservoir \
#  --overwrite -o $TARGET.osm.pbf

echo "render png ... (now grab a coffee or read a book)"
python render.py   $TARGET.osm.pbf $TARGET.png
#viewnior $TARGET.png
