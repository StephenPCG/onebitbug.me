Title: 在逸珑8089上安装Debian Unstable
GitTime: off
Slug: install-debian-sid-on-yeeloong
Date: 2013-11-04 23:03

上个月龙芯突然搞团购（现已结束），279的价格确实动了心，买了两台。
看来龙芯这次是想清仓吧（机器应该08、09年就定型生产了），发货速度奇慢，
似乎每台机器都要再检查一次。不过也反反映出，这次大家对龙芯的热情远超出了梦兰的预期。
细细算来，我有一台2e的盒子，一台2f的盒子，两台2f的笔记本，也算是拥有4台龙芯的设备了。

拿到龙芯的本子，不免又引发了好多回忆。又想起了大三那个夏天的日夜奋战。
又想起了那个夏天，为了龙芯而第一次来到了北京，虽然最后还是选择了放弃这条路，
但是这并没有打消我对龙芯的兴趣。

Well，扯远了，回正题吧。拿到本子，就好像拿到一个电信定制版Android手机一样，第一件事
是：刷机！好吧，这是对原装系统赤裸裸的讽刺。。。
翻查了一下[4年前的文章](http://blackaureole.wordpress.com/2009/05/08/%E9%BE%99%E8%8A%AF%E7%9B%92%E5%AD%90%E7%AC%94%E8%AE%B0%E6%9C%AC%E5%AE%89%E8%A3%85%E7%B3%BB%E7%BB%9F%E6%96%B9%E6%B3%95%E6%B1%87%E6%80%BB/)，
里面的链接几乎全都失效了。去龙芯官网查看，资料也非常的少。
可以说，最近这4年，龙芯仍然没有建立起有效的社区来，这点确实令人失望。

不过现在能在龙芯上跑的发行版已经很多了，这点让人很欣慰。
我用了这么多年的Debian，已经没有动力去折腾其他的发行版了，就Debian吧。
Debian的wiki上已经有很完整的[教程](https://wiki.debian.org/DebianYeeloong/HowTo/Install)，
因此这篇文章也没啥好说的，不过wiki中仅提到了如何安装wheezy和squeeze，没有提如何安装unstable。
其实除了这里以外，debian仓库里的各种installer似乎都没有明确的文档说明该如何安装sid系统（或许是我没有找对地方），在debian仓库里的各种sid installer，默认安装时都是安装的stable版本，
如果需要安装sid，则必须给installer内核加上参数`suite=sid`。

教程正式开始，这个教程并不完整，仅是对Debian官方教程的补充，读者请先完整的读完Debian的教程。

### 安装
* 可以从[这里](http://ftp.cn.debian.org/debian/dists/sid/main/installer-mipsel/current/images/loongson-2f/netboot/)下载安装镜像。而不必非得去d-i.d.o下载。
* 将下载的boot.cfg中，`args nil`这一行改成`args suite=sid`，然后按照教程安装即可。
安装完成后可能会提示安装grub到dummy设备失败，没关系，直接忽略。

### X
* 根据Debian教程，xserver-xorg-video-siliconmotion这个包需要添加三个patch，经过检查，写本文时debian sid仓库中的该包版本为1.7.7-2，该版本仍未应用该patch，所以我将这三个patch打包放到ppa.onebitbug.me中了。
* pixman在debian unstable中已经更新到0.30.2-1，
而安横提供的[patch](http://mirrors.ustc.edu.cn/loongson2f/wheezy/pixman/loongson2f_simd_0.26.0.diff)
已经无法正常apply，我暂时不打包了，回头找个时间看看如何apply这个patch。
看上去龙芯的[代码分支](http://dev.lemote.com/cgit/Pixman.Loongson.git/log/?h=loongson)
已经有一年多没有commit了，不知道是更改仓库了还是merge到上游了还是没人维护了，回头看看吧。
根据[原作者的博文](http://mattst88.com/blog/2012/05/17/Optimizing_pixman_for_Loongson:_Process_and_Results/)，这个应该不难。
简单讲一下pixman是啥东西吧，龙芯2f本子带的显卡太挫了，而且在最新的xorg中表现的更差。
不过龙芯2f的CPU有一套simd指令集，与x86的mmx类似，因此图形相关的许多工作完全可以“软解”。
安装pixman后，如果软件不刻意使用硬件加速的话，那么就能受益于pixman。
龙芯的显卡不支持硬件加速，如果某软件刻意使用硬件加速，反而无法收益pixman。
* Gnome3现在走的离用户越来越远了，我已经开始计划逐步脱离Gnome了
（为何逐步呢？公司里工作用的电脑毕竟没时间折腾，只能慢慢来了）。
龙芯的本正好用来折腾，反正不涉及工作用途，不怕搞挂。。。
准备用回xfce，记得最早用Linux的时候，由于笔记本性能不好，用了一年多的xfce，
后来换芯笔记本之后，觉得仍不住gnome的美观就换回了gnome，没想到这几年gnome走的离用户越来越远了，
只好就扔了。

### 其他
好吧，半夜了，不折腾了，再说吧。。。

记录一下现在想起来的、但还没有折腾的事：

* pixman：前面提到过了。
* 浏览器：看debian教程，似乎iceweasel需要加个patch才能快一些，看看这个patch是啥。另外看看chromium能否使用
(maybe borrow code from gentoo)。
* flash：唉，仅发布二进制的软件都太蛋疼了，基本上意味着小众架构很难得到支持。
看到安恒的源里有一个adobe flash player的二进制，但还没有花时间去adobe官网找。
* java：其实我从没用过openjdk，不知道是否好用。。。
* 无线：貌似每次开机都要按Fn+F5来激活无线设备，看看是否有方法开机自动激活设备。
