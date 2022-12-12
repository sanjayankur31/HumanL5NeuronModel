#!/usr/bin/gnuplot
# 
# Filename: NeuroML/HumanCell/plot_iv.plt
#
# Copyright 2022 Ankur Sinha
# Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
#
# Usage: gnuplot -e "filename=..." plot_iv.plt

set terminal qt enhanced
set xlabel 'time (s)'
set ylabel 'v (mV)'
plot for [i=2:*] filename using 1:i with lines title columnhead(i)
