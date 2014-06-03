Slug: how-factory-reset-works
Date: 2014-02-09
Title: 差分磁盘：从“恢复出厂设置”说起
Category: Reproduced
Author: <a href=https://boj.blog.ustc.edu.cn>Bojie Li</a>
ReproducedSource: https://boj.blog.ustc.edu.cn/index.php/2014/02/how-factory-reset-works/
GitTime: Off

智能手机、路由器等很多嵌入式设备都有“恢复出厂设置”的功能。按照PC机上大家习惯的“备份”做法，似乎需要把出厂时的整个系统备份在只读的
ROM 里。如果是这样，每次恢复出厂设置，ROM 里的内容都要拷贝到 Flash
存储里，浪费大量存储空间，而且恢复出厂设置需要比较长的时间。但事实上，恢复出厂设置只是重启一下就完成了，而且刚恢复的系统里
Flash 存储基本是空的。

（感谢 BW 的评论，Android
系统的恢复出厂设置不是使用差分技术，而是简单清空数据分区，对 /system
分区的修改没有被还原，我弄错了）

[![Capture](/images/reproduced/how-factory-reset-works/Capture8.png)](/images/reproduced/how-factory-reset-works/Capture8.png)

虚拟机快照
----------

在纯软件的世界里，什么地方需要类似“恢复出厂设置”的功能呢？玩过虚拟机的小伙伴们也许知道“快照”（snapshot）功能，只要几秒钟快照就能建好。什么时候虚拟机玩坏了，只要几秒钟就能恢复到“快照”的状态。磁盘快照的秘诀在于“差分磁盘”。执行“快照”命令后，原来的虚拟磁盘就被冻结了，并生成一个新的虚拟差分磁盘。

读一个磁盘块时，如果这个块已经在差分磁盘内，则读出它；否则到原磁盘里读取这个块。写一个磁盘块时，总是写在差分磁盘里。这样，原来的磁盘处于只读状态，所有的写入都在差分磁盘里。当需要恢复到“快照”时，只需将差分磁盘清空即可，因此所需时间很短（实际需要几秒钟时间是因为需要恢复内存状态）。

[![Capture](/images/reproduced/how-factory-reset-works/Capture.png)](/images/reproduced/how-factory-reset-works/Capture.png)

爱折腾的小伙伴也许把“快照”搞成过树形结构（如上图所示，像不像版本控制系统）。Now
这个箭头代表当前状态，每次要读一个块时，要依次查找当前差分磁盘、Windows
XP – SP3 差分磁盘、Windows XP – SP2 差分磁盘、Windows XP – RTM
母盘；写一个块时，总是写进当前差分磁盘。虽然这看起来很好玩，但由于要查好几次，读性能是会下降的。因此，不能把虚拟机的“快照”当成“备份”来用。

差分磁盘用于恢复出厂设置
------------------------

一些嵌入式设备的“恢复出厂设置”就是这样实现的。Linux 的 Device Mapper
可以把一个块设备“覆盖”在另一个块设备之上，底层的块设备是一个压缩过的支持随机访问的只读文件系统（squashfs）（注意不是所有压缩格式都支持随机访问，一个简单例子，有些压缩文件即使只想解压其中的一个文件，也得把很多其他文件都解压出来），上层的块设备是可读写的。

[![figure1](/images/reproduced/how-factory-reset-works/figure1.gif)](/images/reproduced/how-factory-reset-works/figure1.gif)

