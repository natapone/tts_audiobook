import re
import os
import time
import ffmpeg
import datetime
import math


from pathlib import Path
from google.cloud import texttospeech

class TextToAudiobook:
    def __init__(self, project_name, char_limit_per_call=3000):
        self.project_name = project_name
        self.project_path = "./" + project_name + "/"
        self.project_file = self.project_path + "project_file/"
        self.char_limit_per_call = char_limit_per_call
        self.char_breaks = [',','”','"',';',':','.']

        self.tag_chapter_break = "[[-chapter_break-]]"
        self.tag_character_break = "[[-character_break-]]"

    

    def merge_audio_files(self, file_name):
        dir_audio_path = self.project_file + "audio/" + self.file_to_folder_name(file_name) + "/"
        dir_video_path = self.project_file + "video/"
        file_video_path = dir_video_path + self.file_to_folder_name(file_name) + ".mp4"

        # Check target dir
        Path(dir_video_path).mkdir(parents=True, exist_ok=True)

        # List text files
        file_list = []
        file_count = 0
        for a_name in os.listdir(dir_audio_path):
            # check if current path is a file
            if (
                    (os.path.isfile(os.path.join(dir_audio_path, a_name))) &
                    (a_name.lower().endswith(('.mp3')))
                ):
                file_list.append(a_name)

        file_list.sort()
        # write audio tracks list to file
        track_list_file = dir_audio_path + 'track_list.txt'
        with open(track_list_file, "w") as file_track:
            #
            for a_name in file_list:
                file_track.write("file '" + a_name + "'\n")
                file_count+=1
                # print(file_path)

        print(f"Generate track list: {track_list_file} [total: {file_count} files]")

        # merge mp3 files
        file_audio_full_path = self.project_file + "audio/" + self.file_to_folder_name(file_name) + ".mp3"
        cmd_string = '''
        ffmpeg -f concat \
        -i {} \
        -c copy {} -y
        '''
        # print(cmd_string.format(track_list_file, file_audio_full_path))
        os.system(cmd_string.format(track_list_file, file_audio_full_path))

        print(f"Generate full audio: {file_audio_full_path}")

        # check file exist
        # file_image_path = self.project_file + "video/" + self.file_to_folder_name(file_name) + ".png"
        # has_audio_file = os.path.exists(file_audio_full_path)
        # has_image_file = os.path.exists(file_image_path)
        #
        # if not (has_audio_file & has_image_file):
        #     print("Check audio or image files")
        #     return 0

        # merge audio to image


        return file_audio_full_path

    def gen_youtube_chapter_marker(self, file_name):
        dir_audio_path = self.project_file + "audio/" + self.file_to_folder_name(file_name) + "/"

        # List text files
        audio_infos = {}
        file_count = 0
        for file_name in os.listdir(dir_audio_path):
            # check if current path is a file
            # if os.path.isfile(os.path.join(dir_audio_path, file_name)):
            if (
                    (os.path.isfile(os.path.join(dir_audio_path, file_name))) &
                    (file_name.lower().endswith(('.mp3')))
                ):
                file_audio_path = dir_audio_path + file_name
                audio_infos[file_name] = ffmpeg.probe(file_audio_path)['format']['duration']

        total_duration_sec = 0
        chapter_marker = 2
        current_chapter = -1

        chapter_text = "0:00:00 Chapter 1"
        for i in sorted(audio_infos.keys()):
            # check chapter number
            file_parts = i.split('_')
            chapter_num = int(file_parts[0])
            # print("Ch:", chapter_num, "/", chapter_marker, " total=", total_duration_sec)

            # new chapter and start at ch 2
            if chapter_num >= chapter_marker:
                to_minute = str(datetime.timedelta(seconds=math.floor(total_duration_sec)))
                # print ("  Export=>",   to_minute, '(',total_duration_sec,  ')',  "Chaptor", chapter_num )
                chapter_text += ("\n" + to_minute + " " + "Chaptor " + str(chapter_num))
                chapter_marker +=1

            duration_sec = float(audio_infos[i])
            total_duration_sec += duration_sec
            # print("  - ",i, ": ", duration_sec, "=>", total_duration_sec, '=>', total_duration_sec)

        return chapter_text

    def synthesize_ssml(self, ssml, audio_file_path, voice=None, audio_config=None):
        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.SynthesisInput(ssml=ssml)

        if voice == None:
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-GB",
                name="en-GB-Neural2-B",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE,
            )

        if audio_config == None:
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.8
            )

        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )

        # The response's audio_content is binary.
        with open(audio_file_path, "wb") as out:
            out.write(response.audio_content)
            print(f"Generate audio => {audio_file_path}")

        return 1

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
                    file_clean.write(line_clean + "\n")

                    # print("Line {}: {}".format(line_count, line.strip()))
                    # print("     ==> {}".format(line_clean))

        print(f"Clean: {line_count} lines")
        return file_clean_path

    def tag_txt_clean(self, file_name):
        dir_tag_path = self.project_file + "tag/"
        file_tag_path = dir_tag_path + file_name
        file_clean_path = self.project_file + "clean/" + file_name

        # Check target dir
        Path(dir_tag_path).mkdir(parents=True, exist_ok=True)

        with open(file_tag_path, "w") as file_tag:
            with open(file_clean_path, "r") as file_clean:
                lines = file_clean.readlines()

                line_count = 0
                for line in lines:
                    line_count += 1

                    # print("Line {}: {}".format(line_count, line.strip()))
                    line_tag = line.strip()
                    line_tag = self.insert_tag_title(line_tag)
                    line_tag = self.insert_tag_header(line_tag)
                    # print("     1==> {}".format(line_tag))
                    line_tag = self.insert_tag_emphasis(line_tag)
                    # print("     2==> {}".format(line_tag))
                    line_tag = self.insert_tag_paragraph_break(line_tag)
                    # print("     3==> {}".format(line_tag))
                    file_tag.write(line_tag + "\n")

        print(f"Tag: {line_count} lines")
        return file_tag_path

    def break_txt_tag(self, file_name):
        dir_break_path = self.project_file + "break/"
        file_break_path = dir_break_path + file_name
        file_tag_path = self.project_file + "tag/" + file_name

        # Check target dir
        Path(dir_break_path).mkdir(parents=True, exist_ok=True)

        with open(file_break_path, "w") as file_break:
            with open(file_tag_path, "r") as file_tag:
                # print(file_raw.read())
                lines = file_tag.readlines()

                line_count = 0
                char_count = 0
                for line in lines:
                    line_count += 1

                    # insert chapter break
                    if self.is_chapter_header(line):
                        char_count = 0
                        # print(tag_chapter_break)
                        line =  self.tag_chapter_break + "\n" + line

                    # Replace tag with SSML
                    line = self.replace_tag_ssml(line.strip())

                    # insert charactor limit break
                    char_count += len(line)
                    if char_count >= self.char_limit_per_call:
                        # find break point
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
                    # file_split_name = self.project_name + "_" + str(ch_count) + "_" + str(part_count) + ".txt"
                    file_split_name = str(ch_count).zfill(4) + "_" + str(part_count).zfill(3) + ".txt"

                    # print (f"    ===> Write to:{file_split_name} :{text_script}")

                    file_split_path = dir_split_path + file_split_name
                    text_script = "<speak>\n"+text_script+"</speak>"

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

    def synthesize_txt_split(self, file_name, file_limit=100, voice=None, audio_config=None):
        dir_split_path = self.project_file + "split/" + self.file_to_folder_name(file_name) + "/"
        dir_audio_path = self.project_file + "audio/" + self.file_to_folder_name(file_name) + "/"
        dir_backup_path = self.project_file + "split/" + self.file_to_folder_name(file_name) + "/backup/"

        # Check target dir
        Path(dir_audio_path).mkdir(parents=True, exist_ok=True)
        Path(dir_backup_path).mkdir(parents=True, exist_ok=True)

        # List text files
        file_list = []
        file_count = 0
        for file_name in os.listdir(dir_split_path):
            # check if current path is a file
            if os.path.isfile(os.path.join(dir_split_path, file_name)):
                file_list.append(file_name)

                # file_split_path = dir_split_path + file_name
                # print(file_split_path)

        file_list.sort()
        for file_name in file_list:
            file_split_path = dir_split_path + file_name
            file_parts = file_name.split(".")
            file_audio_path = dir_audio_path + file_parts[0] + '.mp3'
            # print("Read: " + file_split_path)

            # Read content
            text_script = ''
            with open(file_split_path, "r") as file_split:
                text_script = file_split.read()

            # Call API
            # print(text_script)
            self.synthesize_ssml(text_script, file_audio_path, voice, audio_config)
            # print(" => Write: " + file_audio_path)

            # Move converted file to backup folder
            file_backup_path = dir_backup_path + file_name
            os.rename(file_split_path, file_backup_path)
            # print(" => Move: " + file_backup_path)

            file_count +=1
            if file_count >= file_limit:
                break

            time.sleep(1)

        print(f"Synthesize: {file_count} files")
        return dir_audio_path

    # def merge_audio_chapter(self, file_name):
    #     dir_audio_path = self.project_file + "audio/" + self.file_to_folder_name(file_name) + "/"
    #     dir_audio_chapter_path = self.project_file + "audio/"
    #
    #     file_list = []
    #     chapter_list = {}
    #     file_count = 0
    #     for file_name in os.listdir(dir_audio_path):
    #         # check if current path is a file
    #         if os.path.isfile(os.path.join(dir_audio_path, file_name)):
    #             file_list.append(file_name)
    #
    #     # print(file_list)
    #     # Merge by chapter
    #     file_list.sort()
    #     for file_name in file_list:
    #         file_parts = re.split('_|\.',file_name)
    #         # print(file_parts)
    #
    #         if file_parts[0] in chapter_list.keys():
    #             # print('goood!')
    #             chapter_list[file_parts[0]].append(file_name)
    #         else:
    #             chapter_list[file_parts[0]] = [file_name]
    #
    #     print(chapter_list)
    #
    #     # merge MP3 files
    #
    #     return 1

    def insert_tag_header(self, s):
        # tag_begin = '<prosody rate="slow" pitch="-2st">'
        # tag_end = '</prosody>'

        tag_begin = '[[-header_begin-]]'
        tag_end = '[[-header_end-]]'

        if len(s.strip()) > 0 and self.is_chapter_header(s):
            return (tag_begin + s + tag_end)
        else:
            return s

    def insert_tag_title(self, s):
        # tag_begin = '<prosody rate="x-slow" pitch="-2st">'
        # tag_end = '</prosody>'

        tag_begin = '[[-title_begin-]]'
        tag_end = '[[-title_end-]]'

        if len(s.strip()) > 0 and self.is_book_title(s):
            return (tag_begin + s + tag_end)
        else:
            return s

    def insert_tag_paragraph_break(self, s):
        # tag = '<break strength="weak"/>'
        tag = '[[-break_weak-]]'

        if len(s.strip()) == 0:
            return (tag + s)
        else:
            return s

    def insert_tag_emphasis(self, s):
        # tag_begin = '<emphasis level="{}">'
        # tag_end = '</emphasis>'

        tag_begin = '[[-emphasis_{}-]]'
        tag_end = '[[-emphasis_end-]]'

        char_strongs = ['!', '?']
        quotes = ['"','“','”']
        quotes = self.char_breaks + quotes
        quotes = list(dict.fromkeys(quotes))

        speechs = re.findall(
            r'(["|“][^"|“|”]+["|”])'
            , s )
    #     print(speechs)

        speechs.sort(key=len, reverse=1)
        for speech in speechs:

            emphasis_level = 'moderate'
            for char_strong in char_strongs:
                idx = speech.find(char_strong)
                if idx > 0:
                    emphasis_level = 'strong'

            # remove quotes and char_break to prevent file break between tag
            speech_clean = speech
            for quote in quotes:
                # print(speech,": clean==>", quote)
                speech_clean = speech_clean.replace(quote, '')

            tag_full = tag_begin.format(emphasis_level) + speech_clean + tag_end
            # print(speech, "==>", tag_full)
            s = s.replace(speech, tag_full, 1)

        return s

    def replace_tag_ssml(self, s):
        ssml_tags = {
            '[[-title_begin-]]': '<prosody rate="slow">',
            '[[-title_end-]]': '</prosody>',
            '[[-header_begin-]]': '<prosody rate="slow">',
            '[[-header_end-]]': '</prosody>',
            '[[-break_weak-]]': '<break time="600ms"/>',
            '[[-emphasis_strong-]]': '<emphasis level="strong">',
            '[[-emphasis_moderate-]]': '<emphasis level="moderate">',
            '[[-emphasis_end-]]': '</emphasis>'
        }

        for key, value in ssml_tags.items():
            s = s.replace(key, value)

        return s

    def read_txt_raw(self, file_name):
        file_path = self.project_file + "raw/"  + file_name

        with open(file_path) as file_raw:
            # print(file_raw.read())
            txt_raw = file_raw.read()

        return txt_raw

    def roman_to_int(self, s):
        rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        int_val = 0
        for i in range(len(s)):
            if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
                int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
            else:
                int_val += rom_val[s[i]]
        return int_val

    def clean_roman_num_in_string(self, s):
        romans = re.findall(
            r'(?=\b[MCDXLVI]{1,6}\b)M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})(?=\.)'
            , s )
        # print(romans)
        romans.sort(key=len, reverse=1)

        for roman in romans:
            s = s.replace(roman, str(self.roman_to_int(roman)))

        return s

    def is_chapter_header(self, s):
        pattern1 = re.compile("^CHAPTER [A-Z|\d]*\.$")
        pattern2 = re.compile("^\[\[-header_begin-\]\]")
        pattern3 = re.compile("^Epilogue")

        if pattern1.match(s) or pattern2.match(s) or pattern3.match(s):
            return True
        else:
            return False

    def is_book_title(self, s):
        pattern = re.compile("^Title:|Author:|Produced by:")

        if pattern.match(s):
            return True
        else:
            return False

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

    def file_to_folder_name(self, f):
        return f.replace('.', '_')

# Steps
# - fetch full text file
# - clean unreadable string
# - insert chapter break
# - insert charactor limit break
# - tag SSML
# - break into small file per api call
# - convert with tts service
# - fix each file to improve reading
