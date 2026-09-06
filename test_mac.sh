#!/bin/bash

# Copy the files needed to run a project to a mac.

set -ex

DESTINATION=$1
DESTINATION=${DESTINATION%/}

cd $(dirname $0)

if [ -z "$DESTINATION" ] || [[ "$DESTINATION" != *:* ]]; then
    echo "Usage: $0 <user>@<host>:<path>"
    exit 1
fi


sync() {
    item=${1%/}
    source=renpy/$item

    if [ -d "$source" ]; then
        source=$source/
    fi

    rsync -a "$source" "$DESTINATION/$item"
}

rpy build --platform mac

sync launcher
sync lib
sync rapt
sync renios
sync renpy
sync renpy.app
sync renpy.py
sync renpy.sh
sync sdk-fonts
sync the_question
sync tutorial
