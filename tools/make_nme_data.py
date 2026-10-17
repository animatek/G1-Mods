#!/usr/bin/env python3
"""Adds the module types of the test OS to NME's data: modules.xml and the classic theme.

    tools/make_nme_data.py ../Nomad2026/data out/nme-data      # copies, in out/
    tools/make_nme_data.py ../Nomad2026/data ../Nomad2026/data # in place (NME's g1-mods branch)

Each new type is a text copy of an existing module's entry in both files, with its index,
component id, names and connectors changed, so the rest of each file stays byte for byte as NME
has it. A type already in a file is replaced by a fresh copy, so running it twice changes
nothing and a changed definition reaches the file.
"""
import os
import re
import sys

# new type: (donor type, name, full name, [(old, new) in modules.xml], [(old, new) in the theme])
NEW_TYPES = {
    119: (19, "Mixer Inv", "3 Inputs Mixer, input 1 inverted (G1-Mods test)", [], []),
    120: (89, None, None, None, None),   # written whole: FULL_ENTRIES below
    122: (53, None, None, None, None),   # written whole: FULL_ENTRIES below
    123: (91, None, None, None, None),   # written whole: FULL_ENTRIES below
    124: (123, None, None, None, None),  # written whole: FULL_ENTRIES below
    125: (124, None, None, None, None),  # written whole: FULL_ENTRIES below
    126: (120, None, None, None, None),  # written whole: FULL_ENTRIES below
    101: (126, None, None, None, None),  # written whole: FULL_ENTRIES below
    121: (19, "Mix1-1A", "1 Input Chain Mixer (G1-Mods)",
          [('name="in1"', 'name="in"'), ('name="in2"', 'name="chain"'),
           ('\n    <connector component-id="c3" index="2" name="in3" type="input" signal="audio" />', ''),
           ('<parameter component-id="p2" index="1" name="in level 2" class="parameter" defaultValue="127" extension="m2" role="audio,in,level" />',
            '<parameter component-id="p2" index="1" name="on" class="parameter" maxValue="1" defaultValue="1" formatter="fmtOffOn" extension="m2" />'),
           ('\n    <parameter component-id="p3" index="2" name="in level 3" class="parameter" defaultValue="127" extension="m3" role="audio,in,level" />', ''),
           ('<parameter component-id="m2" index="1" name="morph:in level 2" class="morph" role="morph"  minValue="-127" maxValue="127" />',
            '<parameter component-id="m2" index="1" name="morph:on" class="morph" role="morph"  minValue="-1" maxValue="1" />'),
           ('\n    <parameter component-id="m3" index="2" name="morph:in level 3" class="morph" role="morph"  minValue="-127" maxValue="127" />', ''),
           ('name="in level 1"', 'name="level"'), ('name="morph:in level 1"', 'name="morph:level"')],
          [("<name>Mixer</name>", "<name>Mix1-1A</name>"),
           ('alt="in1"', 'alt="in"'),
           ('<connector x="103" y="8" size="13" class="cAUDIO">\n\t\t\t<connector component-id="c2" alt="in2" />',
            '<connector x="190" y="8" size="13" class="cAUDIO">\n\t\t\t<connector component-id="c2" alt="chain" />'),
           ('\n\t\t<connector x="154" y="8" size="13" class="cAUDIO">\n\t\t\t<connector component-id="c3" alt="in3" />\n\t\t</connector>', ''),
           ('alt="in level 1"', 'alt="level"'),
           ('<knob x="120" y="4" size="21">\n\t\t\t<parameter component-id="p2" alt="in level 2" />\n\t\t</knob>',
            '<button x="100" y="7" width="30" height="16" cyclic="true" landscape="false">\n\t\t\t<parameter component-id="p2" alt="on" />\n\t\t\t<btn index="0">Ch 1</btn>\n\t\t\t<btn index="1">Ch 1</btn>\n\t\t</button>'),
           ('\n\t\t<knob x="171" y="4" size="21">\n\t\t\t<parameter component-id="p3" alt="in level 3" />\n\t\t</knob>', ''),
           ('\n\t</module>', '\n\t\t<label x="158" y="9">Chain</label>\n\t</module>')]),
}


