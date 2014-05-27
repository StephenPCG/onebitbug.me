Author: Stephen Zhang
GitTime: off
Title: USTC Ethernet Boot Service Update (2011-04-01)
Tags: gpxe, ipxe, pxe, syslinux, ustc
guid: http://onebitbug.me/?p=46
Slug: ustc-ethernet-boot-service-update-2011-04-01

## Introduction to iPXE

USTC Ethernet Boot Service was first started by Fengguang Wu early in 2000.
It enables people within USTC campus to boot their computer through network,
to install Linux, experience Linux, and perform system maintainance tasks such as partitioning and backup.

In 2010, we upgrade the service with gPXE, which is an enhanced version to PXE.
It is capable with protocols like HTTP, FTP, etc, which gains great performance improvement against TFTP.

<!--more-->

Today, we upgrade gPXE to [iPXE][1]. iPXE is the official replacement of gPXE.
It is developed by people who originally developed gPXE (which envolved from Etherboot).
Unfortunately, the gpxe.org and etherboot.org domains are owned by an individual who wishes to exercise a high degree of control over the project and the codebase, so in April 2010 the decision was taken to create a new project named iPXE, using theexisting code base as a starting point. Since the two project diverged, development on gPXE has stopped, while iPXE is very actively updated.

{% img /images/posts/2011-04-01/ipxe.png %}

## Update Contents

The first notable update is the chain load sequence. In previous configuration, our chain is like:

    [PXE (BIOS)]/Grub --> gPXE --> menu.c32 (Syslinux <= 3.86) --> gPXE

As gPXE/iPXE does not support natively load com32r modules from Syslinux newer than 3.86, and is not that compatible with that older than Syslinux 3.86, it caused many incompatible problems. Many PC’s will reboot immediately after hit one menu item. Now then chain load sequence has changed to:

    [PXE (BIOS)]/Grub --> iPXE --> Syslinux 4.0.3 --> menu.c32

Now, it works perfectly!

There are some minor updates with the service.
Added [Offline NT Password & Registry Editor][3].
Added [Hardware Detection Tool][4] from Syslinux.

## Usage

For users within USTC campus, there are generally two ways to use the newly updated iPXE.

*   Chain load from PXE. If your PC supports PXE, you can boot from LAN and get loaded into PXE,
    and then type “iPXE<ret>”, then you will be brought to iPXE.
*   Chain load from Grub. If your PC does not support PXE, or you are in a LAN without DHCP server setup properly,
    you can download [ustc.ipxe.lkrn][5], and boot it with grub. 
    *   Grub 1: `kernel ustc.ipxe.lkrn`
    *   Grub 2: `linux16 ustc.ipxe.lkrn`

## Troublesome

*   If you don’t know how to use it, please post your problem in [Linux board of USTCBBS][6].
*   If you encountered some bugs, please contact lug AT ustc.edu.cn.

## Source Code

The source code are located in <http://git.onebitbug.me/?p=ustc-pxe.git;a=summary>. You can get the code:

    git clone http://git.onebitbug.me/ustc-pxe.git

Then setup your web server, add a virtual path to `ustc-pxe/src`. Then get the binary files:

    cd src
    ./updatebin.sh

you then can boot you other PC with grub loading `bin/ipxe.lkrn`, after iPXE starts, press `CTRL-B` to enter command line. Then type the following commands:

    dhcp
    chain http://your-site/path-to-src/boot.php

If you want native PXE boot environment, you have to set up tftp and dhcp. See instructions here: <http://ipxe.org/howto/chainloading>

Enjoy it!

{% img /images/posts/2011-04-01/ipxe1.png %}

 [1]: http://ipxe.org/
 [3]: http://home.eunet.no/pnordahl/ntpasswd/
 [4]: http://hdt-project.org/
 [5]: http://pxe.ustc.edu.cn/bin/ustc.ipxe.lkrn
 [6]: http://bbs.ustc.edu.cn/cgi/bbsdoc?board=Linux
 []: http://onebitbug.me/wp-content/uploads/2011/04/pxe.png
 [8]: http://onebitbug.me/wp-content/uploads/2011/04/ipxe1.png
