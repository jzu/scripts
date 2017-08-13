#!/bin/bash

# new_mew_labels - jzu@free.fr 2017 - MIT license
# Developed for MyEtherWallet (https://www.myetherwallet.com/)
# Find missing MEW translation strings in app/scripts/translations/XX.js
# and display original en.js key:value pairs
# Example : 
# cd ~/git/etherwallet
# new_mew_labels.sh fr

LANG=C
LC_ALL=C

# Cleanup all temp files

trap "rm -f /tmp/mew.*.$$" 0 1 2 3 15

# Sanity checks

DIR=app/scripts/translations

if [ ! -f $DIR/en.js ]
then
  echo "Where are you?"
  exit 1
fi

if [ $# -eq 0 ] 
then
  echo "Usage: $0 [target language (2 or 4 letters)]"
  exit 2
fi

TARGET=$1

if [ ! -f $DIR/$TARGET.js ]
then
  echo "$1 doesn't exist. Possible arguments are:"
  ls $DIR \
  | sed 's/\.js//' \
  | egrep "^..$|^....$" \
  | xargs
  exit 3 
fi

# Find all translation keys in en.js

grep ' :  *' $DIR/en.js \
| sed 's/ *:.*//' \
| sort \
> /tmp/mew.en.$$

# Find all translation keys in $TARGET.js

grep ' :  *' $DIR/$TARGET.js \
| sed 's/ *:.*//' \
| sort \
> /tmp/mew.$TARGET.$$

# Compare both and extract keys not in $TARGET

diff /tmp/mew.en.$$ /tmp/mew.$TARGET.$$ \
| grep '^<' \
| sed 's/^< //' \
| xargs \
| sed -e 's/ /|/g' \
      -e 's/^/"egrep_kludge|/' \
      -e 's/$/|egrep_kludge"/' \
> /tmp/mew.labels.$$

# Display key:value pairs in en.js with context

egrep -w -B 2 --color `cat /tmp/mew.labels.$$` $DIR/en.js

