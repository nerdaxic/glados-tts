import sys
import os
import logging
import time
from flask import Flask, request, send_file
import urllib.parse
from glados import Glados

sys.path.insert(0, os.getcwd()+'/glados_tts')
logging.basicConfig(filename='glados_engine_service.log',
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s]\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',level=logging.DEBUG)

def printed_log(message):
    logging.info(message)
    print(message)

def print_timelapse(processName,old_time):
    printed_log(f"{processName} took {str((time.time() - old_time) * 1000)} ms")

# If the script is run directly, assume remote engine
if __name__ == "__main__":
    printed_log("Initializing TTS Remote Engine...")
    glados = Glados()
    glados.load_glados_model()
    PORT = 8124

    printed_log("Initializing TTS Server...")
    app = Flask(__name__)
    @app.route('/synthesize/', defaults={'text': ''},methods=["POST","GET"])
    @app.route('/synthesize/<path:text>',methods=["POST","GET"])
    def synthesize(text):
        if(request.method=="GET"):
            if(text == ''): return 'No input'
            input_text = urllib.parse.unquote(request.url[request.url.find('synthesize/')+11:])
        elif(request.method=="POST"):
            input_text = request.data.decode('ascii')

        printed_log(f"Input text: {input_text}")
        # get audio file
        old_time = time.time()
        output_file = glados.generate_tts(input_text)
        print_timelapse("Time Generating audio file: ",old_time)
        return send_file(output_file)

    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    printed_log(f"Listening in http://localhost:{PORT}/synthesize/{'{PRHASE}'}")
    app.run(host="0.0.0.0", port=PORT)
