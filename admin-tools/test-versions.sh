#!/bin/bash
# Run "make check" over lots of python versions
for v in 3.7 3.8 3.9 3.10 3.11 3.12 ; do
    echo ==== $v =====;
    pyenv local $v && make check;
done
