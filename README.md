# Cello: Vial and microtube database for CBCS

## Requirements
The frontend currently only builds on `Python 3.8`, with required package versions listed in `requirements.txt`. Install the required versions with your favourite package manager.

## Frontend
### PyInstaller How-To
Currently only builds on `Python 3.8`, with required package versions listed in `requirements.txt`.
With `frontend` as current directory, build the main Cello executable with:

    <pyinstaller> main.spec
which will build the main executable `ce`(.exe)
</br>or

    <pyinstaller> launcher.spec
which will build the launcher executable `cello`(.exe).

Substitute `<pyinstaller>` with your local appropriate PyInstaller module (possibly `py -3.8 -m PyInstaller` or just `python3 pyinstaller`, case sensitive module names).

<b> Make sure to build a new version of the `ce` executable before using `upload.py` to upload a new version.
</b>

### Using `upload.py`

Invoking `python3 upload.py` should give the following output:
    
    $ .../cello/frontend$ python3 upload.py
    Please specify path(s) to executables and/or version data files
    -t <path>: path to main executable
    -v <path>: path to version data file
    -l <path>: path to launcher executable

To use `upload.py`, use these options to provide files to upload.

If you have built the main executable and launcher from the /frontend directory using *pyinstaller*, sample usage would look like this:

    python3 upload.py -t dist/ce.exe -l dist/cello.exe

Invoking this prompts a login verification from the server, after which the files are sent to the server.

<b>Remember to substitute `python3` with your appropriate `Python 3.8` command.
</b>

## Backend

## Download Launcher
To download the launcher executable from the server, navigate to:

    <baseUrl>getCelloLauncher/Windows/cello.exe
    <baseUrl>getCelloLauncher/Linux/cello
    <baseUrl>getCelloLauncher/Darwin/cello

using your favourite internet browser.