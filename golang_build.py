# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import sys
import os
import threading
import subprocess
import time
import re
import textwrap
import collections

import signal

if sys.version_info < (3,):
    import Queue as queue
    str_cls = unicode  # noqa
else:
    import queue
    str_cls = str

import sublime
import sublime_plugin

import shellenv
import golangconfig
import newterm
import package_events


# A list of the environment variables to pull from settings when creating a
# subprocess. Some subprocesses may have one or more manually overridden.
GO_ENV_VARS = set([
    'GOPATH',
    'GOROOT',
    'GOROOT_FINAL',
    'GOBIN',
    'GOHOSTOS',
    'GOHOSTARCH',
    'GOOS',
    'GOARCH',
    'GOARM',
    'GO386',
    'GORACE',
])

# References to any existing GolangProcess() for a sublime.Window.id(). For
# basic get and set operations, the dict is threadsafe.
_PROCS = {}

# References to any existing GolangPanel() for a sublime.Window.id(). For
# basic get and set operations, the dict is threadsafe.
_PANELS = {}
_PANEL_LOCK = threading.Lock()


class GolangBuildCommand(sublime_plugin.WindowCommand):

    """
    Command to run "go build", "go install", "go test" and "go clean"
    """

    def run(self, task='build', flags=None):
        """
        Runs the "golang_build" command - invoked by Sublime Text via the
        command palette or sublime.Window.run_command()

        :param task:
            A unicode string of "build", "test", "install", "clean"
            or "cross_compile"

        :param flags:
            A list of unicode strings of flags to send to the command-line go
            tool. The "cross_compile" task executes the "build" command with
            the GOOS and GOARCH environment variables set, meaning that
            flags for "build" should be used with it. Execute "go help" on the
            command line to learn about available flags.
        """

        if _yield_to_running_build(self.window):
            return

        working_dir = _determine_working_dir(self.window)
        if working_dir is None:
            return

        go_bin, env = _get_config(
            'go',
            set(['GOPATH']),
            GO_ENV_VARS - set(['GOPATH']),
            view=self.window.active_view(),
            window=self.window,
        )
        if (go_bin, env) == (None, None):
            return

        if flags is None:
            flags, _ = golangconfig.setting_value(
                '%s:flags' % task,
                view=self.window.active_view(),
                window=self.window
            )

        if flags is None:
            flags = ['-v']

        if task == 'run':
            # Allow the user to set a file path into the flags settings,
            # thus requiring that the flags be checked to ensure a second
            # filename is not added
            found_filename = False

            # Allow users to call "run" with a src-relative file path. Because
            # of that, flags may be rewritten since the "go run" does not
            # accept such file paths.
            use_new_flags = False
            new_flags = []

            gopaths = env['GOPATH'].split(os.pathsep)

            for flag in flags:
                if flag.endswith('.go'):
                    absolute_path = flag
                    if os.path.isfile(absolute_path):
                        found_filename = True
                        break

                    # If the file path is src-relative, rewrite the flag
                    for gopath in gopaths:
                        gopath_relative = os.path.join(gopath, 'src', flag)
                        if os.path.isfile(gopath_relative):
                            found_filename = True
                            flag = gopath_relative
                            use_new_flags = True
                            break
                new_flags.append(flag)

            if use_new_flags:
                flags = new_flags

            if not found_filename:
                flags.append(self.window.active_view().file_name())

        if task == 'cross_compile':
            _task_cross_compile(
                self,
                go_bin,
                flags,
                working_dir,
                env
            )
            return

        args = [go_bin, task]
        if flags and isinstance(flags, list):
            args.extend(flags)
        proc = _run_process(
            task,
            self.window,
            args,
            working_dir,
            env
        )
        _set_proc(self.window, proc)


