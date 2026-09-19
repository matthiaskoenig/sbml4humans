# Reports from python

SBML4Humans is also a python package. One call opens the report of a file of your machine in the browser, which is the fastest way to look at a model you have just written with a script:

```python
from sbml4humans import show

show("model.xml")
```

The same from the shell:

```bash
sbml4humans model.xml
```

The path is an SBML file, plain or gzipped, or a COMBINE archive, the [formats](inputs.md#the-accepted-formats) the web application accepts. The report is the one the web application shows, and [Reading a report](report.md) describes it.

## Installation

The package needs python 3.14 or newer:

```bash
pip install sbml4humans
```

It ships the application itself, the api and the built user interface, so nothing else has to be installed or started.

## What happens

The file never leaves your machine. `show` does not send it to sbml4humans.de: it starts a small server on your machine, which listens on a free port of `127.0.0.1` only, lets it create the report, and opens `http://127.0.0.1:<port>/report?local=<token>` in your browser. Once the package is installed the report needs no network, with one exception: the labels of the [annotations](report.md#the-inspector) are looked up at the annotation services when you open an element which has some.

- The report is created when `show` is called. A temporary file may be deleted right afterwards, and a file which changes later is shown as it was; call `show` again to see the new version.
- The server is a process of its own and outlives the call, so a script which calls `show` and ends leaves a working page behind. The next call uses the same server. It keeps the last 16 reports in memory.
- The server ends itself a quarter of an hour after the last report was closed, an open report keeps it alive. `sbml4humans --stop`, or `sbml4humans.stop()`, ends it right away.
- A model of the comp package is shown with the files it is built from. The path is a path you chose, so the files next to it which its [external model definitions](report.md#models-of-other-documents) name are read as further entries of the report, which an upload to the web application cannot do.

`show` returns the url of the report. `show(path, open_browser=False)` and `sbml4humans --no-browser model.xml` create the report and give you the url without opening it, for a notebook or a remote session in which you open the address yourself.

A file which does not exist raises `FileNotFoundError`, and a file which holds no SBML model raises `ValueError` with the errors libsbml reports for it, the ones the web application shows in [the same case](inputs.md#when-a-model-cannot-be-read). The command prints the message and exits with the code 1.

## Who can read the reports

The server answers requests from your own machine only, and it only answers the page it serves itself: a request which names another host, or which comes from the page of another site in your browser, is refused. Creating a report of a path and ending the server need a secret which the server writes into a file only your user can read (`server.json` in the `sbml4humans` directory of your user cache directory, next to the log of the server). The address of a report carries a random token of 128 bits, and the report is read by whoever has that address on your machine.
