import re

class TextToAudiobook:
    def __init__(self, project_name):
        self.project_name = project_name
        self.project_path = "./" + project_name + "/"

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

    # def test(self):
    #     return 'goood!'

# Steps
# - fetch full text file
# - clean unreadable string
# - insert chapter break
# - insert charactor limit break
# - tag SSML
# - break into small file per api call
# - convert with tts service
# - fix each file to improve reading
