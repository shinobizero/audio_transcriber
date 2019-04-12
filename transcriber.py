# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import optparse
import datetime
import filetype
import subprocess
import concurrent.futures
from tqdm import tqdm
import speech_recognition as sr
from pydub import AudioSegment

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

def cleanUp(script_path, FILENAME, DELETE_CONVERT=False):
    shutil.rmtree(script_path + '/temp', ignore_errors=True)
    if FILENAME != None:
        if os.path.isfile(script_path + '/' + FILENAME + ".wav") == True and DELETE_CONVERT == True:
            os.remove(script_path + '/' + FILENAME + ".wav")
    
def makeTemp(script_path, TEMP_FILE):
    if not os.path.exists(script_path + '\\temp'):
        os.mkdir(script_path + '\\temp')
    with open(TEMP_FILE, "w+") as file:
        file.write("")
    file.close()
   
def stripExtension(INPUT_FILE, script_path):
    if '.mp3' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".mp3", "")
    elif '.wav' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".wav", "")
    elif '.m4a' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".m4a", "")
    elif '.mp4' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".mp4", "")
    else:
        FILENAME = INPUT_FILE
    FILENAME = FILENAME.replace(script_path, "")
    FILENAME = FILENAME.replace("\\", "")
    return FILENAME

def fileType(INPUT_FILE):
    """Determines file type of the input file, if it can't find it
    by using file type module, if that fails it will attempt to use the file's
    extension, if it has one"""
    kind = filetype.guess(INPUT_FILE)
    if kind is None:
        FILE_TYPE = None
    elif kind.extension == 'mp3' and kind.mime == 'audio/mpeg':
        FILE_TYPE = kind.extension
    elif kind.extension == 'm4a' and kind.mime == 'audio/m4a':
        FILE_TYPE = kind.extension
    elif kind.extension == 'wav' and kind.mime == 'audio/x-wav':
        FILE_TYPE = kind.extension
    elif kind.extension == 'mp4' and kind.mime == 'video/mp4':
        FILE_TYPE = kind.extension
    if FILE_TYPE == None:
        if ".mp3" in INPUT_FILE:
            FILE_TYPE = 'mp3'
        elif ".m4a" in INPUT_FILE:
            FILE_TYPE = 'm4a'
        elif ".wav" in INPUT_FILE:
            FILE_TYPE = 'wav'
        elif ".mp4" in INPUT_FILE:
            FILE_TYPE = 'mp4'
        else:
            FILE_TYPE = 'Unsupported'
    return FILE_TYPE

def calculateSections(FILENAME, section_length, new_sound):
    sound = new_sound
    duration = (len(sound)+1)/1000
    if duration < section_length:
        sections = 1
    else:
        if duration % section_length == 0:
            sections = duration/section_length
        else:
            sections = duration//section_length+1
    return sections

def extractAudio(FILE_TYPE, FILENAME, script_path):
    AUDIO_OUTPUT_FILE = FILENAME + ".wav"
    command = str("ffmpeg -i " + script_path + "/" + FILENAME + "." + FILE_TYPE +" -f wav -vn -ab 192000 " + script_path + "/" + AUDIO_OUTPUT_FILE)  
    subprocess.call(command, shell=True)
    return AUDIO_OUTPUT_FILE

def convertWAV(INPUT_FILE, FILE_TYPE, FILENAME):
    """Converts the input file to wav format """
    if FILE_TYPE == 'mp3':
        sound = AudioSegment.from_mp3(INPUT_FILE)
    elif FILE_TYPE == 'm4a':
        sound = AudioSegment.from_file(INPUT_FILE, "m4a")
    
    AUDIO_OUTPUT_FILE = FILENAME + ".wav"    
    sound.export(AUDIO_OUTPUT_FILE, format="wav")
    
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
    if sections == 1:
        print("[+]No file splitting!")
        sound_file = script_path + '/' + FILENAME + '.wav'
        new_sound_file = script_path + '/temp/' + FILENAME + '.wav'
        shutil.copyfile(sound_file, new_sound_file)
    else:
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

def createOutput(FILENAME, output_list, script_path):
    TIMESTAMP = str(datetime.datetime.strftime(datetime.datetime.today() , '%Y%m%d-%H%M'))
    OUTPUT_FILENAME = FILENAME + "-" + TIMESTAMP + ".txt"
    with open(script_path + "/" + OUTPUT_FILENAME, "a") as f:
        for line in output_list:   
            f.write(line)
    f.close()
    
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

