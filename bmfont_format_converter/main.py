import sys
import os
import time
import bmfile


filepath = None
source_format = bmfile.FILE_TYPE_INVALID
target_format = bmfile.FILE_TYPE_INVALID


if __name__ != "__main__":
    quit()


##########
# Request filepath
##########

valid_filepath = False

if len(sys.argv) >= 2:
    filepath = sys.argv[1]
    source_format = bmfile.check_file_format(filepath)
    if source_format != bmfile.FILE_TYPE_INVALID:
        valid_filepath = True

while valid_filepath == False:
    filepath = input("Enter the file path to a BMFont .fnt file:\n")
    if filepath == "":
        print("Nothing entered, quitting")
        quit()
    source_format = bmfile.check_file_format(filepath)
    if source_format != bmfile.FILE_TYPE_INVALID:
        valid_filepath = True
    else:
        print("File path does not lead to a valid BMFont .fnt file")


##########
# Request target format
##########

valid_target_format = False

# Parses t, x, b into 0, 1, 2 respectively.
def target_format_parse(x):
    valid_inputs = ["t", "x", "b"]
    for i in range(len(valid_inputs)):
        if x == valid_inputs[i]:
            return i
    return bmfile.FILE_TYPE_INVALID

if len(sys.argv) >= 3:
    target_format = target_format_parse(sys.argv[2])
    if target_format != bmfile.FILE_TYPE_INVALID:
        valid_target_format = True

while valid_target_format == False:
    target_format_string = input("Enter the desired output format (t for text, x for XML, b for binary):\n")
    if target_format_string == "":
        print("Nothing entered, quitting")
        quit()
    target_format = target_format_parse(target_format_string)
    if target_format != bmfile.FILE_TYPE_INVALID:
        valid_target_format = True
    else:
        print("Invalid selection for output format")


##########
# Convert from source to target format
##########

t1 = time.time()
print("Converting...")

os.rename(filepath, filepath + ".old")
original_file = None
new_file = None

if source_format == bmfile.FILE_TYPE_BINARY3:
    original_file = open(filepath + ".old", "rb")
else:
    original_file = open(filepath + ".old", "r")

if target_format == bmfile.FILE_TYPE_BINARY3:
    new_file = open(filepath, "wb")
else:
    new_file = open(filepath, "w")

new_file.write(bmfile.get_file_header(target_format))

b1 = bmfile.get_block_1_data(original_file, source_format)
new_file.write(bmfile.encode_block_1_data(b1, target_format))

b2 = bmfile.get_block_2_data(original_file, source_format)
new_file.write(bmfile.encode_block_2_data(b2, target_format))

b3 = bmfile.Block3Iterator(original_file, source_format, target_format, b2["pages"])
for i in b3:
    new_file.write(i)

b4 = bmfile.Block4Iterator(original_file, source_format, target_format)
for i in b4:
    new_file.write(i)

if bmfile.block_5_exists(original_file, source_format):
    b5 = bmfile.Block5Iterator(original_file, source_format, target_format)
    for i in b5:
        new_file.write(i)

new_file.write(bmfile.get_file_footer(target_format))

original_file.close()
new_file.close()

t2 = time.time()
print("Conversion complete (took {0} seconds)".format(t2 - t1))
print("Old file saved as {0}".format(filepath + ".old"))
