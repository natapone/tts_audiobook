# tts_audiobook
Generate audiobook from text-to-speech

# Start
% cd /Users/dong/src/npc/python/tts_audiobook
% source venv/bin/activate
% jupyter notebook

# Virtual environment
% python3 -m venv ./venv


# Setup Google account
https://cloud.google.com/text-to-speech/docs/before-you-begin

# Note
% export GOOGLE_APPLICATION_CREDENTIALS="/Users/dong/src/npc/google_credentials/tts-audiobook-2023-065dfa735253.json"

% printenv


# New kernal for Jupyter
% python -m ipykernel install --user --name tts_env --display-name "Python tts env"

* select kernal "Python tts env" in Jupyter notebook
