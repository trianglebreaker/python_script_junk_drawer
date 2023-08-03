import re
import io

FILE_TYPE_INVALID = -1
FILE_TYPE_TEXT = 0
FILE_TYPE_XML = FILE_TYPE_TEXT + 1
FILE_TYPE_BINARY3 = FILE_TYPE_XML + 1

##########
# Utility functions
##########

# Given a filepath, determines what format the BMFont file it points to uses,
# and returns the corresponding integer.
# Note that it's easy to spoof this format checker; this script generally
# assumes you're not trying to break it.

def check_file_format(filepath):
    x = ""
    try:
        file = open(filepath, "rb")
        x = file.read(4)
    except:
        return FILE_TYPE_INVALID
    
    if x == bytes("info", "utf-8"): # text
        return FILE_TYPE_TEXT
    elif x == bytes("<?xm", "utf-8"): # XML
        return FILE_TYPE_XML
    elif x == bytes([66, 77, 70, 3]): # binary v3
        return FILE_TYPE_BINARY3
    else:
        return FILE_TYPE_INVALID


# Functions to set and get particular bits.
def get_bit(i, pos):
    mask = 1 << pos
    return int(bool(i & mask))


def set_bit(i, val, pos):
    mask = 1 << pos
    return i | mask if val else i & ~mask


##########
# Header, footer, EOF functions
##########


# Returns a suitable header for the file based on the requested file type.
def get_file_header(file_type):
    headers = ["", "<?xml version=\"1.0\"?>\n<font>\n", b'BMF\x03']
    return headers[file_type]


# Returns a suitable footer for the file based on the requested file type.
def get_file_footer(file_type):
    footers = ["", "</font>\n", b'']
    return footers[file_type]


# Given a file parsed to the end of block 4, checks whether block 5 exists.
def block_5_exists(file, source_file_type):
    pos = file.tell()
    exists = False
    if source_file_type == FILE_TYPE_TEXT:
        x = file.readline()
        exists = True if re.compile(r'kernings').search(x) else False
    elif source_file_type == FILE_TYPE_XML:
        x = file.readline()
        exists = True if re.compile(r'kernings').search(x) else False
    elif source_file_type == FILE_TYPE_BINARY3:
        x = file.read(1)
        exists = True if x == bytes([5]) else False
    file.seek(pos)
    return exists


##########
# Block 1 (info) parsers
##########

# Reads all data from block 1, and returns it in a dictionary.
# Assumes the file has otherwise not been parsed yet.
def get_block_1_data(file, source_file_type):
    functions = [get_block_1_data_txt, get_block_1_data_xml, get_block_1_data_bn3]
    return functions[source_file_type](file)


# Translates all data for block 1 into the file format using a dictionary.
# Does not automatically write the info into the new file!
def encode_block_1_data(data, target_file_type):
    functions = [encode_block_1_data_txt, encode_block_1_data_xml, encode_block_1_data_bn3]
    return functions[target_file_type](data)


# More specific functions that the above two redirect to.
def get_block_1_data_txt(file):
    x = file.readline()
    x = x.rstrip() + " "
    
    data = {}
    data["face"] = re.compile(r'face=\"(.*?)\" ').search(x).group(1)
    data["size"] = int(re.compile(r'size=(.*?) ').search(x).group(1))
    data["bold"] = int(re.compile(r'bold=(.*?) ').search(x).group(1))
    data["italic"] = int(re.compile(r'italic=(.*?) ').search(x).group(1))
    data["charset"] = re.compile(r'charset=\"(.*?)\" ').search(x).group(1)
    data["unicode"] = int(re.compile(r'unicode=(.*?) ').search(x).group(1))
    data["stretchH"] = int(re.compile(r'stretchH=(.*?) ').search(x).group(1))
    data["smooth"] = int(re.compile(r'smooth=(.*?) ').search(x).group(1))
    data["aa"] = int(re.compile(r'aa=(.*?) ').search(x).group(1))
    data["padding"] = list(map(lambda x: int(x), re.compile(r'padding=(.*?) ').search(x).group(1).split(',')))
    data["spacing"] = list(map(lambda x: int(x), re.compile(r'spacing=(.*?) ').search(x).group(1).split(',')))
    data["outline"] = int(re.compile(r'outline=(.*?) ').search(x).group(1))
    
    return data


