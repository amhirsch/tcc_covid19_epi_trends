#!/bin/bash

filename=semester_start_countdown

for format in html python
do
    jupyter nbconvert --to $format $filename.ipynb
done

mv $filename.html docs/index.html
