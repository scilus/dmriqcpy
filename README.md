# dMRIqcpy fork for Imeka QC
Diffusion MRI Quality Check in python

To install dmriqcpy, run the following command: 
```
pip install -e .
```

For Developers
--------------

The python code base should abide with Imeka's Python coding standards, with 
the exception that line wrapping has been kept to 80 characters per line, to 
remain consistent with the base dmriqcpy repository. Black should be run on 
all python files, as described in the procedures, with the argument -l 80 
instead of -l 100, for example :
```
black -l 80 $FILE
```