def get_block_1_data_xml(file):
    x = ""
    while not re.compile(r'^  <info ').search(x):
        x = file.readline()
    x = x.rstrip("/>\n") + " "
    
    data = {}
    data["face"] = re.compile(r'face=\"(.*?)\" ').search(x).group(1)
    data["size"] = int(re.compile(r'size=\"(.*?)\" ').search(x).group(1))
    data["bold"] = int(re.compile(r'bold=\"(.*?)\" ').search(x).group(1))
    data["italic"] = int(re.compile(r'italic=\"(.*?)\" ').search(x).group(1))
    data["charset"] = re.compile(r'charset=\"(.*?)\" ').search(x).group(1)
    data["unicode"] = int(re.compile(r'unicode=\"(.*?)\" ').search(x).group(1))
    data["stretchH"] = int(re.compile(r'stretchH=\"(.*?)\" ').search(x).group(1))
    data["smooth"] = int(re.compile(r'smooth=\"(.*?)\" ').search(x).group(1))
    data["aa"] = int(re.compile(r'aa=\"(.*?)\" ').search(x).group(1))
    data["padding"] = list(map(lambda x: int(x), re.compile(r'padding=\"(.*?)\" ').search(x).group(1).split(',')))
    data["spacing"] = list(map(lambda x: int(x), re.compile(r'spacing=\"(.*?)\" ').search(x).group(1).split(',')))
    data["outline"] = int(re.compile(r'outline=\"(.*?)\" ').search(x).group(1))
    
    return data


def get_block_1_data_bn3(file):
    file.seek(5, io.SEEK_CUR) # Skips over the "block 1" byte
    size = file.read(4)
    size = int.from_bytes(size, byteorder = "little")
    x = file.read(size)
    
    data = {}
    data["face"] = x[14:size - 1].strip(b'\x00').decode()
    data["size"] = int.from_bytes(x[0:2], "little", signed = True)
    data["bold"] = get_bit(x[2], 4)
    data["italic"] = get_bit(x[2], 5)
    data["charset"] = "" # this isn't saved in the format anyway
    data["unicode"] = get_bit(x[2], 6)
    data["stretchH"] = int.from_bytes(x[4:6], "little")
    data["smooth"] = get_bit(x[2], 7)
    data["aa"] = x[6]
    data["padding"] = [x[7], x[8], x[9], x[10]]
    data["spacing"] = [x[11], x[12]]
    data["outline"] = x[13]
    
    return data


def encode_block_1_data_txt(data):
    x = "info "
    x += "face=\"" + data["face"] + "\" "
    x += "size=" + str(data["size"]) + " "
    x += "bold=" + str(data["bold"]) + " "
    x += "italic=" + str(data["italic"]) + " "
    x += "charset=\"" + data["charset"] + "\" "
    x += "unicode=" + str(data["unicode"]) + " "
    x += "stretchH=" + str(data["stretchH"]) + " "
    x += "smooth=" + str(data["smooth"]) + " "
    x += "aa=" + str(data["aa"]) + " "
    x += "padding=" + ",".join(map(lambda x: str(x), data["padding"])) + " "
    x += "spacing=" + ",".join(map(lambda x: str(x), data["spacing"])) + " "
    x += "outline=" + str(data["outline"]) + "\n"
    
    return x


def encode_block_1_data_xml(data):
    x = "  <info "
    x += "face=\"" + data["face"] + "\" "
    x += "size=\"" + str(data["size"]) + "\" "
    x += "bold=\"" + str(data["bold"]) + "\" "
    x += "italic=\"" + str(data["italic"]) + "\" "
    x += "charset=\"" + data["charset"] + "\" "
    x += "unicode=\"" + str(data["unicode"]) + "\" "
    x += "stretchH=\"" + str(data["stretchH"]) + "\" "
    x += "smooth=\"" + str(data["smooth"]) + "\" "
    x += "aa=\"" + str(data["aa"]) + "\" "
    x += "padding=\"" + ",".join(map(lambda x: str(x), data["padding"])) + "\" "
    x += "spacing=\"" + ",".join(map(lambda x: str(x), data["spacing"])) + "\" "
    x += "outline=\"" + str(data["outline"]) + "\"/>\n"
    
    return x


