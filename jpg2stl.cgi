#!/bin/bash

# jpg2stl.cgi - jzu@free.fr 2015 - WTFPL

# CGI wrapper for jpg2stl.sh, called by something like:
#
#  <iframe src="/cgi-bin/jpg2stl.cgi"
#         width="1000"
#         height="100"
#         style="border: 0px">
# </iframe>
#
#
# The CGI verifies that a real JPEG of a reasonable size has been uploaded,
# and sends it to the shell script which generates an STL file for 3D 
# printing. In case of an error at any stage, it simply sends back the
# HTML iframe containing the error message.
# 
# The CGI can be called either from a GET or a POST method. A GET means the
# calling HTML simply wants to display the form. A POST comes from a file
# upload request, and displaying the form in this context means there is an
# error and we want to add a temporary message.


CGIDIR=$PWD
APPDIR=/tmp/jpg2stl

mkdir -p $APPDIR
cd $APPDIR

# Displays the iframe including the upload form and a div
# - without an argument: simply called from the HTML, no error message
# - with an argument: in response to an error, prints the message in the div
# The <p>...</p> part can be customized, and you can replace the <div> with
# a window.alert, for example.

iframe () {
  echo -en "Content-Type: text/html\r\n\r\n"
  echo '
    <!DOCTYPE HTML>
    <html>
    <head>
     <title>File upload iframe</title>
    </head>
    <body>
     <form action="'$CONTEXT_PREFIX'jpg2stl.cgi" 
           method="post" 
           enctype="multipart/form-data">
      <p>
       JPEG &lt; 1M : 
       <input type="file" name="image">
       <input type="submit" value="Go!">
      </p>
      <div id="errormsg"></div>
      <script>
       document.getElementById ('\''errormsg'\'').innerHTML = "'$*'";
       setTimeout (function () {
                     document.getElementById ('\''errormsg'\'').innerHTML = "";
                   }, 
                   5000);
      </script>
     </form>
    </body>
   </html>
  '
  exit 0
}


# iframe called by a GET

[ $REQUEST_METHOD = "GET" ] && \
  iframe


# Upload called by a POST

read
read SOURCEFILE
read
read

SOURCEFILE=`echo $SOURCEFILE \
            | sed -e 's/.*filename="//' \
                  -e 's/".*//g'` 
IMAGENAME=`echo $SOURCEFILE \
           | sed -e 's/[^a-z0-9\-\.]/_/ig' \
                 -e "s/\.jpe*g//i" \
                 -e "s/$/.jpg/"`
STLNAME=`echo $IMAGENAME \
         | sed "s/\.jpg/.stl/"`

# Forget the boundary

head -n -1 > "$IMAGENAME"

# Preliminary checks

[ -z $SOURCEFILE ] &&
  iframe "No file given"

file --mime-type "$IMAGENAME" | grep -q image/jpeg || \
  iframe "$SOURCEFILE is not a JPEG"

[ `stat -c %s "$IMAGENAME"` -gt 1000000 ] && \
  iframe "$SOURCEFILE > 1MB" 

# Hi ho, let's go

$CGIDIR/jpg2stl.sh ${IMAGENAME/.jpg/} 1>&2

# Easy ride?

[ $? -ne 0 ] && \
  iframe "No significant pattern in $SOURCEFILE - increase contrast?"

# All clear, send the file

echo -en "Content-Type: application/force-download\r\n"
echo -en "Content-Disposition: attachment; filename=\"$STLNAME\"\r\n\r\n"

cat "$STLNAME"
 