# Types written whole (no donor's entry to adapt): (modules.xml entry, theme entry), each placed
# right after its donor's. The images are the donor's until the module has its own.
FULL_ENTRIES = {
    120: ("""
  <module component-id="m120" index="120" name="FlipFlop" fullname="Flip-Flop D/RS (G1-Mods)" category="Logic (mods)">
    <image type="screenshot" src="img/modules/module-89.png" width="256" height="30" />
    <image type="icon16x16" src="img/icons/16x16/module-id-89.png" width="16" height="16" />
    <image type="icon32x32" src="img/icons/32x32/module-id-89.png" width="32" height="32" />
    <connector component-id="c1" index="0" name="clk" type="input" signal="logic" />
    <connector component-id="c2" index="1" name="in" type="input" signal="logic" />
    <connector component-id="c3" index="2" name="rst" type="input" signal="logic" />
    <connector component-id="c4" index="0" name="Q" type="output" signal="logic" />
    <connector component-id="c5" index="1" name="NotQ" type="output" signal="logic" />
    <light component-id="ledQ" name="LED Q" index="0" type="led" />
    <!-- parameter(s) -->
    <parameter component-id="p1" index="0" name="type" class="parameter" maxValue="1" extension="m1" />
    <parameter component-id="m1" index="0" name="morph:type" class="morph" role="morph"  minValue="-1" maxValue="1" />
    <!-- custom attributes -->
    <attribute name="cycles" type="double" value="0.8" />
    <attribute name="x-mem" type="double" value="0.25" />
    <attribute name="y-mem" type="double" value="0.0" />
    <attribute name="prog-mem" type="double" value="1.75" />
    <attribute name="dyn-mem" type="double" value="0.25" />
    <attribute name="zero-page" type="double" value="0.875" />
    <attribute name="height" type="integer" value="2" />
    <attribute name="background" value="#fc8642" />
  </module>""", """
\t<module component-id="m120" width="255" height="30">
\t\t<name>FlipFlop</name>
\t\t<label x="96" y="17">Rst</label>
\t\t<connector x="114" y="16" size="13" class="cLOGIC">
\t\t\t<connector component-id="c3" alt="rst" />
\t\t</connector>
\t\t<label x="132" y="17">Clk</label>
\t\t<connector x="152" y="16" size="13" class="cLOGIC">
\t\t\t<connector component-id="c1" alt="clk" />
\t\t</connector>
\t\t<label x="164" y="2">In</label>
\t\t<connector x="170" y="1" size="13" class="cLOGIC">
\t\t\t<connector component-id="c2" alt="in" />
\t\t</connector>
\t\t<button x="186" y="7" width="26" height="16" cyclic="true" landscape="false">
\t\t\t<parameter component-id="p1" alt="type" />
\t\t\t<btn index="0">D</btn>
\t\t\t<btn index="1">RS</btn>
\t\t</button>
\t\t<light component-id="ledQ" type="led" x="226" y="4" width="7" height="7" />
\t\t<label x="218" y="2">Q</label>
\t\t<connector x="236" y="1" size="13" class="cLOGIC">
\t\t\t<connector component-id="c4" alt="Q" />
\t\t</connector>
\t\t<label x="216" y="17">nQ</label>
\t\t<connector x="236" y="16" size="13" class="cLOGIC">
\t\t\t<connector component-id="c5" alt="NotQ" />
\t\t</connector>
\t</module>"""),
    122: ("""
  <module component-id="m122" index="122" name="NoiseS&amp;H" fullname="Noise Sample and Hold, with an inverted out (G1-Mods)" category="Audio (mods)">
    <image type="screenshot" src="img/modules/module-53.png" width="256" height="30" />
    <image type="icon16x16" src="img/icons/16x16/module-id-53.png" width="16" height="16" />
    <image type="icon32x32" src="img/icons/32x32/module-id-53.png" width="32" height="32" />
    <connector component-id="c1" index="0" name="trig" type="input" signal="logic" />
    <connector component-id="c2" index="0" name="out" type="output" signal="control" />
    <connector component-id="c3" index="1" name="inv" type="output" signal="control" />
    <!-- parameter(s) -->
    <parameter component-id="p1" index="0" name="range" class="parameter" maxValue="4" formatter="fmtOctaves1to5" extension="m1" />
    <parameter component-id="p2" index="1" name="unipolar" class="parameter" maxValue="1" formatter="fmtOffOn" extension="m2" />
    <parameter component-id="m1" index="0" name="morph:range" class="morph" role="morph"  minValue="-4" maxValue="4" />
    <parameter component-id="m2" index="1" name="morph:unipolar" class="morph" role="morph"  minValue="-1" maxValue="1" />
    <!-- custom attributes -->
    <attribute name="cycles" type="double" value="0.35" />
    <attribute name="x-mem" type="double" value="0.2" />
    <attribute name="y-mem" type="double" value="0.0" />
    <attribute name="prog-mem" type="double" value="0.75" />
    <attribute name="dyn-mem" type="double" value="0.25" />
    <attribute name="zero-page" type="double" value="0.875" />
    <attribute name="height" type="integer" value="2" />
    <attribute name="background" value="#eda0a4" />
  </module>""", """
\t<module component-id="m122" width="255" height="30">
\t\t<name>Noise S&amp;H</name>
\t\t<textDisplay x="50" y="8" width="34" height="16">
\t\t\t<parameter component-id="p1" alt="range" />
\t\t</textDisplay>
\t\t<knob x="87" y="4" size="21">
\t\t\t<parameter component-id="p1" alt="range" />
\t\t</knob>
\t\t<button x="112" y="8" width="24" height="16" cyclic="true" landscape="false">
\t\t\t<parameter component-id="p2" alt="unipolar" />
\t\t\t<btn index="0">Bi</btn>
\t\t\t<btn index="1">Uni</btn>
\t\t</button>
\t\t<label x="140" y="9">Trig</label>
\t\t<connector x="160" y="8" size="13" class="cLOGIC">
\t\t\t<connector component-id="c1" alt="trig" />
\t\t</connector>
\t\t<label x="178" y="9">Inv</label>
\t\t<connector x="196" y="8" size="13" class="cCONTROL">
\t\t\t<connector component-id="c3" alt="inv" />
\t\t</connector>
\t\t<label x="214" y="9">Out</label>
\t\t<connector x="236" y="8" size="13" class="cCONTROL">
\t\t\t<connector component-id="c2" alt="out" />
\t\t</connector>
\t</module>"""),
    123: ("""
  <module component-id="m123" index="123" name="5-StepSeq" fullname="5-Step Sequencer, one knob a step (G1-Mods)" category="Sequencer (mods)">
    <image type="screenshot" src="img/modules/module-91.png" width="256" height="105" />
    <image type="icon16x16" src="img/icons/16x16/module-id-91.png" width="16" height="16" />
    <image type="icon32x32" src="img/icons/32x32/module-id-91.png" width="32" height="32" />
    <connector component-id="c1" index="0" name="clock" type="input" signal="logic" />
    <connector component-id="c2" index="1" name="reset" type="input" signal="logic" />
    <connector component-id="c3" index="0" name="out" type="output" signal="control" />
    <!-- parameter(s) -->
    <parameter component-id="p1" index="0" name="step 1" class="parameter" defaultValue="64" formatter="value-64" extension="m1" />
    <parameter component-id="p2" index="1" name="step 2" class="parameter" defaultValue="64" formatter="value-64" extension="m2" />
    <parameter component-id="p3" index="2" name="step 3" class="parameter" defaultValue="64" formatter="value-64" extension="m3" />
    <parameter component-id="p4" index="3" name="step 4" class="parameter" defaultValue="64" formatter="value-64" extension="m4" />
    <parameter component-id="p5" index="4" name="step 5" class="parameter" defaultValue="64" formatter="value-64" extension="m5" />
    <parameter component-id="m1" index="0" name="morph:step 1" class="morph" role="morph"  minValue="-127" maxValue="127" />
    <parameter component-id="m2" index="1" name="morph:step 2" class="morph" role="morph"  minValue="-127" maxValue="127" />
    <parameter component-id="m3" index="2" name="morph:step 3" class="morph" role="morph"  minValue="-127" maxValue="127" />
    <parameter component-id="m4" index="3" name="morph:step 4" class="morph" role="morph"  minValue="-127" maxValue="127" />
    <parameter component-id="m5" index="4" name="morph:step 5" class="morph" role="morph"  minValue="-127" maxValue="127" />
    <light component-id="ledStep1-5" type="led-array" name="Step 1-5" minValue="0" maxValue="5" />
    <!-- custom attributes -->
    <attribute name="cycles" type="double" value="0.6" />
    <attribute name="x-mem" type="double" value="0.3" />
    <attribute name="y-mem" type="double" value="0.0" />
    <attribute name="prog-mem" type="double" value="0.9" />
    <attribute name="dyn-mem" type="double" value="0.5" />
    <attribute name="zero-page" type="double" value="0.875" />
    <attribute name="height" type="integer" value="4" />
    <attribute name="background" value="#e5babf" />
  </module>""", """
\t<module component-id="m123" width="255" height="60">
\t\t<name>5-Step Seq</name>
\t\t<label x="5" y="16">Clk</label>
\t\t<connector x="6" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c1" alt="clock" />
\t\t</connector>
\t\t<label x="27" y="16">Rst</label>
\t\t<connector x="28" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c2" alt="reset" />
\t\t</connector>
\t\t<light component-id="ledStep1-5" type="led-array" steps="5" x="55" y="18" width="175" height="7" />
\t\t<label x="55" y="16" width="11" height="10" align="centre">1</label>
\t\t<label x="90" y="16" width="11" height="10" align="centre">2</label>
\t\t<label x="125" y="16" width="11" height="10" align="centre">3</label>
\t\t<label x="160" y="16" width="11" height="10" align="centre">4</label>
\t\t<label x="195" y="16" width="11" height="10" align="centre">5</label>
\t\t<knob x="62" y="28" size="21">
\t\t\t<parameter component-id="p1" alt="step 1" />
\t\t</knob>
\t\t<knob x="97" y="28" size="21">
\t\t\t<parameter component-id="p2" alt="step 2" />
\t\t</knob>
\t\t<knob x="132" y="28" size="21">
\t\t\t<parameter component-id="p3" alt="step 3" />
\t\t</knob>
\t\t<knob x="167" y="28" size="21">
\t\t\t<parameter component-id="p4" alt="step 4" />
\t\t</knob>
\t\t<knob x="202" y="28" size="21">
\t\t\t<parameter component-id="p5" alt="step 5" />
\t\t</knob>
\t\t<label x="233" y="16">Out</label>
\t\t<connector x="236" y="28" size="13" class="cCONTROL">
\t\t\t<connector component-id="c3" alt="out" />
\t\t</connector>
\t</module>"""),
    124: ("""
  <module component-id="m124" index="124" name="TuringMachine" fullname="Turing Machine, a looping random shift register with eight gates (G1-Mods)" category="Sequencer (mods)">
    <image type="screenshot" src="img/modules/module-91.png" width="256" height="105" />
    <image type="icon16x16" src="img/icons/16x16/module-id-91.png" width="16" height="16" />
    <image type="icon32x32" src="img/icons/32x32/module-id-91.png" width="32" height="32" />
    <connector component-id="c1" index="0" name="clock" type="input" signal="logic" />
    <connector component-id="c2" index="0" name="cv" type="output" signal="control" />
    <connector component-id="c3" index="1" name="gate 1" type="output" signal="logic" />
    <connector component-id="c4" index="2" name="gate 2" type="output" signal="logic" />
    <connector component-id="c5" index="3" name="gate 3" type="output" signal="logic" />
    <connector component-id="c6" index="4" name="gate 4" type="output" signal="logic" />
    <connector component-id="c7" index="5" name="gate 5" type="output" signal="logic" />
    <connector component-id="c8" index="6" name="gate 6" type="output" signal="logic" />
    <connector component-id="c9" index="7" name="gate 7" type="output" signal="logic" />
    <connector component-id="c10" index="8" name="gate 8" type="output" signal="logic" />
    <!-- parameter(s) -->
    <parameter component-id="p1" index="0" name="prob" class="parameter" defaultValue="64" formatter="value-64" extension="m1" />
    <parameter component-id="p2" index="1" name="length" class="parameter" maxValue="15" defaultValue="7" formatter="value+1" extension="m2" />
    <parameter component-id="p3" index="2" name="lock" class="parameter" maxValue="1" formatter="fmtOffOn" extension="m3" />
    <parameter component-id="p4" index="3" name="scale" class="parameter" defaultValue="127" extension="m4" />
    <parameter component-id="m1" index="0" name="morph:prob" class="morph" role="morph"  minValue="-127" maxValue="127" />
    <parameter component-id="m2" index="1" name="morph:length" class="morph" role="morph"  minValue="-15" maxValue="15" />
    <parameter component-id="m3" index="2" name="morph:lock" class="morph" role="morph"  minValue="-1" maxValue="1" />
    <parameter component-id="m4" index="3" name="morph:scale" class="morph" role="morph"  minValue="-127" maxValue="127" />
    <light component-id="ledBits" type="led-array" name="Bits 1-8" minValue="0" maxValue="255" />
    <!-- custom attributes -->
    <attribute name="cycles" type="double" value="0.9" />
    <attribute name="x-mem" type="double" value="0.35" />
    <attribute name="y-mem" type="double" value="0.0" />
    <attribute name="prog-mem" type="double" value="2.0" />
    <attribute name="dyn-mem" type="double" value="0.5" />
    <attribute name="zero-page" type="double" value="0.875" />
    <attribute name="height" type="integer" value="5" />
    <attribute name="background" value="#e5babf" />
  </module>""", """
\t<module component-id="m124" width="255" height="75">
\t\t<name>Turing Machine</name>
\t\t<label x="5" y="17">Clk</label>
\t\t<connector x="6" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c1" alt="clock" />
\t\t</connector>
\t\t<label x="30" y="17">Prob</label>
\t\t<knob x="52" y="20" size="21">
\t\t\t<parameter component-id="p1" alt="prob" />
\t\t</knob>
\t\t<label x="84" y="17">Length</label>
\t\t<textDisplay x="84" y="28" width="22" height="14">
\t\t\t<parameter component-id="p2" alt="length" />
\t\t</textDisplay>
\t\t<knob x="110" y="20" size="21">
\t\t\t<parameter component-id="p2" alt="length" />
\t\t</knob>
\t\t<button x="138" y="24" width="28" height="16" cyclic="true" landscape="false">
\t\t\t<parameter component-id="p3" alt="lock" />
\t\t\t<btn index="0">Lock</btn>
\t\t\t<btn index="1">Lock</btn>
\t\t</button>
\t\t<label x="170" y="17">Scale</label>
\t\t<knob x="194" y="20" size="21">
\t\t\t<parameter component-id="p4" alt="scale" />
\t\t</knob>
\t\t<label x="222" y="17">CV</label>
\t\t<connector x="236" y="28" size="13" class="cCONTROL">
\t\t\t<connector component-id="c2" alt="cv" />
\t\t</connector>
\t\t<label x="5" y="58">Gates</label>
\t\t<light component-id="ledBits" type="led-array" steps="8" bits="true" x="40" y="47" width="200" height="7" />
\t\t<connector x="46" y="57" size="13" class="cLOGIC">
\t\t\t<connector component-id="c3" alt="gate 1" />
\t\t</connector>
\t\t<connector x="71" y="57" size="13" class="cLOGIC">
\t\t\t<connector component-id="c4" alt="gate 2" />
\t\t</connector>
\t\t<connector x="96" y="57" size="13" class="cLOGIC">
\t\t\t<connector component-id="c5" alt="gate 3" />
\t\t</connector>
\t\t<connector x="121" y="57" size="13" class="cLOGIC">
\t\t\t<connector component-id="c6" alt="gate 4" />
\t\t</connector>
\t\t<connector x="146" y="57" size="13" class="cLOGIC">
\t\t\t<connector component-id="c7" alt="gate 5" />
\t\t</connector>
\t\t<connector x="171" y="57" size="13" class="cLOGIC">
\t\t\t<connector component-id="c8" alt="gate 6" />
\t\t</connector>
\t\t<connector x="196" y="57" size="13" class="cLOGIC">
\t\t\t<connector component-id="c9" alt="gate 7" />
\t\t</connector>
\t\t<connector x="221" y="57" size="13" class="cLOGIC">
\t\t\t<connector component-id="c10" alt="gate 8" />
\t\t</connector>
\t</module>"""),
    125: ("""
  <module component-id="m125" index="125" name="ScaleQuant" fullname="Scale Quantizer, a pitch to the nearest note of a scale (G1-Mods)" category="Control (mods)">
    <image type="screenshot" src="img/modules/module-98.png" width="256" height="30" />
    <image type="icon16x16" src="img/icons/16x16/module-id-98.png" width="16" height="16" />
    <image type="icon32x32" src="img/icons/32x32/module-id-98.png" width="32" height="32" />
    <connector component-id="c1" index="0" name="in" type="input" signal="control" />
    <connector component-id="c2" index="0" name="out" type="output" signal="control" />
    <!-- parameter(s) -->
    <parameter component-id="p1" index="0" name="root" class="parameter" maxValue="11" formatter="fmtRootNote" extension="m1" />
    <parameter component-id="p2" index="1" name="scale" class="parameter" maxValue="15" defaultValue="1" formatter="fmtScaleName" extension="m2" />
    <parameter component-id="p3" index="2" name="octave" class="parameter" maxValue="8" defaultValue="4" formatter="fmtOctaveShift" extension="m3" />
    <parameter component-id="m1" index="0" name="morph:root" class="morph" role="morph"  minValue="-11" maxValue="11" />
    <parameter component-id="m2" index="1" name="morph:scale" class="morph" role="morph"  minValue="-15" maxValue="15" />
    <parameter component-id="m3" index="2" name="morph:octave" class="morph" role="morph"  minValue="-8" maxValue="8" />
    <!-- custom attributes -->
    <attribute name="cycles" type="double" value="0.35" />
    <attribute name="x-mem" type="double" value="0.5" />
    <attribute name="y-mem" type="double" value="0.0" />
    <attribute name="prog-mem" type="double" value="0.75" />
    <attribute name="dyn-mem" type="double" value="0.5" />
    <attribute name="zero-page" type="double" value="0.875" />
    <attribute name="height" type="integer" value="3" />
    <attribute name="background" value="#c9d4a6" />
  </module>""", """
\t<module component-id="m125" width="255" height="45">
\t\t<name>Scale Quantizer</name>
\t\t<label x="5" y="17">In</label>
\t\t<connector x="6" y="28" size="13" class="cCONTROL">
\t\t\t<connector component-id="c1" alt="in" />
\t\t</connector>
\t\t<label x="28" y="17">Root</label>
\t\t<textDisplay x="28" y="28" width="22" height="14">
\t\t\t<parameter component-id="p1" alt="root" />
\t\t</textDisplay>
\t\t<knob x="54" y="20" size="21">
\t\t\t<parameter component-id="p1" alt="root" />
\t\t</knob>
\t\t<label x="82" y="17">Scale</label>
\t\t<textDisplay x="82" y="28" width="62" height="14">
\t\t\t<parameter component-id="p2" alt="scale" />
\t\t</textDisplay>
\t\t<knob x="148" y="20" size="21">
\t\t\t<parameter component-id="p2" alt="scale" />
\t\t</knob>
\t\t<label x="176" y="17">Oct</label>
\t\t<textDisplay x="176" y="28" width="20" height="14">
\t\t\t<parameter component-id="p3" alt="octave" />
\t\t</textDisplay>
\t\t<knob x="200" y="20" size="21">
\t\t\t<parameter component-id="p3" alt="octave" />
\t\t</knob>
\t\t<label x="230" y="17">Out</label>
\t\t<connector x="236" y="28" size="13" class="cCONTROL">
\t\t\t<connector component-id="c2" alt="out" />
\t\t</connector>
\t</module>"""),
    126: ("""
  <module component-id="m126" index="126" name="8Counter" fullname="8 Counter, one output a step (G1-Mods)" category="Logic (mods)">
    <image type="screenshot" src="img/modules/module-89.png" width="256" height="30" />
    <image type="icon16x16" src="img/icons/16x16/module-id-89.png" width="16" height="16" />
    <image type="icon32x32" src="img/icons/32x32/module-id-89.png" width="32" height="32" />
    <connector component-id="c1" index="0" name="clock" type="input" signal="logic" />
    <connector component-id="c2" index="1" name="reset" type="input" signal="logic" />
    <connector component-id="c3" index="0" name="out 1" type="output" signal="logic" />
    <connector component-id="c4" index="1" name="out 2" type="output" signal="logic" />
    <connector component-id="c5" index="2" name="out 3" type="output" signal="logic" />
    <connector component-id="c6" index="3" name="out 4" type="output" signal="logic" />
    <connector component-id="c7" index="4" name="out 5" type="output" signal="logic" />
    <connector component-id="c8" index="5" name="out 6" type="output" signal="logic" />
    <connector component-id="c9" index="6" name="out 7" type="output" signal="logic" />
    <connector component-id="c10" index="7" name="out 8" type="output" signal="logic" />
    <light component-id="ledStep1-8" type="led-array" name="Step 1-8" minValue="0" maxValue="8" />
    <!-- custom attributes -->
    <attribute name="cycles" type="double" value="0.6" />
    <attribute name="x-mem" type="double" value="0.2" />
    <attribute name="y-mem" type="double" value="0.0" />
    <attribute name="prog-mem" type="double" value="1.5" />
    <attribute name="dyn-mem" type="double" value="0.5" />
    <attribute name="zero-page" type="double" value="0.875" />
    <attribute name="height" type="integer" value="3" />
    <attribute name="background" value="#fc8642" />
  </module>""", """
\t<module component-id="m126" width="255" height="45">
\t\t<name>8Counter</name>
\t\t<label x="5" y="17">Clk</label>
\t\t<connector x="6" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c1" alt="clock" />
\t\t</connector>
\t\t<label x="27" y="17">Rst</label>
\t\t<connector x="28" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c2" alt="reset" />
\t\t</connector>
\t\t<light component-id="ledStep1-8" type="led-array" steps="8" x="50" y="18" width="200" height="7" />
\t\t<connector x="56" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c3" alt="out 1" />
\t\t</connector>
\t\t<connector x="81" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c4" alt="out 2" />
\t\t</connector>
\t\t<connector x="106" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c5" alt="out 3" />
\t\t</connector>
\t\t<connector x="131" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c6" alt="out 4" />
\t\t</connector>
\t\t<connector x="156" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c7" alt="out 5" />
\t\t</connector>
\t\t<connector x="181" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c8" alt="out 6" />
\t\t</connector>
\t\t<connector x="206" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c9" alt="out 7" />
\t\t</connector>
\t\t<connector x="231" y="28" size="13" class="cLOGIC">
\t\t\t<connector component-id="c10" alt="out 8" />
\t\t</connector>
\t</module>"""),
    101: ("""
  <module component-id="m101" index="101" name="Mux8-1" fullname="8 to 1 selector, by a knob and a level (G1-Mods)" category="Mixer (mods)">
    <image type="screenshot" src="img/modules/module-79.png" width="256" height="30" />
    <image type="icon16x16" src="img/icons/16x16/module-id-79.png" width="16" height="16" />
    <image type="icon32x32" src="img/icons/32x32/module-id-79.png" width="32" height="32" />
    <connector component-id="c1" index="0" name="in 1" type="input" signal="control" />
    <connector component-id="c2" index="1" name="in 2" type="input" signal="control" />
    <connector component-id="c3" index="2" name="in 3" type="input" signal="control" />
    <connector component-id="c4" index="3" name="in 4" type="input" signal="control" />
    <connector component-id="c5" index="4" name="in 5" type="input" signal="control" />
    <connector component-id="c6" index="5" name="in 6" type="input" signal="control" />
    <connector component-id="c7" index="6" name="in 7" type="input" signal="control" />
    <connector component-id="c8" index="7" name="in 8" type="input" signal="control" />
    <connector component-id="c9" index="8" name="ctrl" type="input" signal="control" />
    <connector component-id="c10" index="0" name="out" type="output" signal="control" />
    <!-- parameter(s) -->
    <parameter component-id="p1" index="0" name="sel" class="parameter" maxValue="7" formatter="value+1" extension="m1" />
    <parameter component-id="m1" index="0" name="morph:sel" class="morph" role="morph"  minValue="-7" maxValue="7" />
    <light component-id="ledSel1-8" type="led-array" name="Sel 1-8" minValue="0" maxValue="8" />
    <!-- custom attributes -->
    <attribute name="cycles" type="double" value="0.5" />
    <attribute name="x-mem" type="double" value="0.1" />
    <attribute name="y-mem" type="double" value="0.0" />
    <attribute name="prog-mem" type="double" value="1.0" />
    <attribute name="dyn-mem" type="double" value="0.25" />
    <attribute name="zero-page" type="double" value="0.875" />
    <attribute name="height" type="integer" value="4" />
    <attribute name="background" value="#bfcde0" />
  </module>""", """
\t<module component-id="m101" width="255" height="60">
\t\t<name>Mux8-1</name>
\t\t<label x="5" y="17">Ctrl</label>
\t\t<connector x="6" y="28" size="13" class="cCONTROL">
\t\t\t<connector component-id="c9" alt="ctrl" />
\t\t</connector>
\t\t<label x="30" y="17">Sel</label>
\t\t<textDisplay x="30" y="28" width="18" height="14">
\t\t\t<parameter component-id="p1" alt="sel" />
\t\t</textDisplay>
\t\t<knob x="52" y="20" size="21">
\t\t\t<parameter component-id="p1" alt="sel" />
\t\t</knob>
\t\t<label x="226" y="17">Out</label>
\t\t<connector x="236" y="28" size="13" class="cCONTROL">
\t\t\t<connector component-id="c10" alt="out" />
\t\t</connector>
\t\t<label x="5" y="47">In</label>
\t\t<light component-id="ledSel1-8" type="led-array" steps="8" x="50" y="38" width="200" height="7" />
\t\t<connector x="56" y="46" size="13" class="cCONTROL">
\t\t\t<connector component-id="c1" alt="in 1" />
\t\t</connector>
\t\t<connector x="81" y="46" size="13" class="cCONTROL">
\t\t\t<connector component-id="c2" alt="in 2" />
\t\t</connector>
\t\t<connector x="106" y="46" size="13" class="cCONTROL">
\t\t\t<connector component-id="c3" alt="in 3" />
\t\t</connector>
\t\t<connector x="131" y="46" size="13" class="cCONTROL">
\t\t\t<connector component-id="c4" alt="in 4" />
\t\t</connector>
\t\t<connector x="156" y="46" size="13" class="cCONTROL">
\t\t\t<connector component-id="c5" alt="in 5" />
\t\t</connector>
\t\t<connector x="181" y="46" size="13" class="cCONTROL">
\t\t\t<connector component-id="c6" alt="in 6" />
\t\t</connector>
\t\t<connector x="206" y="46" size="13" class="cCONTROL">
\t\t\t<connector component-id="c7" alt="in 7" />
\t\t</connector>
\t\t<connector x="231" y="46" size="13" class="cCONTROL">
\t\t\t<connector component-id="c8" alt="in 8" />
\t\t</connector>
\t</module>"""),
}


