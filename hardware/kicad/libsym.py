"""Minimal S-expression parser and KiCad symbol-library helpers."""
import re
SYMDIR = "/usr/share/kicad/symbols"
def tokenize(s):
    return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)
def parse(s):
    toks = tokenize(s); pos = 0
    def rd():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == '(':
            lst = []
            while toks[pos] != ')':
                lst.append(rd())
            pos += 1
            return lst
        return t
    return rd()
def dump(x, ind=0):
    if isinstance(x, list):
        if all(not isinstance(e, list) for e in x):
            return "(" + " ".join(x) + ")"
        out = "(" + " ".join(e for e in x if not isinstance(e, list) and x.index(e) == 0)
        parts = []
        first = True
        s = "("
        items = []
        for e in x:
            items.append(dump(e, ind + 1) if isinstance(e, list) else e)
        return "(" + " ".join(items[:1]) + ("\n" + "  " * (ind + 1) if len(items) > 1 else "") + ("\n" + "  " * (ind + 1)).join(items[1:]) + ")"
    return x
_cache = {}
def lib(name):
    if name not in _cache:
        _cache[name] = parse(open(f"{SYMDIR}/{name}.kicad_sym").read())
    return _cache[name]
def find_sym(libname, symname):
    L = lib(libname)
    for e in L:
        if isinstance(e, list) and e[0] == 'symbol' and e[1].strip('"') == symname:
            return e
    raise KeyError(symname)
def flatten(libname, symname):
    """Return a symbol S-expr with 'extends' resolved and name prefixed 'lib:sym'."""
    s = find_sym(libname, symname)
    ext = [e for e in s if isinstance(e, list) and e[0] == 'extends']
    if ext:
        base = flatten(libname, ext[0][1].strip('"'))
        bname = ext[0][1].strip('"')
        props = {e[1]: e for e in s if isinstance(e, list) and e[0] == 'property'}
        out = []
        for e in base:
            if isinstance(e, list) and e[0] == 'property' and e[1] in props:
                out.append(props.pop(e[1]))
            elif isinstance(e, list) and e[0] == 'symbol':
                sub = list(e); sub[1] = sub[1].replace(f'{libname}:{bname}', symname).replace(bname, symname)
                sub[1] = '"' + symname + sub[1].strip('"')[len(symname):] + '"' if False else sub[1]
                out.append(sub)
            else:
                out.append(e)
        out[1] = f'"{libname}:{symname}"'
        # rename unit sub-symbols
        for e in out:
            if isinstance(e, list) and e[0] == 'symbol':
                nm = e[1].strip('"')
                e[1] = '"' + symname + nm[nm.rfind('_', 0, nm.rfind('_')):] + '"'
        out += list(props.values())
        return out
    out = list(s); out[1] = f'"{libname}:{symname}"'
    return out
def pins(sym):
    """[(number, name, x, y, angle, length, etype)] in symbol coords (y up)."""
    res = []
    def walk(e):
        if isinstance(e, list):
            if e and e[0] == 'pin':
                at = [x for x in e if isinstance(x, list) and x[0] == 'at'][0]
                ln = [x for x in e if isinstance(x, list) and x[0] == 'length'][0]
                num = [x for x in e if isinstance(x, list) and x[0] == 'number'][0][1].strip('"')
                nm = [x for x in e if isinstance(x, list) and x[0] == 'name'][0][1].strip('"')
                res.append((num, nm, float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, float(ln[1]), e[1]))
            else:
                for x in e: walk(x)
    walk(sym)
    return res
