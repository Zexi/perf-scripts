#!/usr/bin/python
# Keep this dead simple - read from stdin, write to stdout, modify
# lines if env variables are set:
# * any lines in [] mark the start of a section
# * anything else containing '=' is a setting
# * section and setting variable names all have '-' converted to '_'
import sys, os

prefix="IX"
delimr="_"
section=""

for line in sys.stdin:
    if line.strip().startswith("["):
        # [section]
        section = line.strip().strip("[]").replace("-","_").upper()
        sys.stdout.write(line)
    elif len(line.split("=")) == 2:
        # setting
        setting = line.split("=")[0].strip("    #;")
        env_var = prefix + delimr + section + delimr \
            + setting.replace("-","_").upper()
        if os.environ.get(env_var):
            print ('# setting changed by environment variable '+env_var)
            print ('# was: '+line.strip())
            print (setting +' = '+ os.environ.get(env_var) )
        else:
            sys.stdout.write(line)
    else:
        sys.stdout.write(line)