def encode_block_1_data_bn3(data):
    x = bytearray()
    x += data["size"].to_bytes(2, "little", signed = True)          # size
    y = 0                                                           # bitfield mess
    y = set_bit(y, data["smooth"], 7)                               #   smooth
    y = set_bit(y, data["unicode"], 6)                              #   unicode
    y = set_bit(y, data["italic"], 5)                               #   italic
    y = set_bit(y, data["bold"], 4)                                 #   bold
    x += bytes([y])
    x += bytes([0])                                                 # charset
    x += data["stretchH"].to_bytes(2, "little")                     # stretchH
    x += bytes([data["aa"]])                                        # aa
    x += bytes([data["padding"][0]])                                # paddingUp
    x += bytes([data["padding"][1]])                                # paddingRight
    x += bytes([data["padding"][2]])                                # paddingDown
    x += bytes([data["padding"][3]])                                # paddingLeft
    x += bytes([data["spacing"][0]])                                # spacingHoriz
    x += bytes([data["spacing"][1]])                                # spacingVert
    x += bytes([data["outline"]])                                   # outline
    x += bytes(data["face"], "utf-8") + bytes([0])                  # face
    
    head = bytearray(b'\x01')
    head += len(x).to_bytes(4, "little")
    
    return head + x


##########
# Block 2 (common) parsers
##########

# Reads all data from block 2, and returns it in a dictionary.
# Assumes the file is at the beginning of block 2.
def get_block_2_data(file, source_file_type):
    functions = [get_block_2_data_txt, get_block_2_data_xml, get_block_2_data_bn3]
    return functions[source_file_type](file)


# Translates all data for block 2 into the file format using a dictionary.
# Does not automatically write the info into the new file!
def encode_block_2_data(data, target_file_type):
    functions = [encode_block_2_data_txt, encode_block_2_data_xml, encode_block_2_data_bn3]
    return functions[target_file_type](data)


# More specific functions that the above two redirect to.
def get_block_2_data_txt(file):
    x = file.readline()
    x = x.rstrip() + " "
    
    data = {}
    data["lineHeight"] = int(re.compile(r'lineHeight=(.*?) ').search(x).group(1))
    data["base"] = int(re.compile(r'base=(.*?) ').search(x).group(1))
    data["scaleW"] = int(re.compile(r'scaleW=(.*?) ').search(x).group(1))
    data["scaleH"] = int(re.compile(r'scaleH=(.*?) ').search(x).group(1))
    data["pages"] = int(re.compile(r'pages=(.*?) ').search(x).group(1))
    data["packed"] = int(re.compile(r'packed=(.*?) ').search(x).group(1))
    data["alphaChnl"] = int(re.compile(r'alphaChnl=(.*?) ').search(x).group(1))
    data["redChnl"] = int(re.compile(r'redChnl=(.*?) ').search(x).group(1))
    data["greenChnl"] = int(re.compile(r'greenChnl=(.*?) ').search(x).group(1))
    data["blueChnl"] = int(re.compile(r'blueChnl=(.*?) ').search(x).group(1))
    
    return data


def get_block_2_data_xml(file):
    x = file.readline()
    x = x.rstrip("/>\n") + " "
    
    data = {}
    data["lineHeight"] = int(re.compile(r'lineHeight=\"(.*?)\" ').search(x).group(1))
    data["base"] = int(re.compile(r'base=\"(.*?)\" ').search(x).group(1))
    data["scaleW"] = int(re.compile(r'scaleW=\"(.*?)\" ').search(x).group(1))
    data["scaleH"] = int(re.compile(r'scaleH=\"(.*?)\" ').search(x).group(1))
    data["pages"] = int(re.compile(r'pages=\"(.*?)\" ').search(x).group(1))
    data["packed"] = int(re.compile(r'packed=\"(.*?)\" ').search(x).group(1))
    data["alphaChnl"] = int(re.compile(r'alphaChnl=\"(.*?)\" ').search(x).group(1))
    data["redChnl"] = int(re.compile(r'redChnl=\"(.*?)\" ').search(x).group(1))
    data["greenChnl"] = int(re.compile(r'greenChnl=\"(.*?)\" ').search(x).group(1))
    data["blueChnl"] = int(re.compile(r'blueChnl=\"(.*?)\" ').search(x).group(1))
    
    return data


def get_block_2_data_bn3(file):
    file.seek(1, io.SEEK_CUR) # Skips over the "block 2" byte
    size = file.read(4)
    size = int.from_bytes(size, byteorder = "little")
    x = file.read(size)
    
    data = {}
    data["lineHeight"] = int.from_bytes(x[0:2], "little")
    data["base"] = int.from_bytes(x[2:4], "little")
    data["scaleW"] = int.from_bytes(x[4:6], "little")
    data["scaleH"] = int.from_bytes(x[6:8], "little")
    data["pages"] = int.from_bytes(x[8:10], "little")
    data["packed"] = get_bit(x[10], 7)
    data["alphaChnl"] = x[11]
    data["redChnl"] = x[12]
    data["greenChnl"] = x[13]
    data["blueChnl"] = x[14]
    
    return data


