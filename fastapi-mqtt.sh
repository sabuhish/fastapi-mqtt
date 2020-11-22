#!/bin/bash


#!/bin/bash
ISSUE_URL="https://github.com/sabuhish/fastapi-mqtt/issues"
EMAIL="sabuhi.shukurov@gmail.com"
CURRENT_DIRECTORY=$(pwd)


function automated_commands(){

    if [[ "$1" == "clean" || $1 == "install" ]]; then

        if [[ "$1" == "install" ]]; then
                echo ""
                echo -e "Author Sabuhi Shukurov"
                cd "$CURRENT_DIRECTORY/scripts/"
                bash install.sh 
                cd $CURRENT_DIRECTORY
               
                exit 0
        else
            echo ""
            cd "$CURRENT_DIRECTORY/scripts/"
            bash clean.sh 
            cd $CURRENT_DIRECTORY
            
            exit 0
        fi

    elif [[ "$1" == "-h" || $1 == "--help" ]]; then
        echo -e "Thanks for your try at contribution!"

        echo ""
        echo -e "Usefull Commands:"
      
        echo -e "\t install   Creating virtual enviroment and installing dependencies"
        echo -e "\t clean     Cleaning unusefull folders and files"
        echo ""
        echo -e "If you still having problem  please submit issue at: $ISSUE_URL or email me: $EMAIL"
        exit 0
    else
        echo "Unknown command, try with bash fastapi-mqtt.sh -h, --help"
    fi

}

automated_commands $1