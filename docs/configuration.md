# *Golang Build* Configuration

By default, *Golang Build* looks at the user‘s shell environment to find the
values for various Go environment variables, including `GOPATH`.

In some situations the automatic detection may not be able to properly read the
desired configuration. In other situations, it may be desirable to provide
different configuration for different Sublime Text projects.

 - [Environment Autodetection](#environment-autodetection)
 - [Settings Load Order](#settings-load-order)
   - [Global Sublime Text Settings](#global-sublime-text-settings)
   - [OS-Specific Settings](#os-specific-settings)
   - [Project-Specific Settings](#project-specific-settings)
 - [Command Flags](#command-flags)
   - [Formatting Command Flag Settings](#formatting-command-flag-settings)
   - [Command Flag Setting Locations](#command-flag-setting-locations)
   - [Using Command Flags to Specify Build, Run and Install Targets](#using-command-flags-to-specify-build-run-and-install-targets)

## Environment Autodetection

By default *Golang Build* tries to detect all of your Go configuration by
invoking your login shell. It will pull in your `PATH`, `GOPATH`, and any other
environment variables you have set.

## Settings Load Order

Generally, autodetecting the shell environment is sufficient for most users
with a standard Go environment. If your Go configuration is more complex, or
you wish to customize command flags, Golang Build will read settings from the
following sources:

 - [Global Sublime Text Settings](#global-sublime-text-settings)
 - [OS-Specific Settings](#os-specific-settings)
 - [Project-Specific Settings](#project-specific-settings)

Settings are loaded using the following precedence, from most-to-least
specific:

 - OS-specific project settings
 - OS-specific global Sublime Text settings
 - Project settings
 - Global Sublime Text settings
 - Shell environment

### Global Sublime Text Settings

To set variables for use in Sublime Text windows, you will want to edit your
`golang.sublime-settings` file. This can be accessed via the menu:

 1. Preferences
 2. Package Settings
 3. Golang Config
 3. Settings - User

Settings are placed in a json structure. Common settings include:

 - `PATH` - a string containing a list of directories to search for executables
   within. On Windows these are separated by `;`. OS X and Linux use `:` as a
   directory separator.
 - `GOPATH` - a string containing one or more Go workspace paths. Like `PATH`,
   on Windows multiple paths are separated by `;`, on OS X and Linux they are
   separated by `:`.

Other Go environment variables will be used if set. Examples include: `GOOS`,
`GOARCH`, `GOROOT` and `GORACE`. The
[go command documentation](https://golang.org/cmd/go/#hdr-Environment_variables)
has a complete list.

```json
{
    "PATH": "/Users/jsmith/go/bin",
    "GOPATH": "/Users/jsmith/go"
}
```

### OS-Specific Settings

For users that are working on different operating systems, it may be necessary
to segement settings per OS. All settings may be nested under a key of one of
the following strings:

 - "osx"
 - "windows"
 - "linux"

```json
{
    "osx": {
        "PATH": "/Users/jsmith/go/bin",
        "GOPATH": "/Users/jsmith/go"
    },
    "windows": {
        "PATH": "C:\\Users\\jsmith\\go\\bin",
        "GOPATH": "C:\\Users\\jsmith\\go"
    },
    "linux": {
        "PATH": "/home/jsmith/go/bin",
        "GOPATH": "/home/jsmith/go"
    },
}
```

### Project-Specific Settings

When working on Go projects that use different environments, it may be
necessary to define settings in a
[Sublime Text project](http://docs.sublimetext.info/en/latest/file_management/file_management.html#projects)
file. The *Project* menu in Sublime Text provides the interface to create and
edit project files.

Within projects, all Go settings are placed under the `"settings"` key and then
further under a subkey named `"golang"`.

```json
{
    "folders": {
        "/Users/jsmith/projects/myproj"
    },
    "settings": {
        "golang": {
            "PATH": "/Users/jsmith/projects/myproj/env/bin",
            "GOPATH": "/Users/jsmith/projects/myproj/env"
        }
    }
}
```

Project-specific settings may also utilize the OS-specific settings feature.

```json
{
    "folders": {
        "/Users/jsmith/projects/myproj"
    },
    "settings": {
        "golang": {
            "osx": {
                "PATH": "/Users/jsmith/projects/myproj/env/bin",
                "GOPATH": "/Users/jsmith/projects/myproj/env"
            },
            "linux": {
                "PATH": "/home/jsmith/projects/myproj/env/bin",
                "GOPATH": "/home/jsmith/projects/myproj/env"
            }
        }
    }
}
```

## Command Flags

When working with the build system, it may be necessary to set flags to pass
to the `go` executable. Utilizing the various settings locations discussed in
the [Settings Load Order section](#settings-load-order), each build variant may
have its flags customized. The settings names are:

 - `build:flags` for "go build"
 - `run:flags` for "go run"
 - `test:flags` for "go test"
 - `benchmark:flags` for "go test -bench=."
 - `install:flags` for "go install"
 - `clean:flags` for "go clean"
 - `cross_compile:flags` for "go build" with GOOS and GOARCH
 - `get:flags` for "go get"

Any valid flag may be passed to the `go` executable via these settings.

### Formatting Command Flag Settings

Each setting must have a value that is a list of strings. Each list element
contains a single command line argument.

A flag without a value would be formatted as:

```json
{
    "build:flags": ["-x"]
}
```

Multiple flags are formatted as separate strings:

```json
{
    "build:flags": ["-x", "-a"]
}
```

If a flag accepts a value, the value should be added as a second string:

```json
{
    "build:flags": ["-p", "4"]
}
```

Strings arguments may contain spaces. The Golang Build package will ensure
they are properly quoted when invoking the `go ` executable.

```json
{
    "build:flags": ["-ldflags", "-L/usr/local/lib -L/opt/lib"]
}
```

All flags are inserted at the end of the command line arguments, except in the
case of `go get`, where they are placed before the URL to get.

### Command Flag Setting Locations

The most common location to set flag settings will be in a project file:

```json
{
    "folders": {
        "/Users/jsmith/projects/myproj"
    },
    "settings": {
        "golang": {
            "build:flags": ["-a"],
            "install:flags": ["-a"],
            "get:flags": ["-u"]
        }
    }
}
```

As with the `GOPATH` and `PATH` settings, these flag settings may be set on a
per-OS basis, even within project files.

An example of settings for just OS X, within a project file:

```json
{
    "folders": {
        "/Users/jsmith/projects/myproj"
    },
    "settings": {
        "golang": {
            "osx": {
                "build:flags": ["-a", "-race"],
                "install:flags": ["-a", "-race"],
                "get:flags": ["-u"]
            }
        }
    }
}
```

If flags should be applied to all Go builds, irrespective of project, the
settings may be added to the
[global Sublime Text settings](#global-sublime-text-settings):

```json
{
    "build:flags": ["-a", "-race"]
}
```

Do note that settings do not combine from the global Sublime Text settings and
project settings. Instead, any settings in a more specific location will
override those in a less specific location.

### Using Command Flags to Specify Build, Run and Install Targets

The default behavior of the build commands is to execute the `go` tool in the
directory containing the file currently being edited. This behavior is
consistent with other Sublime Text build systems and is what users typically
expect.

With Go projects, you may want to override this default for commands such as
`go install`. Consider a project containing a single executable command
(defined by a Go package containing a main function) in the directory:

```
$GOPATH/src/github.com/username/projectname/mycommand
```

The project contains a large set of library packages that are used by the
`mycommand` program. These libraries are located in:

```
$GOPATH/github.com/username/projectname/users
$GOPATH/github.com/username/projectname/events
```

Running `go install` from within these two directories will result in the
creation of the `.a` files in the `$GOPATH/pkg` directory.

However, it may be more desirable to always have `go install` compile and
install the `mycommand` program into your `$GOPATH/bin` directory, regardless
of the location of the source file you are currently editing.

To achieve this, you can use the flag override mechanism in your project
configuration file:

```json
{
    "folders":
    [
        {
            "path": "/Users/jsmith/workspace/src"
        }
    ],
    "settings": {
        "golang": {
            "install:flags": ["-v", "github.com/myusername/myproject/mycommand"]
        }
    }
}
```

This configuration will cause the following command to be used when running the
`Go: Install` build command:

```
> Environment:
>   GOPATH=/Users/jsmith/workspace-shared:/Users/jsmith/workspace
> Directory: /Users/jsmith
> Command: /Users/jsmith/go15/bin/go install -v github.com/myusername/myprojectname/mycommand
> Output:
github.com/myusername/myprojectname/mycommand
> Elapsed: 0.955s
> Result: Success
```

Another common command to use a custom flag with is `Go: Run`. With the Run
build variant, the file to execute may be specified as either an absolute file
path, or relative to the `$GOPATH/src/` directory.

```json
{
    "folders":
    [
        {
            "path": "/Users/jsmith/workspace/src"
        }
    ],
    "settings": {
        "golang": {
            "run:flags": ["-v", "github.com/myusername/myproject/main.go"]
        }
    }
}
```

If the file path is relative to `$GOPATH/src/`, it will be automatically
expanded so the `go` tool will process it properly. In the case that `$GOPATH`
has multiple entries, the first with a matching filename will be used.
