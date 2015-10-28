# *Golang Build* Usage

The primary functionality of the *Golang Build* package is the *Go* build
system. It includes a number of what Sublime Text refers to as "variants."
It also includes a couple of regular Sublime Text commands for common, related
tasks.

 - [Build System](#build-system)
 - [Other Commands](#other-commands)
 - [Configuration](#configuration)
 - [Commands](#commands)

## Build System

To use the *Go* build system, open the *Tools > Build System* menu and select
*Go*.

The variants included with the build system include:

 - **Build**, which executes `go build`
 - **Run**, which executes `go run` with the current filepath
 - **Test**, which executes `go test`
 - **Install**, which executes `go install`
 - **Cross-Compile (Interactive)**, which executes `go build` with `GOOS` and
   `GOARCH` set
 - **Clean**, which executes `go clean`

Once the *Go* build system is selected, the command palette can be used to run
any of the variants.

On Sublime Text 3, the command palette entries will be:

 - `Build with: Go`
 - `Build with: Go - Run`
 - `Build with: Go - Test`
 - `Build with: Go - Install`
 - `Build with: Go - Cross-Compile (Interactive)`
 - `Build with: Go - Clean`

On Sublime Text 2, the command palette entries will be:

 - `Build: Build`
 - `Build: Run`
 - `Build: Test`
 - `Build: Install`
 - `Build: Cross-Compile (Interactive)`
 - `Build: Clean`

### Cancelling a Build

If a build is running and needs to be stopped, the command palette will contain
an extra entry `Go: Cancel Build`.

### Reopening Build Results

If the output panel for a build is closed, it can be re-opened by using the
command palette to run `Go: Reopen Build Output`. *Once a new build is
started, the old build output is erased.*

## Other Commands

In addition to the build system variants, two other command palette commands are
available:

 - `Go: Get`, which executes `go get` after prompting for a URL
 - `Go: Open Terminal`, which opens a terminal and sets relevant Go
   environment variables

## Configuration

To control the environment variables used with the build system, please read
the [configuration documentation](configuration.md).

## Commands

For information on the available commands, their arguments, example key
bindings and command palette entries, please read the
[commands documentation](commands.md).
