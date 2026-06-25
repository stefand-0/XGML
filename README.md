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
git clone https://github.com/stefand-0/XGML.git
cd XGML
```

* Transpiling XGML scripts

If you want an easier experience, just copy the `xgmlparse.py` file over to your preferred directory.

Run:

```bash
python3 xgmlparse.py filename.xgml
(OR)
python xgmlparse.py filename.xgm
# File is found with the same name, with the .gcode extension.
```