def transcribeAudio(snippet, line_count, TEMP_FILE, total_snippets, pbar, single_file=False):
    if single_file == True:
        try:
            r = sr.Recognizer()
            with sr.AudioFile(snippet) as source:
                audio = r.record(source)        
                text = r.recognize_google(audio)
                text_string = text
        except:
            text_string = "!!!ERROR processing audio!!!"
    elif single_file == False:
        try:
            dummy_diff = len(str(int(total_snippets)))-len(str(line_count))
            dummy_zeros = dummy_diff*str(0)
            line_count = str(dummy_zeros)+str(line_count)        
            r = sr.Recognizer()
            with sr.AudioFile(snippet) as source:
                audio = r.record(source)        
                text = r.recognize_google(audio)
                text_string = str(line_count + "- " + text)
        except:
            text_string = str(line_count) + "- !!!ERROR processing audio!!!"
    with open(TEMP_FILE, "a") as f:
        f.write(text_string + "\n")
    f.close()
    pbar.update(1)

def runTranscription(split_wav, thread_count, TEMP_FILE, total_snippets, single_file=False):
    pbar_total = total_snippets
    working_list =[] 
    if single_file == True:
            with tqdm(total=pbar_total, leave=True, desc="[+]Transcribing audio file") as pbar:
                working_list.append(split_wav[0])
                for snippet in working_list:
                    transcribeAudio(snippet, None, TEMP_FILE, total_snippets, pbar, single_file=True)
    elif single_file == False:
        line_count = 0
        snippets_to_complete = total_snippets
        snippets_completed = 0
        with tqdm(total=pbar_total, leave=True, desc="[+]Transcribing audio file snippets") as pbar:
            while snippets_completed != total_snippets:
                if thread_count > snippets_to_complete:
                    thread_count = snippets_to_complete 
                for i in range(thread_count):
                    working_list.append(split_wav[i])
                for i in working_list:
                    del split_wav[0]
                with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
                    for snippet in working_list:
                        line_count += 1
                        executor.submit(transcribeAudio, snippet, line_count, TEMP_FILE, total_snippets, pbar,)
                working_list.clear()
                snippets_to_complete -= thread_count
                snippets_completed += thread_count

def runOperations(INPUT_FILE, script_path, thread_count, section_length, no_split, keep_wav):
    start_time = time.time()
    FILENAME = stripExtension(INPUT_FILE, script_path)
    TEMP_FILE = script_path + '\\temp\\' + FILENAME + '-TEMP.txt'
    check_required = False
    
    if keep_wav == False:
        DELETE_WAV = True
    elif keep_wav == True:
        DELETE_WAV = False

    FILE_TYPE = fileType(INPUT_FILE)           
    if FILE_TYPE == None or FILE_TYPE == 'Unsupported':
        print("[!]ERROR: Unsupported File Type!!!")
        return
    elif FILE_TYPE == 'mp4':
        print("[+]Extracting Audio from Video...")
        new_sound = extractAudio(FILE_TYPE, FILENAME, script_path)
        check_required = True
    elif FILE_TYPE == 'mp3' or FILE_TYPE == 'm4a':
        print("[+]Converting to WAV format...")
        new_sound = convertWAV(INPUT_FILE, FILE_TYPE, FILENAME)
        check_required = True
    elif FILE_TYPE == 'wav':
        print("[+]No file conversion needed!")
        DELETE_WAV = False
        new_sound = AudioSegment.from_wav(INPUT_FILE)

    if check_required == True:
        AUDIO_OUTPUT_FILE = new_sound
        completed_conversion = False
        while completed_conversion == False:
            test = soundCheck(INPUT_FILE, AUDIO_OUTPUT_FILE)
            if test == True:
                completed_conversion = True
            else:
                time.sleep(5)
        print(" [!]Operation Completed")
        new_sound = AudioSegment.from_wav(AUDIO_OUTPUT_FILE)

    cleanUp(script_path, None)
    makeTemp(script_path,TEMP_FILE)

    if no_split == False:
        sections = calculateSections(FILENAME, section_length, new_sound)
    elif no_split == True:
        sections = 1

    audioSplitter(FILENAME, sections, section_length, script_path, new_sound)  
    split_wav, total_snippets = getSnippets(script_path)
    
    if total_snippets == 1:
        runTranscription(split_wav, thread_count, TEMP_FILE, total_snippets, single_file=True)
    else:
        runTranscription(split_wav, thread_count, TEMP_FILE, total_snippets)
    success = checkSuccess(total_snippets, TEMP_FILE)
    print(success)

    writeOutput(TEMP_FILE, FILENAME, script_path)
    
    if DELETE_WAV == False:
        cleanUp(script_path, None)
    elif DELETE_WAV == True: 
        cleanUp(script_path, FILENAME, DELETE_CONVERT=True)

    print("-------------------------------")
    print("[!]Completed Transcription")

    run_time = runTime(start_time)
    print('[!]Entire job took: ' + run_time)
    print("-------------------------------")

