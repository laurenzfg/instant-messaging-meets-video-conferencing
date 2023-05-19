# Experiment File Specification

We will conduct a lot of experiments. Hence, it is neccesary to maintain
information which files and parameters belong to which experiment.

Every experiment SHALL be documented by a file `<name>.txt`.
The file MUST be an ASCII encoded text file with UNIX line endings.

The first line MUST be the GUID of the test. Something in the lines of
> Signal vs TCP CUBIC Test Run Dec 15 14:30 UTC

The GUID is an arbitrary string.

The first line MUST be followed by an empty line.

Afterwards, we have a Dictionary as front matter.
The key is separated from the value by a semicolon `;`.
The key and the value MUST NOT include a semicolon.
Spaces SHOULD NOT be used except if they are part of the key or value.

Currently defined keys are:

    bpfcapture;filename of the relevant *preprocessed* BPF monitoring script output (the PICKLE file generated with convert_raw.py from the raw monitoring script output)

The front matter is terminated by an empty line.
Apart from the terminating empty line it MUST NOT contain empty lines.

The last section of the file is the timeline of the experiment.
Every timeline entry is a file line and contains three fields separated by a semicolon `;`.
All three fields MUST NOT include a semicolon.
 - The first field is a UNIX timestamp in UTC time zone up to nanosecond precision.
 - The second field is the event name.
 - The third field is reserved for payload associated to the event.
Currently defined event names and associated payloads are:

    bandwidth_changed;new bandwidth in MBit/s
    call_started;
    call_accepted;
    call_ended;

## Example file

To further illustrate the specification, this is a compliant experiment description file:

    Signal vs TCP CUBIC Test Run Dec 15 14:30 UTC

    bpfcapture;1234.pickle

    1639576960663832980;bandwidth_changed;10
    1639577026925615656;call_started;
    1639577054713666465;call_accepted;
    1639577065738689763;bandwidth_changed;0.2
    1639577065738689763;delay_changed;2.0-4.0

A 'delay_changed' event gives new delays for local and netbound packages, e.g. 2ms local
and 4ms netbound.
To get the RTT you have to calculate:
 - delay + uplink RTT for netbound traffic
 - 2x delay + insignificant testbed physical RTT for p2p traffic