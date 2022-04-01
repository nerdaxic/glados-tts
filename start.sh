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
BUILD_CACHE=true
CACHE=false
DAEMON=false
AUDIO_PATH=""

#Check all arguments to assign build values
for i in $@; do
	case $i in
		"-b") 
	        BUILD=true
	        ;;
	     "-f") 
	        BUILD_CACHE=false
	        ;;
	     "-d") 
	        DAEMON=true
	        ;;
	     "-c") 
	        CACHE=true
	        ;;
	    "-h") 
	        #Help requested.
	        usage 
	        exit 1
	        ;;
	esac
done

#Allow an optional audio cache path to be provided
while getopts ":c:" opt; do
	case $opt in
		c)
			if [ ! -z "$OPTARG" ];then
				AUDIO_PATH="$OPTARG"
			fi
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
	if [ ! "$BUILD_CACHE" = true ]; then
		echo "Not using build cache"
		BUILD_ARGS="--no-cache"
	fi
	docker build -f docker/Dockerfile -t $IMAGE_NAME $BUILD_ARGS .
fi

DAEMON_ARG=""
if [ "$DAEMON" = true ]; then
	DAEMON_ARG="-d"
fi

if [[ "$CACHE" = true && -z "$AUDIO_PATH" ]]; then
	#ToDo: Figure out how to make this method handle spaces
	#in the path.  Currently breaks if there is a space
	#in the current directory path.
	AUDIO_PATH="${PWD}"/audio
fi

# Create the mount point command based on the audio path
# provided.  Currently breaks if there is a space
# in the directory path.
AUDIO_MOUNT=""
if [ ! -z "$AUDIO_PATH" ]; then
	AUDIO_MOUNT="--mount type=bind,source="$AUDIO_PATH",target=/glados-tts/audio"
fi

RUN_ARGS="$DAEMON_ARG $AUDIO_MOUNT"

#Create a folder to cache all the audio files locally

mkdir -p audio
echo -e "docker run --name $IMAGE_NAME
		   --rm
		   -p 8124:8124
		   $RUN_ARGS
		   $IMAGE_NAME python3 engine.py"

#Stop any existing instance of this container.
#No need to check if it's already running,
#just call this every time
echo "Stopping existing containers"
docker stop $IMAGE_NAME

#Start the image, the tts engine and map the ports
echo "Starting glados-tts"
docker run --name $IMAGE_NAME \
		   --rm \
		   -p 8124:8124 \
		   $RUN_ARGS  \
		   $IMAGE_NAME python3 engine.py