import re

class TextToAudiobook:
    def __init__(self, project_name):
        self.project_name = project_name
        self.project_path = "./" + project_name + "/"
        self.char_limit_per_call = 200

    def break_txt_raw(self, file_name):
        file_path = self.project_path + "raw/"  + file_name
        clean_path = self.project_path + "clean/"  + file_name

        tag_chapter_break = "[[-chapter_break-]]"
        tag_character_break = "[[-character_break-]]"

        with open(file_path, "r") as file_raw:
            # print(file_raw.read())
            lines = file_raw.readlines()

            line_count = 0
            char_count = 0
            for line in lines:
                line_count += 1

                # insert chapter break
                if self.is_chapter_header(line):
                    char_count = 0
                    print(tag_chapter_break)

                # insert charactor limit break
                char_count += len(line)
                if char_count >= self.char_limit_per_call:
                    # find break point
                    idx = self.get_line_break(line)
                    if idx > -1:
                        line = line[ : idx] + "\n" + tag_character_break + "\n" + line[idx : ]
                        char_count = len(line[idx : ])

                print("Line{} / {}: {}".format(line_count, char_count, line.strip()))

        return 1

    def insert_ssml_header(self, s):
        tag_begin = '<prosody rate="slow" pitch="-2st">'
        tag_end = '</prosody>'

        if len(s.strip()) > 0:
            return (tag_begin + s + tag_end)
        else:
            return s

    def insert_ssml_paragraph_break(self, s):
        tag = '<break strength="weak"/>'

        if len(s.strip()) == 0:
            return (tag + s)
        else:
            return s

    def insert_ssml_emphasis(self, s):
        tag_begin = '<emphasis level="{}">'
        tag_end = '</emphasis>'
        char_strongs = ['!', '?']
        quotes = ['"','“','”']

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

            # remove quotes
            speech_clean = speech
            for quote in quotes:
                speech_clean = speech_clean.replace(quote, '')

            tag_full = tag_begin.format(emphasis_level) + speech_clean + tag_end
    #         print(speech, "==>", tag_full)
            s = s.replace(speech, tag_full, 1)

        return s

    def read_txt_raw(self, file_name):
        file_path = self.project_path + "raw/"  + file_name

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
        pattern = re.compile("^CHAPTER [A-Z|\d]*\.$")

        if pattern.match(s):
            return True
        else:
            return False

    def get_line_break(self, s):
        char_breaks = [',','”','"',';',':','.']

        break_pos = 99999
        for char_break in char_breaks:
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
