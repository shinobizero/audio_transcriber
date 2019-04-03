# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import optparse
import datetime
import filetype
import concurrent.futures
from tqdm import tqdm
import speech_recognition as sr
from pydub import AudioSegment

def timeStamp():
    """Makes a timestamp for the output filename """
    now = datetime.datetime.strftime(datetime.datetime.today() , '%Y%m%d-%H%M')
    timestamp = str(now)
    return timestamp

def runTime(start_time):
    """Returns a formatted string of total duration time"""
    total_duration = time.time() - start_time
    total_duration_seconds = int(total_duration//1)
    total_duration_milliseconds = int((total_duration-total_duration_seconds)*10000)
    
    total_hours = int(total_duration_seconds//3600)
    total_minutes = int(total_duration//60)
    
    total_seconds = int(total_duration-(total_minutes*60))
    total_milliseconds = round(total_duration_milliseconds, 4)
    
    if total_hours > 0:
        run_time_string = str(total_hours) + " hours, " + str(total_minutes) + " minutes, " + str(total_seconds) + " seconds" + str(total_milliseconds) + " milliseconds"
    elif total_hours == 0 and total_minutes > 0:
        run_time_string = str(total_minutes) + " minutes, " + str(total_seconds) + " seconds, " + str(total_milliseconds) + " milliseconds"
    elif total_hours == 0 and total_minutes == 0:
        run_time_string = str(total_seconds) + " seconds " + str(total_milliseconds) + " milliseconds"
    return run_time_string

def cleanUp(script_path):
    shutil.rmtree(script_path + '/temp', ignore_errors=True)
    
def makeTemp(script_path):
    if not os.path.exists(script_path + '\\temp'):
        os.mkdir(script_path + '\\temp')
    
def stripExtension(INPUT_FILE, script_path):
    if '.mp3' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".mp3", "")
    elif '.wav' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".wav", "")
    elif '.m4a' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".m4a", "")
    else:
        FILENAME = INPUT_FILE
    FILENAME = FILENAME.replace(script_path, "")
    FILENAME = FILENAME.replace("\\", "")
    return FILENAME

def fileType(INPUT_FILE):
        kind = filetype.guess(INPUT_FILE)
        if kind is None:
            FILE_TYPE = 'NONE'
        elif kind.extension == 'mp3' and kind.mime == 'audio/mpeg':
            FILE_TYPE = kind.extension
        elif kind.extension == 'm4a' and kind.mime == 'audio/m4a':
            FILE_TYPE = kind.extension
        elif kind.extension == 'wav' and kind.mime == 'audio/x-wav':
            FILE_TYPE = kind.extension
        else:
            FILE_TYPE = 'Unsupported'
        return FILE_TYPE

def calculateSections(FILENAME, section_length, new_sound):
    sound = new_sound
    duration = (len(sound)+1)/1000
    if duration % section_length == 0:
        sections = duration/section_length
    else:
        sections = duration//section_length+1            
    return sections

def convertWAV(INPUT_FILE, FILE_TYPE, FILENAME):
    """Converts the input file to wav format """
    if FILE_TYPE == 'mp3':
        sound = AudioSegment.from_mp3(INPUT_FILE)
    elif FILE_TYPE == 'm4a':
        sound = AudioSegment.from_file(INPUT_FILE, "m4a")
    
    AUDIO_OUTPUT_FILE = FILENAME + ".wav"    
    sound.export(AUDIO_OUTPUT_FILE, format="wav")

    soundCheck(INPUT_FILE, AUDIO_OUTPUT_FILE)
    
    return AUDIO_OUTPUT_FILE

def soundCheck(INPUT_FILE, AUDIO_OUTPUT_FILE):    
    """There can be a delay to outputting the converted file,
    this loop checks the file sizes before continuing. Since wav format
    is less compressed than most other formats its ouput size will be greater
    than the input file's. It outputs data rather quickly onces it start so
    the loop can break when it exceeds the inputs"""
    completed = False
    sound_size = os.path.getsize(INPUT_FILE)
    new_sound_size = os.path.getsize(AUDIO_OUTPUT_FILE)
    if new_sound_size > sound_size:
        completed = True
    return completed

def audioSplitter(FILENAME, sections, section_length, script_path, new_sound):
    section = section_length * 1000
    start = 0
    stop = start + section
    section_count = 0
    print("[+]Splitting audio file...")
    while section_count < sections:
        section_count += 1
        dummy_diff = len(str(int(sections)))-len(str(section_count))
        dummy_zeros = dummy_diff*str(0)
        stop = start + section               
        sound = new_sound[start:stop]
        output_name = script_path + "/temp/" + FILENAME + "-" + str(dummy_zeros) + str(section_count) + ".wav"
        sound.export(output_name, format="wav")
        start = stop

def getSnippets(script_path):
    """Makes a list of all audio snippets in the temp directory"""
    split_wav = []
    for file in os.listdir(script_path + "\\temp"):
        if file.endswith(".wav"):
            file_string = script_path + "\\temp\\" + file
            split_wav.append(file_string)
    total_snippets = len(split_wav)
    return split_wav, total_snippets

def getOutputName(FILENAME):
    TIMESTAMP = timeStamp()
    OUTPUT_FILENAME = FILENAME + "-" + TIMESTAMP + ".txt"
    return OUTPUT_FILENAME

def createOutput(FILENAME, output_list, script_path):
    OUTPUT_FILENAME = getOutputName(FILENAME)
    with open(script_path + "/" + OUTPUT_FILENAME, "a") as f:
        for line in output_list:   
            f.write(line)
    f.close()
    
