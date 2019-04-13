# -*- coding: utf-8 -*-

import os
import sys
from sys import exit
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
from pydub.silence import detect_silence

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
        if os.path.isfile(script_path + '/' + FILENAME + "-EXTRACTED.wav") == True and DELETE_CONVERT == True:
            os.remove(script_path + '/' + FILENAME + "-EXTRACTED.wav")
        elif os.path.isfile(script_path + '/' + FILENAME + "-CONVERTED.wav") == True and DELETE_CONVERT == True:
            os.remove(script_path + '/' + FILENAME + "-CONVERTED.wav")

def makeTemp(TEMP_DIR):
    if not os.path.exists(TEMP_DIR):
        os.mkdir(TEMP_DIR)
   
def stripExtension(INPUT_FILE, script_path):
    """
    Strips extension from filename
    """
    if '.mp3' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".mp3", "")
    elif '.wav' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".wav", "")
    elif '.m4a' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".m4a", "")
    elif '.mp4' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".mp4", "")
    elif '.mkv' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".mkv", "")
    elif '.mpg' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".mpg", "")
    elif '.avi' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".avi", "")
    elif '.mpeg' in INPUT_FILE:
        FILENAME = INPUT_FILE.replace(".mpeg", "")
    else:
        FILENAME = INPUT_FILE
    FILENAME = FILENAME.replace(script_path, "")
    FILENAME = FILENAME.replace("\\", "")
    return FILENAME

def fileType(INPUT_FILE):
    """
    Determines file type of the input file, if it can't find it
    by using file type module, if that fails it will attempt to use the file's
    extension, if it has one
    """
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
    elif kind.extension == 'mkv' and kind.mime == 'video/x-matroska':
        FILE_TYPE = kind.extension
    elif kind.extension == 'mpg' and kind.mime == 'video/mpeg':
        FILE_TYPE = kind.extension
    elif kind.extension == 'avi' and kind.mime == 'video/x-msvideo':
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
        elif ".mkv" in INPUT_FILE:
            FILE_TYPE = 'mkv'
        elif ".mpg" in INPUT_FILE or ".mpeg" in INPUT_FILE:
            FILE_TYPE = 'mpg'
        elif ".avi" in INPUT_FILE:
            FILE_TYPE = 'avi'
        else:
            FILE_TYPE = 'Unsupported'
    return FILE_TYPE

def extractAudio(FILE_TYPE, FILENAME, script_path):
    """
    Extracts audio from a video file
    """
    AUDIO_OUTPUT_FILE = FILENAME + "-EXTRACTED.wav"
    if os.path.isfile(script_path + '/' + AUDIO_OUTPUT_FILE) == True:
        os.remove(script_path + '/' + AUDIO_OUTPUT_FILE)
    command = str("ffmpeg -i " + script_path + "/" + FILENAME + "." + FILE_TYPE +" -f wav -vn -ab 192000 " + script_path + "/" + AUDIO_OUTPUT_FILE)  
    subprocess.call(command, shell=True)
    return AUDIO_OUTPUT_FILE

def convertWAV(INPUT_FILE, FILE_TYPE, FILENAME):
    """
    Converts the input file to wav format 
    """
    if FILE_TYPE == 'mp3':
        sound = AudioSegment.from_mp3(INPUT_FILE)
    elif FILE_TYPE == 'm4a':
        sound = AudioSegment.from_file(INPUT_FILE, "m4a")    
    AUDIO_OUTPUT_FILE = FILENAME + "-CONVERTED.wav"    
    sound.export(AUDIO_OUTPUT_FILE, format="wav")   
    return AUDIO_OUTPUT_FILE

def soundCheck(INPUT_FILE, AUDIO_OUTPUT_FILE):    
    completed = False
    sound_size = os.path.getsize(INPUT_FILE)
    new_sound_size = os.path.getsize(AUDIO_OUTPUT_FILE)
    if new_sound_size > sound_size:
        completed = True
    return completed

def getSnippets(TEMP_DIR):
    """
    Makes a list of all audio snippets in the temp directory
    """
    split_wav = []
    for file in os.listdir(TEMP_DIR):
        if file.endswith(".wav"):
            file_string = TEMP_DIR + "\\" + file
            split_wav.append(file_string)
    total_snippets = len(split_wav)
    return split_wav, total_snippets

def detectSilence(sound, ESTIMATED_SECTIONS):
    min_silence_len = 200
    
    print("[+]Detecting silence sections...")
    while True:
        silences = detect_silence(sound, min_silence_len, silence_thresh=-16, seek_step=1)    
        if len(silences) < ESTIMATED_SECTIONS:
            if min_silence_len == 200:
                min_silence_len = min_silence_len-50
            silences.clear()
        elif len(silences) >= ESTIMATED_SECTIONS:
            silence_found = True
            break
        if min_silence_len < 100:
            silence_found = False
            silences.clear()
            break
    if silence_found == True:
        silence_ranges = []
        for section in silences:
            silence_start = ''
            silence_end = ''
            silence = str(section)
            silence = silence.replace("[", "")
            silence = silence.replace("]", "")
            silence = silence.replace(",", "")
            section_end = False
            for char in silence:
                if char != ' ' and section_end == False:
                    silence_start = silence_start + char
                elif char != ' ' and section_end == True:
                    silence_end = silence_end + char
                elif char == ' ':
                    section_end = True
            silence_ranges.append(int(silence_start))
            silence_ranges.append(int(silence_end))

    return silence_found, silence_ranges

