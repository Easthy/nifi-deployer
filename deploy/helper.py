import yaml
from functools import wraps
import sys

#: Prompt start character sequence.
QSTR = "[y/n] "
#: User input start character sequence.
ISTR = ": "
#: User input function.
_input = input if sys.version_info >= (3, 0) else raw_input
#: Flag to indicate if running in auto mode.
_AUTO = False

def _format_kwargs(func):
    """Decorator to handle formatting kwargs to the proper names expected by
    the associated function. The formats dictionary string keys will be used as
    expected function kwargs and the value list of strings will be renamed to
    the associated key string."""
    formats = {}
    formats['blk'] = ["blank"]
    formats['dft'] = ["default"]
    formats['hdr'] = ["header"]
    formats['hlp'] = ["help"]
    formats['msg'] = ["message"]
    formats['shw'] = ["show"]
    formats['vld'] = ["valid"]
    @wraps(func)
    def inner(*args, **kwargs):
        for k in formats.keys():
            for v in formats[k]:
                if v in kwargs:
                    kwargs[k] = kwargs[v]
                    kwargs.pop(v)
        return func(*args, **kwargs)
    return inner

@_format_kwargs
def ask(msg="Enter input", fmt=None, dft=None, vld=None, shw=True, blk=False, hlp=None, qstr=True, multi=False, **kwargs):
    """Prompts the user for input and returns the given answer. Optionally
    checks if answer is valid.

    **Params**:
      - msg (str) - Message to prompt the user with.
      - fmt (func) - Function used to format user input.
      - dft (int|float|str) - Default value if input is left blank.
      - vld ([int|float|str|func]) - Valid input entries.
      - shw (bool) - If true, show the user's input as typed.
      - blk (bool) - If true, accept a blank string as valid input. Note that
        supplying a default value will disable accepting blank input.
    """
    global _AUTO
    def print_help():
        lst = [v for v in vld if not callable(v)]
        if blk:
            lst.remove("")
        for v in vld:
            if not callable(v):
                continue
            if int == v:
                lst.append("<int>")
            elif float == v:
                lst.append("<float>")
            elif str == v:
                lst.append("<str>")
            else:
                lst.append("(" + v.__name__ + ")")
        if lst:
            echo("[HELP] Valid input: %s" % (" | ".join([str(l) for l in lst])))
        if hlp:
            echo("[HELP] Extra notes: " + hlp)
        if blk:
            echo("[HELP] Input may be blank.")
    vld = vld or []
    hlp = hlp or ""
    if not hasattr(vld, "__iter__"):
        vld = [vld]
    if not hasattr(fmt, "__call__"):
        fmt = lambda x: x  # NOTE: Defaults to function that does nothing.
    msg = "%s%s" % (QSTR if qstr else "", msg)
    dft = fmt(dft) if dft != None else None # Prevents showing [None] default.
    if dft != None:
        msg += " [%s]" % (dft if type(dft) is str else repr(dft))
        vld.append(dft)
        blk = False
    if vld:
        # Sanitize valid inputs.
        vld = list(set([fmt(v) if fmt(v) else v for v in vld]))
        if blk and "" not in vld:
            vld.append("")
        # NOTE: The following fixes a Py3 related bug found in `0.8.1`.
        try: vld = sorted(vld)
        except: pass
    msg += ISTR
    ans = None
    while ans is None:
        get_input = _input if shw else getpass
        ans = get_input(msg)
        if _AUTO:
            echo(ans)
        if "?" == ans:
            print_help()
            ans = None
            continue
        if "" == ans:
            if dft != None:
                ans = dft if not fmt else fmt(dft)
                break
            if "" not in vld:
                ans = None
                continue
        try:
            ans = ans if not fmt else fmt(ans)
        except:
            ans = None
        if vld:
            for v in vld:
                if type(v) is type and cast(ans, v) is not None:
                    ans = cast(ans, v)
                    break
                elif hasattr(v, "__call__"):
                    try:
                        if v(ans):
                            break
                    except:
                        pass
                elif ans in vld:
                    break
            else:
                ans = None
    return ans

def ask_yesno(msg="Proceed?", dft=None, **kwargs):
    """Prompts the user for a yes or no answer. Returns True for yes, False
    for no."""
    yes = ["y", "yes", "Y", "YES"]
    no = ["n", "no", "N", "NO"]
    if dft != None:
        dft = yes[0] if (dft in yes or dft == True) else no[0]
    return ask(msg, dft=dft, vld=yes+no) in yes 