一般来说，下层的只读文件系统和上层的可读写文件系统分别是一个文件（类似虚拟磁盘），在系统启动过程中挂载上来，成为一个文件系统，再
chroot
进去。具体命令的传送门：[http://www.ibm.com/developerworks/cn/linux/1306\_qinzl\_squashfs/](http://www.ibm.com/developerworks/cn/linux/1306_qinzl_squashfs/)

当用户需要恢复出厂设置时，只要清空上层的可读写文件系统就行了。要想修改下层的只读文件系统，只能“刷机”（修改ROM）。（Android
似乎没有用差分磁盘，只是把数据分区挂载在 /data
目录，因此格式化分区就恢复出厂设置了）

差分磁盘技术最早用于什么地方，已无据可考。LiveCD
应该算是比较早的应用。一张只读的光盘启动一个 Linux
发行版，它的根目录就是一个 squashfs。上层是
ramdisk，就是把内存当成磁盘来用。有关 ramdisk 的技术细节，Linux
爱好者可以参考赵磊的《写一个块设备驱动》（或者直接看内核里的 ramdisk
源码），Windows 爱好者可以参考《寒江独钓——Windows
内核安全编程》一书第5章“磁盘的虚拟”（或者直接看 WDK 里的 ramdisk
例子）。

还原卡应该也算比较早的应用。还原卡一般是在硬盘里有个专门的分区用于存放差分内容，写受保护分区时，原来的分区内容根本没有改变，只要清空差分分区就起到了“还原”的作用。顺便说一下，还原卡需要文件系统过滤驱动来拦截磁盘读写请求并送给还原卡处理，是需要操作系统支持的。因此必须在
BIOS 里禁用
USB、网络等启动方式，不然用户进了不带还原卡过滤驱动的操作系统，还原卡就起不到保护作用了。

差分磁盘用于多用户共享系统
--------------------------

差分磁盘不只有保存状态和快速恢复的作用。比如，助教需要给班里每个同学在服务器上搭建一套开发环境，同学之间最好不要互相干扰。我见过的方法有：

-   只准修改自己的家目录。这样装软件就麻烦了。
-   每人一个虚拟机。先做好一个“母盘”，拷贝若干份。这种做法非常浪费磁盘空间，一个搭好开发环境的
    Linux 少说也有几G，幸亏学校里用的是 Linux，如果是 Windows，2T
    的磁盘恐怕还放不下一个班（100人）的虚拟机镜像。这种方法不仅浪费磁盘，还浪费内存。同样一个标准C库，每个人都要用，都要载入进内存而不能共享，会极大影响文件的内存缓存的命中率。

有了“差分磁盘”，事情就变得简单了。只要做好一个母盘，设为只读，每个同学建立一个差分磁盘，让虚拟机使用这个差分磁盘，这样大家可以共享母盘里的开发环境，又可以随心所欲地操纵自己的虚拟系统。只是每个虚拟机操作系统都维护着自己的内存缓存，还是不能共享。

[![IC179979](/images/reproduced/how-factory-reset-works/IC179979.gif)](/images/reproduced/how-factory-reset-works/IC179979.gif)

事实上，少院机房的无盘系统和图书馆查询机，虽然一个是 Windows
平台，一个是 Linux
平台，都是用差分磁盘技术实现的。由于机房PC机的内存不大，而用户可能一次上机写入很多内容，无盘系统的差分磁盘跟母盘一样也存储在服务器上，重启后清空。图书馆查询机的功能比较简单，差分磁盘就直接在内存里了。机房PC机和图书馆查询机都是独立的物理机器，自然不存在共享内存缓存的考虑。

Overlayfs：差分文件系统
-----------------------

如果所有用户都是运行在一台物理机器上，比如前面助教的例子，我们希望共享内存缓存。上述“差分磁盘”方案是块设备层面的，每个差分出来的块设备都有自己的缓存，没办法共享。如果我们不使用虚拟机，而使用同一个操作系统内文件系统层的差分，是不是就能解决缓存共享问题了呢？

答案是肯定的。Overlayfs 就是一个简洁优雅的实现。Overlayfs 使用 Linux
FUSE（用户态文件系统）框架，由于它的简洁，也比较容易移植到其他平台（虽然我没找到）。

Overlayfs
需要两个源目录（一个只读目录，一个差分目录）和一个目标挂载目录。这些目录可以在一个文件系统中，也可以不在，是无所谓的。例如，装好开发环境的母盘系统在 /opt/base，我们需要给三个学生建立虚拟环境，“差分磁盘”
分别在 /opt/diff/1, /opt/diff/2, /opt/diff/3，每个学生看到的根目录分别是
/opt/chroot/1, /opt/chroot/2, /opt/chroot/3。需要执行以下命令：

    mount -t overlayfs overlayfs -olowerdir=/opt/base,upperdir=/opt/diff/1 /opt/chroot/1
    mount -t overlayfs overlayfs -olowerdir=/opt/base,upperdir=/opt/diff/2 /opt/chroot/2
    mount -t overlayfs overlayfs -olowerdir=/opt/base,upperdir=/opt/diff/3 /opt/chroot/3

当学生1登录时，执行 “cd /opt/chroot/1; chroot .”
就进入了学生1的虚拟环境。如果需要对进程、网络等进行隔离，可以采用
LXC、OpenVZ 等操作系统级虚拟化技术。

Overlayfs 是如何工作的呢？

-   读取目录内容时，把 upperdir 和 lowerdir
    对应路径的内容都读出来，再合并（两边都有的文件以 upperdir 为准）
-   打开文件时，把 upperdir 和 lowerdir
    中该文件的指针保存起来以便读写文件时调用。如果有“写”标志且 upperdir
    中不存在，则需要将 lowerdir 中的对应文件复制一份到 upperdir
    里。如果文件很大，则以“写”方式打开文件会需要很长时间。
-   读文件时（注意此时文件已经打开了），如果 upperdir
    中存在此文件，则调用 upperdir 中此文件的读函数；否则调用 lowerdir
    中此文件的读函数。
-   写文件时（注意此时文件已经打开了），调用 upperdir 中此文件的写函数。
-   删除文件时，如果在 upperdir 中有，直接删除；如果在 lowerdir
    中有，则在 upperdir
    中的对应路径创建一个指向特殊路径的符号链接，并设置扩展属性（xattr），以后
    Overlayfs 看到这个墓碑文件（符号链接）时就知道这个路径已被“删除”了。

OpenWRT（开源无线路由器的事实标准）中 ROM
和可读写根文件系统的隔离，用的就是只读的 squashfs 与可读写的 JFFS2
组成的 Overlayfs。

[![Capture](/images/reproduced/how-factory-reset-works/Capture1.png)](/images/reproduced/how-factory-reset-works/Capture1.png)

曾经有小伙伴抱怨开发驱动之麻烦，bug 如果总是导致系统崩溃，就要重启进
LiveCD，删除出错的驱动文件才能正常进入系统。只要使用 Overlayfs
的办法，在 lowerdir 里维护状态良好的系统，把 ramdisk 作为 upperdir，在
overlayfs 里做危险操作。不管出什么问题（只要别把 VFS
搞乱），只要一重启，就恢复到正常状态了。

文件系统快照：备份的捷径
------------------------

如果我们希望在非虚拟化的机器中做备份，文件系统层的快照（snapshot）是个好选择。ext4、btrfs
等现代文件系统支持快照功能。如下图所示：

-   假设初始状态下文件系统中有 A、B、D 三个目录和 C、E、F
    三个文件，形成一棵树，超级块（树根）指向A。做一个快照。
-   某个操作对 C 进行修改，变成
    C’，此时从被修改的节点到树根的所有节点（inode）都要分离出一个新版本，树根指向
    A’，A’ 指向分离出的 B’ 和原来的 D，B’ 指向分离出的 C’ 和原来的
    E。做一个快照。
-   某个操作对 E 进行修改，变成 E’，又要分离出一个新版本，树根指向
    A”，A” 指向从 B’ 分离出的 B” 和原来的 D，B” 指向上个版本的 C’
    和分离出的 E’。

[![image007](/images/reproduced/how-factory-reset-works/image007.jpg)](/images/reproduced/how-factory-reset-works/image007.jpg)

不同于虚拟机差分磁盘，文件系统的快照对读写性能一般是没有影响的，只是每做一个快照，就要占用一些磁盘空间以存储发生变化的文件和它们到根路径上的元数据。

虚拟机差分磁盘、Overlayfs
和文件系统快照都是强大的时光机，在合适的时候用上，也许能解决令您非常挠头的问题。差分存储体现了 DRY（Don’t
Repeat Yourself）原则：我们都知道代码不应该 copy &
paste，文件系统也不应该这样！

References:
-----------

1.  http://technet.microsoft.com/en-us/library/cc720381(v=ws.10).aspx
2.  http://www.ibm.com/developerworks/cn/linux/1306\_qinzl\_squashfs/
3.  淘宝《叠合式文件系统——Overlayfs》：http://wenku.baidu.com/view/2c82473ca32d7375a41780ab.html
4.  http://wiki.openwrt.org/doc/techref/flash.layout

