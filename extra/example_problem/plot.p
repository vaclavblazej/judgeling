set term png
set output 'pic.png'
set datafile separator ","
plot '.tmp/data/big/sol/radix_sort/time.cvs' using 1:3, \
     '.tmp/data/big/sol/default_library_sort/time.cvs' using 1:2
