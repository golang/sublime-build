# *Golang Build* Design

The Golang Build Sublime Text package is structured as follows:

 - The primary user interaction happens through the Sublime Text build system,
   which parses the "Go.sublime-build" file
 - The primary build task is "go build", but variants exists for "go test",
   "go install", "go clean" and cross-compile, which is "go build" with GOOS
   and GOARCH set. All of these tasks are executing by the Sublime Text command
   named "golang_build".
 - Additional Sublime Text commands are implemented that implement the following
   functionality:
    - "golang_build_get" provides an interface to "go get"
    - "golang_terminal" opens a terminal to the Go workspace with all
      appropriate environment variables set
    - "golang_build_cancel" allows users to kill an in-process build
    - "golang_build_reopen" allows users to reopen the build output panel
   Each of these commands is exposed to the command palette via the file
   Default.sublime-commands
 - Configuration uses the Package Control dependency golangconfig, which allows
   users to set settings globally in Sublime Text, for each OS globally,
   per-project, or for each OS in a project
 - Settings exist that allow users to customize command line flags on a
   per-task-basis

As is dictated by the Sublime Text API, the following list shows a mapping of
command to Python class name:

 - `golang_build`: `GolangBuildCommand()`
 - `golang_build_get`: `GolangBuildGetCommand()`
 - `golang_build_cancel`: `GolangBuildCancelCommand()`
 - `golang_build_reopen`: `GolangBuildReopenCommand()`
 - `golang_build_terminal`: `GolangBuildTerminalCommand()`

For `golang_build` and `golang_build_get`, the commands display output to the
user via an output panel. Normally with Sublime Text when a reference to the
`sublime.View` object for an output panel is requested, any existing content is
erased. To prevent a jarring experience for users when a build is interrupted,
a reference to each window's Golang Build output panel is held in memory and
re-used when a user interrupts a running build with a new invocation.

The `GolangProcess()` class reprents an invocation of the `go` executable, and
provides a queue of output information. This output queue is processed by a
`GolangProcessPrinter()` object which adds environment information before the
output starts, and summary information once completed. There is one
`GolangPanel()` object per Sublime Text window, and it contains a lock to ensure
that only one `GolangProcessPrinter()` may be displaying output at a time to
prevent interleaved output.
