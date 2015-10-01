# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import os
import sys
import locale

import sublime
import golangconfig

if sys.version_info < (3,):
    golang_build = sys.modules['golang_build']
else:
    golang_build = sys.modules['Golang Build.golang_build']


class ShellenvMock():

    _env_encoding = locale.getpreferredencoding() if sys.platform == 'win32' else 'utf-8'
    _fs_encoding = 'mbcs' if sys.platform == 'win32' else 'utf-8'

    _shell = None
    _data = None

    def __init__(self, shell, data):
        self._shell = shell
        self._data = data

    def get_env(self, for_subprocess=False):
        if not for_subprocess or sys.version_info >= (3,):
            return (self._shell, self._data)

        shell = self._shell.encode(self._fs_encoding)
        env = {}
        for name, value in self._data.items():
            env[name.encode(self._env_encoding)] = value.encode(self._env_encoding)

        return (shell, env)

    def get_path(self):
        return (self._shell, self._data.get('PATH', '').split(os.pathsep))

    def env_encode(self, value):
        if sys.version_info >= (3,):
            return value
        return value.encode(self._env_encoding)

    def path_encode(self, value):
        if sys.version_info >= (3,):
            return value
        return value.encode(self._fs_encoding)

    def path_decode(self, value):
        if sys.version_info >= (3,):
            return value
        return value.decode(self._fs_encoding)


class SublimeSettingsMock():

    _values = None

    def __init__(self, values):
        self._values = values

    def get(self, name, default=None):
        return self._values.get(name, default)


class SublimeMock():

    _settings = None
    View = sublime.View
    Window = sublime.Window

    def __init__(self, settings):
        self._settings = SublimeSettingsMock(settings)

    def load_settings(self, basename):
        return self._settings


class GolangBuildMock():

    _shellenv = None
    _sublime = None

    _shell = None
    _env = None
    _sublime_settings = None

    def __init__(self, shell=None, env=None, sublime_settings=None):
        self._shell = shell
        self._env = env
        self._sublime_settings = sublime_settings

    def __enter__(self):
        if self._shell is not None and self._env is not None:
            self._shellenv = golangconfig.shellenv
            golangconfig.shellenv = ShellenvMock(self._shell, self._env)
            golang_build.shellenv = golangconfig.shellenv
        if self._sublime_settings is not None:
            self._sublime = golangconfig.sublime
            golangconfig.sublime = SublimeMock(self._sublime_settings)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._shellenv is not None:
            golangconfig.shellenv = self._shellenv
            golang_build.shellenv = self._shellenv
        if self._sublime is not None:
            golangconfig.sublime = self._sublime
