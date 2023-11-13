# A Terminal Based Piano App
This is a simple piano app using the koelsynth library. It is tested and works fine on both Windows and Linux.

## Setup
A set of basic tools have to be installed on the system before we can run this script. It depends on the operating system.
It is better to install these before we setup a venv for the project.

### Linux
The app uses PyAudio for playing the audio. We will need to install development libraries for portaudio and python3. Package names depend on the distro.

The core of the Koelsynth library is written in C++. A compiler like g++ is required to build that.

In my Debian system, I installed these by the following command.

```bash
sudo apt install build-essential portaudio19-dev python3-dev
```

### Windows
PyAudio works without any extra step in windows.

We need a C++ compiler for building Koelsynth. Pybind11 library we use for the project suggested the following:
*Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/*

I installed the above and everything else went fine.

## Install Python Packages
We have to start by creating and enabling a venv.

Then install the requirements for this example.

```bash
pip install -r requirements.txt
```

## Run the app

```bash
python piano.py
```

Setting up the audio may take some time. It may also print some text coming from the PyAudio library. Please ignore those.

We have to wait for the message "Press enter to start:" and then press Enter.

Keys on the row below the numbers (q, w, e, etc) are used for playing the music.

## Quit the app

Control+C or Control+Z will not work. Use ` or ? to quit the app!
