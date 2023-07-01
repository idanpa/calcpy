
def copy(obj):
    '''Copy obj representation 'repr(obj)' to clipboard'''
    if not isinstance(obj, str):
        obj = repr(obj)
    try:
        import pyperclip
        pyperclip.copy(obj)
    except ModuleNotFoundError:
        # this is a bit slower, and when pasting too fast, clash with ipython's access to clipboard
        from tkinter import Tk
        r = Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(obj)
        r.update()
        r.destroy()