def _task_cross_compile(command, go_bin, flags, working_dir, env):
    """
    Prompts the user to select the OS and ARCH to use for a cross-compile

    :param command:
        A sublime_plugin.WindowCommand object

    :param go_bin:
        A unicode string with the path to the "go" executable

    :param flags:
        A list of unicode string of flags to pass to the "go" executable

    :param working_dir:
        A unicode string with the working directory for the "go" executable

    :param env:
        A dict of environment variables to use with the "go" executable
    """

    valid_combinations = [
        ('darwin', '386'),
        ('darwin', 'amd64'),
        ('darwin', 'arm'),
        ('darwin', 'arm64'),
        ('dragonfly', 'amd64'),
        ('freebsd', '386'),
        ('freebsd', 'amd64'),
        ('freebsd', 'arm'),
        ('linux', '386'),
        ('linux', 'amd64'),
        ('linux', 'arm'),
        ('linux', 'arm64'),
        ('linux', 'ppc64'),
        ('linux', 'ppc64le'),
        ('netbsd', '386'),
        ('netbsd', 'amd64'),
        ('netbsd', 'arm'),
        ('openbsd', '386'),
        ('openbsd', 'amd64'),
        ('openbsd', 'arm'),
        ('plan9', '386'),
        ('plan9', 'amd64'),
        ('solaris', 'amd64'),
        ('windows', '386'),
        ('windows', 'amd64'),
    ]

    def on_done(index):
        """
        Processes the user's input and launch the build process

        :param index:
            The index of the option the user selected, or -1 if cancelled
        """

        if index == -1:
            return

        env['GOOS'], env['GOARCH'] = valid_combinations[index]

        args = [go_bin, 'build']
        if flags and isinstance(flags, list):
            args.extend(flags)
        proc = _run_process(
            'cross_compile',
            command.window,
            args,
            working_dir,
            env
        )
        _set_proc(command.window, proc)

    quick_panel_options = []
    for os_, arch in valid_combinations:
        quick_panel_options.append('OS: %s, ARCH: %s' % (os_, arch))

    command.window.show_quick_panel(
        quick_panel_options,
        on_done
    )


class GolangBuildCancelCommand(sublime_plugin.WindowCommand):

    """
    Terminates any existing "go" process that is running for the current window
    """

    def run(self):
        proc = _get_proc(self.window)
        if proc and not proc.finished:
            proc.terminate()
        if proc is not None:
            _set_proc(self.window, None)

    def is_enabled(self):
        proc = _get_proc(self.window)
        if not proc:
            return False
        return not proc.finished


class GolangBuildReopenCommand(sublime_plugin.WindowCommand):

    """
    Reopens the output from the last build command
    """

    def run(self):
        self.window.run_command('show_panel', {'panel': 'output.golang_build'})


class GolangBuildGetCommand(sublime_plugin.WindowCommand):

    """
    Prompts the use to enter the URL of a Go package to get
    """

    def run(self, url=None, flags=None):
        """
        Runs the "golang_build_get" command - invoked by Sublime Text via the
        command palette or sublime.Window.run_command()

        :param url:
            A unicode string of the URL to download, instead of prompting the
            user

        :param flags:
            A list of unicode strings of flags to send to the command-line go
            tool. Execute "go help" on the command line to learn about available
            flags.
        """

        if _yield_to_running_build(self.window):
            return

        working_dir = _determine_working_dir(self.window)
        if working_dir is None:
            return

        go_bin, env = _get_config(
            'go',
            set(['GOPATH']),
            GO_ENV_VARS - set(['GOPATH']),
            view=self.window.active_view(),
            window=self.window,
        )
        if (go_bin, env) == (None, None):
            return

        if flags is None:
            flags, _ = golangconfig.setting_value(
                'get:flags',
                view=self.window.active_view(),
                window=self.window
            )

        if flags is None:
            flags = ['-v']

        def on_done(get_url):
            """
            Processes the user's input and launches the "go get" command

            :param get_url:
                A unicode string of the URL to get
            """

            args = [go_bin, 'get']
            if flags and isinstance(flags, list):
                args.extend(flags)
            args.append(get_url)
            proc = _run_process(
                'get',
                self.window,
                args,
                working_dir,
                env
            )
            _set_proc(self.window, proc)

        if url is not None:
            on_done(url)
            return

        self.window.show_input_panel(
            'go get',
            '',
            on_done,
            None,
            None
        )


class GolangBuildTerminalCommand(sublime_plugin.WindowCommand):

    """
    Opens a terminal for the user to the directory containing the open file,
    setting any necessary environment variables
    """

    def run(self):
        """
        Runs the "golang_build_terminal" command - invoked by Sublime Text via
        the command palette or sublime.Window.run_command()
        """

        working_dir = _determine_working_dir(self.window)
        if working_dir is None:
            return

        relevant_sources = set([
            'project file',
            'project file (os-specific)',
            'golang.sublime-settings',
            'golang.sublime-settings (os-specific)'
        ])

        env_overrides = {}
        for var_name in GO_ENV_VARS:
            value, source = golangconfig.setting_value(var_name, window=self.window)
            # Only set overrides that are not coming from the user's shell
            if source in relevant_sources:
                env_overrides[var_name] = value

        # Get the PATH from the shell environment and then prepend any custom
        # value so the user's terminal searches all locations
        value, source = golangconfig.setting_value('PATH', window=self.window)
        if source in relevant_sources:
            shell, env = shellenv.get_env()
            env_overrides['PATH'] = value + os.pathsep + env.get('PATH', '')

        newterm.launch_terminal(working_dir, env=env_overrides)


