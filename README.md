## py4android

A simple Python3 script to build Python static libraries for Android. 

Of cause, by applying some changes easily, it would also work for shared libraries.

Tested on macOS 10.15 with NDK-r21 for Python 2.7.x. 

> If you dont work on macOS, you might have to change `BUILD` and `NDK_TOOLCHAIN` defined at front.

## Usage

```
> python3 py4android.py [-h] [--api API] --version VERSION ARCH [ARCH ...]

Build Python for Android.

positional arguments:
  ARCH               currently supports: armeabi-v7a armv8a x86 x86_64

optional arguments:
  -h, --help         show this help message and exit
  --api API          specify Android API level (default 21)
  --version VERSION  specify Python version string (directory Python-<VERSION> must exists at this working path)
```

* Download `py4android.py` along with [Python source code](https://www.python.org/downloads/release)
* Unzip your `Python-<VERSION>.tgz` to `Python-<VERSION>` (within the same directory)
* Hit commands like: `python3 py4android.py --api 21 --version 2.7.14 armeabi-v7a armv8a x86 x86_64`
  > assuming you have define `ANDROID_NDK_ROOT` in your environ
* Wait for compilations done, might take a while
* If everything works fine. The include files could be found at `prebuilt/android/<VERSION>/include`, and the (static) libraries could be found at `prebuilt/android/<VERSION>/libs/<ARCH>/libpython.a`
