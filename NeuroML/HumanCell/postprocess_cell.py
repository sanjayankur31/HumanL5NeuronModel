#!/usr/bin/env python3
"""
Post process cell to ready it for modelling

File: postprocess_cell.py

Copyright 2022 Ankur Sinha
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import neuroml
from neuroml.loaders import read_neuroml2_file
from neuroml.neuro_lex_ids import neuro_lex_ids
from pyneuroml.pynml import write_neuroml2_file


def post_process_cell(cellname: str):
    """Load a cell, and clean it to prepare it for further modifications.

    These operations are common for all cells.

    :param cellname: name of cell.
        the file containing the cell should then be <cell>.morph.cell.nml
    :returns: document with cell
    :rtype: neuroml.NeuroMLDocument

    """
    celldoc = read_neuroml2_file(
        f"{cellname}.morph.cell.nml"
    )  # type: neuroml.NeuroMLDocument
    cell = celldoc.cells[0]  # type: neuroml.Cell
    celldoc.networks = []
    cell.id = cellname
    cell.notes += ". Reference: Scott Rich, Homeira Moradi Chameh, Vladislav Sekulic, Taufik A Valiante, Frances K Skinner, Modeling Reveals Human-Rodent Differences in H-Current Kinetics Influencing Resonance in Cortical Layer 5 Neurons, Cerebral Cortex, Volume 31, Issue 2, February 2021, Pages 845-872, https://doi.org/10.1093/cercor/bhaa261"

    # create default groups if they don't exist
    [
        default_all_group,
        default_soma_group,
        default_dendrite_group,
        default_axon_group,
    ] = cell.setup_default_segment_groups(
        use_convention=True,
        default_groups=["all", "soma_group", "dendrite_group", "axon_group"],
    )

    # create apical and basal groups
    basal_group = cell.add_segment_group(
        "basal_dendrite_group",
        neuro_lex_id=neuro_lex_ids["dend"],
        notes="Basal dendrites",
    )
    apical_group = cell.add_segment_group(
        "apical_dendrite_group",
        neuro_lex_id=neuro_lex_ids["dend"],
        notes="Apical dendrite_group",
    )

    # from subsets in ModelSetup.hoc:
    soma_segs = (
        list(range(0, 6 + 1))
        + list(range(9, 10 + 1))
        + [14]
        + list(range(18, 21 + 1))
        + [32]
    )
    axonal_segs = [13]
    apical_segs = (
        [7, 15, 16]
        + list(range(24, 27 + 1))
        + list(range(37, 44 + 1))
        + list(range(59, 66 + 1))
        + list(range(85, 94 + 1))
        + list(range(109, 114 + 1))
        + list(range(123, 128 + 1))
        + list(range(131, 210 + 1))
    )
    basal_segs = (
        [8, 11, 2, 17, 22, 23]
        + list(range(28, 31 + 1))
        + list(range(33, 36 + 1))
        + list(range(45, 58 + 1))
        + list(range(67, 84 + 1))
        + list(range(95, 108 + 1))
        + list(range(115, 122 + 1))
        + [129, 130]
    )
    # populate default groups
    print("Populating necessary segment groups")
    for sg in cell.morphology.segment_groups:
        # segment group id is of the form:
        # filament_100000042_0
        if sg.id.startswith("filament"):
            sg_index = sg.id.split("_")[2]
            if int(sg_index) in soma_segs:
                default_soma_group.add(neuroml.Include, segment_groups=sg.id)
            if int(sg_index) in axonal_segs:
                default_axon_group.add(neuroml.Include, segment_groups=sg.id)
            if int(sg_index) in apical_segs:
                apical_group.add(neuroml.Include, segment_groups=sg.id)
            if int(sg_index) in basal_segs:
                basal_group.add(neuroml.Include, segment_groups=sg.id)

    default_dendrite_group.includes = []
    default_dendrite_group.includes.append(neuroml.Include(segment_groups=apical_group.id))
    default_dendrite_group.includes.append(neuroml.Include(segment_groups=basal_group.id))

    print("Optimising groups")
    cell.optimise_segment_groups()
    print("Reordering groups")
    cell.reorder_segment_groups()


    # biophys
    celldoc.add("IncludeType", href="channels/CaDynamics_E2_NML2.nml", validate=False)
    celldoc.add("IncludeType", href="channels/CaDynamics_E2_NML2__decay460__gamma5_01Emin4.nml", validate=False)
    celldoc.add("IncludeType", href="channels/CaDynamics_E2_NML2__decay122__gamma5_09Emin4.nml", validate=False)

    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="pas",
                             ion_channel="pas",
                             cond_density="1.75E-5 S_per_cm2",
                             erev="-84.395 mV",
                             group_id="all",
                             ion="non_specific",
                             ion_chan_def_file="channels/pas.channel.nml")
    cell.set_resistivity("0.49573 kohm_cm", group_id="all")
    cell.set_specific_capacitance("1.5967 uF_per_cm2", group_id="all")
    cell.set_init_memb_potential("-80mV")

    write_neuroml2_file(celldoc, f"{cellname}.cell.nml")


if __name__ == "__main__":
    post_process_cell("HL5PC")