def _yield_to_running_build(window):
    """
    Check if a build is already running, and if so, allow the user to stop it,
    or cancel the new build

    :param window:
        A sublime.Window of the window the build is being run in

    :return:
        A boolean - if the new build should be abandoned
    """

    proc = _get_proc(window)
    if proc and not proc.finished:
        message = _format_message("""
            Golang Build

            There is already a build running. Would you like to stop it?
        """)
        if not sublime.ok_cancel_dialog(message, 'Stop Running Build'):
            return True
        proc.terminate()
        _set_proc(window, None)

    return False


def _determine_working_dir(window):
    """
    Determine the working directory for a command based on the user's open file
    or open folders

    :param window:
        The sublime.Window object of the window the command was run on

    :return:
        A unicode string of the working directory, or None if no working
        directory was found
    """

    view = window.active_view()
    working_dir = None

    # If a file is open, get the folder from the file, and error if the file
    # has not been saved yet
    if view:
        if view.file_name():
            working_dir = os.path.dirname(view.file_name())

    # If no file is open, then get the list of folders and grab the first one
    else:
        folders = window.folders()
        if len(folders) > 0:
            working_dir = folders[0]

    if working_dir is None or not os.path.exists(working_dir):
        message = _format_message("""
            Golang Build

            No files or folders are open, or the open file or folder does not exist on disk
        """)
        sublime.error_message(message)
        return None

    return working_dir


def _get_config(executable_name, required_vars, optional_vars=None, view=None, window=None):
    """
    :param executable_name:
        A unicode string of the executable to locate, e.g. "go" or "gofmt"

    :param required_vars:
        A list of unicode strings of the environment variables that are
        required, e.g. "GOPATH". Obtains values from setting_value().

    :param optional_vars:
        A list of unicode strings of the environment variables that are
        optional, but should be pulled from setting_value() if available - e.g.
        "GOOS", "GOARCH". Obtains values from setting_value().

    :param view:
        A sublime.View object to use in finding project-specific settings. This
        should be passed whenever available.

    :param window:
        A sublime.Window object to use in finding project-specific settings.
        This will only work for Sublime Text 3, and should only be passed if
        no sublime.View object is available to pass via the view parameter.

    :return:
        A two-element tuple.

        If there was an error finding the executable or required vars:

         - [0] None
         - [1] None

        Otherwise:

         - [0] A string of the path to the executable
         - [1] A dict of environment variables for the executable
    """

    try:
        return golangconfig.subprocess_info(
            executable_name,
            required_vars,
            optional_vars,
            view=view,
            window=window
        )

    except (golangconfig.ExecutableError) as e:
        error_message = '''
            Golang Build

            The %s executable could not be found. Please ensure it is
            installed and available via your PATH.

            Would you like to view documentation for setting a custom PATH?
        '''

        prompt = error_message % e.name

        if sublime.ok_cancel_dialog(_format_message(prompt), 'Open Documentation'):
            window.run_command(
                'open_url',
                {'url': 'https://github.com/golang/sublime-build/blob/master/docs/configuration.md'}
            )

    except (golangconfig.EnvVarError) as e:
        error_message = '''
            Golang Build

            The setting%s %s could not be found in your Sublime Text
            settings or your shell environment.

            Would you like to view the configuration documentation?
        '''

        plural = 's' if len(e.missing) > 1 else ''
        setting_names = ', '.join(e.missing)
        prompt = error_message % (plural, setting_names)

        if sublime.ok_cancel_dialog(_format_message(prompt), 'Open Documentation'):
            window.run_command(
                'open_url',
                {'url': 'https://github.com/golang/sublime-build/blob/master/docs/configuration.md'}
            )

    except (golangconfig.GoRootNotFoundError, golangconfig.GoPathNotFoundError) as e:
        error_message = '''
            Golang Build

            %s.

            Would you like to view the configuration documentation?
        '''

        prompt = error_message % str_cls(e)

        if sublime.ok_cancel_dialog(_format_message(prompt), 'Open Documentation'):
            window.run_command(
                'open_url',
                {'url': 'https://github.com/golang/sublime-build/blob/master/docs/configuration.md'}
            )

    return (None, None)


