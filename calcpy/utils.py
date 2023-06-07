
def copy(object):
    '''Copy object representation 'repr(object)' to clipboard'''
    try:
        import pyperclip
        pyperclip.copy(repr(object))
    except ModuleNotFoundError:
        # this is a bit slower, and when pasting too fast, clash with ipython's access to clipboard
        from tkinter import Tk
        r = Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(repr(object))
        r.update()
        r.destroy()
