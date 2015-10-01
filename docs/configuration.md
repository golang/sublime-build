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

 - `PATH` - a list of directories to search for executables within. On Windows
   these are separated by `;`. OS X and Linux use `:` as a directory separator.
 - `GOPATH` - a string of the path to the root of your Go environment

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
 - `test:flags` for "go test"
 - `install:flags` for "go install"
 - `clean:flags` for "go clean"
 - `cross_compile:flags` for "go build" with GOOS and GOARCH
 - `get:flags` for "go get"

Each setting must have a value that is a list of strings.

The most common location to set these settings will be in a project file:

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
