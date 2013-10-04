#!/usr/bin/env python3

# Copyright 2013 Jussi Pakkanen

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, pickle, os, shutil, subprocess, gzip, platform

class InstallData():
    def __init__(self, prefix, depfixer, dep_prefix):
        self.prefix = prefix
        self.targets = []
        self.depfixer = depfixer
        self.dep_prefix = dep_prefix
        self.headers = []
        self.man = []
        self.data = []
        self.po_package_name = ''
        self.po = []

def do_install(datafilename):
    ifile = open(datafilename, 'rb')
    d = pickle.load(ifile)
    destdir_var = 'DESTDIR'
    if destdir_var in os.environ:
        if d.prefix[0] == '/':
            subdir = d.prefix[1:]
        else:
            subdir = d.prefix
        d.prefix = os.path.join(os.environ[destdir_var], subdir)
    install_targets(d)
    install_headers(d)
    install_man(d)
    install_data(d)
    install_po(d)

def install_po(d):
    packagename = d.po_package_name
    for f in d.po:
        srcfile = f[0]
        localedir = f[1]
        languagename = f[2]
        outfile = os.path.join(d.prefix, localedir, languagename, 'LC_MESSAGES',
                               packagename + '.mo')
        os.makedirs(os.path.split(outfile)[0], exist_ok=True)
        shutil.copyfile(srcfile, outfile)
        shutil.copystat(srcfile, outfile)
        print('Installing %s to %s.' % (srcfile, outfile))

def install_data(d):
    for i in d.data:
        fullfilename = i[0]
        outfilerel = i[1]
        outdir = os.path.join(d.prefix, os.path.split(outfilerel)[0])
        outfilename = os.path.join(outdir, os.path.split(outfilerel)[1])
        os.makedirs(outdir, exist_ok=True)
        print('Installing %s to %s.' % (fullfilename, outdir))
        shutil.copyfile(fullfilename, outfilename)
        shutil.copystat(fullfilename, outfilename)

def install_man(d):
    for m in d.man:
        outfileroot = m[1]
        outfilename = os.path.join(d.prefix, outfileroot)
        full_source_filename = m[0]
        outdir = os.path.split(outfilename)[0]
        os.makedirs(outdir, exist_ok=True)
        print('Installing %s to %s.' % (full_source_filename, outdir))
        if outfilename.endswith('.gz') and not full_source_filename.endswith('.gz'):
            open(outfilename, 'wb').write(gzip.compress(open(full_source_filename, 'rb').read()))
        else:
            shutil.copyfile(full_source_filename, outfilename)
        shutil.copystat(full_source_filename, outfilename)

def install_headers(d):
    for t in d.headers:
        fullfilename = t[0]
        outdir = os.path.join(d.prefix, t[1])
        fname = os.path.split(fullfilename)[1]
        outfilename = os.path.join(outdir, fname)
        print('Installing %s to %s' % (fname, outdir))
        os.makedirs(outdir, exist_ok=True)
        shutil.copyfile(fullfilename, outfilename)
        shutil.copystat(fullfilename, outfilename)

def is_elf_platform():
    platname = platform.system().lower()
    if platname == 'darwin' or platname == 'windows':
        return False
    return True

def install_targets(d):
    for t in d.targets:
        fname = t[0]
        outdir = os.path.join(d.prefix, t[1])
        aliases = t[2]
        outname = os.path.join(outdir, os.path.split(fname)[-1])
        should_strip = t[3]
        print('Installing %s to %s' % (fname, outname))
        os.makedirs(outdir, exist_ok=True)
        shutil.copyfile(fname, outname)
        shutil.copystat(fname, outname)
        if should_strip:
            print('Stripping target')
            ps = subprocess.Popen(['strip', outname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdo, stde) = ps.communicate()
            if ps.returncode != 0:
                print('Could not strip file.\n')
                print('Stdout:\n%s\n' % stdo.decode())
                print('Stderr:\n%s\n' % stde.decode())
                sys.exit(1)
        printed_symlink_error = False
        for alias in aliases:
            try:
                os.symlink(fname, os.path.join(outdir, alias))
            except NotImplementedError:
                if not printed_symlink_error:
                    print("Symlink creation does not work on this platform.")
                    printed_symlink_error = True
        install_rpath = ''
        if is_elf_platform():
            p = subprocess.Popen([d.depfixer, outname, install_rpath], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
            (stdo, stde) = p.communicate()
            if p.returncode != 0:
                print('Could not fix dependency info.\n')
                print('Stdout:\n%s\n' % stdo.decode())
                print('Stderr:\n%s\n' % stde.decode())
                sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Installer script for Meson. Do not run on your own, mmm\'kay?')
        print('%s [install info file]' % sys.argv[0])
    datafilename = sys.argv[1]
    do_install(datafilename)

