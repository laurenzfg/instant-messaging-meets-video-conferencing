#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# tc_probe Trace tc enqueue and dequeue operations.
#           For Linux, uses BCC, eBPF. Embedded C.
#
# USAGE: tc_probe --type <>
#
# You need to name the queue type,
# if you have a stack, say of a HTB and CODEL, you can choose either
# note that choosing the bottom one causes less overhead if other
# queues are present that also use HTB but not say.. CODEL
#
#
# This uses dynamic tracing of the kernel *_dequeue() and *_encqueue() tc functions
# , and will need to be modified to match kernel changes.
#
#
# Copyright (c) 2017 Jan Rüth.
# Modified to serialize data and record skb's (C) 2020 Constantin Sander.
# Updated comments (c) 2021 Laurenz Grote
# Licensed under the Apache License, Version 2.0 (the "License")

from __future__ import print_function

from bcc import BPF
from struct import pack
import ctypes as ct
import sys
from argparse import ArgumentParser
import traceback
import signal


QDISC_FUNCS = {
    "htb": ("htb_enqueue", "htb_dequeue"),
    "hfsc": ("hfsc_enqueue", "hfsc_dequeue"),
    "netem": ("netem_enqueue", "netem_dequeue"),
    "fq": ("fq_enqueue", "fq_dequeue"),
    "fq_codel": ("fq_codel_enqueue", "fq_codel_dequeue"),
    "codel": ("codel_qdisc_enqueue", "codel_qdisc_dequeue"),
    "pfifo": ("pfifo_enqueue", "qdisc_dequeue_head"),
    "bfifo": ("bfifo_enqueue", "qdisc_dequeue_head"),
    "pfifo_head": ("pfifo_head_enqueue", "qdisc_dequeue_head"),
    "prio": ("prio_enqueue", "prio_dequeue"),
    "tbf": ("tbf_enqueue", "tbf_dequeue")
}


parser = ArgumentParser(description="TC Queue monitor")

parser.add_argument('--type', '-t',
                    dest="type",
                    type = str.lower,
                    choices=QDISC_FUNCS.keys(),
                    action="store",
                    help="Queue type to be monitored",
                    required=True)

args = parser.parse_args()

# define BPF program
prog = """
    #include <net/sch_generic.h>
    #include <net/pkt_sched.h>
    #include <linux/rbtree.h>
    #include <uapi/linux/gen_stats.h>
    #include <uapi/linux/if.h>

    #define BPF_COPY(to, from) bpf_probe_read(&to, sizeof(to), &from)
    #define MAX(x, y) (((x) > (y)) ? (x) : (y))
    #define MIN(x, y) (((x) < (y)) ? (x) : (y))
    #define RECLEN REPLACERECLEN

    #define RD 0
    #define RE 1

    struct dummy {
        //RECLEN + 100 is just a rough overapproximation
        //The verifier is quite strict about the size and seems to fail if we exceed it
        char buffer[RECLEN + 100];
    };

    static inline u16 populate(void* out, struct Qdisc* q, struct sk_buff* skb, u8 event_type, u64 misc) {
        void* osize = out;
        out += 2;
        {
        u8* otype = out;
        out += 1;
        *otype = 0;
        }
        {
        void* ots = out;
        out += 8;
        u64 ts = bpf_ktime_get_ns();
        __builtin_memcpy(ots, &ts, 8);
        }
        {
        void* ohandle = out;
        out += 4;
        bpf_probe_read(ohandle, 4, &q->handle);
        }
        {
        void* olimit = out;
        out += 4;
        bpf_probe_read(olimit, 4, &q->limit);
        }
        {
        void* oqlen = out;
        out += 4;
        bpf_probe_read(oqlen, 4, &q->q.qlen);
        }
        {
        void* oqlen_qstats = out;
        out += 4;
        bpf_probe_read(oqlen_qstats, 4, &q->qstats.qlen);
        }
        {
        void* obacklog = out;
        out += 4;
        bpf_probe_read(obacklog, 4, &q->qstats.backlog);
        }
        {
        void* odrops = out;
        out += 4;
        bpf_probe_read(odrops, 4, &q->qstats.drops);
        }
        {
        void* orequeues = out;
        out += 4;
        bpf_probe_read(orequeues, 4, &q->qstats.requeues);
        }
        {
        void* ooverlimits = out;
        out += 4;
        bpf_probe_read(ooverlimits, 4, &q->qstats.overlimits);
        }
        {
        u8* oevent_type = out;
        out += 1;
        *oevent_type = event_type;
        }
        {
        void* omisc = out;
        out += 8;
        __builtin_memcpy(omisc, &misc, 8);
        }
        {
        void* oskb = out;
        out += 8;
        __builtin_memcpy(oskb, &skb, 8);
        }
        {
        u16 skblen = skb->len;
        void* oskblen = out;
        out += 2;
        __builtin_memcpy(oskblen, &skblen, 2);
        }
        {
        u8* oifname_size = out;
        out += 1;
        *oifname_size = IFNAMSIZ;
        }
        {
        u16 skblen = skb->len;
        u16 reclen = MIN(RECLEN, skblen);
        void* oreclen = out;
        out += 2;
        __builtin_memcpy(oreclen, &reclen, 2);
        }
        {
        void* odev_name = out;
        out += IFNAMSIZ;
        struct netdev_queue *dev_queue = q->dev_queue;
        struct net_device *dev = dev_queue->dev;
        void* name = dev->name;
        bpf_probe_read(odev_name, IFNAMSIZ, name);
        }
        u16 size = out - ((void*) osize);
        {
        u16 skblen = skb->len;
        u16 reclen = MIN(RECLEN, skblen);
        void* skbdata = skb->data;
        
        size += reclen;
        
        void* oskbdata = out;
        bpf_probe_read(oskbdata, reclen, skbdata);
        }
        __builtin_memcpy(osize, &size, 2);
        return size;
    }
    BPF_PERF_OUTPUT(events);

    struct entry {
        struct Qdisc *qdisc;
        struct sk_buff *skb;
        struct sk_buff **to_free;
    };

    struct entry_key {
        u32 pid;
        u32 cpu;
    };

    BPF_HASH(currqdisc_de, struct entry_key, struct entry);
    BPF_HASH(currqdisc_en, struct entry_key, struct entry);

    void dequeue_skb(struct pt_regs *ctx, struct Qdisc *q) {
        struct entry e = {};
        e.qdisc = q;

        struct entry_key k = {};
        k.pid = bpf_get_current_pid_tgid();
        k.cpu = bpf_get_smp_processor_id();;

        currqdisc_de.update(&k, &e);
    }

    void enqueue_skb(struct pt_regs *ctx, struct sk_buff *skb, struct Qdisc *q, struct sk_buff **to_free) {
        struct entry e = {};
        e.qdisc = q;
        e.skb = skb;
        e.to_free = to_free;

        struct entry_key k = {};
        k.pid = bpf_get_current_pid_tgid();
        k.cpu = bpf_get_smp_processor_id();

        currqdisc_en.update(&k, &e);
    }

    int ret_dequeue_skb(struct pt_regs *ctx) {
        struct sk_buff * skb = (struct sk_buff *)PT_REGS_RC(ctx);

        struct entry_key k = {};
        k.pid = bpf_get_current_pid_tgid();
        k.cpu = bpf_get_smp_processor_id();

        struct entry *entryp;
        entryp = currqdisc_de.lookup(&k);

        if(entryp == NULL)
            return 0;

        if(skb == NULL) {
            currqdisc_de.delete(&k);
            return 0;
        }

        struct Qdisc *q = entryp->qdisc;

        //bcc segfaults during analysis if this is no struct
        struct dummy dummy = {};
        u32 size = populate(&dummy, q, skb, RD, 0);
        events.perf_submit(ctx, &dummy, size);

        currqdisc_de.delete(&k);

        return 0;
    }

    int ret_enqueue_skb(struct pt_regs *ctx) {
        // Was the enqueue succesful?
        int ret = (int)PT_REGS_RC(ctx);

        struct entry_key k = {};
        k.pid = bpf_get_current_pid_tgid();
        k.cpu = bpf_get_smp_processor_id();

        struct entry *entryp;
        entryp = currqdisc_en.lookup(&k);

        if(entryp == NULL)
            return 0;

        struct Qdisc *q = entryp->qdisc;
        struct sk_buff * skb = entryp->skb;

        //bcc segfaults during analysis if this is no struct
        struct dummy dummy = {};
        u16 size = populate(&dummy, q, skb, RE, ret);
        events.perf_submit(ctx, &dummy, size);

        currqdisc_en.delete(&k);

        return 0;
    }
    """

