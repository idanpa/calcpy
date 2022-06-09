#!/usr/bin/env python3

import calcpy
import IPython
import argparse
import subprocess
import shutil
import multiprocessing

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gui', action='store_true', help='Launch CalcPy GUI')
    parser.add_argument('--version', action='store_true', help='Print version and exit')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('-c', '--command', help="Execute given command and exit")
    args, args_reminder = parser.parse_known_args()

    if args.version:
        print(f"CalcPy {calcpy.__version__}")
        return 0

    ipython_cmd = [
        "--TerminalIPythonApp.display_banner=False",
        "--InteractiveShell.separate_in=",
        #--InteractiveShellApp.extra_extensions is only supported from 7.10
        "--InteractiveShellApp.exec_lines=%load_ext calcpy",
        "--StoreMagics.autorestore=True",
        # TODO: float_precision should be configurable (at startup)
        "--PlainTextFormatter.float_precision=%.6g",
        "--TerminalInteractiveShell.confirm_exit=False",
        "--TerminalInteractiveShell.term_title_format=CalcPy",
        f"--profile={calcpy.CALCPY_PROFILE_NAME}",
    ]

    if args.debug:
        ipython_cmd.append("--CalcPy.debug=True")
        ipython_cmd.append("--TerminalInteractiveShell.xmode=verbose")

    if args.command:
        ipython_cmd.append(f"--InteractiveShellApp.code_to_run={args.command}")

    ipython_cmd.extend(args_reminder)

    if args.gui:
        jupyter_path = shutil.which('jupyter')
        if jupyter_path is None:
            raise Exception('Jupyter was not found')

        qtconsole_cmd = [
            jupyter_path,
            "qtconsole",
            "--JupyterQtConsoleApp.display_banner=False",
            "--JupyterConsoleApp.confirm_exit=False",
            "--JupyterQtConsoleApp.hide_menubar=True",
            "--JupyterWidget.input_sep=",
        ]
        ipython_cmd.insert(0, "kernel")
        try:
            ipython_proc = multiprocessing.Process(target=IPython.start_ipython, args=(ipython_cmd,))
            ipython_proc.start()

            # TODO: sanity check on ipython process
            # TODO: nicer way to wait for ipython to be ready
            import time
            time.sleep(3)
            # TODO: race, would connect to the most recent kernel, would be nicer to get json name from ipython process
            # need jupyter_client==6.1.12 to work
            qtconsole_cmd.append(f"--existing")

            subprocess.run(qtconsole_cmd)
        finally:
            ipython_proc.terminate()
    else:
        IPython.start_ipython(ipython_cmd)

if __name__ == "__main__":
    main()
