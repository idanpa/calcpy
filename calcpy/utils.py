from tkinter import Tk

def copy(object):
    '''Copy object representation 'repr(object)' to clipboard'''
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(repr(object))
    r.update()
    r.destroy()
