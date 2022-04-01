#!/bin/bash

IMAGE_NAME="glados-tts"

function usage {
    echo ""
    echo "usage: start.sh [-b|-f|-h]"
    echo "  -b Build the image."
    echo "  -f Full build.  Do not use build cache."
    echo "  -d Run in background (daemon)."
    echo "  If no arguemnts are supplied the default behavior is to"
    echo "  build the image if a version is not already available, "
    echo "  and start the the glados-tts engine"
}

ARG="${1:-unset}"

#Default options
BUILD=false
CACHE=true
DAEMON=false

#Check all arguments to assign build values
for i in $@; do
	case $i in
		"-b") 
	        BUILD=true
	        ;;
	     "-f") 
	        CACHE=false
	        ;;
	     "-d") 
	        DAEMON=true
	        ;;
	    "-h") 
	        #Help requested.
	        usage 
	        exit 1
	        ;;
	esac
done

#If image does not already exists, override the BUILD option
if [[ -z "$(docker images -q $IMAGE_NAME)" ]];then
	echo "Image does not exist. Setting build option to true"
	BUILD=true
fi

if [ "$BUILD" = true ]; then
	echo "Building image for GLaDOS-tts..."
	BUILD_ARGS=""
	if [ ! "$CACHE" = true ]; then
		echo "Not using build cache"
		BUILD_ARGS="--no-cache"
	fi
	docker build -f docker/Dockerfile -t $IMAGE_NAME $BUILD_ARGS .
fi

RUN_ARGS=""
echo "DAEMON: $DAEMON"
if [ "$DAEMON" = true ]; then
	RUN_ARGS="-d"
fi

mkdir -p audio
#Start the image, the tts engine and map the ports
docker run --name $IMAGE_NAME \
		   --rm \
		   -p 8124:8124 \
		   -v "$PWD"/audio:/glados-tts/audio \
		   $RUN_ARGS \
		   $IMAGE_NAME python3 engine.py