#!/usr/bin/env python3

# this code is from https://gitlab.com/hydrargyrum/asciinario by hydrargyrum

from argparse import ArgumentParser
from pathlib import Path
import re
import subprocess
import sys
import time
from uuid import uuid4

class Play:
    def __init__(self, screen_id):
        self.screen_id = screen_id
        self.status_pos = "top"
        self.type_wait = .2
        self.enter_wait = .5
        self.pre_enter_wait = .1

    def do(self, line):
        for regex, method in self.statements.items():
            match = regex.fullmatch(line)
            if match:
                return method(self, match)
        else:
            raise Exception(f"no pattern matched {line!r}")

    def do_status_change(self, match):
        if match[1] == "hide":
            self.send_screen("hardstatus", "ignore")
        elif match[1] == "show top":
            self.status_pos = "top"
            self.send_screen("hardstatus", "alwaysfirstline")
        elif match[1] == "show bottom":
            self.status_pos = "bottom"
            self.send_screen("hardstatus", "alwayslastline")
        elif match[1] == "clear":
            self.send_screen("hardstatus", "string", "")
        elif match[1] == "show":
            self.do_status_change([None, f"show {self.status_pos}"])

    def do_status_type(self, match):
        flags = match[1]
        message = match[2] or ""
        for n in range(len(message)):
            self.send_screen("hardstatus", "string", escape_hstatus(message[:n + 1]))
            if ">" not in flags:
                time.sleep(self.type_wait)

    def do_type(self, match):
        need_escape = "^"
        flags = set(match[1])
        message = match[2]
        for c in message:
            if c in need_escape:
                c = "\\" + c
            self.send_screen("stuff", c)
            if ">" not in flags:
                time.sleep(self.type_wait)

        if "$" in flags:
            if ">" not in flags:
                time.sleep(self.pre_enter_wait)
            self.send_screen("stuff", "\n")
            if ">" not in flags:
                time.sleep(self.enter_wait)

    def do_type_enter(self, match):
        self.send_screen("stuff", "\\n")
        time.sleep(self.enter_wait)

    def do_send_key(self, match):
        if match[1] == "tab":
            self.send_screen("stuff", r"\t")
        elif match[1] == "enter":
            self.send_screen("stuff", r"\n")
        elif match[1].startswith("^") or match[1].startswith("\\"):
            self.send_screen("stuff", match[1])
        else:
            raise Exception("unhandled key %r" % match[1])

    def do_wait(self, match):
        time.sleep(float(match[1]))

    def do_dialog(self, match):
        self.send_screen("exec", "dialog", "--keep-tite", "--msgbox", match[1], "0", "0")

    def do_set(self, match):
        if match[1] in {"type_wait", "enter_wait", "pre_enter_wait"}:
            setattr(self, match[1], float(match[2]))
        else:
            raise KeyError("unhandled config %r" % match[1])

    def send_screen(self, *args):
        subprocess.check_output(["screen", "-S", self.screen_id, "-X", *args])

    statements = {
        re.compile(r"(\$?>?)> (.*)"): do_type,
        re.compile("->(>?)(?: (.*))?"): do_status_type,
        re.compile(r"key (\^.*|\\[nrt]|\\\d{3}.*|enter|tab)"): do_send_key,
        re.compile("enter"): do_type_enter,
        re.compile("status (show(?: top| bottom)?|hide|clear)"): do_status_change,
        re.compile(r"w(?:ait)? (\d+(?:\.\d*)?|\d*\.\d+)"): do_wait,
        re.compile(r"set (\w+) = (.*)"): do_set,
        re.compile(r"dialog (.*)"): do_dialog,
    }

def escape_hstatus(text):
    return text.replace("%", "%%")

def play_inscript(text, screen_id):
    player = Play(screen_id)
    lines = text.strip().split("\n")
    for line in lines:
        if not line or line.lstrip().startswith("#"):
            continue
        player.do(line)

parser = ArgumentParser()
parser.add_argument("scenario")
parser.add_argument("output")
args, args_reminder = parser.parse_known_args()
instructions = Path(args.scenario).read_text()

screen_id = str(uuid4())
cmd = f"screen -S {screen_id}"
recorder_proc = subprocess.Popen(["asciinema", "rec", "--overwrite", "--cols", "80", "--rows", "20", "-c", cmd, args.output])

# give some time for screen to start
for _ in range(10):
    time.sleep(.5)
    # echo -n "" is a noop
    checking = subprocess.run(["screen", "-S", screen_id, "-X", "echo", "-n", ""], encoding="utf8", capture_output=True)
    if checking.returncode == 0:
        break
    assert checking.stdout == "No screen session found.\n"
    if recorder_proc.poll() is not None:
        sys.exit("asciinema exited prematurely")
else:
    sys.exit(f"screen session {screen_id} could not be found")

play_inscript(instructions, screen_id)
subprocess.check_output(["screen", "-S", screen_id, "-X", "quit"])
recorder_proc.wait()
