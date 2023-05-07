import os
from TextToAudiobookAi import *




os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/Users/dong/src/npc/google_credentials/tts-audiobook-2023-065dfa735253.json"

folder_name = "test"
book_name = "test"
file_name = "test_text.txt"

test_tta = TextToAudiobookAi(folder_name, book_name, char_limit_per_call=500)

test_tta.clean_text_script()

# #1 Clean raw file and copy to clean folder
# print(test_tta.clean_txt_raw(file_name))

# #2 Mark break point by chapter and characters limit
# print(test_tta.break_txt_clean(file_name))

# #3 Split Split into files by chapter and characters break
# print(test_tta.split_txt_break(file_name))

#4 Call OpenAI API to tag emotion

#5 replace tag with SSML


#6 Call Google API to convert to audio


test_tta.fetch_prompt("say hello in japanese")