class GolangProcess():

    """
    A wrapper around subprocess.Popen() that provides information about how
    the process was started and finished, plus a queue.Queue of output
    """

    # A float of the unix timestamp of when the process was started
    started = None

    # A list of strings (unicode for Python 3, byte string for Python 2) of
    # the process path and any arguments passed to it
    args = None

    # A unicode string of the process working directory
    cwd = None

    # A dict of the env passed to the process
    env = None

    # A subprocess.Popen() object of the running process
    proc = None

    # A queue.Queue object of output from the process
    output = None

    # The result of the process, a unicode string of "cancelled", "success" or "error"
    result = None

    # A float of the unix timestamp of when the process ended
    finished = None

    # A threading.Lock() used to prevent the stdout and stderr handlers from
    # both trying to perform process cleanup at the same time
    _cleanup_lock = None

    def __init__(self, args, cwd, env):
        """
        :param args:
            A list of strings (unicode for Python 3, byte string for Python 2)
            of the process path and any arguments passed to it

        :param cwd:
            A unicode string of the working directory for the process

        :param env:
            A dict of strings (unicode for Python 3, byte string for Python 2)
            to pass to the process as the environment variables
        """

        self.args = args
        self.cwd = cwd
        self.env = env

        startupinfo = None
        preexec_fn = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # On posix platforms we create a new process group by executing
            # os.setsid() after the fork before the go binary is executed. This
            # allows us to use os.killpg() to kill the whole process group.
            preexec_fn = os.setsid

        self._cleanup_lock = threading.Lock()
        self.started = time.time()
        self.proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            startupinfo=startupinfo,
            preexec_fn=preexec_fn
        )
        self.finished = False

        self.output = queue.Queue()

        self._stdout_thread = threading.Thread(
            target=self._read_output,
            args=(
                self.output,
                self.proc.stdout.fileno(),
                'stdout'
            )
        )
        self._stdout_thread.start()

        self._stderr_thread = threading.Thread(
            target=self._read_output,
            args=(
                self.output,
                self.proc.stderr.fileno(),
                'stderr'
            )
        )
        self._stderr_thread.start()

        self._cleanup_thread = threading.Thread(target=self._cleanup)
        self._cleanup_thread.start()

    def wait(self):
        """
        Blocks waiting for the subprocess to complete
        """

        self._cleanup_thread.wait()

    def terminate(self):
        """
        Terminates the subprocess
        """

        self._cleanup_lock.acquire()
        try:
            if not self.proc:
                return

            if sys.platform != 'win32':
                # On posix platforms we send SIGTERM to the whole process
                # group to ensure both go and the compiled temporary binary
                # are killed.
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            else:
                # On Windows, there is no API to get the child processes
                # of a process and send signals to them all. Attempted to use
                # startupinfo.dwFlags with CREATE_NEW_PROCESS_GROUP and then
                # calling self.proc.send_signal(signal.CTRL_BREAK_EVENT),
                # however that did not kill the temporary binary. taskkill is
                # part of Windows XP and newer, so we use that.
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                kill_proc = subprocess.Popen(
                    ['taskkill', '/F', '/T', '/PID', str_cls(self.proc.pid)],
                    startupinfo=startupinfo
                )
                kill_proc.wait()

            self.result = 'cancelled'
            self.finished = time.time()
            self.proc = None
        finally:
            self._cleanup_lock.release()

    def _read_output(self, output_queue, fileno, output_type):
        """
        Handler to process output from stdout/stderr

        RUNS IN A THREAD

        :param output_queue:
            The queue.Queue object to add the output to

        :param fileno:
            The fileno to read output from

        :param output_type:
            A unicode string of "stdout" or "stderr"
        """

        while self.proc and self.proc.poll() is None:
            chunk = os.read(fileno, 32768)
            if len(chunk) == 0:
                break
            output_queue.put((output_type, chunk.decode('utf-8')))

    def _cleanup(self):
        """
        Cleans up the subprocess and marks the state of self appropriately

        RUNS IN A THREAD
        """

        self._stdout_thread.join()
        self._stderr_thread.join()

        self._cleanup_lock.acquire()
        try:
            if not self.proc:
                return
            # Get the returncode to prevent a zombie/defunct child process
            self.proc.wait()
            self.result = 'success' if self.proc.returncode == 0 else 'error'
            self.finished = time.time()
            self.proc = None
        finally:
            self._cleanup_lock.release()
            self.output.put(('eof', None))


