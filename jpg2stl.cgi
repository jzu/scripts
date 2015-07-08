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
# It works with most major browsers with a reasonable version number - MS
# refuses to implement SSE in IE11, though its behaviour could be emulated. 
# See e.g. https://github.com/remy/polyfills/blob/master/EventSource.js


CGIDIR=$PWD
APPDIR=/tmp/jpg2stl
EVTFILE=$APPDIR/$REMOTE_HOST-$REMOTE_PORT.evt
[ -z $REMOTE_HOST ] && \
  EVTFILE=$APPDIR/$REMOTE_ADDR-$REMOTE_PORT.evt

mkdir -p $APPDIR
cd $APPDIR


# Error management

error () {
  echo -en "Status: 204\r\n\r\n"
  echo -n $* > $EVTFILE
  rm -f "$IMAGENAME"
  exit 1
}


# Session management

echo $HTTP_COOKIE | grep -q jpg2stl
if [ $? = 0 ]
then
  COOKIE="Cookie: "`echo $HTTP_COOKIE \
                    | sed -e 's/.*jpg2stl=//' \
                          -e 's/;.*//'`
else
  COOKIE="Set-Cookie: jpg2stl=$REMOTE_HOST-$REMOTE_PORT"
fi


# Notification handler

if [ "$HTTP_ACCEPT" = "text/event-stream" ]
then
  echo -en "$COOKIE\r\n"
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

file --mime-type "$IMAGENAME" | grep -q image/jpeg || \
  error "This file is not a JPEG"

[ `stat -c %s "$IMAGENAME"` -gt 1000000 ] && \
  error "$IMAGENAME > 1MB" 

# Hi ho, let's go

$CGIDIR/jpg2stl.sh ${IMAGENAME/.jpg/} 1>&2

[ $? -ne 0 ] && \
  error "No significant pattern in $IMAGENAME - increase contrast?"

# All clear, send the file

echo -en "$COOKIE\r\n"
echo -en "Content-Type: application/force-download\r\n"
echo -en "Content-Disposition: attachment; filename=\"$STLNAME\"\r\n\r\n"

cat "$STLNAME"
 

