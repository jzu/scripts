#!/bin/bash

# jpg2stl.cgi - jzu@free.fr 2015 - WTFPL

# Basic CGI wrapper for jpg2stl.sh
# To be called by something like
# <form action="/cgi-bin/jpg2stl.cgi" 
#       method="post" 
#       enctype="multipart/form-data">

CGIDIR=$PWD

mkdir -p /tmp/jpg2stl
cd /tmp/jpg2stl

read
read IMAGENAME
read
read

IMAGENAME=`echo $IMAGENAME \
           | sed -e 's/.*filename="//' \
                 -e 's/".*//g' \
                 -e 's/[^a-z0-9\-\.]/_/ig' \
           | tr A-Z a-z`
STLNAME=`echo $IMAGENAME \
         | sed "s/\.jpe*g/.stl/"`

head -n -5 > "$IMAGENAME"

file --mime-type "$IMAGENAME" | grep -q image/jpeg
if [[ $? -ne 0 ]]
then
  echo -e "Content-Type: text/html\r\n\r"
  echo "<html><head></head>
        <body>
        <p>ERROR: $IMAGENAME is not a JPEG</p>
        <p><a href=\"$HTTP_REFERER\">Return</a></p>
        </body></html>"
  exit 1
fi

if [ `stat -c %s "$IMAGENAME"` -gt 1000000 ]
then 
  echo -e "Content-Type: text/html\r\n\r"
  echo "<html><head></head>
        <body>
        <p>ERROR: File $IMAGENAME &gt; 1MB</p>
        <p><a href=\"$HTTP_REFERER\">Return</a></p>
        </body></html>"
  exit 2
fi

$CGIDIR/jpg2stl.sh ${IMAGENAME/.jpg/} 1>&2

echo "IMAGENAME=$IMAGENAME STLNAME=$STLNAME" 1>&2

echo -e "Content-Type: application/force-download\r"
echo -e "Content-Disposition: attachment; filename=\"$STLNAME\"\r\n\r"

cat "$STLNAME"
 

