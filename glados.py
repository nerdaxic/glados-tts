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

def printedLog(message):
    logging.info(message)
    print(message)

def printTimelapse(processName,old_time):
    printedLog(f"{processName} took {str((time.time() - old_time) * 1000)} ms")

def selectDevice():
    if torch.is_vulkan_available():
        device = 'vulkan'
    elif torch.cuda.is_available():
        device = 'cuda'
    else:
        device = 'cpu'
    printedLog(f"Device selected: {device}.")
    return device

def loadModels(device):
    glados = torch.jit.load('models/glados.pt')
    vocoder = torch.jit.load('models/vocoder-gpu.pt', map_location=device)

    # Prepare models in RAM
    for i in range(4):
        init = glados.generate_jit(prepare_text(str(i)))
        init_mel = init['mel_post'].to(device)
        init_vo = vocoder(init_mel)
    printedLog(f"Models loaded.")
    return glados,vocoder

def playSound(fileName):
    if 'winsound' in mod:
        winsound.PlaySound(fileName, winsound.SND_FILENAME)
    else:
        call(["aplay", f"./{fileName}"])


def main():
    printedLog("Initializing TTS Engine...")
    # Select the device
    device = selectDevice()
    # Load models
    glados,vocoder = loadModels(device)

    while(1):
        input_text = input("Input: ")

        # Tokenize, clean and phonemize input text
        x = prepare_text(input_text).to('cpu')

        with torch.no_grad():

            # Generate generic TTS-output
            old_time = time.time()
            tts_output = glados.generate_jit(x)
            printTimelapse("Forward Tacotron",old_time)

            # Use HiFiGAN as vocoder to make output sound like GLaDOS
            old_time = time.time()
            mel = tts_output['mel_post'].to(device)
            audio = vocoder(mel)
            printTimelapse("HiFiGAN",old_time)

            # Normalize audio to fit in wav-file
            audio = audio.squeeze()
            audio = audio * 32768.0
            audio = audio.cpu().numpy().astype('int16')

            # Write audio file to disk
            # 22,05 kHz sample rate
            output_file = input_text.replace(" ", "_")
            logging.info(f"Saving audio as {output_file}")
            write(output_file, 22050, audio)

            # Play audio file
            playSound(output_file)


if __name__ == "__main__":
    main()
