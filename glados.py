import torch
import logging
from utils.tools import prepare_text
from scipy.io.wavfile import write
import time
from sys import modules as mod
try:
    import winsound
except ImportError:
    from subprocess import call

logging.basicConfig(filename='glados_service.log',
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s]\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',level=logging.DEBUG)

#Global variables
glados = None
vocoder = None
device = None
audioPath = "audio/"

def printedLog(message):
    logging.info(message)
    print(message)

def printTimelapse(processName,old_time):
    printedLog(f"{processName} took {str((time.time() - old_time) * 1000)} ms")

def selectDevice(optionDevices):
    if "vulkan" in optionDevices and torch.is_vulkan_available():
        device = 'vulkan'
    elif "cuda" in optionDevices and torch.cuda.is_available():
        device = 'cuda'
    else:
        device = 'cpu'
    printedLog(f"Device selected: {device}.")
    return device

def loadModelsOnDevice(device):
    glados = torch.jit.load('models/glados.pt')
    vocoder = torch.jit.load('models/vocoder-gpu.pt', map_location=device)

    # Prepare models in RAM
    for i in range(4):
        init = glados.generate_jit(prepare_text(str(i)))
        init_mel = init['mel_post'].to(device)
        init_vo = vocoder(init_mel)
    printedLog(f"Models loaded.")
    return glados,vocoder

def loadModels():
    global glados,vocoder,device
    optionDevices = ["vulkan","cuda"]
    while(glados==None):
        # Select the device
        deviceAux = selectDevice(optionDevices)
        try:
            # Load models
            glados,vocoder = loadModelsOnDevice(deviceAux)
            device = device
        except:
            printedLog(f"Execption loading device "+deviceAux)
            optionDevices.remove(deviceAux)
    return glados!=None

def playSound(fileName):
    if 'winsound' in mod:
        winsound.PlaySound(fileName, winsound.SND_FILENAME)
    else:
        call(["aplay", f"./{fileName}"])

def saveAudioFile(audio,output_key=None):
    output_file_name = "GLaDOS-tts-tempfile"
    if(output_key):
        output_file_name = output_key
    output_file = (f"{audioPath}{output_key}.wav")
    # Write audio file to disk at 22,05 kHz sample rate
    logging.info(f"Saving audio as {output_file}")
    write(output_file, 22050, audio)
    return output_file

def glados_tts(text):
	# Tokenize, clean and phonemize input text
    x = prepare_text(text).to('cpu')
    with torch.no_grad():
        # Generate generic TTS-output
        old_time = time.time()
        tts_output = glados.generate_jit(x)

        # Use HiFiGAN as vocoder to make output sound like GLaDOS
        mel = tts_output['mel_post'].to(device)
        audio = vocoder(mel)
        printTimelapse("The audio sample",old_time)

        # Normalize audio to fit in wav-file
        audio = audio.squeeze()
        audio = audio * 32768.0
        audio = audio.cpu().numpy().astype('int16')
    return audio

def main():
    printedLog("Initializing TTS Engine...")
    loadModels()
    while(1):
        input_text = input("Input: ")
        output_key = input_text.replace(" ", "_")
        audio = glados_tts(input_text)
        output_file = saveAudioFile(audio,output_key)
        playSound(output_file)

if __name__ == "__main__":
    main()
