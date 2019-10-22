'''
POLA READER
https://github.com/alephnaughtpix/Pola-Reader

v0.1 Michael James 2019-10-18

Internet Audio reader. Developed from the SHipping Forecast Reader. ( https://github.com/alephnaughtpix/shippingforecast )

Technologies used:
* Google Text to Speech
* PyRubberband: https://pyrubberband.readthedocs.io/
* PyDub: https://github.com/jiaaro/pydub/
* PySoundfile: https://pysoundfile.readthedocs.io/
'''
import requests
import lxml.etree as ET
from gtts import gTTS 
from pydub import AudioSegment
import numpy as np
import pyrubberband as pyrb
import soundfile as sf
import pyttsx3
import os
import os.path

SHOWS_DIRECTORY = './shows'

THEME_TUNE = True           # OPTIONAL: Include the unofficial theme tune "Sailing By" before the forecast. (If you have an MP3 of it.)
REMOVE_TEMP_FILES = True    # Remove temp files after processsing
PITCH_SHIFT = True          # Pitch shift voice down
COMPRESS_DYNAMICS = True    # Compress overall result


def create_show( show ):
    source_url = show['source_url']     # URL of source feed
    xml_filename = 'source.xml'         # Saved RSS of Shipping Forecast
    xsl_filename = 'translate.xsl'      # Translates RSS to human readable text
    script_filename = 'script.txt'      # Human readable version of Shipping Forecast
    source_mp3 = "speech.mp3"           # Text to speech result
    pitch_file = "output_pitch.flac"    # Pitch-shifted Text to speech result
    theme_mp3 = show['intro_theme']     # Intro theme
                                        # ^^^ You'll need to supply this yourself!!!
    combined_file = "output_combined.mp3"
    output_file = "output.mp3"
    if PITCH_SHIFT:
        speech_file = pitch_file
    else:
        speech_file = source_mp3
    
    working_directory = os.path.join(SHOWS_DIRECTORY, show['directory'])
    
    # Get source RSS
    response = requests.get(source_url)
    source_text = response.text
    
    # Save on local system
    file = open(os.path.join(working_directory, xml_filename),'w')
    file.write(source_text)
    file.close()
    
    # Translate RSS to human readable text for Text to Speech
    dom = ET.parse(os.path.join(working_directory, xml_filename))
    xslt = ET.parse(os.path.join(working_directory, xsl_filename))
    transform = ET.XSLT(xslt)
    newdom = transform(dom)
    output = " ".join(str(newdom).split())                  # Strip extra spaces
    output = output.replace('<?xml version="1.0"?>', '')    # Remove XML header.
    file = open(os.path.join(working_directory, script_filename),'w')
    file.write(output)
    file.close()
    
    # Google Text to speech
    engine = gTTS(text=output, lang='en-UK', slow=False) 
    engine.save(os.path.join(working_directory,source_mp3))
    if PITCH_SHIFT:
        word_src = AudioSegment.from_mp3(os.path.join(working_directory,source_mp3))
        sample_rate = word_src.frame_rate
        samples = np.array(word_src.get_array_of_samples())
        pitched_down = pyrb.pitch_shift(samples, sample_rate, n_steps=-4)
        sf.write(os.path.join(working_directory,pitch_file), pitched_down, sample_rate)
        if REMOVE_TEMP_FILES:
            os.remove(os.path.join(working_directory,source_mp3))
                    
    if os.path.exists(os.path.join(working_directory,output_file)):
        os.remove(os.path.join(working_directory,output_file))
            
    if THEME_TUNE:
        theme_src = AudioSegment.from_mp3(os.path.join(working_directory, 'media', theme_mp3)).normalize()        # Get theme tune
        feature_src = AudioSegment.from_file(os.path.join(working_directory,speech_file)).normalize()   # Get spoken word
        programme_start = len(theme_src) + show['programme_start']      # Speech starts x seconds before the theme is complete
        programme_length = programme_start + len(feature_src)           # Combined programme is the combined length of the two files minus 6 seconds
        playlist = AudioSegment.silent( duration=programme_length )     # Make new blank segment with the combine programme length
        programme = playlist.overlay(theme_src).overlay(feature_src, position=programme_start)  # Overlay theme and speech onto blank segment
        if COMPRESS_DYNAMICS:
            programme = programme.compress_dynamic_range()
        programme.export(os.path.join(working_directory,combined_file), format="mp3")
        if REMOVE_TEMP_FILES:
            os.rename(os.path.join(working_directory,combined_file), os.path.join(working_directory,output_file))
    else:
        if REMOVE_TEMP_FILES:
            os.rename(os.path.join(working_directory,speech_file), os.path.join(working_directory,output_file))
            
    if REMOVE_TEMP_FILES:
        os.remove(os.path.join(working_directory,speech_file))
        os.remove(os.path.join(working_directory,script_filename))
        os.remove(os.path.join(working_directory,xml_filename))
    
    return None

shipping_forecast_show = {
    'name': 'The Shipping Forecast',
    'directory': '01_shipping_forecast',
    'intro_theme': 'sailingby.mp3',
    'programme_start': -6 * 1000,
    'source_url': 'https://www.metoffice.gov.uk/public/data/CoreProductCache/ShippingForecast/Latest'
}

shows = []
shows.append( shipping_forecast_show )
for current_show in shows:
    create_show(current_show)
