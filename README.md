# Cello: Vial and microtube database for CBCS

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

<b> Make sure to build a new version of the `ce` executable before using `upload.py` to upload a new version!
</b>

## Backend