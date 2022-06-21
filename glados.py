import torch
import logging
from utils.tools import prepare_text
from scipy.io.wavfile import write
import time
import os.path
from sys import modules as mod
import sys
try:
    import winsound
except ImportError:
    from subprocess import call

logging.basicConfig(filename='glados_service.log',
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s]\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',level=logging.DEBUG)

#Global variables
audio_path = "audio/"

class Glados:
    glados_model = None
    vocoder = None
    device = None

    def __init__(self):
        pass

    def get_available_device(self,option_devices):
        if "vulkan" in option_devices and torch.is_vulkan_available():
            device_found = 'vulkan'
        elif "cuda" in option_devices and torch.cuda.is_available():
            device_found = 'cuda'
        else:
            device_found = 'cpu'
        printed_log(f"Device selected: {device_found}.")
        return device_found

    def load_models(self):
        self.glados_model = torch.jit.load('models/glados.pt')
        self.vocoder = torch.jit.load('models/vocoder-gpu.pt', map_location=self.device)

        for i in range(4):
            init = self.glados_model.generate_jit(prepare_text(str(i)))
            init_mel = init['mel_post'].to(self.device)
            init_vo = self.vocoder(init_mel)
        printed_log(f"Models loaded.")

    def load_glados_model(self):
        #option_devices = ["vulkan","cuda"]
        option_devices = []
        while(self.glados_model==None):
            self.device = self.get_available_device(option_devices)
            try:
                self.load_models()
            except:
                printed_log(f"Execption loading device "+self.device)
                if(self.device != 'cpu'): option_devices.remove(self.device)
                else: sys.exit()

    def get_audio_from_text(self,text):
    	# Tokenize, clean and phonemize input text
        phonemized_text = prepare_text(text).to(self.device)
        with torch.no_grad():
            # Generate generic TTS-output
            old_time = time.time()
            tts_output = self.glados_model.generate_jit(phonemized_text)

            # Use HiFiGAN as vocoder to make output sound like GLaDOS
            mel = tts_output['mel_post'].to(self.device)
            audio = self.vocoder(mel)
            print_timelapse("The audio sample",old_time)

            # Normalize audio to fit in wav-file
            audio = audio.squeeze()
            audio = audio * 32768.0
            audio = audio.cpu().numpy().astype('int16')
        return audio

    def generate_tts(self, input_text):
        output_key = input_text.replace(" ", "_")
        audio_file_exist = check_audio_file(output_key)
        if (audio_file_exist):
            output_file = f"{audio_path}{output_key}.wav"
        else:
            audio = self.get_audio_from_text(input_text)
            output_file = save_audio_file(audio,output_key)
        play_sound(output_file)

def printed_log(message):
    logging.info(message)
    print(message)

def print_timelapse(processName,old_time):
    printed_log(f"{processName} took {str((time.time() - old_time) * 1000)} ms")

def play_sound(fileName):
    if 'winsound' in mod:
        winsound.PlaySound(fileName, winsound.SND_FILENAME)
    else:
        call(["aplay", f"./{fileName}"])

def save_audio_file(audio,output_key=None):
    output_file_name = "GLaDOS-tts-tempfile"
    if(output_key and len(output_key)<200):
        output_file_name = output_key
    output_file = (f"{audio_path}{output_file_name}.wav")
    # Write audio file to disk at 22,05 kHz sample rate
    logging.info(f"Saving audio as {output_file}")
    write(output_file, 22050, audio)
    return output_file

def check_audio_file(file_name):
    alreadyExist = os.path.exists(f"{audio_path}{file_name}.wav")
    return alreadyExist

def main():
    printed_log("Initializing TTS Engine...")
    glados = Glados()
    glados.load_glados_model()
    if(len(sys.argv)==2):
        printed_log("Using command line argument as text")
        glados.generate_tts(sys.argv[1])
    else:
        while(1):
            printed_log("Using user input as text")
            input_text = input("Input: ")
            glados.generate_tts(input_text)

if __name__ == "__main__":
    main()
