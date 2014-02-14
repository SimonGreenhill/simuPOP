#!/usr/bin/env python

#
# $File: setup.py $
# $LastChangedDate$
# $Rev$
#
# This file is part of simuPOP, a forward-time population genetics
# simulation environment. Please visit http://simupop.sourceforge.net
# for details.
#
# Copyright (C) 2004 - 2010 Bo Peng (bpeng@mdanderson.org)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
simuPOP installer: 

A standard simuPOP package has boost and needed SWIG-generated wrapper files so
you should be able to run this script and install simuPOP using:
  > python setup.py install

If your copy of simuPOP is checked out from the subversion server, you will
need to download a supported version of boost (see variable boost_versions
below) and uncompress it under the simuPOP source directory. You also need to
install swig >= 1.3.35 for the generation of Python wrapper files. Please see
http://simupop.sourceforge.net/main/GetInvolved for details.

"""
import os, sys, platform, shutil, glob, re, tempfile, subprocess
import distutils.sysconfig
USE_DISTRIBUTE = False
try:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages, Extension
    USE_DISTRIBUTE = True
except ImportError:
    from distutils.core import setup, Extension
    print("fail to import distribute/setuptools, build the program with distutils")

if sys.version_info[0] <= 2 and sys.version_info[1] <= 4:
    print("simuPOP supports Python version 2.5 or higher, including Python 3.x. Please upgrade your Python installation and try again.")
    sys.exit(1)

# Change this to False if you would like to compile simuPOP without openMP support
USE_OPENMP = True

if os.name == 'nt':
    VS9PATH =  os.environ.get('VS90COMNTOOLS')
    if VS9PATH is None or not os.path.isfile(VS9PATH.replace('Common7\\Tools\\','VC\\lib\\vcomp.lib')):
        USE_OPENMP = False
else:
    p = subprocess.Popen('gcc -v', shell=True,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        close_fds=True)
    fin, fout, ferr = (p.stdin, p.stdout, p.stderr)
    output = ferr.readlines()[-1].decode('utf8')
    try:
        version = re.match('.*gcc version\s*(\d+).(\d+).(\d+).*', output).groups()
        if int(version[0]) < 4 or int(version[1]) < 2:
            print('Support for openMP is turned off because version %s.%s.%s of gcc does not support this feature' % version)
            USE_OPENMP = False
        if int(version[0]) == 4 and int(version[1]) == 2 and int(version[2]) == 1 and 'LLVM' in output:
            print('Support for openMP is turned off because of a bug in LLVM-gcc version 4.2.1.')
            USE_OPENMP = False
    except:
        print('Can not obtain version of gcc, and openMP is disable')
        USE_OPENMP = False

USE_ICC = False
if distutils.sysconfig.get_config_var('CC') is not None:
    USE_ICC = 'icc' in distutils.sysconfig.get_config_var('CC')

# simuPOP works with these boost versions. Newer versions will be used if these
# versions are not available, and will most likely work just fine.
boost_versions = ['1_35_0', '1_36_0', '1_37_0', '1_38_0', '1_39_0', '1_40_0',
    '1_42_0', '1_43_0', '1_44_0', '1_45_0', '1_46_0', '1_46_1', '1_47_0',
    '1_48_0', '1_49_0']
invalid_boost_versions = ['1_41_0']

included_version = [x for x in boost_versions if os.path.isdir('boost_' + x)]
invalid_version = [x for x in invalid_boost_versions if os.path.isdir('boost_' + x)]
unsupported_version = [x for x in glob.glob('boost_*') if os.path.isdir(x) \
    and x[6:] not in invalid_version + included_version]

boost_dir = ''
if len(included_version) > 0:
    boost_dir = 'boost_' + included_version[-1]  # use the latest version
elif len(invalid_version) > 0:
    print('This version of boost is known to cause problems to simuPOP: ' + ', '.join(invalid_version))

if boost_dir == '' and len(unsupported_version) > 0:
    print('This version of boost is not tested. It may or may not work: ' + ', '.join(unsupported_version))
    boost_dir = unsupported_version[-1]  # use the latest version

if boost_dir == '':
    def downloadProgress(count, blockSize, totalSize):
        perc = count * blockSize * 100 // totalSize
        if perc > downloadProgress.counter: 
            sys.stdout.write('.' * (perc - downloadProgress.counter))
            downloadProgress.counter = perc
        sys.stdout.flush()
    import urllib
    import tarfile
    downloadProgress.counter = 0
    try:
        BOOST_URL = 'http://hivelocity.dl.sourceforge.net/project/boost/boost/1.49.0/boost_1_49_0.tar.gz'
        sys.stdout.write('Downloading boost C++ library 1.49.0 ')
        sys.stdout.flush()
        if not os.path.isfile('boost_1_49_0.tar.gz'):
            urllib.urlretrieve(BOOST_URL, 'boost_1_49_0.tar.gz', downloadProgress)
        sys.stdout.write('\n')
        # extract needed files
        with tarfile.open('boost_1_49_0.tar.gz', 'r:gz') as tar:
            files = [h for h in tar.getmembers() if h.name.startswith('boost_1_49_0/boost') \
                or h.name.startswith('boost_1_49_0/libs/iostreams') \
                or h.name.startswith('boost_1_49_0/libs/serialization') \
                or h.name.startswith('boost_1_49_0/libs/regex') \
                or h.name.startswith('boost_1_49_0/libs/detail') ]
            sys.stdout.write('Extracting %d files\n' % len(files))
            tar.extractall(members=files)
        EMBEDED_BOOST = True
        boost_dir = 'boost_1_49_0'
    except Exception as e:
        print(e)
        print('The boost C++ library version 1.49.0 is not found under the current directory. Will try to use the system libraries.')
        print('Cannot find or download an useful version of boost header files.')
        print('Please download boost from http://www.boost.org and unpack it under the simuPOP directory')
        sys.exit(1)
elif len(included_version + unsupported_version) > 1:
    print('Using boost version: %s' % boost_dir)

boost_include_dir = boost_dir
boost_serialization_dir = os.path.join(boost_dir, 'libs', 'serialization', 'src')
boost_iostreams_dir = os.path.join(boost_dir, 'libs', 'iostreams', 'src')
boost_regex_dir = os.path.join(boost_dir, 'libs', 'regex', 'src')

# if you need to use full path name for swig, change it here.
SWIG = 'swig'

############################################################################
#
# THE FOLLOWING IS NOT SUPPOSED TO BE MODIFIED
#
############################################################################

from distutils.sysconfig import get_config_var
try:
   from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
   from distutils.command.build_py import build_py


def swig_version():
    ''' get the version of swig '''
    fout = subprocess.Popen(SWIG + ' -version', shell=True, stdout=subprocess.PIPE).stdout
    output = fout.readlines()[1].decode('utf8')
    #
    try:
        version = re.match('SWIG Version\s*(\d+).(\d+).(\d+).*', output).groups()
    except:
        print('Can not obtain swig version, please install swig')
        sys.exit(1)
    return [int(x) for x in version]


def simuPOP_version():
    import simuPOP_version
    SIMUPOP_VER = simuPOP_version.SIMUPOP_VER
    SIMUPOP_REV = simuPOP_version.SIMUPOP_REV
    if SIMUPOP_VER.endswith('svn'):
        rev = SIMUPOP_REV
        try:
            fout = subprocess.Popen('svnversion .', shell=True, stdout=subprocess.PIPE).stdout
            rev = fout.readline().strip()
            if ':' in rev:
                rev = rev.split(':')[1]
            rev = rev.rstrip('M')
        except:
            pass
        # if 'svnversion' exists and the revision has changed
        if rev != '':
            SIMUPOP_REV = rev
    return SIMUPOP_VER, SIMUPOP_REV


def replaceIntHeader(file):
    ''' Replace "#include <stdint.h>" with "#include <inttypes.h>"
        Try to keep time stamp unchanged '''
    # save file modification time
    time = os.path.getmtime(file)
    # create a temp file
    tmp, name = tempfile.mkstemp()
    input = open(file)
    output = open(name, 'w')
    for line in input.readlines():
        if '#include <stdint.h>' in line:
            output.write('#include <inttypes.h>  /* no stdint.h is found so we use inttypes.h instead */\n')
        else:
            output.write(line)
    output.close()
    input.close()
    # replace file with temp file
    shutil.copyfile(name, file)
    os.remove(name)    
    # restore old file modification time
    try:
        os.utime(file, (-1, time))
    except:
        pass

#
# SOURCE FILES
#

HEADER_FILES = [
    'mutant_vector.h',
    'simuPOP_cfg.h',
    'utility.h',
    'genoStru.h',
    'individual.h',
    'population.h',
    'simulator.h',
    'mating.h',
    'operator.h',
    'initializer.h',
    'migrator.h',
    'outputer.h',
    'selector.h',
    'penetrance.h',
    'qtrait.h',
    'stator.h',
    'mutator.h',
    'transmitter.h',
    'tagger.h',
    'pedigree.h',
    'virtualSubPop.h',
    'sandbox.h',
]

SOURCE_FILES = [
    'utility.cpp',
    'genoStru.cpp',
    'individual.cpp',
    'population.cpp',
    'simulator.cpp',
    'mating.cpp',
    'operator.cpp',
    'initializer.cpp',
    'migrator.cpp',
    'outputer.cpp',
    'selector.cpp',
    'penetrance.cpp',
    'qtrait.cpp',
    'stator.cpp',
    'mutator.cpp',
    'transmitter.cpp',
    'tagger.cpp',
    'pedigree.cpp',
    'virtualSubPop.cpp',
    'sandbox.cpp',
#    'main.cpp',
]

# since it is troublesome to link to external gsl library,
# I embed some GSL files with simuPOP. 
LIB_FILES = [ 
    'gsl/sys/infnan.c',
    'gsl/sys/coerce.c',
    'gsl/sys/fdiv.c',
    'gsl/sys/pow_int.c',
    'gsl/sys/fcmp.c',
    'gsl/sys/log1p.c',
    'gsl/sys/invhyp.c',
    'gsl/complex/math.c',
    'gsl/specfunc/beta.c',
    'gsl/specfunc/psi.c',
    'gsl/specfunc/trig.c',
    'gsl/specfunc/exp.c',
    'gsl/specfunc/expint.c',
    'gsl/specfunc/log.c',
    'gsl/specfunc/erfc.c',
    'gsl/specfunc/zeta.c',
    'gsl/specfunc/elementary.c',
    'gsl/specfunc/gamma.c',
    'gsl/specfunc/gamma_inc.c',
    'gsl/rng/borosh13.c',
    'gsl/rng/fishman2x.c',
    'gsl/rng/mt.c',
    'gsl/rng/rand.c',
    'gsl/rng/ranmar.c',
    'gsl/rng/types.c',
    'gsl/rng/cmrg.c',
    'gsl/rng/gfsr4.c',
    'gsl/rng/r250.c',
    'gsl/rng/random.c',
    'gsl/rng/rng.c',
    'gsl/rng/uni32.c',
    'gsl/rng/coveyou.c',
    'gsl/rng/knuthran2.c',
    'gsl/rng/ran0.c',
    'gsl/rng/randu.c',
    'gsl/rng/slatec.c',
    'gsl/rng/uni.c',
    'gsl/rng/default.c',
    'gsl/rng/knuthran.c',
    'gsl/rng/ran1.c',
    'gsl/rng/ranf.c',
    'gsl/rng/taus113.c',
    'gsl/rng/vax.c',
    'gsl/rng/file.c',
    'gsl/rng/lecuyer21.c',
    'gsl/rng/ran2.c',
    'gsl/rng/ranlux.c',
    'gsl/rng/taus.c',
    'gsl/rng/waterman14.c',
    'gsl/rng/fishman18.c',
    'gsl/rng/minstd.c',
    'gsl/rng/ran3.c',
    'gsl/rng/ranlxd.c',
    'gsl/rng/transputer.c',
    'gsl/rng/zuf.c',
    'gsl/rng/fishman20.c',
    'gsl/rng/mrg.c',
    'gsl/rng/rand48.c',
    'gsl/rng/ranlxs.c',
    'gsl/rng/tt.c',
    'gsl/rng/knuthran2002.c',
    'gsl/randist/binomial.c',
    'gsl/randist/binomial_tpe.c',
    'gsl/randist/beta.c',
    'gsl/randist/exponential.c',
    'gsl/randist/geometric.c',
    'gsl/randist/nbinomial.c',
    'gsl/randist/poisson.c',
    'gsl/randist/multinomial.c',
    'gsl/randist/chisq.c',
    'gsl/randist/gauss.c',
    'gsl/randist/gausszig.c',
    'gsl/randist/gamma.c',
    'gsl/cdf/gammainv.c',
    'gsl/cdf/binomial.c',
    'gsl/cdf/beta.c',
    'gsl/cdf/betainv.c',
    'gsl/cdf/gauss.c',
    'gsl/cdf/gaussinv.c',
    'gsl/cdf/chisq.c',
    'gsl/cdf/chisqinv.c',
    'gsl/cdf/gamma.c',
    'gsl/cdf/poisson.c',
    'gsl/error.c' 
] + [x for x in glob.glob(os.path.join(boost_serialization_dir, '*.cpp')) if 'xml' not in x and 'binary' not in x]\
  + [x for x in glob.glob(os.path.join(boost_iostreams_dir, '*.cpp')) if 'bzip' not in x]\
  + glob.glob(os.path.join(boost_regex_dir, '*.cpp'))


GSL_FILES = [
    'gsl/error.c', 
    'gsl/sys/infnan.c',
    'gsl/sys/coerce.c',
    'gsl/sys/fdiv.c',
    'gsl/sys/pow_int.c',
    'gsl/sys/fcmp.c',
    'gsl/sys/log1p.c',
    'gsl/sys/invhyp.c',
    'gsl/sys/expm1.c',
    'gsl/complex/math.c',
    'gsl/specfunc/beta.c',
    'gsl/specfunc/elementary.c',
    'gsl/specfunc/erfc.c',
    'gsl/specfunc/exp.c',
    'gsl/specfunc/expint.c',
    'gsl/specfunc/log.c',
    'gsl/specfunc/psi.c',
    'gsl/specfunc/gamma.c',
    'gsl/specfunc/gamma_inc.c',
    'gsl/specfunc/trig.c',
    'gsl/specfunc/zeta.c',
    'gsl/cdf/beta.c',
    'gsl/cdf/betainv.c',
    'gsl/cdf/binomial.c',
    'gsl/cdf/gauss.c',
    'gsl/cdf/gaussinv.c',
    'gsl/cdf/exponential.c',
    'gsl/cdf/exponentialinv.c',
    # pdf functions for gamma, binomial, poisson and beta distributions are copied to gsl.i
    # to avoid subsequent inclusion of RNG related functions.
    #'gsl/randist/gamma.c',
    #'gsl/randist/binomial.c',
    #'gsl/randist/beta.c',
    #'gsl/randist/poisson.c',
    'gsl/cdf/gamma.c',
    'gsl/cdf/gammainv.c',
    'gsl/cdf/chisq.c',
    'gsl/cdf/chisqinv.c',
    'gsl/cdf/poisson.c',
]

# build zlib from source for windows system to avoid distributing zlib1.dll
# along with simuPOP.
if os.name == 'nt':
    LIB_FILES.extend([os.path.join('win32', 'zlib-1.2.3', x) for x in [
        'adler32.c',
        'compress.c',
        'crc32.c',
        'gzio.c',
        'uncompr.c',
        'deflate.c',
        'trees.c',
        'zutil.c',
        'inflate.c',
        'infback.c',
        'inftrees.c',
        'inffast.c'
        ]
    ])


SWIG_CPP_FLAGS = '-O -templatereduce -shadow -python -c++ -keyword -nodefaultctor -w-503,-312,-511,-362,-383,-384,-389,-315,-509,-525 -Ibuild'
SWIG_CC_FLAGS = '-python -keyword'

if sys.version_info[0] == 3:
    SWIG_CPP_FLAGS += ' -py3'
    SWIG_CC_FLAGS += ' -py3'

SWIG_RUNTIME_FLAGS = '-python -external-runtime'
# python setup.py reads py_modules from src so we have to produce simuPOP_std.py
# etc to this directory.
SWIG_OUTDIR = 'src'
if not os.path.isdir('build'):
    os.mkdir('build')
                
MACROS = {
    'std':    [('SIMUPOP_MODULE', 'simuPOP_std'), 
                ('_SECURE_SCL', 1), ('_HAS_ITERATOR_DEBUGGING', 0)],
    'op':     [('SIMUPOP_MODULE', 'simuPOP_op'), ('OPTIMIZED', None), 
                ('NDEBUG', None), ('BOOST_UBLAS_NDEBUG', None),
                ('_SECURE_SCL', 0), ('_HAS_ITERATOR_DEBUGGING', 0)],
    'la':     [('SIMUPOP_MODULE', 'simuPOP_la'), ('LONGALLELE', None), 
                ('_SECURE_SCL', 1), ('_HAS_ITERATOR_DEBUGGING', 0)],
    'laop':   [('SIMUPOP_MODULE', 'simuPOP_laop'), ('LONGALLELE', None),
                ('OPTIMIZED', None),('NDEBUG', None), ('BOOST_UBLAS_NDEBUG', None),
                ('_SECURE_SCL', 0), ('_HAS_ITERATOR_DEBUGGING', 0)],
    'ba':     [('SIMUPOP_MODULE', 'simuPOP_ba'), ('BINARYALLELE', None), 
                ('_SECURE_SCL', 1), ('_HAS_ITERATOR_DEBUGGING', 0)],
    'baop':   [('SIMUPOP_MODULE', 'simuPOP_baop'), ('BINARYALLELE', None),
                ('OPTIMIZED', None),('NDEBUG', None), ('BOOST_UBLAS_NDEBUG', None),
                ('_SECURE_SCL', 0), ('_HAS_ITERATOR_DEBUGGING', 0)],
    'mu':     [('SIMUPOP_MODULE', 'simuPOP_mu'), ('MUTANTALLELE', None), 
                ('_SECURE_SCL', 1), ('_HAS_ITERATOR_DEBUGGING', 0)],
    'muop':   [('SIMUPOP_MODULE', 'simuPOP_muop'), ('MUTANTALLELE', None),
                ('OPTIMIZED', None),('NDEBUG', None), ('BOOST_UBLAS_NDEBUG', None),
                ('_SECURE_SCL', 0), ('_HAS_ITERATOR_DEBUGGING', 0)],
    'lin':    [('SIMUPOP_MODULE', 'simuPOP_lin'), ('LINEAGE', None), 
                ('_SECURE_SCL', 1), ('_HAS_ITERATOR_DEBUGGING', 0)],
    'linop':  [('SIMUPOP_MODULE', 'simuPOP_linop'), ('LINEAGE', None),
                ('OPTIMIZED', None),('NDEBUG', None), ('BOOST_UBLAS_NDEBUG', None),
                ('_SECURE_SCL', 0), ('_HAS_ITERATOR_DEBUGGING', 0)],
 
}
 
WRAP_INFO = {
    'std':    ['src/simuPOP_std_wrap.cpp', 'src/simuPOP_std.i', ''],
    'op':     ['src/simuPOP_op_wrap.cpp', 'src/simuPOP_op.i', '-DOPTIMIZED'],
    'la':     ['src/simuPOP_la_wrap.cpp', 'src/simuPOP_la.i', '-DLONGALLELE'],
    'laop':   ['src/simuPOP_laop_wrap.cpp', 'src/simuPOP_laop.i', '-DLONGALLELE -DOPTIMIZED'],
    'ba':     ['src/simuPOP_ba_wrap.cpp', 'src/simuPOP_ba.i', '-DBINARYALLELE'],
    'baop':   ['src/simuPOP_baop_wrap.cpp', 'src/simuPOP_baop.i', '-DBINARYALLELE -DOPTIMIZED'],
    'mu':     ['src/simuPOP_mu_wrap.cpp', 'src/simuPOP_mu.i', '-DMUTANTALLELE'],
    'muop':   ['src/simuPOP_muop_wrap.cpp', 'src/simuPOP_muop.i', '-DMUTANTALLELE -DOPTIMIZED'],
    'lin':    ['src/simuPOP_lin_wrap.cpp', 'src/simuPOP_lin.i', '-DLINEAGE'],
    'linop':  ['src/simuPOP_linop_wrap.cpp', 'src/simuPOP_linop.i', '-DLINEAGE -DOPTIMIZED'],
}

if os.name == 'nt':
    # NOTE:
    # In theory, we should distribute
    # 1. 'msvcr80.dll' for simuPOP 1.5.x for python 2.5 and earlier. MS Visual
    #     studio 2003.net should be used.
    # 2. 'msvcr90.dll' should be distributed for simuPOP 1.5.x for python 2.6
    #     and later.
    # 3. These two files are for simuPOP 1.6.x, for python 2.6 and later.
    # We do not distribute msvcr80.dll because there is little need to support
    # python 2.5 under windows.
    PACKAGE_DATA = ['vcomp90.dll', 'msvcr90.dll']
else:
    PACKAGE_DATA = []

DESCRIPTION = """
simuPOP is a forward-time population genetics simulation environment.
The core of simuPOP is a scripting language (Python) that provides 
a large number of objects and functions to manipulate populations, 
and a mechanism to evolve populations forward in time. Using this 
R/Splus-like environment, users can create, manipulate and evolve 
populations interactively, or write a script and run it as a batch 
file. Owing to its flexible and extensible design, simuPOP can simulate
large and complex evolutionary processes with ease. At a more 
user-friendly level, simuPOP provides an increasing number of built-in
scripts that perform simulations ranging from implementation of basic 
population genetics models to generating datasets under complex 
evolutionary scenarios.
"""
            

#
def ModuInfo(modu, SIMUPOP_VER, SIMUPOP_REV):
    #
    boost_inc_path = boost_include_dir
    boost_lib_names = []
    boost_lib_path = None
    res = {}
    res['src'] =  ['src/simuPOP_' + modu + '_wrap.cpp']
    for src in SOURCE_FILES:
        res['src'].append('build/%s/%s' % (modu, src))
    res['src'].extend(LIB_FILES)
    # lib
    if os.name == 'nt':    # Windows, build zlib from source
        res['libraries'] = []
    else:
        res['libraries'] = ['stdc++', 'z']
        if USE_OPENMP:
            if USE_ICC:
                res['libraries'].append('iomp5')
                res['libraries'].append('tbb')
            else:
                res['libraries'].append('gomp')
    res['libraries'].extend(boost_lib_names)
    res['include_dirs'] = ['.', 'gsl', boost_inc_path]
    res['library_dirs'] = ['build']
    if os.name == 'nt':
        # I have a portable stdint.h for msvc, to avoid distributing
        # zdll1.dll, I also build zlib from source
        res['include_dirs'].extend(['win32', 'win32/zlib-1.2.3'])
        # zdll.lib is under win32
        res['library_dirs'].append('win32')
    if os.name == 'nt':
        # msvc does not have O3 option, /GR is to fix a C4541 warning
        # /EHsc is for VC exception handling,
        # /wd4819 disables warning messages for non-unicode character in boost/uitlity/enable_if.hpp
        # /wd4996 disables warning messages for unsafe function call in boost/serialization
        # /wd4068 disables warning messages for unknown pragma set by gcc 
        res['extra_compile_args'] = ['/O2', '/GR', '/EHsc', '/wd4819', '/wd4996', '/wd4068'] 
        # Enable openMP if USE_OPENMP = True
        if USE_OPENMP:
            res['extra_compile_args'].append('/Qopenmp' if USE_ICC else '/openmp')   
    else:
        res['extra_compile_args'] = ['-O3', '-Wall', '-Wno-unknown-pragmas', '-Wno-unused-parameter']
        if not USE_ICC:   # for gcc, turn on extra warning message
            res['extra_compile_args'].append('-Wextra')
        if USE_OPENMP:
            res['extra_compile_args'].append('-openmp' if USE_ICC else '-fopenmp')
    # if Intel ICC is used, turn off remark 981
    if USE_ICC:
        res['extra_compile_args'].extend(['-wd981', '-wd191'])
    # define_macros (deep copy)
    res['define_macros'] = [x for x in MACROS[modu]]
    res['define_macros'].extend([('SIMUPOP_VER', SIMUPOP_VER), ('SIMUPOP_REV', SIMUPOP_REV)])
    if os.name == 'nt':
        res['define_macros'].extend([('BOOST_ALL_NO_LIB', None),
            ('NO_ZLIB', 0), ('NO_BZIP' , 1),
            # this one disables a lot of warnings about VC Checked iterators.
            #('_SCL_SECURE_NO_WARNINGS', None)
            ])
    else:
        if not USE_ICC:
            if USE_OPENMP:
                res['define_macros'].append(('_GLIBCXX_PARALLEL', None))
    res['undef_macros'] = []
    return res


############################################################################
#
# Build extensions
#
############################################################################
import filecmp

if os.name == 'nt':    # Windows
    # copy platform dependent dll files
    machine = platform.uname()[4].lower()
    if machine == '':  # have to guess
        machine = 'x86'
    shutil.copy('win32/%s/vcomp90.dll' % machine, 'src/vcomp90.dll')
    shutil.copy('win32/%s/msvcr90.dll' % machine, 'src/msvcr90.dll')

if __name__ == '__main__':
    SIMUPOP_VER, SIMUPOP_REV = simuPOP_version()
    # create source file for each module
    MODULES = ['std', 'op', 'la', 'laop', 'ba', 'baop', 'mu', 'muop', 'lin', 'linop']
    #
    # Generate Wrapping files
    #
    # if any of the wrap files does not exist
    # or if the wrap files are older than any of the source files.
    if (not os.path.isfile('src/gsl_wrap.c') or (not os.path.isfile('src/swigpyrun.h')) or \
        False in [os.path.isfile(WRAP_INFO[x][0]) for x in MODULES]) or \
        (max( [os.path.getmtime('src/' + x) for x in HEADER_FILES] ) > \
         min( [os.path.getmtime(WRAP_INFO[x][0]) for x in MODULES])):
        (v1, v2, v3) = swig_version()
        if (v1, v2, v3) < (1, 3, 35):
            print('Swig >= 1.3.35 is required, please upgrade it.')
            sys.exit(1)
        if sys.version_info[0] >= 3 and sys.version_info[1] >= 2 and (v1, v2, v3) < (2, 0, 4):
            print('Swig >= 2.0.4 is required for Python 3.2 or higher')
            sys.exit(1)
        # generate header file 
        print("Generating external runtime header file src/swigpyrun.h...")
        os.system('%s %s src/swigpyrun.h' % (SWIG, SWIG_RUNTIME_FLAGS))
        # try the first option set with the first library
        for lib in MODULES:
            print("Generating wrapper file " + WRAP_INFO[lib][0])
            if os.system('%s %s -outdir %s %s -o %s %s' % (SWIG, SWIG_CPP_FLAGS, \
                SWIG_OUTDIR, WRAP_INFO[lib][2], WRAP_INFO[lib][0], WRAP_INFO[lib][1])) != 0:
                print("Calling swig failed. Please check your swig version.")
                sys.exit(1)
        print("Generating wrapper file src/gsl_wrap.c")
        if os.system('%s %s -outdir %s %s -o %s %s' % (SWIG, SWIG_CC_FLAGS, \
            SWIG_OUTDIR, '', 'src/gsl_wrap.c', 'src/gsl.i')) != 0:
            print("Calling swig failed. Please check your swig version.")
            sys.exit(1)
        print("\nAll wrap files are generated successfully.\n")
    # under solaris, there is no stdint.h so I need to replace stdint.h
    # in the wrap files with inttypes.h
    if sys.platform == 'sunos5':
        for lib in MODULES:
            replaceIntHeader(WRAP_INFO[lib][0])
    # copy needed files
    copied_files = []
    for modu in MODULES:
        if not os.path.isdir('build/%s' % modu):
            os.mkdir('build/%s' % modu)
        for src in SOURCE_FILES:
            mod_src = 'build/%s/%s' % (modu, src)
            if not os.path.isfile(mod_src) or not filecmp.cmp(mod_src,'src/'+src):
                shutil.copy('src/'+src, mod_src)
    # build
    # For module simuPOP.gsl
    EXT_MODULES = [
        Extension('simuPOP._gsl',
            sources = GSL_FILES + ['src/gsl_wrap.c'],
            include_dirs = ['gsl', 'gsl/specfunc', 'build', '.'],
        )
    ]
    for modu in MODULES:
        info = ModuInfo(modu, SIMUPOP_VER=SIMUPOP_VER, SIMUPOP_REV=SIMUPOP_REV)
        EXT_MODULES.append(
            Extension('simuPOP._simuPOP_%s' % modu,
                sources = info['src'],
                extra_compile_args = info['extra_compile_args'],
                # src for config.h etc, build for swigpyrun.h
                include_dirs = info['include_dirs'] + ['src', 'build'],
                library_dirs = info['library_dirs'],
                libraries = info['libraries'],
                define_macros = info['define_macros'],
                undef_macros = info['undef_macros'],
            )
        )
    if  USE_DISTRIBUTE :
        setup_params = dict(packages = find_packages(), include_package_data = True,
                        exclude_package_data = {'':['README.txt']}, zip_safe = False,
                        install_requires = ['distribute'])
    else :
        setup_params = dict(packages = ['simuPOP'])

    setup(
        name = "simuPOP",
        version = SIMUPOP_VER,
        author = "Bo Peng",
        author_email = "bpeng@mdanderson.org",
        maintainer = "Bo Peng",
        maintainer_email = "bpeng@mdanderson.org",
        url = "http://simupop.sourceforge.net",
        description = "Forward-time population genetics simulation environment",
        long_description = DESCRIPTION, 
        download_url = 'http://simupop.sourceforge.net/Main/Download',
        classifiers = [
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Education',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: C++',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Topic :: Scientific/Engineering :: Bio-Informatics',
        ],
        platforms = ['all'],
        #
        package_dir = {'simuPOP': 'src'}, 
        package_data = {'simuPOP': PACKAGE_DATA},
        py_modules = [
            'simuOpt', 
            'simuPOP.__init__',
            'simuPOP.gsl',
            'simuPOP.utils', 
            'simuPOP.plotter', 
            'simuPOP.sampling', 
            'simuPOP.sandbox',
        ] + ['simuPOP.simuPOP_%s' % x for x in MODULES],
        ext_modules = EXT_MODULES,
        cmdclass = {'build_py': build_py},
        **setup_params
    )



