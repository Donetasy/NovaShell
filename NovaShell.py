import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import shlex
import subprocess
import os

COMMANDS = {}
ENV = {}

def command(name):
    def deco(fn):
        COMMANDS[name] = fn
        return fn
    return deco

def write(text):
    term.insert(tk.END, text + "\n")
    term.see(tk.END)

@command("help")
def cmd_help(args):
    write("available commands:")
    for c in sorted(COMMANDS):
        write(f"  {c}")
    write("all other commands are passed to Windows CMD")

@command("echo")
def cmd_echo(args):
    write(" ".join(args))

@command("set")
def cmd_set(args):
    if len(args) < 2:
        write("usage: set <name> <value>")
        return
    ENV[args[0]] = " ".join(args[1:])

@command("vars")
def cmd_vars(args):
    for k, v in ENV.items():
        write(f"{k} = {v}")

@command("winhelp")
def cmd_winhelp(args):
    try:
        cmd = "help " + args[0] if args else "help"

        result = subprocess.run(
            ["cmd", "/c", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )

        output = result.stdout.decode("cp1252", errors="ignore")
        if output.strip():
            write(output.rstrip())
        else:
            write("no output")

    except Exception as e:
        write(f"error: {e}")

@command("exit")
def cmd_exit(args):
    root.destroy()

PROMPT = "nova> "
input_start = None

def show_prompt():
    global input_start
    term.insert(tk.END, PROMPT)
    input_start = term.index(tk.INSERT)

def handle_command(line):
    if not line.strip():
        return

    try:
        tokens = shlex.split(line)
    except ValueError as e:
        write(str(e))
        return

    cmd, *args = tokens

    # Built-in NovaShell command
    if cmd in COMMANDS:
        COMMANDS[cmd](args)
        return

    # Handle persistent `cd`
    if cmd == "cd":
        try:
            target = args[0] if args else os.path.expanduser("~")
            os.chdir(target)
        except Exception as e:
            write(str(e))
        return

    # Pass through to Windows CMD
    try:
        result = subprocess.run(
            line,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env={**os.environ, **ENV}
        )

        if result.stdout:
            write(result.stdout.rstrip())
        if result.stderr:
            write(result.stderr.rstrip())

    except Exception as e:
        write(f"execution error: {e}")

def on_return(event):
    global input_start
    line = term.get(input_start, tk.END).strip()
    term.insert(tk.END, "\n")
    handle_command(line)
    show_prompt()
    return "break"

def on_backspace(event):
    if term.compare(tk.INSERT, "<=", input_start):
        return "break"

root = tk.Tk()
root.title("NovaShell")
root.geometry("700x450")

term = ScrolledText(
    root,
    bg="#0f0f0f",
    fg="#00ff99",
    insertbackground="white",
    font=("Consolas", 11),
)
term.pack(fill=tk.BOTH, expand=True)

term.bind("<Return>", on_return)
term.bind("<BackSpace>", on_backspace)

term.focus()

write("Welcome to my Custom shell")
show_prompt()

root.mainloop()
