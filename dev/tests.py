# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import sys
import threading
import unittest
from os import path
import time
import re
import shutil
import os

import sublime

import shellenv
import package_events

if sys.version_info < (3,):
    from Queue import Queue
else:
    from queue import Queue

from .mocks import GolangBuildMock


TEST_GOPATH = path.join(path.dirname(__file__), 'go_projects')
TEST_GOPATH2 = path.join(path.dirname(__file__), 'go_projects2')
VIEW_SETTINGS = {
    'GOPATH': TEST_GOPATH,
    'GOOS': None,
    'GOARCH': None,
    'GOARM': None,
    'GO386': None,
    'GORACE': None
}

CROSS_COMPILE_OS = 'darwin' if sys.platform != 'darwin' else 'linux'


class GolangBuildTests(unittest.TestCase):

    def setUp(self):
        skip_entries = {}
        skip_entries[TEST_GOPATH] = set(['.git-keep', 'good', 'bad', 'runnable'])
        skip_entries[TEST_GOPATH2] = set(['.git-keep', 'runnable2'])

        for gopath in (TEST_GOPATH, TEST_GOPATH2):
            for subdir in ('pkg', 'bin', 'src'):
                full_path = path.join(gopath, subdir)
                for entry in os.listdir(full_path):
                    if entry in skip_entries[gopath]:
                        continue
                    entry_path = path.join(full_path, entry)
                    if path.isdir(entry_path):
                        shutil.rmtree(entry_path)
                    else:
                        os.remove(entry_path)

    def test_build(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build')

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go build" succeed?'))

    def test_build_flags(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'flags': ['-v', '-x']})

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go build" succeed and print all commands?'))

    def test_build_flags_from_settings(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        with GolangBuildMock(sublime_settings={'build:flags': ['-v', '-x']}):
            def _run_build(view, result_queue):
                view.window().run_command('golang_build')

            result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
            result = wait_build(result_queue)
            self.assertEqual('success', result)
            self.assertTrue(confirm_user('Did "go build" succeed and print all commands?'))

    def test_install_flags_from_view_settings(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'install'})

        custom_view_settings = VIEW_SETTINGS.copy()
        custom_view_settings['install:flags'] = ['-v', '-x']

        result_queue = open_file(file_path, custom_view_settings, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go install" succeed and print all commands?'))

    def test_clean(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'clean'})

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go clean" succeed?'))

    def test_test(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'test'})

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go test" succeed?'))

    def test_benchmark(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'benchmark'})

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go test" succeed running all benchmarks?'))

    def test_benchmark_with_bench_flag(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'benchmark'})

        custom_view_settings = VIEW_SETTINGS.copy()
        custom_view_settings['benchmark:flags'] = ['-bench', 'BenchmarkRuneLenResumeNew']

        result_queue = open_file(file_path, custom_view_settings, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go test" succeed running only BenchmarkRuneLenResumeNew?'))

    def test_benchmark_with_benchmem_flag(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'benchmark'})

        custom_view_settings = VIEW_SETTINGS.copy()
        custom_view_settings['benchmark:flags'] = ['-benchmem']

        result_queue = open_file(file_path, custom_view_settings, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go test" succeed running benchmarks with memory allocation stats?'))

    def test_run(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'runnable', 'main.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'run'})

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go run" succeed?'))

    def test_run_with_file_path_flag_absolute(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'run'})

        custom_view_settings = VIEW_SETTINGS.copy()
        custom_view_settings['run:flags'] = [os.path.join(TEST_GOPATH, 'src', 'runnable', 'main.go')]

        result_queue = open_file(file_path, custom_view_settings, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go run" succeed for runnable/main.go?'))

    def test_run_with_file_path_flag_relative(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'run'})

        custom_view_settings = VIEW_SETTINGS.copy()
        custom_view_settings['run:flags'] = ['runnable/main.go']

        result_queue = open_file(file_path, custom_view_settings, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go run" succeed for runnable/main.go?'))

    def test_run_with_file_path_flag_relative_multiple_gopath(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'run'})

        custom_view_settings = VIEW_SETTINGS.copy()
        custom_view_settings['GOPATH'] = os.pathsep.join([TEST_GOPATH, TEST_GOPATH2])
        custom_view_settings['run:flags'] = ['runnable2/main.go']

        result_queue = open_file(file_path, custom_view_settings, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go run" succeed for runnable2/main.go?'))

    def test_install(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build', {'task': 'install'})

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go install" succeed?'))

    def test_cross_compile(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')
        begin_event = threading.Event()

        def _run_build(view, result_queue):
            notify_user('Select %s/amd64 from quick panel' % CROSS_COMPILE_OS)
            begin_event.set()
            view.window().run_command('golang_build', {'task': 'cross_compile'})

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        begin_event.wait()
        result = wait_build(result_queue, timeout=15)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did the cross-compile succeed?'))

    def test_get(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')
        begin_event = threading.Event()

        def _run_build(view, result_queue):
            sublime.set_clipboard('github.com/golang/example/hello')
            notify_user('Paste from the clipboard into the input panel')
            begin_event.set()
            view.window().run_command('golang_build_get')

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        begin_event.wait()
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go get" succeed?'))

    def test_get_flags(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')
        begin_event = threading.Event()

        def _run_build(view, result_queue):
            sublime.set_clipboard('github.com/golang/example/hello')
            notify_user('Paste from the clipboard into the input panel')
            begin_event.set()
            view.window().run_command('golang_build_get', {'flags': ['-v', '-d']})

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        begin_event.wait()
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go get" download but not install?'))

    def test_get_flags_from_settings(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        with GolangBuildMock(sublime_settings={'get:flags': ['-v', '-d']}):
            def _run_build(view, result_queue):
                view.window().run_command('golang_build_get', {'url': 'github.com/golang/example/hello'})

            result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
            result = wait_build(result_queue)
            self.assertEqual('success', result)
            self.assertTrue(confirm_user('Did "go get" download but not install?'))

    def test_get_url(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build_get', {'url': 'github.com/golang/example/hello'})

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)
        self.assertTrue(confirm_user('Did "go get" succeed for "github.com/golang/example/hello"?'))

    def test_terminal(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build_terminal')

        open_file(file_path, VIEW_SETTINGS, _run_build)
        self.assertTrue(confirm_user('Did a terminal open to Packages/Golang Build/dev/go_projects/src/good/?'))

    def test_build_bad(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'bad', 'hello.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build')

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('error', result)
        self.assertTrue(confirm_user('Did "go build" fail?'))

    def test_build_cancel(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build')

            def _cancel_build():
                view.window().run_command('golang_build_cancel')

            sublime.set_timeout(_cancel_build, 50)

        # We perform a cross-compile so the user has time to interrupt the build
        custom_view_settings = VIEW_SETTINGS.copy()
        custom_view_settings['GOOS'] = CROSS_COMPILE_OS
        custom_view_settings['GOARCH'] = 'amd64'

        result_queue = open_file(file_path, custom_view_settings, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('cancelled', result)
        self.assertTrue(confirm_user('Was "go build" successfully cancelled?'))

    def test_build_reopen(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

        def _run_build(view, result_queue):
            view.window().run_command('golang_build')

        result_queue = open_file(file_path, VIEW_SETTINGS, _run_build)
        result = wait_build(result_queue)
        self.assertEqual('success', result)

        time.sleep(0.4)

        def _hide_panel():
            sublime.active_window().run_command('hide_panel')
        sublime.set_timeout(_hide_panel, 1)

        time.sleep(0.4)
        self.assertTrue(confirm_user('Was the build output hidden?'))

        def _reopen_panel():
            sublime.active_window().run_command('golang_build_reopen')
        sublime.set_timeout(_reopen_panel, 1)

        time.sleep(0.4)
        self.assertTrue(confirm_user('Was the build output reopened?'))

    def test_build_interrupt(self):
        ensure_not_ui_thread()

        file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')
        begin_event = threading.Event()
        second_begin_event = threading.Event()

        def _run_build(view, result_queue):
            notify_user('Press the "Stop Running Build" button when prompted')

            begin_event.set()
            view.window().run_command('golang_build')

            def _new_build():
                view.window().run_command('golang_build')
                second_begin_event.set()

            sublime.set_timeout(_new_build, 50)

        # We perform a cross-compile so the user has time to interrupt the build
        custom_view_settings = VIEW_SETTINGS.copy()
        custom_view_settings['GOOS'] = CROSS_COMPILE_OS
        custom_view_settings['GOARCH'] = 'amd64'

        result_queue = open_file(file_path, custom_view_settings, _run_build)
        begin_event.wait()
        result1 = wait_build(result_queue)
        self.assertEqual('cancelled', result1)
        second_begin_event.wait()
        result2 = wait_build(result_queue)
        self.assertEqual('success', result2)
        self.assertTrue(confirm_user('Was the first build cancelled and the second successful?'))

    def test_build_go_missing(self):
        ensure_not_ui_thread()

        shell, _ = shellenv.get_env()
        search_path = path.expanduser('~')
        with GolangBuildMock(shell=shell, env={'PATH': search_path}):

            file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

            def _run_build(view, result_queue):
                notify_user('Press the "Open Documentation" button when prompted about go not being found in the PATH')

                view.window().run_command('golang_build')

            open_file(file_path, VIEW_SETTINGS, _run_build)
            time.sleep(0.5)
            self.assertTrue(confirm_user('Were you prompted that go could not be found in the PATH?'))
            self.assertTrue(confirm_user('When you pressed "Open Documentation", was it opened in your browser?'))

    def test_build_no_gopath(self):
        ensure_not_ui_thread()

        shell, env = shellenv.get_env()
        if 'GOPATH' in env:
            del env['GOPATH']
        with GolangBuildMock(shell=shell, env=env):

            file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

            def _run_build(view, result_queue):
                notify_user('Press the "Open Documentation" button when prompted about GOPATH not being set')

                view.window().run_command('golang_build')

            custom_view_settings = VIEW_SETTINGS.copy()
            del custom_view_settings['GOPATH']
            open_file(file_path, custom_view_settings, _run_build)
            time.sleep(0.5)
            self.assertTrue(confirm_user('Were you prompted that GOPATH was not set?'))
            self.assertTrue(confirm_user('When you pressed "Open Documentation", was it opened in your browser?'))

    def test_build_missing_gopath(self):
        ensure_not_ui_thread()

        shell, env = shellenv.get_env()
        env['GOPATH'] += '12345678'
        with GolangBuildMock(shell=shell, env=env):

            file_path = path.join(TEST_GOPATH, 'src', 'good', 'rune_len.go')

            def _run_build(view, result_queue):
                notify_user('Press the "Open Documentation" button when prompted about GOPATH not being found')

                view.window().run_command('golang_build')

            custom_view_settings = VIEW_SETTINGS.copy()
            del custom_view_settings['GOPATH']
            open_file(file_path, custom_view_settings, _run_build)
            time.sleep(0.5)
            self.assertTrue(confirm_user('Were you prompted that GOPATH was not found?'))
            self.assertTrue(confirm_user('When you pressed "Open Documentation", was it opened in your browser?'))


def ensure_not_ui_thread():
    """
    The tests won't function properly if they are run in the UI thread, so
    this functions throws an exception if that is attempted
    """

    if isinstance(threading.current_thread(), threading._MainThread):
        raise RuntimeError('Tests can not be run in the UI thread')


def open_file(file_path, view_settings, callback):
    """
    Open a file in Sublime Text, sets settings on the view and then executes
    the callback once the file is opened

    :param file_path:
        A unicode string of the path to the file to open

    :param view_settings:
        A dict of settings to set the "golang" key of the view's settings to

    :param callback:
        The callback to execute in the UI thread once the file is opened
    """

    result_queue = Queue()
    file_param = file_path
    if sys.platform == 'win32':
        file_param = re.sub('^([a-zA-Z]):', '/\\1', file_param)
        file_param = file_param.replace('\\', '/')

    def open_file_callback():
        window = sublime.active_window()

        window.run_command(
            'open_file',
            {
                'file': file_param
            }
        )

        when_file_opened(window, file_path, view_settings, callback, result_queue)
    sublime.set_timeout(open_file_callback, 50)
    return result_queue


def when_file_opened(window, file_path, view_settings, callback, result_queue):
    """
    Periodic polling callback used by open_file() to find the newly-opened file

    :param window:
        The sublime.Window to look for the view in

    :param file_path:
        The file path of the file that was opened

    :param view_settings:
        A dict of settings to set to the view's "golang" setting key

    :param callback:
        The callback to execute when the file is opened

    :param result_queue:
        A Queue() object the callback can use to communicate with the test
    """

    view = window.active_view()
    if view and view.file_name() == file_path:
        view.settings().set('golang', view_settings)
        callback(view, result_queue)
        return
    # If the view was not ready, retry a short while later
    sublime.set_timeout(lambda: when_file_opened(window, file_path, view_settings, callback, result_queue), 50)


def wait_build(result_queue, timeout=5):
    """
    Uses the result queue to wait for a result from the open_file() callback

    :param result_queue:
        The Queue() to get the result from

    :param timeout:
        How long to wait before considering the test a failure

    :return:
        The value from the queue
    """

    def _send_result(package_name, event_name, payload):
        result_queue.put(payload.result)

    try:
        package_events.listen('Golang Build', _send_result)
        return result_queue.get(timeout=timeout)
    finally:
        package_events.unlisten('Golang Build', _send_result)


def confirm_user(message):
    """
    Prompts the user to via a dialog to confirm a question

    :param message:
        A unicode string of the message to present to the user

    :return:
        A boolean - if the user clicked "Yes"
    """

    queue = Queue()

    def _show_ok_cancel():
        response = sublime.ok_cancel_dialog('Test Suite for Golang Build\n\n' + message, 'Yes')
        queue.put(response)

    sublime.set_timeout(_show_ok_cancel, 1)
    return queue.get()


def notify_user(message):
    """
    Open a dialog for the user to inform them of a user interaction that is
    part of the test suite

    :param message:
        A unicode string of the message to present to the user
    """

    sublime.ok_cancel_dialog('Test Suite for Golang Build\n\n' + message, 'Ok')