class GolangProcessPrinter():

    """
    Describes a Go process, the environment it was started in and its result
    """

    # The GolangProcess() object the printer is displaying output from
    proc = None

    # The GolangPanel() object the information is written to
    panel = None

    def __init__(self, proc, panel):
        """
        :param proc:
            A GolangProcess() object

        :param panel:
            A GolangPanel() object to write information to
        """

        self.proc = proc
        self.panel = panel

        self.thread = threading.Thread(
            target=self._run
        )
        self.thread.start()

    def _run(self):
        """
        GolangProcess() output queue processor

        RUNS IN A THREAD
        """

        self.panel.printer_lock.acquire()
        self.panel.set_base_dir(self.proc.cwd)

        try:
            self._write_header()

            while True:
                message_type, message = self.proc.output.get()

                if message_type == 'eof':
                    break

                if message_type == 'stdout':
                    output = message

                if message_type == 'stderr':
                    output = message

                self.panel.write(output)

            self._write_footer()

        finally:
            self.panel.printer_lock.release()

    def _write_header(self):
        """
        Displays startup information about the process
        """

        title = ''

        env_vars = []
        for var_name in GO_ENV_VARS:
            var_key = var_name if sys.version_info >= (3,) else var_name.encode('ascii')
            if var_key in self.proc.env:
                value = self.proc.env.get(var_key)
                if sys.version_info < (3,):
                    value = value.decode('utf-8')
                env_vars.append((var_name, value))
        if env_vars:
            title += '> Environment:\n'
            for var_name, value in env_vars:
                title += '>   %s=%s\n' % (var_name, value)

        title += '> Directory: %s\n' % self.proc.cwd
        title += '> Command: %s\n' % subprocess.list2cmdline(self.proc.args)
        title += '> Output:\n'

        self.panel.write(title, content_separator='\n\n')

    def _write_footer(self):
        """
        Displays result information about the process, blocking until the
        write is completed
        """

        formatted_result = self.proc.result.title()
        runtime = self.proc.finished - self.proc.started

        output = '> Elapsed: %0.3fs\n> Result: %s' % (runtime, formatted_result)

        event = threading.Event()
        self.panel.write(output, content_separator='\n', event=event)
        event.wait()

        package_events.notify(
            'Golang Build',
            'build_complete',
            BuildCompleteEvent(
                task='',
                args=list(self.proc.args),
                working_dir=self.proc.cwd,
                env=self.proc.env.copy(),
                runtime=runtime,
                result=self.proc.result
            )
        )


BuildCompleteEvent = collections.namedtuple(
    'BuildCompleteEvent',
    [
        'task',
        'args',
        'working_dir',
        'env',
        'runtime',
        'result',
    ]
)