enqueue, dequeue = QDISC_FUNCS[args.type.lower()]

# load BPF program
b = BPF(text=prog.replace("REPLACERECLEN", "100"), debug=0x0)
b.attach_kprobe(event=enqueue, fn_name="enqueue_skb")
b.attach_kretprobe(event=enqueue, fn_name="ret_enqueue_skb")
b.attach_kprobe(event=dequeue, fn_name="dequeue_skb")
b.attach_kretprobe(event=dequeue, fn_name="ret_dequeue_skb")

f = sys.stdout

dotCounter = 0

def tofile(cpu, data, size):
    global dotCounter
    dotCounter = dotCounter + 1

    array = ct.cast(data, ct.POINTER(ct.c_uint8*size)).contents
    b = bytearray(array)
    size = b[0] + b[1] * 256
    f.write(b[:size])
    f.flush()

def lost(x):
    if x >= 255:
        x = 255
    b = bytearray([4, 0, 1, x])
    f.write(b)
    f.flush()

def big_exception():
    b = bytearray([3, 0, 3])
    f.write(b)
    f.flush()

def write_debug(debug):
    b = bytearray(debug)
    b = bytearray([3+len(b), 0, 4]) + b
    f.write(b)
    f.flush()

def write_diff():
    with open("/proc/constantin") as time:
        diff = time.readline()
    b = bytearray(diff)
    l = len(b)
    b = bytearray([3+l, 0, 2]) + b
    f.write(b)
    f.flush()
    sys.stderr.write("BPF READY\n")
    sys.stderr.flush()

write_diff()

b["events"].open_perf_buffer(tofile, page_cnt=2**16, lost_cb=lost)

def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

try:
    while 1:
        b.perf_buffer_poll()
except KeyboardInterrupt:
    pass
except Exception as thrown_exception:
    big_exception()
    print("Error during monitor_queue_bpf", file=sys.stderr)
    print("----------------------------------------------------------------", file=sys.stderr)
    print(thrown_exception, file=sys.stderr)
    print(traceback.print_exc(), file=sys.stderr)
finally:
    write_debug("lengths %d:%d" % (len(b['currqdisc_de'].items()), len(b['currqdisc_en'].items())))