MODULES_ENTRY = r'\n  <module component-id="m{t}" index="{t}" .*?\n  </module>'
THEME_ENTRY = r'\n\t<module component-id="m{t}" .*?\n\t</module>'


def place(text, pattern, donor, new, block):
    """Puts a whole entry right after the donor's, replacing an earlier one of the same type."""
    old = re.search(pattern.format(t=new), text, re.S)
    if old:
        text = text[:old.start()] + text[old.end():]
    m = re.search(pattern.format(t=donor), text, re.S)
    if not m:
        sys.exit(f"type {donor} not found")
    return text[:m.end()] + block + text[m.end():]


def clone(text, pattern, donor, new, header, subs):
    old = re.search(pattern.format(t=new), text, re.S)
    if old:                      # made by an earlier run: made again from the donor
        text = text[:old.start()] + text[old.end():]
    m = re.search(pattern.format(t=donor), text, re.S)
    if not m:
        sys.exit(f"type {donor} not found")
    block = m.group(0).replace(f'component-id="m{donor}"', f'component-id="m{new}"', 1)
    if header:
        block = re.sub(header[0], header[1], block, count=1)
    for old, rep in subs:
        if old not in block:
            sys.exit(f"type {new}: '{old}' not in type {donor}'s entry")
        block = block.replace(old, rep)
    return text[:m.end()] + block + text[m.end():], not old


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1:]
    os.makedirs(dst, exist_ok=True)
    mods = open(os.path.join(src, "modules.xml"), encoding="utf-8").read()
    theme = open(os.path.join(src, "classic-theme.xml"), encoding="utf-8").read()
    added = []
    for new, (donor, name, fullname, mod_subs, theme_subs) in NEW_TYPES.items():
        if new in FULL_ENTRIES:
            mods = place(mods, MODULES_ENTRY, donor, new, FULL_ENTRIES[new][0])
            theme = place(theme, THEME_ENTRY, donor, new, FULL_ENTRIES[new][1])
            added.append(new)
            continue
        # in NME the new types sit in "<donor's family> (mods)", listed right after the family
        header = (r'index="%d" name="[^"]*" fullname="[^"]*" category="([^"]*)"' % donor,
                  f'index="{new}" name="{name}" fullname="{fullname}" category="\\1 (mods)"')
        mods, a = clone(mods, MODULES_ENTRY, donor, new, header, mod_subs)
        theme, b = clone(theme, THEME_ENTRY, donor, new, None, theme_subs)
        added.append(new)
    open(os.path.join(dst, "modules.xml"), "w", encoding="utf-8").write(mods)
    open(os.path.join(dst, "classic-theme.xml"), "w", encoding="utf-8").write(theme)
    print(f"written {dst}: types {added}")


if __name__ == "__main__":
    main()
