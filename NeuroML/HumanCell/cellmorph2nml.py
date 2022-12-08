#!/usr/bin/env python3
"""
Convert cell morphology to NeuroML.

We only export morphologies here. We add the biophysics manually.

File: NeuroML2/scripts/cell2nml.py

Copyright 2022 Ankur Sinha
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import os
import sys

import pyneuroml
from pyneuroml.neuron import export_to_neuroml2
from pyneuroml.plot.PlotMorphology import plot_2D
from neuron import h


def main(acell):
    """Main runner method.

    :param acell: name of cell
    :returns: None

    """
    loader_hoc_file = f"{acell}_loader.hoc"
    loader_hoc_file_txt = """
    /*load_file("nrngui.hoc")*/
    load_file("stdrun.hoc")

    //=================== creating cell object ===========================
    load_file("import3d.hoc")
    objref newcell

    load_file("../../HumanCell/ModelSetup.hoc")

    define_shape()
    """

    with open(loader_hoc_file, 'w') as f:
        print(loader_hoc_file_txt, file=f)

    export_to_neuroml2(loader_hoc_file, f"{acell}.morph.cell.nml",
                       includeBiophysicalProperties=False, validate=False)

    os.remove(loader_hoc_file)


def plot_morph(acell):
    """Plot morphology

    :param acell: name of cell
    :returns: None
    """
    for plane in ["xy", "yz", "zx"]:
        plot_2D(f"{acell}.morph.cell.nml", plane2d=plane, nogui=True,
                save_to_file=f"{acell}.morph.{plane}.png")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("This script only accepts one argument.")
        sys.exit(1)
    main(sys.argv[1])
    plot_morph(sys.argv[1])