def encode_block_2_data_txt(data):
    x = "common "
    x += "lineHeight=" + str(data["lineHeight"]) + " "
    x += "base=" + str(data["base"]) + " "
    x += "scaleW=" + str(data["scaleW"]) + " "
    x += "scaleH=" + str(data["scaleH"]) + " "
    x += "pages=" + str(data["pages"]) + " "
    x += "packed=" + str(data["packed"]) + " "
    x += "alphaChnl=" + str(data["alphaChnl"]) + " "
    x += "redChnl=" + str(data["redChnl"]) + " "
    x += "greenChnl=" + str(data["greenChnl"]) + " "
    x += "blueChnl=" + str(data["blueChnl"]) + "\n"
    
    return x


def encode_block_2_data_xml(data):
    x = "  <common "
    x += "lineHeight=\"" + str(data["lineHeight"]) + "\" "
    x += "base=\"" + str(data["base"]) + "\" "
    x += "scaleW=\"" + str(data["scaleW"]) + "\" "
    x += "scaleH=\"" + str(data["scaleH"]) + "\" "
    x += "pages=\"" + str(data["pages"]) + "\" "
    x += "packed=\"" + str(data["packed"]) + "\" "
    x += "alphaChnl=\"" + str(data["alphaChnl"]) + "\" "
    x += "redChnl=\"" + str(data["redChnl"]) + "\" "
    x += "greenChnl=\"" + str(data["greenChnl"]) + "\" "
    x += "blueChnl=\"" + str(data["blueChnl"]) + "\"/>\n"
    
    return x


def encode_block_2_data_bn3(data):
    x = bytearray()
    x += data["lineHeight"].to_bytes(2, "little")                   # lineHeight
    x += data["base"].to_bytes(2, "little")                         # base
    x += data["scaleW"].to_bytes(2, "little")                       # scaleW
    x += data["scaleH"].to_bytes(2, "little")                       # scaleH
    x += data["pages"].to_bytes(2, "little")                        # pages
    y = 0                                                           # bitfield mess 2
    y = set_bit(y, data["packed"], 7)                               #   packed
    x += bytes([y])
    x += bytes([data["alphaChnl"]])                                 # alphaChnl
    x += bytes([data["redChnl"]])                                   # redChnl
    x += bytes([data["greenChnl"]])                                 # greenChnl
    x += bytes([data["blueChnl"]])                                  # blueChnl
    
    head = bytearray(b'\x02')
    head += len(x).to_bytes(4, "little")
    
    return head + x


##########
# Block 3 (pages) iterator
##########

