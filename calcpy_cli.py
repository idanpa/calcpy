#!/usr/bin/env python3

import calcpy
import IPython
import argparse
import subprocess
import shutil
import os

import threading
import prompt_toolkit.patch_stdout

# TODO: how to do this dynamically?
from prompt_toolkit.styles.defaults import PROMPT_TOOLKIT_STYLE
PROMPT_TOOLKIT_STYLE.remove((('bottom-toolbar', 'reverse')))
PROMPT_TOOLKIT_STYLE.append((('bottom-toolbar', 'noreverse')))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='store_true', help='Print version and exit')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('-c', '--command', help="Execute given command and exit")
    args, args_reminder = parser.parse_known_args()

    if args.version:
        print(f"CalcPy {calcpy.__version__}")
        return 0

    ipython_args = [
        "--TerminalIPythonApp.display_banner=False",
        "--InteractiveShell.separate_in=",
        #--InteractiveShellApp.extra_extensions is only supported from 7.10
        "--InteractiveShellApp.exec_lines=%load_ext calcpy",
        "--InteractiveShellApp.hide_initial_ns=False", # we partially hide them
        "--PlainTextFormatter.float_precision=%.6g",
        "--TerminalInteractiveShell.confirm_exit=False",
        "--TerminalInteractiveShell.term_title_format=CalcPy",
        f"--profile={calcpy.CALCPY_PROFILE_NAME}",
    ]

    if args.debug:
        ipython_args.append("--CalcPy.debug=True")
        ipython_args.append("--TerminalInteractiveShell.xmode=verbose")

    if args.command:
        ipython_args.append(f"--InteractiveShellApp.code_to_run={args.command}")

    ipython_args.extend(args_reminder)

    # monkey patch prompt_toolkit to avoid printin from background for preview
    # TODO: need a better fix
    stdoutproxy_write = prompt_toolkit.patch_stdout.StdoutProxy.write
    def skip_asyncio_thread_write(self, data):
        if not threading.current_thread().name.startswith('asyncio'):
            return stdoutproxy_write(self, data)
        return len(data)  # Pretend everything was written.
    prompt_toolkit.patch_stdout.StdoutProxy.write = skip_asyncio_thread_write

    IPython.start_ipython(ipython_args)

if __name__ == "__main__":
    main()