def audioSplitter(FILENAME, recommended_section_length, new_sound, duration, TEMP_DIR, range_list, total_sections=0, silence_split=False):
    if silence_split == False:
        if duration % recommended_section_length == 0:
            sections = duration/recommended_section_length
        else:
            sections = duration//recommended_section_length+1
        start = 0
        section = recommended_section_length * 1000
        print(" [!]Splitting into " + str(int(sections)) + " sections")
    elif silence_split == True:
        sections = total_sections
    sections_processed = 0
    section_ends = []
    print("[+]Splitting audio file...")
    while sections_processed != sections:
        section_number = sections_processed+1
        dummy_diff = len(str(int(sections)))-len(str(section_number))
        dummy_zeros = dummy_diff*str(0)
        output_name = TEMP_DIR + "/" + FILENAME + "-" + str(dummy_zeros) + str(section_number) + ".wav"
        if silence_split == True:
            start = range_list[0]
            stop = range_list[1]
        elif silence_split == False:
            stop = start + section
        sound = new_sound[start:stop]
        sound.export(output_name, format="wav")   
        if silence_split == True:
            section_ends.append(range_list[1])
            del range_list[1]
            del range_list[0]
        elif silence_split == False:
            section_ends.append(stop)
            start = stop
        sections_processed += 1
    return section_ends
            
