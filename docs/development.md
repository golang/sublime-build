# *Golang Build* Development

## Setup

 - Install [Package Coverage](https://packagecontrol.io/packages/Package%20Coverage)
   to run tests
 - Install this package by executing
   `git clone https://go.googlesource.com/sublime-build "Golang Build"`
   inside of your `Packages/` folder
 - Use the Package Control command "Satisfy Dependencies" to install the
   `shellenv`, `newterm`, `package_events` and `golangconfig` dependencies
   and then restart Sublime Text

## General Notes

 - All code must pass the checks of the Sublime Text package
   [Python Flake8 Lint](https://packagecontrol.io/packages/Python%20Flake8%20Lint).
   The `python_interpreter` setting should be set to `internal`.
 - Tests and coverage measurement can not be run in the UI thread since the
   tests interact with the user interface and would become deadlocked
 - Sublime Text 2 and 3 must be supported, on Windows, OS X and Linux
 - All functions must include a full docstring with parameter and return types
   and a list of exceptions raised
 - All code should use a consistent Python header

```python
# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function
```
