## BMFont Format Converter

Converts [BMFont](https://www.angelcode.com/products/bmfont/) files between text, XML, and binary (version 3) formats.

### Requirements

None

### Usage Instructions

The script can be run normally. When doing so, you will be prompted to enter a source file and the target format.

```bash
python3 main.py
Enter the file path to a BMFont .fnt file:
example.fnt
Enter the desired output format (t for text, x for XML, b for binary):
b
Converting...
Conversion complete (took 0.01725602149963379 seconds)
Old file saved as example.fnt.old
```

Alternatively, you can supply the arguments early via the command line in the following format:

```
python3 main.py <filepath> <format>
```

 - `<filepath>`: Filepath to the .fnt file.
 - `<format>`: Target file format. Enter `t` for text, `x` for XML, and `b` for binary.

```bash
python3 main.py example.fnt b
Converting...
Conversion complete (took 0.01776909828186035 seconds)
Old file saved as example.fnt.old
```

### Notes and Issues

 - `charset` information is not stored in the binary format, and will be lost when converting to and from binary.