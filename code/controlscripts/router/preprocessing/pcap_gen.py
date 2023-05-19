import ctypes as ct

# pcap_gen generates a dump in the PCAP format.
# To generate such a dump, create an instance of the PcapFileGen using the designated writer f
# Then you can add packets to the dump by invoking addPacket()

#4	uint32	magic_number	'A1B2C3D4' means the endianness is correct
#2	uint16	version_major	major number of the file format
#2	uint16	version_minor	minor number of the file format
#4	int32	thiszone	correction time in seconds from UTC to local time (0)
#4	uint32	sigfigs	accuracy of time stamps in the capture (0)
#4	uint32	snaplen	max length of captured packed (65535)
#4	uint32	network	type of data link (1 = ethernet)
#d4 c3 b2 a1 02 00 04 00 00 00 00 00 00 00 00 00 c8 00 00 00 01 00 00 00

class PCAPGlobalHeader(ct.Structure):
    _pack_ = 1
    _fields_ = [("magic_number", ct.c_uint32),
                ("version_major", ct.c_uint16),
                ("version_minor", ct.c_uint16),
                ("thiszone", ct.c_int32),
                ("sigfigs", ct.c_uint32),
                ("snaplen", ct.c_uint32),
                ("network", ct.c_uint32)]

#4	uint32	ts_sec	timestamp seconds
#4	uint32	ts_usec	timestamp microseconds
#4	uint32	incl_len	number of octets of packet saved in file
#4	uint32	orig_len	actual length of packet

class PCAPPacketHeader(ct.Structure):
    _pack_ = 1
    _fields_ = [("ts_sec", ct.c_uint32),
                ("ts_usec", ct.c_uint32),
                ("incl_len", ct.c_uint32), # in file
                ("orig_len", ct.c_int32)] # total

class PcapFileGen:
    def __init__(self, snaplen, f):
        self.snaplen = snaplen
        self.f = f
        p = PCAPGlobalHeader(int("A1B2C3D4", 16), 2, 4, 0, 0, snaplen, 1)
        f.write(bytearray(p))

    def addPacket(self, data, ts, orig_len):
        ts_sec = int(ts)
        ts_sec_rest = ts - ts_sec
        ts_usec = int(ts_sec_rest * 10 ** 6)
        p = PCAPPacketHeader(ts_sec, ts_usec, len(data), orig_len)
        self.f.write(bytearray(p))
        self.f.write(bytearray(data))
