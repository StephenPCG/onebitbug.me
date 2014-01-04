Title: Tuning KVM for Guest OS Win7
Slug: tuning-kvm-for-guest-win7
Date: 2013-04-15
Category: Linux

MacbookAir终究太小了，出差旅行不错、坐床上看电视写博客不错，但要向干点活还是不舒服。 这周买了台台式机，配置还算比较高端，i7 3770、骇客神条16G，另外忍痛放血买了两个不错的显示器。

我发现折腾工具总是有个周期性。比如vim，每半年或者一年，会突然有一天心血来潮，狠狠的折腾各一天， 把各种插件更新一遍，找各种新的教程等。这个周末，心血来潮着腾了一下kvm。

之前一直用kvm，还算是比较顺手，不过也有许多不满意的地方。

* 最不满意的当然是显卡。弱弱的显卡，实在不忍心装win7，一直都装的xp。 用rdesktop连上去比vnc要好很多，流畅很多，但仍然惨不忍睹，比如Evernote里滚一下鼠标滚轮，可以卡半天。
* 网络。用上了virtio，但效果并不是很好，-netdev user的速度，只有十几MB/s。（猜测性能瓶颈可能在nat的实现上。）
* usb设备。由于长久没有着腾过、没有挂usb的需求，所以一直没有弄很明白。

这次折腾kvm，在显卡和网络方面都有了改进，各项表现基本满意，除了不支持3D加速/Areo效果外，跟VMware差不了多少了。 本文中所提到的kvm版本为Debian 1.4.0+dfsg-1exp，内核版本为Debian 3.8.5-1~experimental.1。


#### 优化网络
**关键字**：`vhost_net`

根据kvm wiki[这个页面][1]，使用vhost会大大提高传输速度。 我简单做了下测试，分别用下面两种参数启动机器，再比较传输速度：

* `-netdev user,id=hostnet0 -device virtio-net-pci,netdev=hostnet0`
* `-netdev tap,id=hostnet1,vhost=on -device virtio-net-pci,netdev=hostnet1`

跟主机同网段的其他机器裸拷数据，前者的速度只有100mbps左右，而后者可以达到600mbps，效果非常明显。 vhost的文档并不多，经过自己尝试，似乎只有tap模式可以用。 而我的虚拟机之前是这样的，一个user类型的网卡，guest系统设置固定IP，然后通过smb将host系统上的一个目录 映射为网络驱动器D盘，将所有重要数据保存在D盘。而这个网卡的速度显然对系统的性能影响会很大。 因此，这里要优化时，就要避开用user类型的网卡，改用tap，但又要尽可能不跟外界网络发生冲突，因此选择这样的方法：

* 主机里建两个桥：`vnet0`, `vnet1`
* `eth0` –-> `vnet0`
* 虚拟机两块`tap`网卡，一块`kinet0`，桥接到`vnet0`上，上外网
* 另外一块`khost0`，桥接到`vnet1`，跟主机内部通信使用。

配置文件如下：

`/etc/network/interfaces`
```bash
iface eth0 inet manual

auto vnet0
iface vnet0 inet static
    pre-up brctl addbr vnet0
    post-down brctl delbr vnet0
    bridge_ports eth0
    bridge_stp off
    bridge_maxwait 0
    bridge_fd 0
    address 192.168.0.150
    netmask 255.255.255.0
    gateway 192.168.0.1
    dns-nameservers 192.168.0.1
    dns-search local.onebitbug.me

auto vnet1
iface vnet1 inet static
    pre-up brctl addbr vnet1
    post-down brctl delbr vnet1
    address 172.16.254.1
    netmask 255.255.255.0
    bridge_stp off
    bridge_maxwait 0
    bridge_fd 0
```

`ifup`脚本:
```bash
#!/bin/sh

PATH=$PATH:/sbin:/usr/sbin
ip=$(which ip)

if [ -n "$ip" ]; then
   ip link set "$1" up
else
   brctl=$(which brctl)
   if [ ! "$ip" -o ! "$brctl" ]; then
     echo "W: $0: not doing any bridge processing: neither ip nor brctl utility not found" >&2
     exit 0
   fi
   ifconfig "$1" 0.0.0.0 up
fi

br=vnet1

if [ -d /sys/class/net/$br/bridge/. ]; then
    if [ -n "$ip" ]; then
        ip link set "$1" master "$br"
    else
        brctl addif $br "$1"
    fi
    exit
fi

echo "W: $0: $br does not exist"
```

