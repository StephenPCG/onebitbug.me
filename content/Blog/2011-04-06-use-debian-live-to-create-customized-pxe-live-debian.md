Author: Stephen Zhang
GitTime: off
Title: Use debian-live to Create Customized PXE Live Debian
Tags: debian, linux, pxe
guid: http://onebitbug.me/?p=57
Slug: use-debian-live-to-create-customized-pxe-live-debian

There already have been a lot of Live Linux there. However they are mostly just for general purpose and may not be suitable for you. The debian group introduced a [Debian Live Project ][1]which makes it easier  for you to customize a Live Linux. [Here][2] is the full manual. It is too long if your purpose is as simple as to make a customized PXE Live Debian. In this post, I will give a simplified instruction.

<!--more-->

## Create Live Debian

We use live-build tools to build Live Debian, first install it:

    sudo apt-get install live-debian

Then, we will get many `lb *` commands, you can observe them with `man lb_*`. However, only three commands we use directly, `lb config/build/clean`, all others are low level implementations.

Let’s first create a folder for our live system, and copy a sample auto-scripts:

    mkdir live && cd live
    mkdir auto
    cp /usr/share/live/build/examples/auto/* auto/

There are three files in `auto/`, `config`, `build`, `clean`. `auto/config` is executed when you run `lb config`, `auto/build` is executed by `lb build` and `auto/clean` is executed by `lb clean`.

Let’s make a little modifications to `auto/config`:

    cat auto/config
    #!/bin/sh

    lb config noauto \
        --architectures i386 \
        --binary-images net \
        --bootloader syslinux \
        --compression bzip2 \
        --distribution squeeze \
        --hostname debian-live \
        --language zh \
        --linux-flavours 686 \
        --parent-mirror-bootstrap http://debian.ustc.edu.cn/debian/ \
        --parent-mirror-chroot-security http://debian.ustc.edu.cn/debian-security/ \
        --parent-mirror-binary http://debian.ustc.edu.cn/debian/ \
        --parent-mirror-binary-security http://debian.ustc.edu.cn/debian-security/ \
        --mirror-bootstrap http://debian.ustc.edu.cn/debian/ \
        --mirror-chroot-security http://debian.ustc.edu.cn/debian-security/ \
        --mirror-binary http://debian.ustc.edu.cn/debian/ \
        --mirror-binary-security http://debian.ustc.edu.cn/debian-security/ \
        --packages "ibus-pinyin" \
        --archive-areas "main non-free contrib" \
            "${@}"

Most of the parameters are literally self explained. For detailed instructions, see `man lb_config`

Then we run `config` and `build` process.

    lb config
    sudo lb build

`lb config` may take a long time (20min or more, depends on you network bandwidth and your package settings). It will first run `debootstrap` to install a standard system in `chroot/` directory. Then it will do install packages in `chroot` environment. It will procedure further customization.

After a long time waiting, we get `binary/live/`. files in this directory are all we need to boot from PXE.

## Customize Live Debian

Till now, we’ve get a PXE bootable live system. If you’re can’t wait to have a try on it, you can goto the next section. But you’re sure to come back.

The system does not have a normal user, meanwhile, you don’t know password for root user. So you cannot login into that system. So the first thing is to create a user and set the password. First we have to change root to the live system, and all stuffs in this section should be done in the `chroot` environment.

    sudo chroot chroot/ /bin/bash
    useradd yourusername
    passwd yourusername
    adduser yourusername sudo  # so you can use sudo
    passwd root  # in case you wanna use root user
    exit  # exit chroot environment

You can install packages, write scripts and all other customizations in the `chroot` environment.

    sudo chroot chroot/ /bin/bash
    aptitude update
    aptitude install xxx  # install more packages
    # do other customizations.
    exit

## Boot Live Debian via PXE

I an not going deep into how to setup PXE boot environment in this post. I just give you the menu entry to boot this system.

First, you should export `filesystem.squashfs` via NFS.

    cp -r binary/live /nfsroot/debian/
    echo '/nfsroot/debian/ *(ro,async,no_root_squash_no_subtree_check)' >> /etc/exports
    exportfs -a

Then the syslinux menu entry:

    LABEL live-debian
    MENU LABEL My Live Debian
    KERNEL vmlinuz-xxx
    INITRD initrd.img-xxx
    APPEND boot=live netboot=nfs nfsroot=your-ip:/nfsroot/debian/

Done!

[1]: http://live.debian.net/
[2]: http://live.debian.net/manual/en/html/live-manual.html
