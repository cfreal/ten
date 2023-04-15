# Shell commands

- [Shell commands](#shell-commands)
    - [Running a shell command](#running-a-shell-command)
    - [Running a program to completion](#running-a-program-to-completion)
    - [Running a program in the background](#running-a-program-in-the-background)
    - [Running a program to completion and get its output](#running-a-program-to-completion-and-get-its-output)
    - [Misc](#misc)

## Running a shell command

There are two ways to specify the command you want to run: either with a string
or a list of arguments. The two following lines are equivalent:

```python
shell.call('cat /etc/passwd')
shell.call(('cat', '/etc/passwd'))
```

If you want to use bash-specific constructs such as file redirections or other,
you should use the string argument:

```python
shell.call('cat /etc/passwd > /tmp/other') # works
shell.call(('cat', '/etc/passwd', '>', '/tmp/other')) # does not
```

## Running a program to completion

Use `shell.call()`, as described in the previous section.

Use `shell.stdout` or `shell.stderr` files to get the output:

```python
p = shell.call("cat /etc/passwd")
contents = p.stdout.read()
```

## Running a program in the background

If you want to start a command and keep interacting with it, or simply let it
run in the background, use `shell.run_background()`:

```python
# Start a program
p = shell.background('/bin/slow-program arg0 arg1')

# Do some other stuff ...
...

# Wait for the program to end
p.wait()
```

## Running a program to completion and get its output

Run a program and gets its output as a string:

```python
stdout, stderr = shell.get_output('cat /etc/passwd')
```

or as bytes:

```python
stdout, stderr = shell.get_output('cat /etc/passwd', text=False)
```

## Misc

Both `call()` and `background()` return a [`Popen` instance](https://docs.python.org/3/library/subprocess.html#subprocess.Popen).
