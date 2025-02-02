# Prerequisites:

## Python 3 (incl. pip)

Install the Python 3 distribution depending on your OS (Linux might already come with it, Anaconda or ActiveState Python on Windows, ...)

## Install or upgrade pip:
`python -m ensurepip --upgrade`

## Install virtualenv through pip
`pip install virtualenv`

## Set up your virtualenv specifically to use Python 3.11 (latest supported Python version at the time of the latest revision of audalign)

```
pyenv install 3.11
~/.pyenv/versions/3.11.10/bin/python3.11 -m pip install --upgrade pip
~/.pyenv/versions/3.11.10/bin/pip3 install audalign
~/.pyenv/versions/3.11.10/bin/pip3 install audalign[visrecognize]
~/.pyenv/versions/3.11.10/bin/pip3 install pydub
```

#Parameters:

The script accepts four required command-line parameters:

## Input Directory (-i, --input)
* Path to the directory containing WAV files to be processed
* Contains both the reference file and files to be aligned
* Only processes WAV files in the root directory (subdirectories are ignored)

## Reference File (-r, --reference)
* Basename (filename) of the reference WAV file
* This file serves as the timing reference for aligning other files
* Must be located in the input directory
* Can be either mono or stereo

## Temporary Directory (-t, --temp)
* Path where intermediate mono files are stored
* Used for storing split channels from stereo files
* Stores both reference and input file channels during processing
* Files in this directory are reused if they already exist

## Destination Directory (-o, --destination)
* Path where the final aligned files are saved
* Contains the alignment log file
* Stores the final merged stereo files after alignment
* Intermediate aligned mono files are created here before merging

## Optional Channel Mode (-c, --channel)
* Specifies which channel to use for alignment: 'L' (left), 'R' (right), or 'auto'
* In 'auto' mode, left channels are aligned with left, right with right
* When using 'L' or 'R', all channels are aligned against the specified reference channel
* Particularly useful when one channel of the reference might be silent or corrupted

# Usage example:

```
~/.pyenv/versions/3.11.10/bin/python ./trackalign.py  -i bak/  -t temp/ -o destination -r 

20160117_CHVE_44.1Khz-16bit.wav -c auto
2025-02-01 14:17:24,761 - INFO - Logging system initialized. Full log at destination/alignment.log
2025-02-01 14:17:52,828 - INFO - Split stereo file 'bak/AUD.wav' into:
2025-02-01 14:17:52,828 - INFO -   - Left channel: 'temp/AUD_L.wav'
2025-02-01 14:17:52,828 - INFO -   - Right channel: 'temp/AUD_R.wav'
2025-02-01 14:17:54,119 - INFO - Using stereo reference channels independently
2025-02-01 14:17:54,484 - INFO - Fingerprinting 20160117_CHVE_44.1Khz-16bit_L.wav
2025-02-01 14:17:55,574 - INFO - Fingerprinting AUD_L.wav
2025-02-01 14:18:56,511 - INFO - Finished fingerprinting AUD_L.wav
2025-02-01 14:19:01,108 - INFO - Finished fingerprinting 20160117_CHVE_44.1Khz-16bit_L.wav
2025-02-01 14:19:01,635 - INFO - 20160117_CHVE_44.1Khz-16bit_L.wav: Finding Matches...
2025-02-01 14:19:01,844 - INFO - Aligning matches
2025-02-01 14:19:01,929 - INFO - AUD_L.wav: Finding Matches...
2025-02-01 14:19:02,041 - INFO - Aligning matches
2025-02-01 14:19:03,873 - INFO - Writing destination/20160117_CHVE_44.1Khz-16bit_L._L_aligned.wav
2025-02-01 14:19:03,954 - INFO - Writing destination/AUD_L._L_aligned.wav
2025-02-01 14:19:04,802 - INFO - Writing destination/total._L_aligned.wav
2025-02-01 14:19:04,891 - INFO - 2 out of 2 found and aligned
2025-02-01 14:19:04,891 - INFO - Total fingerprints: 949603
2025-02-01 14:19:05,282 - INFO - Fingerprinting 20160117_CHVE_44.1Khz-16bit_R.wav
2025-02-01 14:19:06,359 - INFO - Fingerprinting AUD_R.wav
2025-02-01 14:20:07,225 - INFO - Finished fingerprinting AUD_R.wav
2025-02-01 14:20:12,142 - INFO - Finished fingerprinting 20160117_CHVE_44.1Khz-16bit_R.wav
2025-02-01 14:20:12,699 - INFO - 20160117_CHVE_44.1Khz-16bit_R.wav: Finding Matches...
2025-02-01 14:20:12,820 - INFO - Aligning matches
2025-02-01 14:20:12,896 - INFO - AUD_R.wav: Finding Matches...
2025-02-01 14:20:13,145 - INFO - Aligning matches
2025-02-01 14:20:14,859 - INFO - Writing destination/20160117_CHVE_44.1Khz-16bit_R._R_aligned.wav
2025-02-01 14:20:14,943 - INFO - Writing destination/AUD_R._R_aligned.wav
2025-02-01 14:20:15,797 - INFO - Writing destination/total._R_aligned.wav
2025-02-01 14:20:15,881 - INFO - 2 out of 2 found and aligned
2025-02-01 14:20:15,881 - INFO - Total fingerprints: 1898676
2025-02-01 14:20:15,983 - INFO - Renamed 'AUD_R._R_aligned.wav' to 'AUD_R_aligned.wav'.
2025-02-01 14:20:15,983 - INFO - Renamed '20160117_CHVE_44.1Khz-16bit_L._L_aligned.wav' to '20160117_CHVE_44.1Khz-16bit_L_aligned.wav'.
2025-02-01 14:20:15,983 - INFO - Renamed '20160117_CHVE_44.1Khz-16bit_R._R_aligned.wav' to '20160117_CHVE_44.1Khz-16bit_R_aligned.wav'.
2025-02-01 14:20:15,983 - INFO - Renamed 'AUD_L._L_aligned.wav' to 'AUD_L_aligned.wav'.
2025-02-01 14:20:16,859 - INFO - Merged 'destination/20160117_CHVE_44.1Khz-16bit_L_aligned.wav' and 'destination/20160117_CHVE_44.1Khz-16bit_R_aligned.wav' into stereo file 'destination/20160117_aligned_stereo.wav'.
2025-02-01 14:20:16,906 - INFO - Deleted intermediate mono files
2025-02-01 14:20:17,889 - INFO - Merged 'destination/AUD_L_aligned.wav' and 'destination/AUD_R_aligned.wav' into stereo file 'destination/AUD_aligned_stereo.wav'.
2025-02-01 14:20:17,932 - INFO - Deleted intermediate mono files
2025-02-01 14:20:18,804 - INFO - Merged 'destination/total._L_aligned.wav' and 'destination/total._R_aligned.wav' into stereo file 'destination/total._aligned_stereo.wav'.
2025-02-01 14:20:18,853 - INFO - Deleted intermediate mono files
2025-02-01 14:20:18,855 - INFO - Processing completed successfully
```
