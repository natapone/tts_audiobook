import re
from pathlib import Path

class TextToAudiobook:
    def __init__(self, project_name):
        self.project_name = project_name
        self.project_path = "./" + project_name + "/"
        self.project_file = self.project_path + "project_file/"
        self.char_limit_per_call = 500
        self.char_breaks = [',','”','"',';',':','.']

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

        print(f"Clean: {line_count} lines")
        return file_tag_path

    def break_txt_tag(self, file_name):
        dir_break_path = self.project_file + "break/"
        file_break_path = dir_break_path + file_name
        file_tag_path = self.project_file + "tag/" + file_name

        # Check target dir
        Path(dir_break_path).mkdir(parents=True, exist_ok=True)

        tag_chapter_break = "[[-chapter_break-]]"
        tag_character_break = "[[-character_break-]]"

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
                        line =  tag_chapter_break + "\n" + line

                    # Replace tag with SSML
                    line = self.replace_tag_ssml(line.strip())

                    # insert charactor limit break
                    char_count += len(line)
                    if char_count >= self.char_limit_per_call:
                        # find break point
                        idx = self.get_line_break(line)
                        if idx > -1:
                            line = line[ : idx] + "\n" + tag_character_break + "\n" + line[idx : ]
                            char_count = len(line[idx : ])

                    file_break.write(line + "\n")
                    # print("Line{} / {}: {}".format(line_count, char_count, line.strip()))

        return file_break_path

    def split_txt_break(self, file_name):
        pass

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
            '[[-title_begin-]]': '<prosody rate="x-slow" pitch="-2st">',
            '[[-title_end-]]': '</prosody>',
            '[[-header_begin-]]': '<prosody rate="slow" pitch="-2st">',
            '[[-header_end-]]': '</prosody>',
            '[[-break_weak-]]': '<break strength="weak"/>',
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
            r'(?=\b[MCDXLVI]{1,6}\b)M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})'
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
        pattern = re.compile("^Title:|Author:")

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

# Steps
# - fetch full text file
# - clean unreadable string
# - insert chapter break
# - insert charactor limit break
# - tag SSML
# - break into small file per api call
# - convert with tts service
# - fix each file to improve reading
