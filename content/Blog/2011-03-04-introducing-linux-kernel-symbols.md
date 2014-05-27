Author: Stephen Zhang
GitTime: off
Title: Introducing Linux Kernel Symbols
Tags: kallsyms, linux kernel, lkm, procfs
guid: http://onebitbug.me/?p=21
Slug: introducing-linux-kernel-symbols

In kernel developing, sometimes we have to examine some kernel status,
or we want to reuse some kernel facilities, we need to access (read, write, execute) kernel symbols.
In this article, we will see how the kernel maintains the symbol table, and how we can use the kernel symbols.

This article is more of a guide to reading kernel source code and kernel development.
So we will work a lot with source code.

<!--more-->

## What are kernel symbols

Let’s begin with some basic knowledge.
In programming language, a symbol is either a variable or a function.
Or more generally, we can say, a symbol is a name representing an space in the memory,
which stores data (variable, for reading and writing) or instructions (function, for executing).
To make life easier for cooperation among various kernel function unit, there are thousands of global symbols in Linux kernel.
A global variable is defined outside of any function body.
A global function is declared without `inline` and `static`.
All global symbols are listed in `/proc/kallsyms`. It looks like this:

    $ tail /proc/kallsyms
    ffffffff81da9000 b .brk.dmi_alloc
    ffffffff81db9000 B __brk_limit
    ffffffffff600000 T vgettimeofday
    ffffffffff600140 t vread_tsc
    ffffffffff600170 t vread_hpet
    ffffffffff600180 D __vsyscall_gtod_data
    ffffffffff600400 T vtime
    ffffffffff600800 T vgetcpu
    ffffffffff600880 D __vgetcpu_mode
    ffffffffff6008c0 D __jiffies

