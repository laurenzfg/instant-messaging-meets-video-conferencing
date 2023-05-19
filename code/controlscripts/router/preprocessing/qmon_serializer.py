import ctypes as ct
import struct
import datetime

# This scripts serializes a raw queue capture produced with monitorbpf.py
# Author: Constantin Sander
# Improved by: Laurenz Grote

class Data(ct.Structure):
    _fields_ = [("size", ct.c_uint8),
                ("ts", ct.c_uint64),
                ("handle", ct.c_uint32),
                ("limit", ct.c_uint32),
                ("qlen", ct.c_uint32),
                ("qlen_qstats", ct.c_uint32),
                ("backlog", ct.c_uint32),
                ("drops", ct.c_uint32),
                ("requeues", ct.c_uint32),
                ("overlimits", ct.c_uint32),
                ("pkt_len_dequeued", ct.c_uint),
                ("retval", ct.c_uint64),
                ("inval", ct.c_uint64),
                ("event_type", ct.c_char*3),
                ("dev_name", ct.c_char*16),
                ("skblen", ct.c_uint16),
                ("reclen", ct.c_uint16),
                ("skbdata", ct.c_ubyte*200)]



serialization = """
u64 ts
u32 handle
u32 limit
u32 qlen
u32 qlen_qstats
u32 backlog
u32 drops
u32 requeues
u32 overlimits
u8 event_type
u64 misc
u64 skb
u16 skblen
u8 ifname_size
u16 reclen
char* dev_name
char* skbdata
"""

mapping = {"u8": "B", "u16": "H", "u32": "L", "u64": "Q", "char*": None}

def get_full_deserializer():
    fields = []
    struct_components = ["<"]
    stop = False
    for line in serialization.split("\n"):
        splitted = line.split()
        if len(splitted) == 2:
            fields.append(splitted[1])
            m = mapping[splitted[0]]
            if m is None:
                stop = True
            else:
                assert not stop
                struct_components.append(m)
    structstr = "".join(struct_components)
    structinstance = struct.Struct(structstr)
    size = struct.calcsize(structstr)
    unpack = structinstance.unpack
    return lambda b: (size, dict(zip(fields, unpack(b[:size]))))

def get_header_deserializer():
    return struct.Struct("<HB").unpack

def till_null(bytes_in):
    out = []
    for b in bytes_in:
        if b == 0:
            break
        out.append(b)
    return bytearray(out)

def get_qmon_items(f):

    header_deserializer = get_header_deserializer()
    full_deserializer = get_full_deserializer()

    mono2real = None
    while True:
        s = f.read(3)
        if len(s) != 3:
            break
        size, typ = header_deserializer(s)
        if size > 3:
            s = f.read(size - 3)
            assert len(s) == size - 3
        else:
            s = []
        assert typ != 1
        if typ == 2:
            assert mono2real is None
            mono2real = int(s)
        elif typ == 0:
            assert mono2real is not None
            hoffs, h = full_deserializer(s)
            ifn_size = h['ifname_size']
            reclen = h['reclen']
            h['ifname'] = till_null(s[hoffs:hoffs+ifn_size]).decode('utf-8')
            h['skbdata'] = s[hoffs+ifn_size:hoffs+ifn_size+reclen]
            h['ts'] += mono2real
            h['ts'] /= 10**9
            h['dt'] = datetime.datetime.fromtimestamp(h['ts'])
            yield h
        elif typ == 1:
            print("lost packets!")
            assert False
        elif typ == 3:
            print("bad exception", f.read())
            assert False
        elif typ == 4:
            deq, enq = [int(x) for x in s.decode('utf-8').split(" ")[1].split(":")]
            assert deq < 5 and enq < 5, s.decode('utf-8')
        else:
            print("unknown")
            assert False
