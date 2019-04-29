# FØCAL

Architecture-aware profiling for computer vision applications.

For each library that your application uses, `f0cal` provides a set of tracepoints that perform efficient runtime inspection of the call stack. Other profiling tools can time function calls; `f0cal` can show you the relationship between call latency, data size, scheduler events, memory caching, and much more.

`f0cal` runs in a development sandbox built on top of `python3-venv` and `conan`. Use it inside the sandbox, just like you would any other Python command line tool. The profiler output is a set of pre-baked reports for your CI/CD pipeline. And if you really want to nerd out, you can access the trace data directly with `pandas`.

## Quick start

We've made compiling and configuring the profiling infrastructure as easy as possible by providing a bootstrap script.

From the bootstrap URL (recommended):

```bash
VENV_DIR=_venv
curl bootstrap.f0cal.com/master | python3 - -v ${VENV_DIR} git
source ${VENV_DIR}/bin/activate
eval $(f0cal env activate -a) # only do this the first time
conan install f0cal-opencv/4.0.1@f0cal/testing --build=missing
f0cal pr add -- <your-exe> <your-exe-args> <...>
f0cal pr view
```

From git:

```bash
VENV_DIR=_venv
git clone https://github.com/f0cal/f0cal && python3 f0cal/scripts/bootstrap.py -v ${VENV_DIR} local
source ${VENV_DIR}/bin/activate
eval $(f0cal env activate -a) # only do this the first time
conan install f0cal-opencv/4.0.1@f0cal/testing --build=missing
f0cal pr add -- <your-exe> <your-exe-args> <...>
f0cal pr view
```

Here's a complete example you can run to test the workflow:

```bash
conan install f0cal-opencv/4.0.1@f0cal/testing --build=missing
conan install invisible_demo/0.1@f0cal/testing
f0cal pr add -- Invisibility_Cloak
f0cal pr view
```

## Output

Simple terminal output:

```
                                    Latency (ms)             Throughput (fps)                     
                              count          min   max  mean              max       min       mean
prefix           width height                                                                     
cv::add          640   480     1158         0.02  0.09  0.05         48461.35  10861.18   19247.80
cv::addWeighted  640   480      772         0.20  1.09  0.47          5059.68    919.17    2142.63
cv::bitwise_and  640   480     2316         0.29  1.42  0.74          3456.45    704.70    1354.75
cv::bitwise_not  640   480      772         0.01  0.18  0.04         69132.39   5417.38   25808.52
cv::countNonZero 3     3       1158         0.00  0.05  0.00       1221001.22  18233.54  302150.20
cv::cvtColor     640   480     2050         0.03  8.16  1.16         33158.70    122.55     859.75
cv::dilate       3     3        772         0.06  0.38  0.17         17585.82   2637.09    5760.23
                 640   480     1544         0.06  0.38  0.17         17585.82   2637.09    5760.23
cv::erode        3     3        386         0.07  0.34  0.19         14511.05   2926.26    5187.10
                 640   480      772         0.07  0.34  0.19         14511.05   2926.26    5187.10
cv::inRange      1     4       1544         0.25  1.17  0.80          3983.87    852.97    1253.34
                 640   480      772         0.25  1.17  0.80          3983.87    852.97    1253.34
cv::morphologyEx 3     3        772         0.06  0.74  0.28         16902.17   1343.41    3574.38
                 640   480     1544         0.06  0.74  0.28         16902.17   1343.41    3574.38
```

HTML output:

![HTML table](/html_table.png?raw=true "Profiler output as HTML")

## Library support

To view a complete list of the AI/ML/CV libraries that `f0cal` provides tracepoints for:

```bash
conan search -r f0cal
```
