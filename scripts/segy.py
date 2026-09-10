"""Minimal SEG-Y reader, rev0/rev1, big-endian. No external deps beyond numpy."""
import numpy as np, struct

def _ibm2ieee(b4):
    i = b4.astype(np.uint32)
    sign = ((i >> 31) & 0x01).astype(np.int32)
    expo = ((i >> 24) & 0x7f).astype(np.int32)
    mant = (i & 0x00ffffff).astype(np.float64)
    out = (1 - 2 * sign) * mant * np.power(16.0, expo - 64) / 16777216.0
    return out.astype(np.float64)

BIN = {  # byte offset (1-based in 3201..3600) : (name, fmt)
    3213: ('ntraces_ens', 'h'), 3217: ('sample_interval_us', 'h'),
    3219: ('si_orig', 'h'), 3221: ('nsamples', 'h'), 3223: ('ns_orig', 'h'),
    3225: ('format_code', 'h'), 3227: ('ensemble_fold', 'h'),
    3229: ('trace_sorting', 'h'), 3255: ('measurement_system', 'h'),
    3501: ('segy_rev', 'h'), 3503: ('fixed_length', 'h'),
    3505: ('n_ext_headers', 'h'),
}
TRC = {
    1: ('tracl', 'i'), 5: ('tracr', 'i'), 9: ('fldr', 'i'), 13: ('tracf', 'i'),
    17: ('ep', 'i'), 21: ('cdp', 'i'), 25: ('cdpt', 'i'), 29: ('trid', 'h'),
    37: ('offset', 'i'), 41: ('gelev', 'i'), 45: ('selev', 'i'),
    69: ('scalel', 'h'), 71: ('scalco', 'h'),
    73: ('sx', 'i'), 77: ('sy', 'i'), 81: ('gx', 'i'), 85: ('gy', 'i'),
    89: ('counit', 'h'), 105: ('sdel','h'),
    109: ('delrt', 'h'), 111: ('muts', 'h'), 113: ('mute', 'h'),
    115: ('ns', 'h'), 117: ('dt', 'h'),
    181: ('cdpx', 'i'), 185: ('cdpy', 'i'), 189: ('iline', 'i'), 193: ('xline', 'i'),
    201: ('unassigned201', 'h'),
}

def read(path, want_data=True, maxtr=None):
    raw = open(path, 'rb').read()
    txt = raw[:3200]
    bh = {}
    for off, (nm, f) in BIN.items():
        bh[nm] = struct.unpack('>' + f, raw[off - 1:off - 1 + struct.calcsize(f)])[0]
    ns = bh['nsamples']; fc = bh['format_code']
    bps = {1: 4, 2: 4, 3: 2, 5: 4, 8: 1}[fc]
    tsz = 240 + ns * bps
    ntr = (len(raw) - 3600) // tsz
    if maxtr: ntr = min(ntr, maxtr)
    hdrs = []
    data = np.empty((ntr, ns), dtype=np.float64) if want_data else None
    for t in range(ntr):
        o = 3600 + t * tsz
        h = {}
        for off, (nm, f) in TRC.items():
            h[nm] = struct.unpack('>' + f, raw[o + off - 1:o + off - 1 + struct.calcsize(f)])[0]
        hdrs.append(h)
        if want_data:
            b = raw[o + 240:o + 240 + ns * bps]
            if fc == 1:
                data[t] = _ibm2ieee(np.frombuffer(b, dtype='>u4'))
            elif fc == 5:
                data[t] = np.frombuffer(b, dtype='>f4')
            elif fc == 2:
                data[t] = np.frombuffer(b, dtype='>i4')
            elif fc == 3:
                data[t] = np.frombuffer(b, dtype='>i2')
    return dict(text=txt, bin=bh, hdrs=hdrs, data=data, ntr=ntr, ns=ns, fc=fc, nbytes=len(raw))

def ebcdic_or_ascii(b):
    import codecs
    try:
        s = b.decode('cp037')
        if sum(c.isprintable() or c in '\r\n' for c in s) > 0.85 * len(s): return s
    except Exception: pass
    return b.decode('latin-1', 'replace')
