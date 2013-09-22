Title: Duplicate PIPE in python
Slug: python-duplicate-pipe
Date: 2012-11-03
Author: Stephen Zhang
Tags: python
Category: Python

It’s sometimes convenient to pipe output of one program simultaneously to several other programs. For example, grep two different keywords from a long time running program’s output, e.g. output of varnishncsa.

In Bash script, it’s quite simple. Create two (or more) fifo files, use tee to duplicate procuder program’s stdout to fifo files:

```
mkfifo fifo1 fifo2
producer | tee fifo1 fifo2 >/dev/null &
customer1 < fifo1 &
customer2 < fifo2 &
wait
```

But there are two cons:

* it requires a filesystem that supports fifo file, NTFS only environment will not work.
* it requires to run each program in backend, and wait explicitly.

However, with bash, we can do it more elegantly:
```
producer | tee >(fifo1) >(fifo2) >/dev/null
```

This time, I have the same problem to solve in python. A couple of googleing didn’t find me any library which provide a method to duplicate PIPE. So I write one myself.

```
from threading import Thread
from subprocess import Popen, PIPE

class PipeDuplicater(object):
    def __init__(self, inp, bufsize=1024):
        self.inp = inp
        self.outps = []
        self.bufsize = 1024

    def copy_to(self, outp):
        self.outps.append(outp)

    def start(self):
        try:
            while True:
                block = self.inp.read(self.bufsize)
                map(lambda outp: outp.write(block), self.outps)
                if len(block) < self.bufsize:
                    return
        except Exception as e:
            print e

## TEST Code
nilout = open("/dev/null", "w+")
prog1 = Popen(["cat", "/proc/self/cmdline"], stdout=PIPE)
prog2 = Popen(["tee", "/tmp/out1.txt"], stdin=PIPE, stdout=nilout)
prog3 = Popen(["tee", "/tmp/out2.txt"], stdin=PIPE, stdout=nilout)
prog4 = Popen(["tee", "/tmp/out3.txt"], stdin=PIPE, stdout=nilout)

dupper = PipeDuplicater(prog1.stdout)
dupper.copy_to(prog2.stdin)
dupper.copy_to(prog3.stdin)
dupper.copy_to(prog4.stdin)

Thread(target=dupper.start).start()
```

The code is quite simple, I’m not going to explain it in details.
