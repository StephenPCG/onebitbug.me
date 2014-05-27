Author: Stephen Zhang
GitTime: off
Title: Using LKM and procfs -- Part II
Tags: lkm, procfs, linux kernel
guid: http://onebitbug.me/?p=17
Slug: using-lkm-and-procfs-part-ii

In the [last post][1], we saw that it is very simple to implement an loadable kernel module in Linux.
In this post, we will see how to use procfs.

<!--more-->

## Introduction to procfs

I believe that most Linux users know `/proc`,
we can obtain much information on processes from it,
we can lookup the basic usage from the [proc manpage][2].
There are also a lot of materials.
Then, have you think of using procfs to help us providing other information?
OK, we will see how to do it soon. Believe that, it can’t be more complicated than writing lkm.

### Create/Remove proc entry

Let’s first have a look at how to create an remove proc entry.
We use `create_proc_entry()` to create a proc entry.
The three args are filename, access mode, and parent directory.
If the parent directory is `/proc`, we can pass `NULL`.
The return value is a pointer of `struct proc_dir_entry` (NULL on failure).
With this pointer, we can manipulate the other properties of the file,
like the what to do when a user read the file.
Here is the prototype of `create_proc_entry()` and `struct proc_dir_entry`:

    struct proc_dir_entry *create_proc_entry(const char *name, mode_t mode,
    						struct proc_dir_entry *parent);
    struct proc_dir_entry {
    	unsigned int low_ino;
    	unsigned short namelen;
    	const char *name;
    	mode_t mode;
    	nlink_t nlink;
    	uid_t uid;
    	gid_t gid;
    	loff_t size;
    	const struct inode_operations *proc_iops;
    	const struct file_operations *proc_fops;
    	struct proc_dir_entry *next, *parent, *subdir;
    	void *data;
    	read_proc_t *read_proc;
    	write_proc_t *write_proc;
    	atomic_t count;		/* use count */
    	int pde_users;	/* number of callers into module in progress */
    	spinlock_t pde_unload_lock; /* proc_fops checks and pde_users bumps */
    	struct completion *pde_unload_completion;
    	struct list_head pde_openers;	/* who did ->open, but not ->release */
    };

Soon we will see how to use `proc_read()` and `proc_write()` to set the handler for reading and writing this file.

We use `proc_remove_entry()` to delete a proc entry.
The two args are the filename and the parent dir’s pointer.
If the parent dir is `/proc`, you can use NULL. Here is the declaration:

    void remove_proc_entry(const char *name, struct proc_dir_entry *parent);

### Write callback function

When a user writes to a proc file, the relevent `proc_write()` will be called.
This is the declaration:

    typedef	int (write_proc_t)(struct file *file, const char __user *buffer,
    			   unsigned long count, void *data);

Among the arguments, `buffer` is the data user written, and `len` is the size of data.
This buffer is a user space address so you can not access it directlly inside the kernel.
You should use `copy_from_user()` to copy it into the kernel space address.
`data is a pointer to your private data.`

### Read callback function

When a user tries to read from the proc entry, the relevent `read_proc()` will be invoked,
and inside this function, the kernel prepares the data user will get.
Here is the declaration:

    typedef	int (read_proc_t)(char *page, char **start, off_t off,
    			   int count, int *eof, void *data);

In the following example, we will see how to use these functions.

### Other useful functions

Linux kernel also provides some other useful functions to use procfs.

    struct proc_dir_entry *proc_symlink(const char *,
    		struct proc_dir_entry *, const char *);
    struct proc_dir_entry *proc_mkdir(const char *,struct proc_dir_entry *);
    struct proc_dir_entry *proc_mkdir_mode(const char *name, mode_t mode,
    			struct proc_dir_entry *parent);
    static inline long copy_from_user(void *to,
    		const void __user * from, unsigned long n)；
    static inline long copy_to_user(void __user *to,
    		const void *from, unsigned long n);
    void *vmalloc(unsigned long size);
    void vfree(const void *addr);

## A simple calculator via procfs

We will use procfs to implement a simple accumulator.
After the module is loaded, it will create a file `/proc/simacc`,
then we can use `echo` to put some integers into this file,
the next time we read the file, we will get the sum of these integers.

