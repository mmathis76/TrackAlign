# Installation steps on **Linux**

## Python 3 (incl. pip)

Install the Python 3 distribution depending on your OS (your Linux distro might already come with Python 3 installed)

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

# Specific installation steps on **Windows 11**

Download and install Anaconda (https://www.anaconda.com/download) or an alternative Python distribution of your choice 

When done, make sure that pip is installed

`python -m ensurepip --upgrade`   

Open Powershell as Admin and run 

`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

The official pyenv package doesn't work on Windows. However, there is an equivalent package named pyenv-win. 
Install it with Powershell as Admin

`Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"`

Verify whether or not pyenv works by listing the supported Python versions

```
pyenv --version
pyenv install -l
```
Install the latest supported point release for Python 3.11. (This was the supported Python version at the time of the latest Audalign release.)

`pyenv install 3.11`

Set the local and/or global Python environment to 3.11.9

```
pyenv local 3.11.9
pyenv global 3.11.9
```

Upgrade pip and install the audalign package

```
%USERPROFILE%\.pyenv\pyenv-win\versions\3.11.9\python3.11.exe -m pip install --upgrade pip
%USERPROFILE%\.pyenv\pyenv-win\versions\3.11.9\python3.11.exe -m pip install audalign
```

To compile the optional packages, you'll have to install some C++ compilers for the Windows 64 platform. 
Windows doesn't come with C++ installed out of the box.

Download the setup file for VisualStudio 2022 Community edition (via PowerShell and winget)

`winget install Microsoft.VisualStudio.2022.Community --silent --override "--wait --quiet --add ProductLang En-us --add Microsoft.VisualStudio.Workload.NativeDesktop --includeRecommended"`

Install Visual Studio Build Tools

In addition, please also install clang+llvm (https://github.com/llvm/llvm-project/releases/) from the LLVM project.

Add it to your user's Windows environment variables

![CLANG_HOME](https://github.com/user-attachments/assets/25ff6997-3116-4993-9c70-c7d491e4b850)
![CLANG_PATH](https://github.com/user-attachments/assets/1fb75aaa-1843-4206-9ae7-d378cec16389)

Reboot your machine and log into Windows 11 again.

Now, open your shell again and install the remaining dependencies

```
%USERPROFILE%\.pyenv\pyenv-win\versions\3.11.9\python3.11.exe -m pip install audalign[visrecognize]
%USERPROFILE%\.pyenv\pyenv-win\versions\3.11.9\python3.11.exe -m pip install pydub
```

# Building a stand-alone exe version (incl Python 3.11 and all dependencies) on Windows 11 

```
pip install --upgrade nuitka
cd %USERPROFILE%\Documents\Projects\TrackAlign
%USERPROFILE%\.pyenv\pyenv-win\versions\3.11.9\python3.11.exe -m nuitka --standalone --no-deployment-flag=self-execution --onefile --include-package=audalign --include-package=pydub .\trackalign.py
```

> Please note that on the one hand compiling the script and all of its dependencies will render the distribution and installation of the application easier.
On the other hand, the compilation of the code and all of its dependencies will lead to an overhead in terms of memory usage. 
Rule of thumb: This will double the requirements in term of RAM. 
16 GiB of RAM are recommended with the stand-alone *.exe version. 

Please note that the correlation algorithms are supposedly the most accurate ones. They're also consuming less memory than "fingerprinting".

In practise, depending on the specific source files, one algorithm might be more accurate than the others.

# Program parameters:

## Required Parameters

### Input Directory (-i, --input)
* Path to the directory containing WAV files to be processed
* Contains both the reference file and files to be aligned
* Only processes WAV files in the root directory (subdirectories are ignored)

### Reference File (-r, --reference)
* Basename (filename) of the reference WAV file
* This file serves as the timing reference for aligning other files
* Must be located in the input directory
* Can be either mono or stereo

### Temporary Directory (-t, --temp)
* Path where intermediate mono files are stored
* Used for storing split channels from stereo files
* Stores both reference and input file channels during processing
* Files in this directory are reused if they already exist

### Destination Directory (-o, --destination)
* Path where the final aligned files are saved
* Contains the alignment log file
* Stores the final merged stereo files after alignment
* Intermediate aligned mono files are created here before merging

## Optional Parameters

### Channel Mode (-c, --channel)
* Specifies which channel to use for alignment: 'L' (left), 'R' (right), or 'auto'
* In 'auto' mode, left channels are aligned with left, right with right
* When using 'L' or 'R', all channels are aligned against the specified reference channel
* Particularly useful when one channel of the reference might be silent or corrupted

### Algorithm (-a, --algorithm)
* Specifies the alignment algorithm to use
* Available options: 'fingerprint', 'correlation', 'correlation_spectrogram', 'visual'
* Default: 'fingerprint'

### Accuracy (-acc, --accuracy)
* Sets the accuracy level for the fingerprint algorithm
* Integer value that affects the precision of audio fingerprinting
* Default value: 3
* Higher values increase accuracy but require more processing time

# Usage example:

```
~/.pyenv/versions/3.11.10/bin/python ./trackalign.py -i bak/ -t temp/ -o destination -r reference.wav -c auto -a fingerprint -acc 5
```
