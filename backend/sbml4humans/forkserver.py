"""Imported first by the forkserver of the validation, before anything else.

numpy, which the report imports through pint and pymetadata, starts the thread
pool of OpenBLAS at its import, a thread per cpu with a stack of its own. In
the forkserver it would make the process which forks the children a
multithreaded one, and every child would start with the address space of those
stacks, a gigabyte on 20 cpus, which counts against its memory limit. The
native thread pools are single threaded in the forkserver alone; the server
keeps its own.
"""

import os


for _variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_variable] = "1"
