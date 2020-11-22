#!/bin/bash



#cleaning unnecassery stufs

function cleaning_function(){
    DIRECTORY=$(pwd)
    cd ..  
       
    if [ -d 'dist' ] ; then
        rm -r dist
    fi

    if [ -d 'site' ] ; then
        rm -r site

    fi
    cd $DIRECTORY
    echo "Successfully cleaned..."
}
cleaning_function