`ifdown`脚本(空)：
```bash
#!/bin/sh
:
```

kvm启动参数：
```
sudo qemu-system-x86_64 \
    -netdev tap,id=nic0,ifname=kinet1,vhost=on -device virtio-net-pci,netdev=nic0,mac=0f:ee:d0:00:10:00 \
    -netdev tap,id=nic1,ifname=khost1,vhost=on,script=/path/to/ifup,downscript=/path/to/ifdown -device virtio-net-pci,netdev=nic1,mac=0f:ee:d0:00:11:00 \
    ${other_options}
```

#### 显卡优化
**关键字**：`qxl`、`spice` 主要参考了[这个页面][2]。
系统使用-vga qxl，并给guest os安装spice驱动。
具体需要的文件和使用方法，可以参考前面所给的链接，以及[spice的主页][3]。
这里直接给出有关的参数：

```
qemu-system-x86_64 \
        -vga qxl \
        -usb -usbdevice tablet \
        -spice port=$((5800+VNC)),addr=127.0.0.1,disable-ticketing \
        ${other_options}
```

这是最终的参数，在此之前，需要先安装guest系统，安装spice guest组件等，过程都略过，很简单。

#### USB
**关键字**：`ehci`

主要参考[这个页面][4]。
较新版本的kvm已经支持usb2.0了。这里我需要将一个usb2.0的摄像头映射到虚拟机中：
```
qemu-system-x86_64 \
            -usb -usbdevice tablet \
            -device usb-ehci,id=ehci \
            -device usb-host,bus=ehci.0,vendorid=0x1e4e,productid=0x0102 \
            ${other_options}
```

其他参数基本跟以前用的一样，没有太大的变化。不过spice的表现令人十分满意，以后不需要用rdesktop了。 给个系统评级的截图：

{% img center /static/images/posts/2013-04-15/win7-score.png %}

#### Assigning physical VGA adapters

这次买机器，选择CPU时，特别关注了vt-d技术，以及kvm的支持情况。
其实最关心的是显卡的pass through。 
进展可以看[这个页面][5]。
当前是in progress，并且似乎看到了些曙光了。我准备暂时不够买显卡，等kvm 这边有更多进展时，再选择购买显卡。到时候双显示器就能更加发挥作用了，真正做到一台机器两个系统同时 使用，基本五缝顺切:-P

最后给出我使用的完整的kvm启动脚本。

```
ROOT=/path/to/vm/dir/
VNC=0
sudo qemu-system-x86_64 \
    -machine accel=kvm:tcg \
    -name win7-$VNC \
    -cpu host \
    -smp 2 \
    -m 4096 \
    -drive file=$ROOT/win7.qcow2,cache=writeback,if=none,media=disk,id=virt-disk0,aio=native -device virtio-blk-pci,drive=virt-disk0 \
    -drive if=ide,index=0,media=cdrom \
    -netdev tap,id=nic0,ifname=kinet1,vhost=on -device virtio-net-pci,netdev=nic0,mac=0f:ee:d0:00:10:0$VNC \
    -netdev tap,id=nic1,ifname=khost1,vhost=on,script=$ROOT/ifup,downscript=$ROOT/ifdown -device virtio-net-pci,netdev=nic1,mac=0f:ee:d0:00:11:0$VNC \
    -device virtio-serial-pci \
    -chardev spicevmc,id=vdagent,name=vdagent -device virtserialport,chardev=vdagent,name=com.redhat.spice.0 \
    -soundhw hda \
    -vga qxl \
    -daemonize \
    -localtime \
    -usb -usbdevice tablet \
    -device usb-ehci,id=ehci \
    -device usb-host,bus=ehci.0,vendorid=0x1e4e,productid=0x0102 \
    -pidfile $ROOT/pid-$VNC \
    -spice port=$((5800+VNC)),addr=127.0.0.1,disable-ticketing \
    -vnc :$VNC \
    $@
```

[1]: http://www.linux-kvm.org/page/UsingVhost 
[2]: http://www.linux-kvm.org/page/SPICE
[3]: http://spice-space.org/download.html
[4]: http://www.kraxel.org/cgit/qemu/tree/docs/usb2.txt
[5]: http://www.linux-kvm.org/page/VGA_device_assignment
