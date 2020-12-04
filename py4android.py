#!/usr/bin/env python3

import os
import sys
import shutil
import argparse
import subprocess

BUILD = 'x86_64-apple-darwin'
NDK_ROOT = os.environ['ANDROID_NDK_ROOT']
NDK_TOOLCHAIN = '%s/toolchains/llvm/prebuilt/darwin-x86_64' % NDK_ROOT

ARCH_CONFIG = {
    # <arch>:      [ <eabi>,                    <macro>,       <minimum_api_level> ]
    'armeabi-v7a': ['armv7a-linux-androideabi', '__arm__',     16],
    'armv8a':      ['aarch64-linux-android',    '__aarch64__', 21],
    'x86':         ['i686-linux-android',       '__x86__',     16],
    'x86_64':      ['x86_64-linux-android',     '__x86_64__',  21]
}

def buildPython(version, api, arch, eabi):
    print('>>> building Python v%s for %s' % (version, arch))

    # common environ
    ENV = {
        'API': str(api),
        'AR': '%s/bin/%s-ar' % (NDK_TOOLCHAIN, eabi),
        'AS': '%s/bin/%s-as' % (NDK_TOOLCHAIN, eabi),
        'CC': '%s/bin/%s%d-clang' % (NDK_TOOLCHAIN, eabi, api),
        'CXX': '%s/bin/%s%d-clang++' % (NDK_TOOLCHAIN, eabi, api),
        'LD': '%s/bin/%s-ld' % (NDK_TOOLCHAIN, eabi),
        'RANLIB': '%s/bin/%s-ranlib' % (NDK_TOOLCHAIN, eabi),
        'STRIP': '%s/bin/%s-strip' % (NDK_TOOLCHAIN, eabi)
    }

    # configure params
    confArgs = [
        '--build', BUILD,
        '--host', eabi,
        #'--enable-optimizations',
        '--disable-ipv6',
        'ac_cv_file__dev_ptmx=no',
        'ac_cv_file__dev_ptc=no',
        'ac_cv_have_long_long_format=yes'
    ]
    subprocess.run(['./configure'] + confArgs, env = ENV, check = True)

    # copy pyconfig.h to pyconfig_<arch>.h
    shutil.copy('pyconfig.h', '%s/pyconfig_%s.h' % (destIncludePath, arch))

    # make clean && make -j4 <staticLib>
    staticLib = 'libpython%s.a' % version[:version.rindex('.')]
    subprocess.run(['make', 'clean'], check = True)
    subprocess.run(['make', '-j8', staticLib], env = ENV, check = True)

    # copy libpython<ver_short>.a to libs/<arch>/libpython.a
    shutil.copy(staticLib, '../prebuilt/android/%s/libs/%s/libpython.a' % (version, arch))

    print('<<< arch %s build done\n' % arch)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build Python for Android.')
    parser.add_argument('archs', type = str, metavar = 'ARCH', nargs = '+', help = 'currently supports: armeabi-v7a armv8a x86 x86_64')
    parser.add_argument('--api', type = int, default = 21, help = 'specify Android API level (default 21)')
    parser.add_argument('--version', type = str, required = True, help = 'specify Python version string (directory Python-<VERSION> must exists at this working path)')
    args = parser.parse_args()

    # check ndk root
    if (len(NDK_ROOT) == 0):
        print('define ${ANDROID_NDK_ROOT} in your env!')
        sys.exit(1)

    # check files
    api = args.api
    version = args.version
    if not os.path.exists('Python-%s' % version):
        print('directory Python-%s not found!' % version)
        sys.exit(1)

    # clear previous directory
    shutil.rmtree('prebuilt/android/%s' % version, ignore_errors = True)
    os.makedirs('prebuilt/android/%s/libs' % version)

    # change working directory
    os.chdir('Python-%s' % version)

    # copy Include directory
    destIncludePath = '../prebuilt/android/%s/include' % version
    shutil.copytree('Include', destIncludePath)

    # build specified archs
    firstShot = True
    pyconfigHeaderContent = []
    for arch in args.archs:
        if (arch in ARCH_CONFIG):
            cfg = ARCH_CONFIG[arch]
            # minimum api level to support arch
            fixedApi = cfg[2] if api < cfg[2] else api
            if api != fixedApi:
                print('>>> warning: set to API level %d (minimum support level) for arch %s' % (fixedApi, arch))
            # do build
            os.makedirs('../prebuilt/android/%s/libs/%s' % (version, arch))
            buildPython(version, fixedApi, arch, cfg[0])
            # append to header
            pyconfigHeaderContent.append('#%s defined(%s)\n#include "pyconfig_%s.h"\n' % ('if' if firstShot else 'elif', cfg[1], arch))
            firstShot = False
        else:
            print('unrecognized arch %s' % arch)
            sys.exit(1)

    if (len(pyconfigHeaderContent) > 0):
        pyconfigHeaderContent.append('#endif\n')

    # create combined pyconfig.h
    fd = os.open('../prebuilt/android/%s/include/pyconfig.h' % version, os.O_RDWR | os.O_CREAT)
    os.write(fd, bytes(''.join(pyconfigHeaderContent), encoding='utf-8'))
    os.close(fd)
