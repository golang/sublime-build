# Golang Build

*Golang Build* is a Sublime Text package for compiling Go projects. It provides
integration between Sublime Text and the command line `go` tool.

The package consists of the following features:

 - A Sublime Text build system for executing:
   - `go build`
   - `go run`
   - `go install`
   - `go test` to run Tests or Benchmarks
   - `go clean`
   - Cross-compilation using `go build` with `GOOS` and `GOARCH`
 - Sublime Text command palette commands to:
   - Execute `go get`
   - Open a terminal into a Go workspace

## Installation

The *Golang Build* package is installed by using
[Package Control](https://packagecontrol.io).

 - If Package Control is not installed, follow the [Installation Instructions](https://packagecontrol.io/installation)
 - Open the Sublime Text command palette and run the `Package Control: Install
   Package` command
 - Type `Golang Build` and select the package to perform the installation

## Documentation

### End User

 - [Usage](docs/usage.md)
 - [Configuration](docs/configuration.md)
 - [Commands](docs/commands.md)
 - [Changelog](changelog.md)
 - [License](LICENSE)
 - [Patents](PATENTS)

### Contributor

 - [Contributing](CONTRIBUTING.md)
 - [Design](docs/design.md)
 - [Development](docs/development.md)
 - [Contributors](CONTRIBUTORS)
 - [Authors](AUTHORS)