def createOutput(FILENAME, TEMP_FILE, script_path, total_snippets, section_ends):
    OUTPUT_LIST = []
    TIMESTAMP = str(datetime.datetime.strftime(datetime.datetime.today() , '%Y%m%d-%H%M'))
    OUTPUT_FILENAME = FILENAME + "-" + TIMESTAMP + ".txt"
    
    line_count = 0
    with open(TEMP_FILE, "r+") as temp:
        for line in temp:
            line_count += 1
            
            dummy_diff = len(str(int(total_snippets)))-len(str(line_count))
            dummy_zeros = dummy_diff*str(0)
            string_line_count = str(dummy_zeros)+str(line_count)+"-"
            
            total_time_output = section_ends[0]
            output_minutes = int(total_time_output//60000)
            if output_minutes >= 1:
                for minute in range(output_minutes):
                    total_time_output -= 60000
            output_seconds = int(total_time_output)//1000
            if output_seconds >= 1:
                for second in range(output_seconds):
                    total_time_output -= 1000
            output_milliseconds = total_time_output
            if len(str(output_minutes)) != 2:
                output_minutes = str(0)+str(output_minutes)
            if len(str(output_seconds)) != 2:
                output_seconds = str(0)+str(output_seconds)
            if len(str(output_milliseconds)) != 2:
                output_milliseconds = str(0)+str(output_milliseconds)
            time_string = (str(output_minutes) + ":" + str(output_seconds) + ":" + str(output_milliseconds) + "-")

            new_line = line.replace(string_line_count, time_string)
            OUTPUT_LIST.append(new_line)
            del section_ends[0]
    temp.close()
    with open(script_path + "/" + OUTPUT_FILENAME, "a") as f:
        for line in OUTPUT_LIST:   
            f.write(line)
    f.close()

def checkSuccess(total_snippets, TEMP_FILE):
    """
    There is a delay in outputing transcription to file this loop runs until
    all the transcription lines are completed
    """
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
    return

def organizeTemp(TEMP_FILE, script_path):
    output_list = []
    with open(TEMP_FILE, "r") as f:
        for line in f:
            output_list.append(line)
    f.close()
    output_list.sort()
    os.remove(TEMP_FILE)
    with open(TEMP_FILE, "a") as temp:
        for line in output_list:
            temp.write(line)
    temp.close()

def transcribe(snippet):
    try:
        r = sr.Recognizer()
        with sr.AudioFile(snippet) as source:
            r.adjust_for_ambient_noise(source)
            audio = r.record(source)        
            text = r.recognize_google(audio)
            text_string = text
    except:
        text_string = "!!!ERROR processing audio!!!"
    return text_string

def transcribeAudio(snippet, line_count, TEMP_FILE, total_snippets, pbar, single_file=False):
    """Transcribes the audio input file/snippets and writes to a temp file"""
    if single_file == True:       
        text = transcribe(snippet)
        text_string = text
    elif single_file == False:
        dummy_diff = len(str(int(total_snippets)))-len(str(line_count))
        dummy_zeros = dummy_diff*str(0)
        line_count = str(dummy_zeros)+str(line_count)
        text = transcribe(snippet)
        text_string = str(line_count) + "- " + text
    with open(TEMP_FILE, "a") as f:
        f.write(text_string + "\n")
    f.close()
    pbar.update(1)

def runTranscription(split_wav, thread_count, TEMP_FILE, total_snippets, single_file=False):
    """Main function to run transcription operation"""
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

def runOperations(INPUT_FILE, script_path, thread_count, keep_wav, silence_detection):
    """All the main functions & operations are run from this function."""
    if thread_count == None:
        thread_count = 10

    start_time = time.time()
    FILENAME = stripExtension(INPUT_FILE, script_path)
    TEMP_DIR = script_path + '\\temp'
    TEMP_FILE = TEMP_DIR + '\\' + FILENAME + '-TEMP.txt'
    check_required = False

    FILE_TYPE = fileType(INPUT_FILE)           
    if FILE_TYPE == None or FILE_TYPE == 'Unsupported':
        print("[!]ERROR: Unsupported File Type!!!")
        return
    elif FILE_TYPE == 'mp4' or FILE_TYPE == 'mkv' or FILE_TYPE == 'mpg' or FILE_TYPE == 'avi':
        print("[+]Extracting Audio from Video...")
        new_sound = extractAudio(FILE_TYPE, FILENAME, script_path)
        operation = 'Extraction'
        check_required = True
    elif FILE_TYPE == 'mp3' or FILE_TYPE == 'm4a':
        print("[+]Converting to WAV format...")
        new_sound = convertWAV(INPUT_FILE, FILE_TYPE, FILENAME)
        operation = 'Conversion'
        check_required = True
    elif FILE_TYPE == 'wav':
        print("[!]No file conversion or extraction needed!")
        keep_wav = True
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
        print(" [!]" + operation + " Completed")
        new_sound = AudioSegment.from_wav(AUDIO_OUTPUT_FILE)

    cleanUp(script_path, None)
    makeTemp(TEMP_DIR)
    
    recommended_section_length = 30
    duration = (len(new_sound)+1)/1000
    
    if duration < recommended_section_length:
        new_sound_file = TEMP_DIR + '/' + new_sound
        shutil.copyfile(new_sound, new_sound_file)
    else:
        if silence_detection == True:
            ESTIMATED_SECTIONS = duration//recommended_section_length+1
            SILENCE_DETECTED, range_list = detectSilence(new_sound, ESTIMATED_SECTIONS)
            if SILENCE_DETECTED == True:
                silences_found = int(len(range_list)/2)
                print(" [!]Found " + str(silences_found) + " silence sections")
                section_ends = audioSplitter(FILENAME, recommended_section_length, new_sound, duration, TEMP_DIR, range_list, silences_found, silence_split=True)
            else:
                print(" [!]No suitable silence sections found")
                silence_detection = False
    if silence_detection == False:
        section_ends = audioSplitter(FILENAME, recommended_section_length, new_sound, duration, TEMP_DIR, None)

        
    split_wav, total_snippets = getSnippets(TEMP_DIR)
    
    if total_snippets == 1:
        runTranscription(split_wav, thread_count, TEMP_FILE, total_snippets, single_file=True)
    else:
        runTranscription(split_wav, thread_count, TEMP_FILE, total_snippets)
        
    checkSuccess(total_snippets, TEMP_FILE)
    organizeTemp(TEMP_FILE, script_path)    

    print("[!]Transcription successful")
    createOutput(FILENAME, TEMP_FILE, script_path, total_snippets, section_ends)
    
    if keep_wav == True:
        cleanUp(script_path, None)
    elif keep_wav == False: 
        cleanUp(script_path, FILENAME, DELETE_CONVERT=True)

    print("-------------------------------")
    print("[!]Completed Transcription")

    run_time = runTime(start_time)
    print('[!]Entire job took: ' + run_time)
    print("-------------------------------")

def printTitle():
    VERSION = 2.0
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
                                   '\n -k --keep <keep converted/extracted wav file>' +\
                                   '\n Splitting Options:' +\
                                   '\n -s --silence <silence splitting>' )

    parser.add_option('-f', '--file',
                      action='store', dest='filename', type='string',\
                      help='specify target file', metavar="FILE")

    parser.add_option('-t', '--threads',
                      action='store', dest='threads', type='int',\
                      help='specify amount of threads to use')
    
    parser.add_option('-k', '--keep',
                      action='store_true', dest='keep', default=False,\
                      help='Keep wav file, if converting')

    parser.add_option('-s', '--silence',
                      action='store_true', dest='silence', default=False,\
                      help='Will use silence detection & splitting')
    
    (options, args) = parser.parse_args()

    script_path = os.path.abspath(os.path.dirname(sys.argv[0]))    

    INPUT_FILE = options.filename
    thread_count = options.threads
    keep_wav = options.keep
    silence_detection = options.silence
    
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
    runOperations(INPUT_FILE, script_path, thread_count, keep_wav, silence_detection)

if __name__ == '__main__':
    main()