# Returns an iterator that provides one line at a time.
class Block3Iterator:
    # Also this initializes the file seek position
    def get_block_3_metadata(self, file):
        data = {}
        
        if self.source_file_type == FILE_TYPE_TEXT:
            pos = file.tell()
            x = file.readline().rstrip() + " "
            texture_name = re.compile(r'file=\"(.*?)\" ').search(x).group(1)
            data["block_size"] = len(texture_name) + 1 # +1 is the b'\x00' at the end of the string
            file.seek(pos)
        elif self.source_file_type == FILE_TYPE_XML:
            file.readline() # Skips over the "  <pages>" opening tag
            pos = file.tell()
            x = file.readline().rstrip("/>\n") + " "
            texture_name = re.compile(r'file=\"(.*?)\" ').search(x).group(1)
            data["block_size"] = len(texture_name) + 1 # +1 is the b'\x00' at the end of the string
            file.seek(pos)
        elif self.source_file_type == FILE_TYPE_BINARY3:
            file.seek(1, io.SEEK_CUR) # Skips over the "block 3" byte
            size = file.read(4)
            size = int.from_bytes(size, byteorder = "little")
            data["block_size"] = size
        data["entry_size"] = int(data["block_size"] / self.limit)
        return data
    
    
    # Returns the text or bytes that should go in front of the first entry
    def get_fragment_header(self):
        if self.target_file_type == FILE_TYPE_TEXT:
            return ""
        if self.target_file_type == FILE_TYPE_XML:
            return "  <pages>\n"
        if self.target_file_type == FILE_TYPE_BINARY3:
            return bytearray([3]) + self.metadata["block_size"].to_bytes(4, "little")
    
    
    # Returns the text or bytes that should go behind the last entry
    def get_fragment_footer(self):
        if self.target_file_type == FILE_TYPE_TEXT:
            return ""
        if self.target_file_type == FILE_TYPE_XML:
            return "  </pages>\n"
        if self.target_file_type == FILE_TYPE_BINARY3:
            return bytearray()
    
    
    # Reads a line (or entry) of data from block 3, and returns it in a dictionary.
    # Assumes the file is at the beginning of block 3.
    def get_block_3_data(self, file):
        functions = [self.get_block_3_data_txt, self.get_block_3_data_xml, self.get_block_3_data_bn3]
        return functions[self.source_file_type](file)
    
    
    # Translates a line (or entry) of data for block 3 into the file format using a dictionary.
    # Does not automatically write the info into the new file!
    def encode_block_3_data(self, data):
        functions = [self.encode_block_3_data_txt, self.encode_block_3_data_xml, self.encode_block_3_data_bn3]
        return functions[self.target_file_type](data)
    
    
    # More specific functions that the above two redirect to.
    def get_block_3_data_txt(self, file):
        x = file.readline()
        x = x.rstrip() + " "
        
        data = {}
        data["file"] = re.compile(r'file=\"(.*?)\" ').search(x).group(1)
        
        return data
    
    
    def get_block_3_data_xml(self, file):
        x = file.readline()
        x = x.rstrip("/>\n") + " "
        
        data = {}
        data["file"] = re.compile(r'file=\"(.*?)\" ').search(x).group(1)
        
        return data
    
    
    def get_block_3_data_bn3(self, file):
        x = file.read(self.metadata["entry_size"])
    
        data = {}
        data["file"] = x.strip(b'\x00').decode()
        
        return data
    
    
    def encode_block_3_data_txt(self, data):
        x = "page "
        x += "id=" + str(data["id"]) + " "
        x += "file=\"" + data["file"] + "\"\n"
        
        return x
    
    
    def encode_block_3_data_xml(self, data):
        x = "    <page "
        x += "id=\"" + str(data["id"]) + "\" "
        x += "file=\"" + str(data["file"]) + "\" />\n"
        
        return x
    
    
    def encode_block_3_data_bn3(self, data):
        x = bytearray()
        x += bytes(data["file"], "utf-8") + bytes([0])              # file
        
        return x
    
    
    def __init__(self, _file, _source_file_type, _target_file_type, _page_count):
        self.file = _file
        self.source_file_type = _source_file_type
        self.target_file_type = _target_file_type
        self.index = 0
        self.limit = _page_count
        
        self.metadata = self.get_block_3_metadata(self.file)
    
    
    def __iter__(self):
        return self
    
    
    def __next__(self):
        if self.index < self.limit:
            data = self.get_block_3_data(self.file)
            data["id"] = self.index
            x = self.encode_block_3_data(data)
            
            if self.index == 0:
                x = self.get_fragment_header() + x
            elif self.index == self.limit - 1:
                if self.source_file_type == FILE_TYPE_XML:
                    self.file.readline() # Skips over the "  </pages>" closing tag
                x = x + self.get_fragment_footer()
            
            self.index += 1
            return x
        else:
            raise StopIteration


##########
# Block 4 (chars) iterator
##########

