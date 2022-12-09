#!/usr/bin/env python3
"""
Post process cell to ready it for modelling

File: postprocess_cell.py

Copyright 2022 Ankur Sinha
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

import numpy
import neuroml
from neuroml.loaders import read_neuroml2_file
from neuroml.neuro_lex_ids import neuro_lex_ids
from pyneuroml.pynml import write_neuroml2_file
from pyneuroml.analysis import generate_current_vs_frequency_curve


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

    # somatic
    cell.set_specific_capacitance("1 uF_per_cm2", group_id=default_soma_group.id)

    # K
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="SK_E2_somatic",
                             ion_channel="SK_E2",
                             cond_density="2.4536e-09 S_per_cm2",
                             erev="-77 mV",
                             group_id=default_soma_group.id,
                             ion="k",
                             ion_chan_def_file="channels/SK_E2.channel.nml")
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="SKv3_1_somatic",
                             ion_channel="SKv3_1",
                             cond_density="0.04 S_per_cm2",
                             erev="-77 mV",
                             group_id=default_soma_group.id,
                             ion="k",
                             ion_chan_def_file="channels/SKv3_1.channel.nml")
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="K_Tst_somatic",
                             ion_channel="K_Tst",
                             cond_density="2e-05 S_per_cm2",
                             erev="-77 mV",
                             group_id=default_soma_group.id,
                             ion="k",
                             ion_chan_def_file="channels/K_Tst.channel.nml")
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="K_Pst_somatic",
                             ion_channel="K_Pst",
                             cond_density="0.065 S_per_cm2",
                             erev="-77 mV",
                             group_id=default_soma_group.id,
                             ion="k",
                             ion_chan_def_file="channels/K_Pst.channel.nml")
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="Ih_somatic",
                             ion_channel="Ih",
                             cond_density="5.135E-05 S_per_cm2",
                             erev="-49.85 mV",
                             group_id=default_soma_group.id,
                             ion="hcn",
                             ion_chan_def_file="channels/Ih.channel.nml")

    # Na
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="NaTa_t_somatic",
                             ion_channel="NaTa_t",
                             cond_density="2.1 S_per_cm2",
                             erev="50 mV",
                             group_id=default_soma_group.id,
                             ion="na",
                             ion_chan_def_file="channels/NaTa_t.channel.nml")
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="Nap_Et2_somatic",
                             ion_channel="Nap_Et2",
                             cond_density="1E-6 S_per_cm2",
                             erev="50 mV",
                             group_id=default_soma_group.id,
                             ion="na",
                             ion_chan_def_file="channels/Nap_Et2.channel.nml")
    # Ca
    # internal and external concentrations are set to defaults that NEURON
    # starts with
    cell.add_intracellular_property("Species", validate=False,
                                    id="ca",
                                    concentration_model="CaDynamics_E2_NML2__decay460__gamma5_01Emin4",
                                    ion="ca",
                                    initial_concentration="5.0E-11 mol_per_cm3",
                                    initial_ext_concentration="2.0E-6 mol_per_cm3",
                                    segment_groups=default_soma_group.id)
    # https://www.neuron.yale.edu/neuron/static/new_doc/modelspec/programmatic/ions.html
    cell.add_channel_density_v(
        "ChannelDensityNernst",
        nml_cell_doc=celldoc,
        id="Ca_HVA_somatic",
        ion_channel="Ca_HVA",
        cond_density="5.6938e-09 S_per_cm2",
        segment_groups=default_soma_group.id,
        ion="ca",
        ion_chan_def_file="channels/Ca_HVA.channel.nml")
    cell.add_channel_density_v(
        "ChannelDensityNernst",
        nml_cell_doc=celldoc,
        id="Ca_LVAst_somatic",
        ion_channel="Ca_LVAst",
        cond_density="0.00099839 S_per_cm2",
        segment_groups=default_soma_group.id,
        ion="ca",
        ion_chan_def_file="channels/Ca_LVAst.channel.nml")

    # apical
    # K
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="SK_E2_apical",
                             ion_channel="SK_E2",
                             cond_density="2.4536e-09 S_per_cm2",
                             erev="-77 mV",
                             group_id=apical_group.id,
                             ion="k",
                             ion_chan_def_file="channels/SK_E2.channel.nml")
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="SKv3_1_apical",
                             ion_channel="SKv3_1",
                             cond_density="0.04 S_per_cm2",
                             erev="-77 mV",
                             group_id=apical_group.id,
                             ion="k",
                             ion_chan_def_file="channels/SKv3_1.channel.nml")
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="Im_apical",
                             ion_channel="Im",
                             cond_density=".0002 S_per_cm2",
                             erev="-77 mV",
                             group_id=apical_group.id,
                             ion="k",
                             ion_chan_def_file="channels/Im.channel.nml")
    sg.add(
        "InhomogeneousParameter",
        id="PathLengthOverApicDends",
        variable="p",
        metric="Path Length from root",
        proximal=sg.component_factory(
            "ProximalDetails",
            translation_start="0")
    )
    # distribute Ih
    cdnonuniform_Ih = cell.add_channel_density_v(
        "ChannelDensityNonUniform",
        nml_cell_doc=celldoc,
        id="Ih_apical",
        ion_channel="Ih",
        ion="hcn",
        erev="-49.85 mV",
        validate=False
    )
    varparam_Ih = cdnonuniform_Ih.add(
        "VariableParameter",
        parameter="condDensity",
        segment_groups=sg.id,
        validate=False
    )
    # 0.0002 S/cm2 is 2 S/m2
    # 5.135e-05 S/cm2 is 5.135E-1 S/m2
    varparam_Ih.add(
        "InhomogeneousValue",
        inhomogeneous_parameters="PathLengthOverApicDends",
        value="5.135E-01 * ((2.087 * exp( 3.6161 * (p/1000))) - 0.8696)"
    )

    cdnonuniform_ca_lva = cell.add_channel_density_v(
        "ChannelDensityNonUniformNernst",
        nml_cell_doc=celldoc,
        id="Ca_LVA_apic",
        ion_channel="Ca_LVAst",
        ion="ca",
        validate=False
    )
    varparam_ca_lva = cdnonuniform_ca_lva.add(
        "VariableParameter",
        parameter="condDensity",
        segment_groups=sg.id,
        validate=False
    )
    # The conditional is implemented using a heaviside function:
    # https://github.com/NeuroML/org.neuroml.export/blob/master/src/main/java/org/neuroml/export/neuron/NRNUtils.java#L174
    # if both values in H are true, 99 is added to 1 = 100
    # otherwise, 1
    varparam_ca_lva.add(
        "InhomogeneousValue",
        inhomogeneous_parameters="PathLengthOverApicDends",
        value="1E8 * 0.00099839 * 1E-4 * (1 + (99 * (H(p - 360) * H(600 - p))))"
    )
    cdnonuniform_ca_hva = cell.add_channel_density_v(
        "ChannelDensityNonUniformNernst",
        nml_cell_doc=celldoc,
        id="Ca_HVA_apic",
        ion_channel="Ca_HVA",
        ion="ca",
        validate=False
    )
    varparam_ca_hva = cdnonuniform_ca_hva.add(
        "VariableParameter",
        parameter="condDensity",
        segment_groups=sg.id,
        validate=False
    )
    # The conditional is implemented using a heaviside function:
    # https://github.com/NeuroML/org.neuroml.export/blob/master/src/main/java/org/neuroml/export/neuron/NRNUtils.java#L174
    # if both values in H are true, 9 is added to 1 = 10
    # otherwise, 1
    varparam_ca_hva.add(
        "InhomogeneousValue",
        inhomogeneous_parameters="PathLengthOverApicDends",
        value="1E8 * 5.6938e-09 * 1E-4 * (1 + (9 * (H(p - 360) * H(600 - p))))"
    )
    # Na
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="NaTa_t_apical",
                             ion_channel="NaTa_t",
                             cond_density="0.001 S_per_cm2",
                             erev="50 mV",
                             group_id=apical_group.id,
                             ion="na",
                             ion_chan_def_file="channels/NaTa_t.channel.nml")

    # basal
    cell.add_channel_density(nml_cell_doc=celldoc,
                             cd_id="Ih_basal",
                             ion_channel="Ih",
                             cond_density="5.135E-05 S_per_cm2",
                             erev="-49.85 mV",
                             group_id=basal_group.id,
                             ion="hcn",
                             ion_chan_def_file="channels/Ih.channel.nml")

    # axonal
    # nothing here

    write_neuroml2_file(celldoc, f"{cellname}.cell.nml")


def analyse_HL5PC(hyperpolarising: bool = True, depolarising: bool = True):
    """Generate various curves for HL5PC cells

    :returns: None

    """
    cellname = "HL5PC"
    print(f"Analysing {cellname}")
    generate_current_vs_frequency_curve(
        nml2_file=f"{cellname}.cell.nml",
        cell_id=cellname,
        custom_amps_nA=[-400E-3, -350E-3, -300E-3, -250E-3, -50E-3, 50E-3, 100E-3, 150E-3],
        temperature="34 degC",
        pre_zero_pulse=1000,
        post_zero_pulse=1000,
        plot_voltage_traces=True,
        plot_iv=True,
        plot_if=False,
        simulator="jNeuroML_NEURON",
        analysis_delay=300.,
        analysis_duration=1000.,
        num_processors=8,
    )


if __name__ == "__main__":
    post_process_cell("HL5PC")
    analyse_HL5PC()
