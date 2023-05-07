import re
import os
import time
# import ffmpeg
import datetime
import math
import shutil
import json
import openai

from pathlib import Path
# from google.cloud import texttospeech
from google.cloud import texttospeech

class TextToAudiobookAi:
    def __init__(self, project_name, book_name, char_limit_per_call=1500):
        self.project_name = project_name
        self.book_name = book_name
        self.project_path = "./" + project_name + "/"
        self.project_file = self.project_path + "project_file/"
        self.char_limit_per_call = char_limit_per_call
        self.char_breaks = [',','”','"',';',':','.']

        self.tag_chapter_break = "[[-chapter_break-]]"
        self.tag_character_break = "[[-character_break-]]"

        self.config_path = "./config/config_example.json"
        self.config = self.load_config()
        # self.load_config()

    # load config from json file
    def load_config(self):
        with open(self.config_path) as config_file:
            config = json.load(config_file)
            
        print('=====', config )
        return config

    #0 Clean previous script
    def clean_text_script(self):
        # delete all files and folders in following list: clean, tag, split 
        dir_clean_path = self.project_file +  "clean/"
        dir_tag_path = self.project_file + "tag/"
        dir_split_path = self.project_file + "split/"
        dir_split_path = self.project_file + "break/"

        # add paths to list
        dir_list = [dir_clean_path, dir_tag_path, dir_split_path]
        
        # loop delete all files and folders in list
        for dir_path in dir_list:
            
            # if dir exist
            if os.path.exists(dir_path):
                # os.rmdir(dir_path)
                shutil.rmtree(dir_path)
                print(" - Directory '% s' has been removed successfully" % dir_path)


    #1 Clean raw file and copy to clean folder
    def clean_txt_raw(self, file_name):
        dir_clean_path = self.project_file + "clean/"
        file_clean_path = dir_clean_path + file_name
        file_raw_path = self.project_file + "raw/" + file_name

        # Check target dir
        Path(dir_clean_path).mkdir(parents=True, exist_ok=True)

        with open(file_clean_path, "w") as file_clean:
            with open(file_raw_path, "r") as file_raw:
                lines = file_raw.readlines()

                line_count = 0
                for line in lines:
                    line_count += 1

                    # Replace Roman chapter number with numeric
                    line_clean = self.clean_roman_num_in_string(line.strip())
                    # line_clean = line.strip()
                    
                    # Fix all upper case sentence
                    if not self.is_chapter_header(line_clean):
                        line_clean = self.fix_all_upper(line_clean)

                    line_clean = self.clean_invalid_symbol(line_clean)

                    file_clean.write(line_clean + "\n")

                    # print("Line {}: {}".format(line_count, line.strip()))
                    # print("     ==> {}".format(line_clean))

        print(f"Clean: {line_count} lines")
        return file_clean_path

    #2 Mark break point by chapter and characters limit
    def break_txt_clean(self, file_name):
        dir_clean_path = self.project_file + "clean/"
        file_clean_path = dir_clean_path + file_name
        file_break_path = self.project_file + "break/" + file_name

        # Check target dir and create if not exist
        Path(self.project_file + "break/").mkdir(parents=True, exist_ok=True)

        with open(file_break_path, "w") as file_break:
            with open(file_clean_path, "r") as file_clean:
                lines = file_clean.readlines()

                line_count = 0
                char_count = 0
                chapter_count = 0
                for line in lines:
                    line_count += 1
                    char_count += len(line)

                    # Check chapter break
                    if self.is_chapter_header(line):
                        chapter_count += 1
                        char_count = 0
                        file_break.write(self.tag_chapter_break + "\n")

                    # Check character break
                    if char_count > self.char_limit_per_call:
                        # find break point at char_breaks
                        idx = self.get_line_break(line)
                        if idx > -1:
                            line = line[ : idx] + "\n" + self.tag_character_break + "\n" + line[idx : ]
                            char_count = len(line[idx : ])

                    file_break.write(line + "\n")
                    # print("Line{} / {}: {}".format(line_count, char_count, line.strip()))

            # Insert last break
            file_break.write(self.tag_chapter_break)

        print(f"Break: {line_count} lines")
        return file_break_path
                    
        
    #3 Split Split into files by chapter and characters break
    def split_txt_break(self, file_name):
        dir_split_path = self.project_file + "split/" + self.file_to_folder_name(file_name) + "/"
        file_break_path = self.project_file + "break/" + file_name

        # Check target dir
        Path(dir_split_path).mkdir(parents=True, exist_ok=True)

        with open(file_break_path, "r") as file_break:

            lines = file_break.readlines()

            line_count = 0
            file_count = 0
            ch_count = 0
            part_count = 1
            file_split_name = ''
            text_script = ''

            for line in lines:
                line_count += 1

                line = line.strip()

                if (
                    (line == self.tag_chapter_break)
                    | (line == self.tag_character_break)
                ):


                    # Write to file
                    file_split_name = str(ch_count).zfill(4) + "_" + str(part_count).zfill(3) + ".txt"

                    print (f"    ===> Write to:{file_split_name} :{text_script}")

                    file_split_path = dir_split_path + file_split_name

                    with open(file_split_path, "w") as file_split:
                        file_split.write(text_script)

                    text_script = ''
                    file_count +=1

                    if (line == self.tag_chapter_break):
                        ch_count += 1
                        part_count = 1

                    if (line == self.tag_character_break):
                        part_count += 1

                else:
                    # Find break
                    text_script += line + "\n"
                    # print("Line {}: {}".format(line_count, line.strip()))

        print(f"Split: {file_count} files")
        return dir_split_path

    #4 Call OpenAI API to tag emotion

    #5 replace tag with SSML


    #6 Call Google API to convert to audio

    #7 Merge audio files

    #8 Convert to mp3

    #9 Add cover

    #10 Add meta data

    #Helper function
    def clean_roman_num_in_string(self, s):
        romans = re.findall(
            r'(?=\b[MCDXLVI]{1,7}\b)M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})(?=\.)'
            , s )

        # print(romans)
        romans.sort(key=len, reverse=1)

        for roman in romans:
            s = s.replace(roman, str(self.roman_to_int(roman)))

        return s
    
    def roman_to_int(self, s):
        roman_map = {'M': 1000, 'D': 500, 'C': 100, 'L': 50, 'X': 10, 'V': 5, 'I': 1}
        int_num = 0
        for i in range(len(s)):
            if i > 0 and roman_map[s[i]] > roman_map[s[i - 1]]:
                int_num += roman_map[s[i]] - 2 * roman_map[s[i - 1]]
            else:
                int_num += roman_map[s[i]]
        return int_num
    
    def clean_invalid_symbol(self, s):
        s = s.replace('&', 'and')
        s = s.replace('_', ' ')

        return s
    
    def is_chapter_header(self, s):
        pattern1 = re.compile("^CHAPTER [A-Z|\d]*\.$")
        pattern2 = re.compile("^\[\[-header_begin-\]\]")
        pattern3 = re.compile("^Epilogue")

        if pattern1.match(s) or pattern2.match(s) or pattern3.match(s):
            return True
        else:
            return False
        
    def file_to_folder_name(self, f):
        return f.replace('.', '_')

    def fix_all_upper(self, sentence):
        if sentence.isupper():
            sentence = sentence.lower()
            sentence = sentence.title()
        return sentence
    
    def get_line_break(self, s):

        break_pos = 99999
        for char_break in self.char_breaks:
            idx = s.find(char_break + ' ')
            if (idx > -1) and idx < break_pos:
                break_pos = idx

            # print(f"find '{char_break}' => {idx} ==> break: {break_pos}")

        if break_pos == 99999:
            return -1
        else:
            return break_pos+1

    def fetch_prompt(self, prompt_input):
        # init key
        openai.api_key = self.config['OPENAI']['key']

        prompt_input=[
            {"role": "user", "content": prompt_input}
        ]

        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = prompt_input,
            temperature = 0.7,
            # max_tokens = prompt_params.get('max_tokens',2500)
        )

        print(response)
        return response
    
    def enhance_prompt_interpret_test_result(self, prompt_input):
        pass