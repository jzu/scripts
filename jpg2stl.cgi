#!/bin/bash

# jpg2stl.cgi - jzu@free.fr 2015 - WTFPL

# CGI wrapper for jpg2stl.sh, called by something like:
#
# <script>
#   var source = new EventSource ("/cgi-bin/jpg2stl.cgi")
#   source.onmessage = function (event) {
#                        window.alert (event.data); 
#                      };
# </script>
# <form action="/cgi-bin/jpg2stl.cgi" 
#       method="post" 
#       enctype="multipart/form-data">
#
# The CGI verifies that a real JPEG of a reasonable size has been uploaded,
# and sends it to the shell script which generates an STL file for 3D 
# printing. In case of an error at any stage, it simply writes a message in 
# a session-specific file and sends back a 204 No Content status code, so 
# nothing changes on the page. Then...
# 
# The <script> part subscribes the page to a Server-Sent Event URL which is
# this very CGI. At the beginning, the text/event-stream content-type is
# detected and, if an error has been encountered, a message is displayed
# within 3 seconds in a window.alert() on the browser with the content of the 
# the session-specific file, and we quit. Else, if no error had happened, we 
# simply quit. 
#
# This appears to be the only way to stay on the same page in case of a
# processing error, so that the form can be transparently integrated into any 
# application: an XHR would not easily allow an unattended download, instead
# forcing the user to click on a link (which we'd have to manage, etc.) 
# It should work with all major browsers with a reasonable version number.


CGIDIR=$PWD
APPDIR=/tmp/jpg2stl
EVTFILE=$APPDIR/$REMOTE_HOST-$REMOTE_PORT.evt

mkdir -p $APPDIR
cd $APPDIR

# Notification handler

if [ "$HTTP_ACCEPT" = "text/event-stream" ]
then
  echo -en 'Content-Type: text/event-stream\r\n'
  echo -en 'Cache-Control: no-cache\r\n\r\n'
  if [ -f $EVTFILE ]
  then
    echo -en "data: ERROR - "
    cat $EVTFILE
    echo -en "\n\n"
    /bin/rm $EVTFILE
    # Clean up possible residual error files (older than 15 mn)
    for OLDEVT in $APPDIR/*.evt 
    do 
      [ $[`date +%s`-`stat -c %Z $OLDEVT`] -gt 900 ] && \
        /bin/rm $OLDEVT
    done
  fi
  exit 0
fi

# Not an event, so this is a processing request

read
read IMAGENAME
read
read

IMAGENAME=`echo $IMAGENAME \
           | sed -e 's/.*filename="//' \
                 -e 's/".*//g' \
                 -e 's/[^a-z0-9\-\.]/_/ig' \
                 -e "s/\.jpe*g//i" \
                 -e "s/$/.jpg/"`
STLNAME=`echo $IMAGENAME \
         | sed "s/\.jpg/.stl/"`

head -n -5 > "$IMAGENAME"

# Preliminary checks

file --mime-type "$IMAGENAME" | grep -q image/jpeg
if [[ $? -ne 0 ]]
then
  echo -en "Status: 204\r\n\r\n"
  echo -n "$IMAGENAME is not a JPEG" > $EVTFILE
  exit 1
fi

if [ `stat -c %s "$IMAGENAME"` -gt 1000000 ]
then 
  echo -en "Status: 204\r\n\r\n"
  echo -n "$IMAGENAME > 1MB" > $EVTFILE
  exit 2
fi

# This is called a "business method" in books on Java. Ok, whatever.

$CGIDIR/jpg2stl.sh ${IMAGENAME/.jpg/} 1>&2

if [ $? -ne 0 ]
then
  echo -en "Status: 204\r\n\r\n"
  echo -n "No significant pattern in $IMAGENAME - increase contrast?" > $EVTFILE
  exit 3
fi

# All clear, send the file

echo -e "Content-Type: application/force-download\r"
echo -e "Content-Disposition: attachment; filename=\"$STLNAME\"\r\n\r"

cat "$STLNAME"
 