class GolangPanel():

    """
    Holds a reference to an output panel used by the Golang Build package,
    and provides synchronization features to ensure output is printed in proper
    order
    """

    # A sublime.View object of the output panel being printed to
    panel = None

    # A queue.Queue() that holds all of the info to be written to the panel
    queue = None

    # A lock used to ensure only on GolangProcessPrinter() is using the panel
    # at any given time
    printer_lock = None

    def __init__(self, window):
        """
        :param window:
            The sublime.Window object the output panel is contained within
        """

        self.printer_lock = threading.Lock()
        self.reset(window)

    def reset(self, window):
        """
        Creates a new, fresh output panel and output Queue object

        :param window:
            The sublime.Window object the output panel is contained within
        """

        if not isinstance(threading.current_thread(), threading._MainThread):
            raise RuntimeError('GolangPanel.reset() must be run in the UI thread')

        self.queue = queue.Queue()
        self.panel = window.get_output_panel('golang_build')

        st_settings = sublime.load_settings('Preferences.sublime-settings')
        panel_settings = self.panel.settings()
        panel_settings.set('syntax', 'Packages/Golang Build/Golang Build Output.tmLanguage')
        panel_settings.set('color_scheme', st_settings.get('color_scheme'))
        panel_settings.set('result_file_regex', '^(.+\.go):([0-9]+):(?:([0-9]+):)?\s*(.*)')
        panel_settings.set('draw_white_space', 'selection')
        panel_settings.set('word_wrap', False)
        panel_settings.set("auto_indent", False)
        panel_settings.set('line_numbers', False)
        panel_settings.set('gutter', False)
        panel_settings.set('scroll_past_end', False)

    def set_base_dir(self, cwd):
        """
        Set the directory the process is being run in, for the sake of result
        navigation

        :param cwd:
            A unicode string of the working directory
        """

        def _update_settings():
            self.panel.settings().set('result_base_dir', cwd)
        sublime.set_timeout(_update_settings, 1)

    def write(self, string, content_separator=None, event=None):
        """
        Queues data to be written to the output panel. Normally this will be
        called from a thread other than the UI thread.

        :param string:
            A unicode string to write to the output panel

        :param content_separator:
            A unicode string to prefix to the string param if there is already
            output in the output panel. Is only prefixed if the previous number
            of characters are not equal to this string.

        :param event:
            An optional threading.Event() object to set once the data has been
            written to the output panel
        """

        self.queue.put((string, content_separator, event))
        sublime.set_timeout(self._process_queue, 1)

    def _process_queue(self):
        """
        A callback that is run in the UI thread to actually perform writes to
        the output panel. Reads from the queue until it is empty.
        """

        try:
            while True:
                chars, content_separator, event = self.queue.get(False)

                if content_separator is not None and self.panel.size() > 0:
                    end = self.panel.size()
                    start = end - len(content_separator)
                    if self.panel.substr(sublime.Region(start, end)) != content_separator:
                        chars = content_separator + chars

                # In Sublime Text 2, the "insert" command does not handle newlines
                if sys.version_info < (3,):
                    edit = self.panel.begin_edit('golang_panel_print', [])
                    self.panel.insert(edit, self.panel.size(), chars)
                    self.panel.end_edit(edit)

                else:
                    self.panel.run_command('insert', {'characters': chars})

                if event:
                    event.set()

        except (queue.Empty):
            pass


def _run_process(task, window, args, cwd, env):
    """
    Starts a GolangProcess() and creates a GolangProcessPrinter() for it

    :param task:
        A unicode string of the build task name - one of "build", "test",
        "cross_compile", "install", "clean", "get"

    :param window:
        A sublime.Window object of the window to display the output panel in

    :param args:
        A list of strings (unicode for Python 3, byte string for Python 2)
        of the process path and any arguments passed to it

    :param cwd:
        A unicode string of the working directory for the process

    :param env:
        A dict of strings (unicode for Python 3, byte string for Python 2)
        to pass to the process as the environment variables

    :return:
        A GolangProcess() object
    """

    panel = _get_panel(window)

    proc = GolangProcess(args, cwd, env)

    # If there is no printer using the panel, reset it
    if panel.printer_lock.acquire(False):
        panel.reset(window)
        panel.printer_lock.release()

    GolangProcessPrinter(proc, panel)

    window.run_command('show_panel', {'panel': 'output.golang_build'})

    return proc


def _set_proc(window, proc):
    """
    Sets the GolangProcess() object associated with a sublime.Window

    :param window:
        A sublime.Window object

    :param proc:
        A GolangProcess() object that is being run for the window
    """

    _PROCS[window.id()] = proc


def _get_proc(window):
    """
    Returns the GolangProcess() object associated with a sublime.Window

    :param window:
        A sublime.Window object

    :return:
        None or a GolangProcess() object. The GolangProcess() may or may not
        still be running.
    """

    return _PROCS.get(window.id())


def _get_panel(window):
    """
    Returns the GolangPanel() object associated with a sublime.Window

    :param window:
        A sublime.Window object

    :return:
        A GolangPanel() object
    """

    _PANEL_LOCK.acquire()
    try:
        if window.id() not in _PANELS:
            _PANELS[window.id()] = GolangPanel(window)
        return _PANELS.get(window.id())
    finally:
        _PANEL_LOCK.release()


def _format_message(string):
    """
    Takes a multi-line string and does the following:

     - dedents
     - converts newlines with text before and after into a single line
     - strips leading and trailing whitespace

    :param string:
        The string to format

    :return:
        The formatted string
    """

    output = textwrap.dedent(string)

    # Unwrap lines, taking into account bulleted lists, ordered lists and
    # underlines consisting of = signs
    if output.find('\n') != -1:
        output = re.sub('(?<=\\S)\n(?=[^ \n\t\\d\\*\\-=])', ' ', output)

    return output.strip()
