Author: Stephen Zhang
Title: 'Using LKM and procfs -- Part I'
Category: Linux
Tags: LKM, proc, procfs, Linux Kernel
guid: http://onebitbug.me/?p=15
Slug: using-lkm-and-procfs-part-i

The proc filesystem was originally designed for providing information on the processes in a system.
But given the usefulness of procfs, many elements use it both to report information and enable dynamic module configuration.
It can also be used as an communication mechanism between kernel space and user space.
LKM is for Loadable kernel module.
In this post, we will practice to write our own module, and use procfs to communicate with user environment.

<!--more-->

## An example of LKM

This book is very detailed on LKM programming, [The Linux Kernel Module Programming Guide][1].
For a quick start, I just provide a very simple hello world module to demonstrate usage of lkm.

{% codeblock simple_lkm.c lang:c %}
#include

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Simple LKM sample");
MODULE_AUTHOR("Stephen Zhang");

int init_simple_lkm(void)
{
    printk(KERN_INFO "SLKM: module loaded. speaking from kernel.\n");
    return 0;
}

void cleanup_simple_lkm(void)
{
    printk(KERN_INFO "SLKM: module unloaded.\n");
}

module_init(init_simple_lkm);
module_exit(cleanup_simple_lkm);
{% endcodeblock %}

In this simple code, line 19-20 defines the entrance and exit function of the module,
they will be invoked while the module is loaded/unloaded.
The declaration is in `linux/init.h`:

```
typedef int (*initcall_t)(void);
typedef void (*exitcall_t)(void);
```

Sometimes you will see two macros `__init` and `__exit`, `__init`.
The `__init` macro causes the init function to be discarded and its memory freed once the init function finishes.
And the same, the `__exit` macro causes the omission of the function.

As `stdin` is an `fd` associated with a specific process, kernel module don’t have `stdin` or `stdout`,
thus you cannot use printf to put messages on a terminal.
Instead, you should use printk, and the messages will go to `/var/log/messages`.
You can use `dmesg` or `cat /var/log/messages` to examine them.
`KERN_INFO` is the level of the message, defined in `linux/printk.h`:

```
#define KERN_EMERG      "<0>"   /* system is unusable                   */
#define KERN_ALERT      "<1>"   /* action must be taken immediately     */
#define KERN_CRIT       "<2>"   /* critical conditions                  */
#define KERN_ERR        "<3>"   /* error conditions                     */
#define KERN_WARNING    "<4>"   /* warning conditions                   */
#define KERN_NOTICE     "<5>"   /* normal but significant condition     */
#define KERN_INFO       "<6>"   /* informational                        */
#define KERN_DEBUG      "<7>"   /* debug-level messages                 */
```

In kernel 2.6+, build a kernel module is quite simple, just use the following Makefile:

```
obj-m += simple_lkm.o
all:
	make -C /lib/modules/${shell uname -r}/build/ M=${PWD} modules
```

And now just type `make` in your current directory, everything will be done for you.
You will get a `simple_lkm.ko`, load it with `insmod`:

```
$ insmod simple_lkm.ko
```

Now we can see the module is loaded with `lsmod` and `dmesg`:

```
$ lsmod | grep simple_lkm
simple_lkm               938  0
```

```
$ dmesg | tail -n 1
[349718.844315] SLKM: module loaded. speaking from kernel.
```

We can use `rmmod` to unload the module:

```
$ rmmod simple_lkm
$ dmesg | tail -n 1
[349913.592481] SLKM: module unloaded.
```

So far, the first lkm is finished. In the [next post][2],
I will demonstrate how to use procfs with an simple procfs calculator.

## Reference

In this post, I referred the following materials.
But be ware that, some of them may be outdated, keep an eye on the version of linux they are using.

*   [The Linux Kernel Module Programming Guide][1]


[1]: http://www.tldp.org/LDP/lkmpg/2.6/html/index.html
[2]: http://onebitbug.me/?p=60 "LKM和procfs练习（二）"
