# *Golang Build* Commands

This page lists the commands provided by this package and the arguments they
accept.

 - [Commands](#commands)
   - [golang_build](#golang_build)
   - [golang_build_get](#golang_build_get)
   - [golang_build_terminal](#golang_build_terminal)
 - [Key Binding Example](#key-binding-example)
 - [Command Palette Example](#command-palette-example)

## Commands

### golang_build

The `golang_build` command executes various `go` commands and accepts the
following args:

 - `task`: A string of the build task to perform. Accepts the following values:
   - `"build"`: executes `go build -v`
   - `"test"`: executes `go test -v`
   - `"install"`: executes `go install -v`
   - `"clean"`: executes `go clean -v`
   - `"cross_compile"`: executes `go build -v` with `GOOS` and `GOARCH` set
 - `flags`: A list of strings to pass to the `go` executable as flags. The list
   of valid flags can be determined by executing `go help {task}` in the
   terminal.

### golang_build_get

The `golang_build_get` command executes `go get -v` and accepts the following
args:

 - `url`: A string of the URL to get, instead of prompting the user for it.
 - `flags`: A list of strings to pass to the `go` executable as flags. The list
   of valid flags can be determined by executing `go help get` in the
   terminal.

### golang_build_terminal

The `golang_build_terminal` command opens a terminal to the directory containing
the currently open file. The command does not accept any args.

## Key Binding Example

The following JSON structure can be added to the file opened by the
*Preferences > Key Bindings – User* menu entry.

```json
[
    {
        "keys": ["super+ctrl+g", "super+ctrl+t"],
        "command": "golang_build",
        "args": {
            "task": "test",
            "flags": ["-x"]
        }
    }
]
```

## Command Palette Example

The following JSON structure can be added to
`Packages/User/Default.sublime-commands`. The `Packages/` folder can be located
by the *Preferences > Browse Packages...* menu entry.

```json
[
    {
        "caption": "Go: Test (Print Commands)",
        "command": "golang_build",
        "args": {
            "task": "test",
            "flags": ["-x"]
        }
    }
]
```
