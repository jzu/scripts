#/bin/bash

# scan2stl.sh - jzu@free.fr 2015 - WTFPL

# Extrudes an image so that it can be 3D-printed
# Run as a standalone script, or from a CGI wrapper
# Depends on ImageMagick, potrace, pstoedit, OpenSCAD

if [ $# -eq 0 ] 
then
  echo Usage: `basename $0` '[filename without extension]' 1>&2
  exit 1
fi

NAME=$1
TMP=tmp-$NAME
SCALESCAD=.82
SCALEXY="\/7+1"
MARGIN="*1.01+1"

trap "/bin/rm $NAME.ppm $NAME.eps $NAME.dxf $NAME.scad $TMP.ppm $TMP.stl" 0 1 2 3 11 15

# Make a B&W image and remove details, then trim it

convert $NAME.jpg -blur 7x7 -threshold 50% $TMP.ppm
convert $TMP.ppm -trim +repage $NAME.ppm

# Vectorize to EPS

potrace $NAME.ppm

# Convert to DXF

pstoedit -q -dt -f "dxf: -polyaslines -mm" $NAME.eps $NAME.dxf

# Compute image mesh size

export X=`grep '%%BoundingBox:' $NAME.eps \
          | sed 's/.* 0 0 \(.*\) .*/\1'$SCALEXY'/' \
          | bc`
export Y=`grep '%%BoundingBox:' $NAME.eps \
          | sed 's/.* \(.*\)/\1'$SCALEXY'/' \
          | bc`

# Generate OpenSCAD file on the fly

echo "// Generated by $0 on "`date "+%Y-%m-%d %H:%M"`"
translate ([-$X, -$Y, 0])
  scale ($SCALESCAD)
    linear_extrude (height = 7)
      import (\"$NAME.dxf\", center=true);
" > $NAME.scad 

# Convert image to extruded mesh

openscad -o $TMP.stl $NAME.scad

# Suppress "endsolid OpenSCAD_Model"

head -n -1 $TMP.stl > $NAME.stl

# Compute base size

X=`echo "$X$MARGIN" | bc`
Y=`echo "$Y$MARGIN" | bc`

# This blob contains STL directives for the base:
# facet normal 1 0 0\n outer loop\n vertex X -Y 3\n vertex X Y 3 (...)
# X and Y are substituted with computed values
# The resulting stream is concatenated to the image mesh

echo "H4sIAIrLjVUAA62UQQ7CIBBF9z3FvwBJG09gdGtcuNGVaWRMTBAaRNPjS6uuOm0H
LKvhh8xjfj4A1/pCAdb5e22gKpQoC8TlnoE8jHNNvwVe5AO1UEeoE1YDkdPiwU8z
svrbKVY9MZZ55FJEloMjFVX6xLz2kxbCjnj6F7YzOt3mUW1x8ESKcskde97qAYPL
WkKiZVxuuCn3JVyB0RMhyn1GIiozK3MRKXT+zxAbLM+TEMr9FynUWDycuWnsG7KH
zXp73jlNpngDEPvBWLIFAAA=" \
| base64 -d \
| gunzip \
| sed -e "s/X/$X/" \
      -e "s/Y/$Y/" \
>> $NAME.stl

