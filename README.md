# audio_transcriber
Transcodes audio files to text, supports MP3, M4A, WAV, MP4, MKV, MPG, MPEG & AVI
Does File Conversion & Audio Extraction. No Online API's. Python 3

For big files the program will crash if you don't split the file, it splits automatically by default

Install prequisites

To run the app you need several things installed:

    Python 3
    the module pydub
    the module optparse
    the module filetype
    the module tqdm
    the program ffmpeg
    the module SpeechRecognition

You can install the Python modules with pip. 

Linux:
ffmpeg can be installed with your package manager (apt-get, emerge, yum, pacman)

Windows:
follow the instructions at https://www.wikihow.com/Install-FFmpeg-on-Windows and add it to your PATH
