Author: Stephen Zhang
GitTime: off
Title: USTC Cloud Live Debian
Tags: cloud, debian, pxe, ustc
guid: http://onebitbug.me/?p=63
Slug: ustc-cloud-live-debian

Leverage USTC PXE Service, we are developing a Customized Cloud Live System for USTCers. In the past, we can boot Live Linux systems from PXE in USTC campus, however, all modifications after boot are remained in the RAM, so they won’t persist after system reboot. Thanks to the 300M free ftp space provided by USTC Network Center to every student and teacher, our customized system now will mount it on home directory, so modifications in $HOME will persist.

<!--more-->

After the system boot up, you will be asked to enter your membership, username and password (the same with email.ustc.edu.cn account):

{% img /images/posts/2011-04-06/setup.png %}

After you entered the correct username/password, the system is ready for login. You can login with the same username as email account, without password. You will have sudo privilege.

{% img /images/posts/2011-04-06/mount.png %}

Currently, it’s just a debian basic system, without any desktop environment installed. We will further customized it for USTC environment. E.g. setting up thunderbird to use email.ustc.edu.cn by default, install software popular among USTCers. 

We will also try to make `apt-get` installed software to be saved in home dir, so they will also persist. 

Enjoy it! Period.

