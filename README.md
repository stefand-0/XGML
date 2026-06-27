# XGML
XGML: eXtensible G-code Markup Language, the lightweight markup language specifically designed for easier prototyping of G-Code, without the complex G commands. Simple tags, no closing tag boilerplate from XML and others (</>).

# What does it *solve*?

It solves having to read clunky G-code, let alone actually... understand it at the same efficiency you would understand XGML. It is also an easy markup language to test 3D-printers, make complex patterns, for people who... just don't have well-established experience with 3D modelling.

# Why a Markup Language?

Markup languages are *really* lightweight, declarative, and serve their simple purposes well.

# How to use XGML?

* Installation

Run:
```bash
pip install xgml
```

* Transpiling XGML scripts

If cloning from GitHub, just copy the `parse/xgmlparse.py` file over to your preferred directory.

Run:

```bash
xgml FILENAME.xgml
# File is found with the same name, with the .gcode extension.
```

# What 3D printers does it support?

I'm a WASP enthusiast. so the coordinate system is exactly like the one in their printers, though it supports any 3D printer that can process standard Marlin G-Code.

** Two things to keep in mind...

• Print bed size might not match up to the scripts coordinates. Double check before loading onto the printer.

• Some printers require complex start codes, e.g. Bambu Lab X1C

# Try it out!
Here, I've written some XGML code (also found here at test/layers.xgml)

```xml
<module XGML_3D_TEST_PRINT
    <var print_bed_temp: 60.0>
    <var print_noz_temp: 210.0>
    <var circle_radius: 12.5>
    <var total_layers: 4>

    <temperature nozzle:print_noz_temp bed:print_bed_temp end>
    <fan speed:255 end>

    <path @f4000 end>
    <path x:0.0 y:0.0 z:0.3 e:0.0 end>
    <path x:10.0 y:10.0 z:0.3 e:1.25 end>

    <loop @for total_layers @zstep 0.4
        ; This circle will automatically print higher on every single pass
        <polygon @PREDEF CIRCLE r:circle_radius end>
        
        ; A travel and extrusion path inside the layer loop
        <path x:30.0 y:30.0 e:2.5 end>
        
        ; This square will stack right along with the circle
        <polygon @PREDEF SQUARE size:20.0 end>
    end>

    <fan speed:0 end>
    <temperature nozzle:0.0 bed:0.0 end>
end>

```

# License

This project is licensed under the Apache License 2.0. Feel free to use, modify, distribute, and build upon this core engine for both personal and commercial 3D printing workflows! See the source headers and the LICENSE for more details.