Here is the full code:

    #include
    #include
    #include
    #include
    #include

    MODULE_LICENSE("GPL");
    MODULE_AUTHOR("Stephen Zhang");
    MODULE_DESCRIPTION("Simple accumulator via procfs");

    #define MAX_INPUT_SIZE 1024
    char input_buf[MAX_INPUT_SIZE];
    char result[16];
    static struct proc_dir_entry *simacc_file;

    static int simacc_read(char *page, char **start, off_t off,
        int count, int *eof, void *data)
    {
        int len;
        len = sprintf(page, "%s\n", result);
        return len;
    }

    static int simacc_write(struct file *file, const char *buffer,
        unsigned long count, void *data)
    {
        int len;
        unsigned long num = 0, sum = 0;
        int i;
        char c;
        if (count > MAX_INPUT_SIZE)
        len = MAX_INPUT_SIZE;
        else
        len = count;

        if(copy_from_user(input_buf, buffer, len))
        return -EFAULT;
        input_buf[len] = '&#92;&#48;';

        i = 0;
        do {
        c = input_buf[i++];
        if (c >= '0' && c <= '9') {
            num = num * 10 + c - '0';
        } else {
            sum += num;
            num = 0;
        }
        } while (c != '&#92;&#48;' && i < MAX_INPUT_SIZE);
        sprintf(result, "%lu", sum);
        return len;
    } 

    static int __init init_simacc(void) {
        simacc_file = create_proc_entry("simacc", 0666, NULL);
        if (simacc_file == NULL) {
        return -ENOMEM;
        }
        input_buf[MAX_INPUT_SIZE - 1] = '&#92;&#48;';
        result[0] = '0'; result[1] = '&#92;&#48;';
        simacc_file->data = input_buf;
        simacc_file->read_proc = simacc_read;
        simacc_file->write_proc = simacc_write;
        printk(KERN_INFO "simacc: Module loaded.\n");

        return 0;
    }

    static void __exit cleanup_simacc(void)
    {
        remove_proc_entry("simacc", NULL);
        printk(KERN_INFO "simacc: Module unloaded.\n");
    }

    module_init(init_simacc);
    module_exit(cleanup_simacc);

In the initialization function `init_simacc()`, we use `create_proc_entry()` to create `/proc/simacc`,
and then set the read/write handler for this file.
The file is created with access mode 0666, so any one can read and write to it.
(The file’s owner is root, and main group is also root.)
In the exit function `cleanup_simacc()`, we deleted this function.

In the write callback function `simacc_write()`,
we first use `copy_from_user()` to copy the user written data to a buffer in kernel.
As we only allocated `MAX_INPUT_SIZE` for `input_buf`, we have to first check the size of input data,
we can at most copy `MAX_INPUT_SIZE` bytes of data to `input_buf`,
or we will suffer buffer overflow, which may at worst crash the whole system.
And then comes the code for calculating.
As this is not the keypoint of this article, I make it in a very naive way,
all characters beyond `[0-9]` is recognized as delimiters.
After calculating, the resule is written to another buffer `result`.

The read callback function `simacc_read()` is very simple,
as `page` is a kernel space address, we can directory write data into it,
we can use either `strcpy` or `sprintf` to make it.

Now let’s examine the result:

    sudo insmod simacc.ko
    ls -l /proc/simacc
    -rw-rw-rw- 1 root root 0 Feb  3 10:28 /proc/simacc
    cat /proc/simacc
    0
    echo 1 2 3 > /proc/simacc
    cat /proc/simacc
    6
    echo 12d34 > /proc/simacc
    cat /proc/simacc
    46
    sudo rmmod simacc

## Conclusion

In these two post, we have seen how to write our own loadable kernel module, and written an very simple snip.
Although the example is very simple, it demonstrate the basic elements of the kernel.
We know how kernel generate data when we read or write to a proc entry.
In later posts, I will write more about how to use procfs to help debug Linux kernel.

## Reference

I referred to these materials, but be aware that some of these articles maybe outdated.
Keep an eye on what version of kernel they were using. I am using Linux 2.6.37 when writing this post.

* procfs example in linux kernel source: [Documentation/DocBook/procfs_example][3]
* [Access the Linux Kernel using the /proc filesystem][4], 
    In this article, another example is given, but they were using linux 2.6.11, and some datastructures are obsoleted, the following two articles explains:
* [Where has the 'owner' field of struct 'proc\_dir\_entry' gone?][5], owner field is no longer used.
* [Linux Kernel Module - Creating proc file - proc_root undeclared error][6], `proc_root` macro is obsoleted, just use NULL instead.

[1]: {% post_url 2011-02-02-using-lkm-and-procfs-part-i %}
[2]: http://linuxmanpages.com/man5/proc.5.php
[3]: http://lxr.linux.no/linux+v2.6.32/Documentation/DocBook/procfs_example.c
[4]: http://www.ibm.com/developerworks/linux/library/l-proc.html
[5]: http://stackoverflow.com/questions/1728499/where-has-the-the-owner-field-of-struct-proc-dir-entry-gone-linux-kernel
[6]: http://stackoverflow.com/questions/2531730/linux-kernel-module-creating-proc-file-proc-root-undeclared-error
