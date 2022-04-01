FROM ubuntu:20.04

#Update before we do anything else
RUN apt-get update

# Install all required linux packages
#   - python3 -> run glados-tts 
#	- pip -> gather required python packages
#   - espeak-ng -> required for tts to work
RUN apt-get install python3-pip espeak-ng -y --no-install-recommends

#Setup the project directory with all files
RUN mkdir -p glados-tts/audio
COPY models glados-tts/models
COPY utils glados-tts/utils
ADD engine.py glados-tts/
ADD glados.py glados-tts/
ADD requirements.txt glados-tts/

#Move into the project directory
WORKDIR /glados-tts

#Install all the pythond module requirements
RUN pip3 install -r requirements.txt