def removeOldTemp(TEMP_FILE):
    if os.path.isfile(TEMP_FILE) == True:
        os.remove(TEMP_FILE)
    
def checkSuccess(total_snippets, TEMP_FILE):
    print("[+]Writing transcription to file...")
    line_count = 0
    while True:
        time.sleep(3)
        line_count = 0
        with open(TEMP_FILE, "r") as f:
            for line in f:
                line_count += 1
        if int(line_count) == int(total_snippets):
            f.close
            break
        f.close()
    completed_string = " [!]Transcription Successful!"
    return completed_string

def writeOutput(TEMP_FILE, FILENAME, script_path):
    output_list = []
    with open(TEMP_FILE, "r") as f:
        for line in f:
            output_list.append(line)
    output_list.sort()
    createOutput(FILENAME, output_list, script_path)

def transcribeAudio(snippet, line_count, TEMP_FILE, total_snippets, pbar):
    dummy_diff = len(str(int(total_snippets)))-len(str(line_count))
    dummy_zeros = dummy_diff*str(0)
    line_count = str(dummy_zeros)+str(line_count)
    
    r = sr.Recognizer()
    with sr.AudioFile(snippet) as source:
        audio = r.record(source)        
        text = r.recognize_google(audio)
        text_string = str(line_count + "- " + text)
        writeTranscription(TEMP_FILE, text_string, pbar)   
        
def writeTranscription(TEMP_FILE, text_string, pbar):
    with open(TEMP_FILE, "a") as f:
        f.write(text_string + "\n")
    f.close()
    pbar.update(1)

def runTranscription(split_wav, thread_count, TEMP_FILE, total_snippets):
    line_count = 0
    pbar_total = total_snippets
    with tqdm(total=pbar_total, leave=True, desc="[+]Transcribing audio file snippets") as pbar:
        while total_snippets != 0:
            if thread_count > total_snippets:
                thread_count = total_snippets
            working_list =[]    
            for i in range(thread_count):
                working_list.append(split_wav[i])
            for i in working_list:
                del split_wav[0]
            with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
                for snippet in working_list:
                    line_count += 1
                    executor.submit(transcribeAudio, snippet, line_count, TEMP_FILE, total_snippets, pbar,)
            working_list.clear()
            total_snippets -= thread_count

def runOperations(INPUT_FILE, script_path, start_time, thread_count):
    #Settings   
    section_length = 30 # In Seconds
    
    FILENAME = stripExtension(INPUT_FILE, script_path)
    FILE_TYPE = fileType(INPUT_FILE)   
    TEMP_FILE = script_path + '\\temp\\' + FILENAME + '-TEMP.txt'
        
    if FILE_TYPE == 'NONE' or FILE_TYPE == 'Unsupported':
        exit(0)
    elif FILE_TYPE == 'mp3' or FILE_TYPE == 'm4a':
        print("[+]Converting to WAV format...")
        new_sound = convertWAV(INPUT_FILE, FILE_TYPE, FILENAME)
        AUDIO_OUTPUT_FILE = new_sound
        completed_conversion = False
        while completed_conversion == False:
            test = soundCheck(INPUT_FILE, AUDIO_OUTPUT_FILE)
            if test == True:
                completed_conversion = True
            else:
                time.sleep(5)
        print(" [!]Completed file converion")
        new_sound = new_sound = AudioSegment.from_wav(AUDIO_OUTPUT_FILE)
    else:
        print("[+]No file conversion needed!")
        new_sound = AudioSegment.from_wav(INPUT_FILE)

    makeTemp(script_path)

    sections = calculateSections(FILENAME, section_length, new_sound)    
    audioSplitter(FILENAME, sections, section_length, script_path, new_sound)
    
    split_wav, total_snippets = getSnippets(script_path)
    
    
    runTranscription(split_wav, thread_count, TEMP_FILE, total_snippets)
    success = checkSuccess(total_snippets, TEMP_FILE)
    print(success)

    writeOutput(TEMP_FILE, FILENAME, script_path)    
    cleanUp(script_path)
    print("[!]Completed Transcription")

    run_time = runTime(start_time)
    print('Entire job took: ' + run_time)
    
def main():
    VERSION = 1.0
    print("-------------------------------")
    print("     Audio Transcriber - v" + str(VERSION))
    print("-------------------------------")   

    parser = optparse.OptionParser('Options: '+\
                                   '\n -h --help <show this help message and exit>' +\
                                   '\n -f --file <target file> (REQUIRED)' +\
                                   '\n -t --threads <threads to use> (10 Default)')
    
    parser.add_option('-f', '--file',
                      action='store', dest='filename', type='string',\
                      help='specify target file', metavar="FILE")

    parser.add_option('-t', '--threads',
                      action='store', dest='threads', type='int',\
                      help='specify amount of threads to use')
    
    (options, args) = parser.parse_args()

    start_time = time.time()
    script_path = os.path.abspath(os.path.dirname(sys.argv[0]))    

    INPUT_FILE = options.filename
    thread_count = options.threads
    
    if thread_count == None:
        thread_count = 10

    if INPUT_FILE == None:
        print("[!]No Input File Supplied!\n")
        print(parser.usage)
        exit
    else:  
        while True:
            if os.path.isfile("/" + str(INPUT_FILE)) == True:
                INPUT_FILE = str(INPUT_FILE)
                break
            elif os.path.isfile(script_path + "\\" + str(INPUT_FILE)) == True:
                INPUT_FILE = str(script_path + "\\" + INPUT_FILE)
                break
            else:
                print("[!]ERROR: Cannot find specified file!")
                break
                exit
        runOperations(INPUT_FILE, script_path, start_time, thread_count)
    
if __name__ == '__main__':
    main()