def assistedOperations(script_path):
    print("    --- Assisted Mode ---")
    print("-------------------------------")
    #List Files
    supported_files = ['.wav', '.m4a', '.mp3', '.mp4']
    files_list = []
    for file_type in supported_files:
        for file in os.listdir(script_path):
            if file.endswith(file_type):
                files_list.append(file)
    files_list.sort()
    while True:
        try:
            print("Listing compatible files:")
            item_number = 0
            for item in files_list:
                item_number += 1
                print(" " + str(item_number) + "- " + str(item))
            selection = int(input("Please select a file: "))
            INPUT_FILE = files_list[selection-1]
            INPUT_FILE = str(script_path + "\\" + INPUT_FILE)
            break
        except:
            print("\nPlease make a valid selection!")
            time.sleep(3)
    #Sections/No Split
    try:
        print("\nSplitting Options:")
        print(" Define in seconds how long the sections should be cut into.")
        print(" 30 seconds or smaller is recommended as bigger can have errors.")
        print(" ie: 30, 60, 90 etc. 0 for No Splitting (NOT RECOMMENDED) ")
        section_length = abs(int(input("Please input a section length for splitting: ")))
        if section_length == 0:
            no_split = True
        else:
            no_split = False
    except:
        section_length = 30
        no_split = False
    #Threads
    try:
        print("\nThreads Option:")
        print(" Running multiple threads is for multitasking the processing of")
        print(" audio snippets. Default is 10")
        thread_count = abs(int(input("How many threads would you like to use?: ")))
    except:
        thread_count = 10
    #Keep Wav
    if '.wav' not in INPUT_FILE:
        selection = input("Would you like to keep the converted wav file? y/N: ")
        if selection.lower() == 'y':
            keep_wav = True
        else:
            keep_wav = False
    #Review
    print("\n")
    printTitle()
    runOperations(INPUT_FILE, script_path, thread_count, section_length, no_split, keep_wav)

def printTitle():
    VERSION = 1.0
    print("-------------------------------")
    print("    Audio Transcriber - v" + str(VERSION))
    print("-------------------------------")
    
def main():
    """This just processes user input & options and passes it to runOperations()"""
    printTitle()

    parser = optparse.OptionParser('Options: '+\
                                   '\n -h --help <show this help message and exit>' +\
                                   '\n -f --file <target file> (REQUIRED)' +\
                                   '\n -t --threads <threads to use> (10 Default)' +\
                                   '\n -a --assisted <assisted mode>' +\
                                   '\n\nSplitting Options: ' +\
                                   '\n -s --section <Length of splitting sections> (In Seconds)' +\
                                   '\n -n --nosplit <Specify no splitting of input file> (Not Recommended)')

    parser.add_option('-f', '--file',
                      action='store', dest='filename', type='string',\
                      help='specify target file', metavar="FILE")

    parser.add_option('-t', '--threads',
                      action='store', dest='threads', type='int',\
                      help='specify amount of threads to use')

    parser.add_option('-a', '--assisted',
                      action='store_true', dest='assisted', default=False,\
                      help='Assisted mode for easy operation')

    parser.add_option('-s', '--section',
                      action='store', dest='section_length', type='int',\
                      help='specify length of sections for splitting')

    parser.add_option('-n', '--nosplit',
                      action='store_true', dest='nosplit', default=False,\
                      help='Specify no splitting of input file')
    
    parser.add_option('-k', '--keep',
                      action='store_true', dest='keep', default=False,\
                      help='Keep wav file, if converting')
    
    (options, args) = parser.parse_args()

    script_path = os.path.abspath(os.path.dirname(sys.argv[0]))    

    INPUT_FILE = options.filename
    thread_count = options.threads
    ASSISTED = options.assisted
    section_length = options.section_length
    no_split = options.nosplit
    keep_wav = options.keep

    if ASSISTED == True:
        assistedOperations(script_path)
    else:
        if thread_count == None:
            thread_count = 10
    
        if section_length == None:
            section_length = 30
        elif section_length < 1:
            section_length = 1
            
        if INPUT_FILE == None:
            print("[!]No Input File Supplied!\n")
            print(parser.usage)
            return
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
            runOperations(INPUT_FILE, script_path, thread_count, section_length, no_split, keep_wav)
        
if __name__ == '__main__':
    main()
