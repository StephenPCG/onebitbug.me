Title: Biography
Author: Zhang Cheng
Slug: biography
Date: 2012-04-01
Sidebar: off

{% img right /images/pages/snsface.png 180 %}
## Contact
* __Email__: base64 --decode <<< c3RlcGhlbnBjZ0BnbWFpbC5jb20K
* __Tel__: (+86) 158-5697-7094
* __Addr__: Dongcheng District, Beijing

## Education
* 2010 - 2013 **Master of Engineer of CS**, _Embedded System_, _University of Science and Technology of China_, Hefei, China (Quited)
* 2006 - 2010 **Bachelor of CS**, _Universy of Science and Technology of China_, Hefei, China

## Work Experience
* 2012.03 - 2014.05, **System Administrator**, _Cloudacc Interactive, Inc._, Beijing
    * Setup a private deb package repository with reprepro, built deb packages to manage system settings and deploy applications.
    * Bootstrap saltstack to make managing system easier while number of servers bursting. Skilled in saltstack, and have good knowledge of other configuration management systems.
    * Built a CDN system to distribute video files using varnish and nginx, supporting more than 50 Gbps bandwidth at peak time.
    * Setup a web content cache cluster using varnish with complex caching rules, serving up to 500k rps load. Experienced in using and tuning varnish.
    * Developed an HTTP gateway for sending email (postfix as backend) and SMS (smstools as backend), so other applications may send alerts easier.
    * Developed a service checking daemon to make application monitoring easier, as a supplement of nagios.
    * Built and maintained an LXC virtual machine cluster in office, developers can apply for containers in web browser by self. have good knowledge of virtual technologies and tools.
    * Setup and maintained the openldap server for the company, integrated applications with it.
    * Setup and maintained the office gateway - a Debian box with customized iptables and iproute2 rules. Experienced with iptables and iproute2, have good knowledge of networking stack.
    * Developed many other tools and applications with python during two years, proficient in python programming.
* 2011.09 - 2012.02, **System Engineer**, _Linux Deepin Dev Team_, Wuhan
    * Created [scripts to build Deepin cdimage][11] and setup daily-build task.
    * Manage [Deepin package repository][12] with reprepro.
    * Maintained most of Deepin addon packages, skilled with pbuilder and the packaging toolchain.
    * Setup a PXE environment to make testing daily-build cdimage easier.
* Apr-Sep 2010, **Intern**, _Microsoft Research Asia_, Beijing
    * Worked on multimedia applications for mobile devices in Multimedia Computing group, mentored by [Tao Mei][1].

## Project and Activities
* _[nginx-lua-simpleauth-module][13]_. This nginx lua module provides a cookie cache for authn results and a group based authz configuration.
* _[Personal Package Archive][14]_. A ppa with many packages not shipped with debian official repository. It is not advertised since some of the packages are not tested.
* _[extend-left-box][15]_. A gnome-shell extension to extend left box of top panel. The project discontinued as I no longer use gnome-shell.
* _Early developer of [USTC Campus Ethernet Boot Service][5]_. A PXE boot service in USTC campus, people can boot their computer via LAN to install Linux, experience distros without installation, repair system, etc. Also [made an live debian system]({filename}../2011/2011-04-06-ustc-cloud-live-debian.md) which mount an ftp space as home directory so people can boot 'their own' system everywhere.
* _[Maintainer of USTC Open Source Mirror][4]_. It has the highest traffic among open source mirror sites in China, and is official mirror of many distros and projects, e.g. Debian, Ubuntu, etc. Did a lot of work tuning kernel, filesystem and applications for high traffic load.
* _RoboGame_. It is an traditional robot contest in USTC campus. Built a complete robot from scrach with sensors, motors and AVR mega16 chips as controller, in collaboration with 3 other classmates. i was mainly responsible for controlling algorithm design and implementation.

## Social Activities (During school days)
* Vice president [Linux User Group @USTC][3]
* Maintainer of [Open Source Software Mirrors][4] of USTC
* Maintainer and developer of [PXE Service][5] of USTC
* Administrator of [Freeshell Service][6] of USTC
    * _NOTE_ [Bojie Li][10] has redeveloped the freeshell service.
* Board manager of [Linux][7] and [Ansic][8] of [USTCBBS][9]

##

[download](../upload/resume.201405.pdf).

[1]: http://research.microsoft.com/en-us/people/tmei/default.aspx
[2]: http://staff.ustc.edu.cn/~yuzhang/compiler/index.html
[3]: http://lug.ustc.edu.cn/
[4]: http://mirrors.ustc.edu.cn/
[5]: http://pxe.ustc.edu.cn/
[6]: http://freeshell.ustc.edu.cn
[7]: http://bbs.ustc.edu.cn/cgi/bbstdoc?board=Linux 
[8]: http://bbs.ustc.edu.cn/cgi/bbstdoc?board=AnsiC
[9]: http://bbs.ustc.edu.cn/
[10]: http://boj.blog.ustc.edu.cn/index.php/whoami/
[11]: https://github.com/StephenPCG/Deepin-System
[12]: http://packages.linuxdeepin.com/deepin/
[13]: https://github.com/StephenPCG/nginx-lua-simpleauth-module
[14]: http://ppa.onebitbug.me/
[15]: https://github.com/StephenPCG/extend-left-box
