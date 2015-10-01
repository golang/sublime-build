# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import sys
from os import path
import time


module_name = 'golang_build'
if sys.version_info >= (3,):
    module_name = 'Golang Build.' + module_name
    from imp import reload

if module_name in sys.modules:
    reload(sys.modules[module_name])

if 'Golang Build.dev.mocks' in sys.modules:
    reload(sys.modules['Golang Build.dev.mocks'])

filepath = path.join(path.dirname(__file__), '..', 'golang_build.py')
open(filepath, 'ab').close()
# Wait for Sublime Text to reload the file
time.sleep(0.5)