It’s in `nm`'s output format. The first column is the symbol’s address, the second column is the symbol type.
You can see the detailed instruction in [`nm`'s manpage][1].

In general, one will tell you this is the output of `nm vmlinux`.
However, some entries in this symbol table are from loadable kernel modules, how can they be listed here?
Let’s see how this table is generated.

## How is /proc/kallsyms generated

As we have seen in the last two articles, contents of procfs files are generated on reading,
so don’t try to find this file anywhere on your disk.
But we can directly go to the kernel source for the answer.
First, let’s find the code that creates this file in `kernel/kallsyms.c`.

    static const struct file_operations kallsyms_operations = {
            .open = kallsyms_open,
            .read = seq_read,
            .llseek = seq_lseek,
            .release = seq_release_private,
    };

    static int __init kallsyms_init(void)
    {
            proc_create("kallsyms", 0444, NULL, &kallsyms_operations);
            return 0;
    }
    device_initcall(kallsyms_init);

On creating the file, the kernel associates the `open()` operation with
`kallsyms_open()`, `read()->seq_read()`, `llseek()->seq_lseek()` and `release()->seq_release_private()`.
Here we see that this file is a sequence file.

The detail about sequence file is out of scope of this article.
There is a comprehensive description located in kernel documentation,
please go through [`Documentation/filesystems/seq_file.txt`][2] if you don’t know what is sequence file.
In a short way, due to the `page` limitation in `proc_read_t`,
the kernel introduced sequence file for kernel to provide large amount of information to the user.

Ok, back to the source. In `kallsyms_open()`,
it does nothing more than create and reset the iterator for `seq_read` operation, and of course set the `seq_operations`:

    static const struct seq_operations kallsyms_op = {
            .start = s_start,
            .next = s_next,
            .stop = s_stop,
            .show = s_show
    };

So, for our goals, we care about `s_start()` and `s_next()`.
They both invoke `update_iter()`, and the core of `update_iter()` is `get_ksymbol_mod()`,
and followed by `get_ksymbol_mod()`. At last, we reached `module_get_kallsym()` in `kernel/module.c`:

    int module_get_kallsym(unsigned int symnum, unsigned long *value, char *type,
                            char *name, char *module_name, int *exported)
    {
            struct module *mod;

            preempt_disable();
            list_for_each_entry_rcu(mod, &modules, list) {
                    if (symnum < mod->num_symtab) {
                            *value = mod->symtab[symnum].st_value;
                            *type = mod->symtab[symnum].st_info;
                            strlcpy(name, mod->strtab + mod->symtab[symnum].st_name,
                                    KSYM_NAME_LEN);
                            strlcpy(module_name, mod->name, MODULE_NAME_LEN);
                            *exported = is_exported(name, *value, mod);
                            preempt_enable();
                            return 0;
                    }
                    symnum -= mod->num_symtab;
            }
            preempt_enable();
            return -ERANGE;
    }

In `module_get_kallsym()`, it iterates all modules and symbols.
Five properties are assigned values.
`value` is the symbol’s address, `type` is the symbol’s type, `name` is the symbol’s name,
`module_name` is the module name if the module is not compiled in core, otherwise empty.
`exported` indicates whether the symbol is exported.
Have you ever wondered why there are some many “local” (the type char is in lower case) symbols in the symbol table?
Let’s have a lookat `s_show()`:

    if (iter->module_name[0]) {
                    char type;

                    /*
                     * Label it "global" if it is exported,
                     * "local" if not exported.
                     */
                    type = iter->exported ? toupper(iter->type) :
                                            tolower(iter->type);
                    seq_printf(m, "%0*lx %c %s\t[%s]\n",
                               (int)(2 * sizeof(void *)),
                               iter->value, type, iter->name, iter->module_name);
            } else
                    seq_printf(m, "%0*lx %c %s\n",
                               (int)(2 * sizeof(void *)),
                               iter->value, iter->type, iter->name);

Ok, clear about it? All these symbols are global in C language aspect, but only exported symbols are labeled as “global”.

After the iteration finished, we see the contents of `/proc/kallsyms`.

## How to access symbols

Here, access can be read, write and execute. Let’s have a look at this simplest module:

    #include <linux/module.h>
    #include <linux/init.h>
    #include <linux/kernel.h>
    #include <linux/jiffies.h>

    MODULE_AUTHOR("Stephen Zhang");
    MODULE_LICENSE("GPL");
    MODULE_DESCRIPTION("Use exported symbols");

    static int __init lkm_init(void)
    {
        printk(KERN_INFO "[%s] module loaded.\n", __this_module.name);
        printk("[%s] current jiffies: %lu.\n", __this_module.name, jiffies);
        return 0;
    }

    static void __exit lkm_exit(void)
    {
        printk(KERN_INFO "[%s] module unloaded.\n", __this_module.name);
    }

    module_init(lkm_init);
    module_exit(lkm_exit);


In this module, we used `printk()` and `jiffies`, which are both symbols from kernel space.
Why are these symbols available in our code? Because they are “exported”.

You can think of kernel symbols as visible at three different levels in the kernel source code:

*   “static”, and therefore visible only within their own source file
*   “external”, and therefore potentially visible to any other code built into the kernel itself, and
*   “exported”, and therefore visible and available to any loadable module.

The kernel use two macros to export symbols:

*   `EXPORT_SYMBOL` exports the symbol to any loadable module
*   `EXPORT_SYMBOL_GPL` exports the symbol only to GPL-licensed modules.

We find the two symbols exported in the kernel source code: 

    kernel/printk.c:EXPORT_SYMBOL(printk);
    kernel/time.c:EXPORT_SYMBOL(jiffies);

Except for examine the kernel code to find whether a symbol is exported,
is there anyway to identify it more easily?
The answer is sure! All exported entry have another symbol prefixed with `__ksymab_`. e.g.

    ffffffff81a4ef00 r __ksymtab_printk
    ffffffff81a4eff0 r __ksymtab_jiffies

Let’s just have another look at the definition of `EXPORT_SYMBOL`:

    /* For every exported symbol, place a struct in the __ksymtab section */
    #define __EXPORT_SYMBOL(sym, sec)                               \
            extern typeof(sym) sym;                                 \
            __CRC_SYMBOL(sym, sec)                                  \
            static const char __kstrtab_##sym[]                     \
            __attribute__((section("__ksymtab_strings"), aligned(1))) \
            = MODULE_SYMBOL_PREFIX #sym;                            \
            static const struct kernel_symbol __ksymtab_##sym       \
            __used                                                  \
            __attribute__((section("__ksymtab" sec), unused))       \
            = { (unsigned long)&sym, __kstrtab_##sym }

    #define EXPORT_SYMBOL(sym)                                      \
            __EXPORT_SYMBOL(sym, "")

The highlighted line places a `struct kernel_symbol __ksymtab_##sym` int the symbol table.

There is one more thing that worth noting, `__this_module` is not an exported symbol,
nor is it defined anywhere in the kernel source.
In the kernel, all we can find about `__this_module` are nothing more than the following two lines:

    extern struct module __this_module;
    #define THIS_MODULE (&__this_module)

How?! It’s not defined in the kernel, what to link against while `insmod` then? Don’t panic.
Have you noticed the temporary file `hello.mod.c` while compiling the module ? Here is the definition for `__this_module`:

    struct module __this_module
    __attribute__((section(".gnu.linkonce.this_module"))) = {
     .name = KBUILD_MODNAME,
     .init = init_module,
    #ifdef CONFIG_MODULE_UNLOAD
     .exit = cleanup_module,
    #endif
     .arch = MODULE_ARCH_INIT,
    };

So far, as we see, we can use any exported symbols directly in our module;
the only thing we have to do is to include the corresponding header file, or just to have the right declaration.
Then, what if we want to access the other symbols in the kernel?
Though it’s not a good idea to do such a thing, any symbol that is not exported,
usually don’t expect anyone else to visit them, avoiding potential disasters;
someday, just to fulfill one’s curiosity, or one knows exactly what he is doing,
we have to access the non-exported symbols. Let’s go further.

## How to access non-exported symbol

For each symbol in the kernel, we have an entry in `/proc/kallsyms`,
and we have addresses for all of them. Since we are in the kernel,
we can see any bit we want to see! Just read from that address.
Let’s take `resume_file` as an example. Source code comes first:

    #include <linux/module.h>
    #include <linux/kallsyms.h>
    #include <linux/string.h>

    MODULE_LICENSE("GPL");
    MODULE_DESCRIPTION("Access non-exported symbols");
    MODULE_AUTHOR("Stephen Zhang");

    static int __init lkm_init(void)
    {
        char *sym_name = "resume_file";
        unsigned long sym_addr = kallsyms_lookup_name(sym_name);
        char filename[256];

        strncpy(filename, (char *)sym_addr, 255);

        printk(KERN_INFO "[%s] %s (0x%lx): %s\n", __this_module.name, sym_name, sym_addr, filename);

        return 0;
    }

    static void __exit lkm_exit(void)
    {
    }

    module_init(lkm_init);
    module_exit(lkm_exit);

Here, instead of parsing `/proc/kallsyms` to find the a symbol’s address, we use `kallsyms_lookup_name()` to do it.
Then, we just treat the address as `char *`, which is the type of `resume_file`, and read it using `strncpy()`.

Let’s see what happens when we run:

    sudo insmod lkm_hello.ko
    dmesg | tail -n 1
    [lkm_hello] resume_file (0xffffffff81c17140): /dev/sda6
    grep resume_file /proc/kallsyms
    ffffffff81c17140 d resume_file

Yeap! We did it! And we see the symbol address returned by `kallsyms_lookup_name()` is exactly the same as in `/proc/kallsyms`. 
Just like read, you can also write to a symbol’s address,
but be careful, some addresses are in `rodata` section or `text` section, which cannot be written.
If you try to write to a readonly address, you will probably get a kernel oops.
However, this does not mean NO. You can turn off the protection.
Follow instructions [in this page][3]. The basic idea is changing the page attribute:

    int set_page_rw(long unsigned int _addr)
    {
        struct page *pg;
        pgprot_t prot;
        pg = virt_to_page(_addr);
        prot.pgprot = VM_READ | VM_WRITE;
        return change_page_attr(pg, 1, prot);
    }

    int set_page_ro(long unsigned int _addr)
    {
        struct page *pg;
        pgprot_t prot;
        pg = virt_to_page(_addr);
        prot.pgprot = VM_READ;
        return change_page_attr(pg, 1, prot);
    }

## Conclusion

Well, that’s too much for this post.
In this article, we first dig into the Linux kernel source code, to find out how the kernel symbol table is generated.
Then we learned how to use exported kernel symbols in our modules.
Finally, we saw the tricky way to access all kernel symbols within a module.

## Reference

*   [Kernel Symbols: What’s Available to Your Module, What Isn’t][4]
*   [Documentation/filesystems/seq_file.txt][2]
*   [Linux Kernel: System call hooking example][3]

[1]: http://www.linuxmanpages.com/man1/nm.1.php
[2]: http://lxr.linux.no/#linux+v2.6.37/Documentation/filesystems/seq_file.txt
[3]: http://stackoverflow.com/questions/2103315/linux-kernel-system-call-hooking-example
[4]: http://ldn.linuxfoundation.org/article/kernel-symbols-whats-available-your-module-what-isnt
