import subprocess
import shlex
import io
import csv

# This scripts parses a wireshark PCAP file into a python-esque data structure.
# All relevant data are copied into to the ip and l3 fields
# Author: Constantin Sander
# Improved by: Laurenz Grote

class PcapTshark:
    def __init__(self, f):
        # We invoke tshark to decode the PCAP file
        cmd = 'tshark -i - -Q -T fields -e frame.time_epoch -e frame.len ' + \
            '-e ip.src -e ip.dst ' + \
            '-e eth.src -e eth.dst ' + \
            '-e ipv6.src -e ipv6.dst ' + \
            '-e tcp.srcport -e tcp.dstport -e tcp.stream -e tcp.len ' + \
            '-e udp.srcport -e udp.dstport -e udp.stream -e udp.length ' + \
            '-E header=y -E separator=, -E quote=d -E occurrence=f'
        # We pipe in a file descriptor and get the STDOUT of tshark into a new PIPE
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stdin=f)
        self.process = process # save a reference to the process
        # read tshark's STDOUT into a csv.DictReader
        output = io.TextIOWrapper(process.stdout, encoding='utf-8')
        self.reader = csv.DictReader(output, delimiter=',', quotechar='"')
        
    def get_packets(self):
        # the actual parsing routine
        def _parse(row):
            def _int(x):
                if x == "":
                    return -1
                return int(x)

            parsing_functions = {'frame.time_epoch': float, "frame.len": int,
                                'tcp.srcport': _int, 'tcp.dstport': _int, 'tcp.stream': _int, 'tcp.len': _int,
                                'udp.srcport': _int, 'udp.dstport': _int, 'udp.stream': _int, 'udp.length': _int}

            for key in row.keys():
                if key in parsing_functions:
                    row[key] = parsing_functions[key](row[key])

            is_ipv4 = row['ip.src'] != ""
            is_ipv6 = row['ipv6.src'] != ""

            assert (not (is_ipv4 and is_ipv6))

            if is_ipv4:
                row['l3.src'] = row['ip.src']
                row['l3.dst'] = row['ip.dst']
                row['l3.proto'] = 'ipv4'
            elif is_ipv6:
                row['l3.src'] = row['ipv6.src']
                row['l3.dst'] = row['ipv6.dst']
                row['l3.proto'] = 'ipv6'
            else:
                return None

            is_tcp = row['tcp.len'] != -1
            is_udp = row['udp.length'] != -1

            assert (not (is_tcp and is_udp))

            if is_tcp:
                row['l4.srcport'] = row['tcp.srcport']
                row['l4.dstport'] = row['tcp.dstport']
                row['l4.len'] = row['tcp.len']
                row['l4.stream'] = "tcp:%d" % row['tcp.stream']
                row['l4.proto'] = 'tcp'
            elif is_udp:
                row['l4.srcport'] = row['udp.srcport']
                row['l4.dstport'] = row['udp.dstport']
                row['l4.len'] = row['udp.length']
                row['l4.stream'] = "udp:%d" % row['udp.stream']
                row['l4.proto'] = 'udp'
            else:
                return None

            return row

        # read every line from the CSV reader started above and parse it
        for row in self.reader:
            row = _parse(row)
            yield row # yield it back as a pythonic element
        assert 0 == self.process.wait() # wait until tshark exits
