FROM ubuntu:20.04

#Update before we do anything else
RUN apt-get update

# Install all required linux packages
#   - python3 -> run glados-tts 
#	- pip -> gather required python packages
#   - espeak-ng -> required for tts to work
RUN apt-get install python3-pip espeak-ng -y --no-install-recommends

#Create the project directory
RUN mkdir -p glados-tts/audio

#Install all the pythond module requirements
ADD requirements.txt glados-tts/
RUN pip3 install -r glados-tts/requirements.txt

#Add all the project files
COPY models glados-tts/models
COPY utils glados-tts/utils
ADD engine.py glados-tts/
ADD glados.py glados-tts/

#Move into the project directory
WORKDIR /glados-tts