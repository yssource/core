# FØCAL

Architecture-aware profiling for computer vision applications.

For each library that your application uses, `f0cal` provides a set of tracepoints that perform efficient runtime inspection of the call stack. Other profiling tools can time function calls; `f0cal` can show you the relationship between call latency, data size, scheduler events, memory caching, and much more.

`f0cal` runs in a development sandbox built on top of `python3-venv` and `conan`. Use it inside the sandbox, just like you would any other Python command line tool. The profiler output is a set of pre-baked reports your CI/CD reporting. And if you really want to nerd out, you can access the trace data directly with `pandas`.

## Quick start

We've made compiling and configuring the profiling infrastructure as easy as possible by providing a bootstrap script.

From the bootstrap URL (reccommended):

```bash
$ curl bootstrap.f0cal.com/master | python3 - -v <venv-dir> git
$ source <venv-dir>/bin/activate
$ eval $(f0cal env activate) # only do this the first time
$ conan install f0cal-opencv/4.0.1@f0cal/testing
$ f0cal pr add -- <your-opencv-exe> <your-exe-args> <...>
```

From git:

```bash
$ git clone https://github.com/f0cal/public && python3 public/scripts/bootstrap.py -v <venv-dir> local
...
```