# Returns an iterator that provides one line at a time.
class Block4Iterator:
    BLOCK_4_BINARY3_ENTRY_SIZE = 20
    
    # Also this initializes the file seek position
    def get_block_4_metadata(self, file):
        data = {}
        
        if self.source_file_type == FILE_TYPE_TEXT:
            x = file.readline().rstrip() + " "
            data["count"] = int(re.compile(r'count=(.*?) ').search(x).group(1))
        elif self.source_file_type == FILE_TYPE_XML:
            x = file.readline().rstrip("/>\n") + " "
            data["count"] = int(re.compile(r'count=\"(.*?)\" ').search(x).group(1))
        elif self.source_file_type == FILE_TYPE_BINARY3:
            file.seek(1, io.SEEK_CUR) # Skips over the "block 4" byte
            size = file.read(4)
            size = int.from_bytes(size, byteorder = "little")
            data["count"] = int(size / Block4Iterator.BLOCK_4_BINARY3_ENTRY_SIZE)
        return data
    
    
    # Returns the text or bytes that should go in front of the first entry
    def get_fragment_header(self):
        if self.target_file_type == FILE_TYPE_TEXT:
            return "chars count=" + str(self.metadata["count"]) + "\n"
        if self.target_file_type == FILE_TYPE_XML:
            return "  <chars count=\"" + str(self.metadata["count"]) + "\">\n"
        if self.target_file_type == FILE_TYPE_BINARY3:
            return bytearray([4]) + self.metadata["count"].to_bytes(4, "little")
    
    
    # Returns the text or bytes that should go behind the last entry
    def get_fragment_footer(self):
        if self.target_file_type == FILE_TYPE_TEXT:
            return ""
        if self.target_file_type == FILE_TYPE_XML:
            return "  </chars>\n"
        if self.target_file_type == FILE_TYPE_BINARY3:
            return bytearray()
    
    
    # Reads a line (or entry) of data from block 4, and returns it in a dictionary.
    # Assumes the file is at the beginning of block 4.
    def get_block_4_data(self, file):
        functions = [self.get_block_4_data_txt, self.get_block_4_data_xml, self.get_block_4_data_bn3]
        return functions[self.source_file_type](file)
    
    
    # Translates a line (or entry) of data for block 4 into the file format using a dictionary.
    # Does not automatically write the info into the new file!
    def encode_block_4_data(self, data):
        functions = [self.encode_block_4_data_txt, self.encode_block_4_data_xml, self.encode_block_4_data_bn3]
        return functions[self.target_file_type](data)
    
    
    # More specific functions that the above two redirect to.
    def get_block_4_data_txt(self, file):
        x = file.readline()
        x = x.rstrip() + " "
        
        data = {}
        data["id"] = int(re.compile(r'id=(.*?) ').search(x).group(1))
        data["x"] = int(re.compile(r'x=(.*?) ').search(x).group(1))
        data["y"] = int(re.compile(r'y=(.*?) ').search(x).group(1))
        data["width"] = int(re.compile(r'width=(.*?) ').search(x).group(1))
        data["height"] = int(re.compile(r'height=(.*?) ').search(x).group(1))
        data["xoffset"] = int(re.compile(r'xoffset=(.*?) ').search(x).group(1))
        data["yoffset"] = int(re.compile(r'yoffset=(.*?) ').search(x).group(1))
        data["xadvance"] = int(re.compile(r'xadvance=(.*?) ').search(x).group(1))
        data["page"] = int(re.compile(r'page=(.*?) ').search(x).group(1))
        data["chnl"] = int(re.compile(r'chnl=(.*?) ').search(x).group(1))
        
        return data
    
    
    def get_block_4_data_xml(self, file):
        x = file.readline()
        x = x.rstrip("/>\n") + " "
        
        data = {}
        data["id"] = int(re.compile(r'id=\"(.*?)\" ').search(x).group(1))
        data["x"] = int(re.compile(r'x=\"(.*?)\" ').search(x).group(1))
        data["y"] = int(re.compile(r'y=\"(.*?)\" ').search(x).group(1))
        data["width"] = int(re.compile(r'width=\"(.*?)\" ').search(x).group(1))
        data["height"] = int(re.compile(r'height=\"(.*?)\" ').search(x).group(1))
        data["xoffset"] = int(re.compile(r'xoffset=\"(.*?)\" ').search(x).group(1))
        data["yoffset"] = int(re.compile(r'yoffset=\"(.*?)\" ').search(x).group(1))
        data["xadvance"] = int(re.compile(r'xadvance=\"(.*?)\" ').search(x).group(1))
        data["page"] = int(re.compile(r'page=\"(.*?)\" ').search(x).group(1))
        data["chnl"] = int(re.compile(r'chnl=\"(.*?)\" ').search(x).group(1))
        
        return data
    
    
    def get_block_4_data_bn3(self, file):
        x = file.read(Block4Iterator.BLOCK_4_BINARY3_ENTRY_SIZE)
    
        data = {}
        data["id"] = int.from_bytes(x[0:4], "little")
        data["x"] = int.from_bytes(x[4:6], "little")
        data["y"] = int.from_bytes(x[6:8], "little")
        data["width"] = int.from_bytes(x[8:10], "little")
        data["height"] = int.from_bytes(x[10:12], "little")
        data["xoffset"] = int.from_bytes(x[12:14], "little", signed = True)
        data["yoffset"] = int.from_bytes(x[14:16], "little", signed = True)
        data["xadvance"] = int.from_bytes(x[16:18], "little", signed = True)
        data["page"] = x[18]
        data["chnl"] = x[19]
        
        return data
    
    
    def encode_block_4_data_txt(self, data):
        x = ""
        
        y = "char "
        y += "id=" + str(data["id"])
        y = y.ljust(max(13, len(y) + 1))
        x += y
        
        y = "x=" + str(data["x"])
        y = y.ljust(max(8, len(y) + 1))
        x += y
        
        y = "y=" + str(data["y"])
        y = y.ljust(max(8, len(y) + 1))
        x += y
        
        y = "width=" + str(data["width"])
        y = y.ljust(max(12, len(y) + 1))
        x += y
        
        y = "height=" + str(data["height"])
        y = y.ljust(max(13, len(y) + 1))
        x += y
        
        y = "xoffset=" + str(data["xoffset"])
        y = y.ljust(max(14, len(y) + 1))
        x += y
        
        y = "yoffset=" + str(data["yoffset"])
        y = y.ljust(max(14, len(y) + 1))
        x += y
        
        y = "xadvance=" + str(data["xadvance"])
        y = y.ljust(max(15, len(y) + 1))
        x += y
        
        y = "page=" + str(data["page"])
        y = y.ljust(max(8, len(y) + 1))
        x += y
        
        x += "chnl=" + str(data["chnl"]) + "\n"
        
        return x
    
    
    def encode_block_4_data_xml(self, data):
        x = "    <char "
        x += "id=\"" + str(data["id"]) + "\" "
        x += "x=\"" + str(data["x"]) + "\" "
        x += "y=\"" + str(data["y"]) + "\" "
        x += "width=\"" + str(data["width"]) + "\" "
        x += "height=\"" + str(data["height"]) + "\" "
        x += "xoffset=\"" + str(data["xoffset"]) + "\" "
        x += "yoffset=\"" + str(data["yoffset"]) + "\" "
        x += "xadvance=\"" + str(data["xadvance"]) + "\" "
        x += "page=\"" + str(data["page"]) + "\" "
        x += "chnl=\"" + str(data["chnl"]) + "\" />\n"
        
        return x
    
    
    def encode_block_4_data_bn3(self, data):
        x = bytearray()
        x += data["id"].to_bytes(4, "little")                       # id
        x += data["x"].to_bytes(2, "little")                        # x
        x += data["y"].to_bytes(2, "little")                        # y
        x += data["width"].to_bytes(2, "little")                    # width
        x += data["height"].to_bytes(2, "little")                   # height
        x += data["xoffset"].to_bytes(2, "little", signed = True)   # xoffset
        x += data["yoffset"].to_bytes(2, "little", signed = True)   # yoffset
        x += data["xadvance"].to_bytes(2, "little", signed = True)  # xadvance
        x += data["page"].to_bytes(2, "little")                     # page
        x += data["chnl"].to_bytes(2, "little")                     # chnl
        
        return x
    
    
    def __init__(self, _file, _source_file_type, _target_file_type):
        self.file = _file
        self.source_file_type = _source_file_type
        self.target_file_type = _target_file_type
        self.index = 0
        self.limit = 0
        
        self.metadata = self.get_block_4_metadata(self.file)
        self.limit = self.metadata["count"]
    
    
    def __iter__(self):
        return self
    
    
    def __next__(self):
        if self.index < self.limit:
            data = self.get_block_4_data(self.file)
            x = self.encode_block_4_data(data)
            
            if self.index == 0:
                x = self.get_fragment_header() + x
            elif self.index == self.limit - 1:
                if self.source_file_type == FILE_TYPE_XML:
                    self.file.readline() # Skips over the "  </chars>" closing tag
                x = x + self.get_fragment_footer()
            
            self.index += 1
            return x
        else:
            raise StopIteration


##########
# Block 5 (kernings) iterator
##########

# Returns an iterator that provides one line at a time.
class Block5Iterator:
    BLOCK_5_BINARY3_ENTRY_SIZE = 10
    
    # Also this initializes the file seek position
    def get_block_5_metadata(self, file):
        data = {}
        
        if self.source_file_type == FILE_TYPE_TEXT:
            x = file.readline().rstrip() + " "
            data["count"] = int(re.compile(r'count=(.*?) ').search(x).group(1))
        elif self.source_file_type == FILE_TYPE_XML:
            x = file.readline().rstrip("/>\n") + " "
            data["count"] = int(re.compile(r'count=\"(.*?)\" ').search(x).group(1))
        elif self.source_file_type == FILE_TYPE_BINARY3:
            file.seek(1, io.SEEK_CUR) # Skips over the "block 5" byte
            size = file.read(4)
            size = int.from_bytes(size, byteorder = "little")
            data["count"] = int(size / Block5Iterator.BLOCK_5_BINARY3_ENTRY_SIZE)
        return data
    
    
    # Returns the text or bytes that should go in front of the first entry
    def get_fragment_header(self):
        if self.target_file_type == FILE_TYPE_TEXT:
            return "kernings count=" + str(self.metadata["count"]) + "\n"
        if self.target_file_type == FILE_TYPE_XML:
            return "  <kernings count=\"" + str(self.metadata["count"]) + "\">\n"
        if self.target_file_type == FILE_TYPE_BINARY3:
            return bytearray([5]) + self.metadata["count"].to_bytes(4, "little")
    
    
    # Returns the text or bytes that should go behind the last entry
    def get_fragment_footer(self):
        if self.target_file_type == FILE_TYPE_TEXT:
            return ""
        if self.target_file_type == FILE_TYPE_XML:
            return "  </kernings>\n"
        if self.target_file_type == FILE_TYPE_BINARY3:
            return bytearray()
    
    
    # Reads a line (or entry) of data from block 4, and returns it in a dictionary.
    # Assumes the file is at the beginning of block 4.
    def get_block_5_data(self, file):
        functions = [self.get_block_5_data_txt, self.get_block_5_data_xml, self.get_block_5_data_bn3]
        return functions[self.source_file_type](file)
    
    
    # Translates a line (or entry) of data for block 4 into the file format using a dictionary.
    # Does not automatically write the info into the new file!
    def encode_block_5_data(self, data):
        functions = [self.encode_block_5_data_txt, self.encode_block_5_data_xml, self.encode_block_5_data_bn3]
        return functions[self.target_file_type](data)
    
    
    # More specific functions that the above two redirect to.
    def get_block_5_data_txt(self, file):
        x = file.readline()
        x = x.rstrip() + " "
        
        data = {}
        data["first"] = int(re.compile(r'first=(.*?) ').search(x).group(1))
        data["second"] = int(re.compile(r'second=(.*?) ').search(x).group(1))
        data["amount"] = int(re.compile(r'amount=(.*?) ').search(x).group(1))
        
        return data
    
    
    def get_block_5_data_xml(self, file):
        x = file.readline()
        x = x.rstrip("/>\n") + " "
        
        data = {}
        data["first"] = int(re.compile(r'first=\"(.*?)\" ').search(x).group(1))
        data["second"] = int(re.compile(r'second=\"(.*?)\" ').search(x).group(1))
        data["amount"] = int(re.compile(r'amount=\"(.*?)\" ').search(x).group(1))
        
        return data
    
    
    def get_block_5_data_bn3(self, file):
        x = file.read(Block5Iterator.BLOCK_5_BINARY3_ENTRY_SIZE)
        
        data = {}
        data["first"] = int.from_bytes(x[0:4], "little")
        data["second"] = int.from_bytes(x[4:8], "little")
        data["amount"] = int.from_bytes(x[8:10], "little", signed = True)
        
        return data
    
    
    def encode_block_5_data_txt(self, data):
        x = ""
        
        y = "kerning "
        y += "first=" + str(data["first"])
        y = y.ljust(max(18, len(y) + 1))
        x += y
        
        y = "second=" + str(data["second"])
        y = y.ljust(max(11, len(y) + 1))
        x += y
        
        y = "amount=" + str(data["amount"])
        y = y.ljust(max(11, len(y) + 1))
        x += y + "\n"
        
        return x
    
    
    def encode_block_5_data_xml(self, data):
        x = "    <kerning "
        x += "first=\"" + str(data["first"]) + "\" "
        x += "second=\"" + str(data["second"]) + "\" "
        x += "amount=\"" + str(data["amount"]) + "\" />\n"
        
        return x
    
    
    def encode_block_5_data_bn3(self, data):
        x = bytearray()
        x += data["first"].to_bytes(4, "little")                    # first
        x += data["second"].to_bytes(4, "little")                   # second
        x += data["amount"].to_bytes(2, "little", signed = True)    # amount
        
        return x
    
    
    def __init__(self, _file, _source_file_type, _target_file_type):
        self.file = _file
        self.source_file_type = _source_file_type
        self.target_file_type = _target_file_type
        self.index = 0
        self.limit = 0
        
        self.metadata = self.get_block_5_metadata(self.file)
        self.limit = self.metadata["count"]
    
    
    def __iter__(self):
        return self
    
    
    def __next__(self):
        if self.index < self.limit:
            data = self.get_block_5_data(self.file)
            x = self.encode_block_5_data(data)
            
            if self.index == 0:
                x = self.get_fragment_header() + x
            elif self.index == self.limit - 1:
                if self.source_file_type == FILE_TYPE_XML:
                    self.file.readline() # Skips over the "  </kernings>" closing tag
                x = x + self.get_fragment_footer()
            
            self.index += 1
            return x
        else:
            raise StopIteration
