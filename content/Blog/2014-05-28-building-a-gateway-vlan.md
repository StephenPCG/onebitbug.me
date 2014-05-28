Title: 搭建网关系列 —— VLAN篇
Tags: gateway, debian, vlan

### 为何使用vlan

在接触vlan之前，总是觉得vlan是一个很高大上的东西，感觉这辈子我不可能用上。
（许多码农都这样吧，所有不明真相的东西都是高大上的东西。）
vlan的作用简单的说就是隔离，在上学时看到这个东西，认为或许只有大公司人很多的时候采用的上吧。
初次接触vlan是在公司里，有一阵子大家突然发现有许多ip冲突，虽然ip冲突的主要原因是因为不规范
的手动配置ip，但根本原因是设备越来越多。
于是我就脑子一热，让公司买了个支持vlan的交换机，将大家按部门划分网段，每个部门一个网段，
每个网段内的主机数量都比较少了，这时候跟大家约定每个网段里有一个不太大的dhcp池，
手动指定ip时请避开dhcp池，于是基本没有了ip冲突。这里就通过vlan来将大家划分网段。

那么家里的网络为何要使用vlan呢？根据[预告篇]({filename}2014-05-28-building-a-gateway.md)的介绍，
现在家里有两个isp接入，如果直接接到路由器上，那么路由器至少要有三个网卡（两个上联，一个局域网）。
现在2个以上网口的设备并不多（要么自己攒一台多网卡的主机，要么是很贵的专用路由设备）。
VLAN在起到隔离作用的同时，其实也为路由器虚拟出多个网卡。

### vlan基本概念简介

这里并不打算解剖vlan的以太网帧头这类细节，感兴趣的童鞋可以作为课外作业自己充电。
这里更注重实用主义，知道的东西够用就行了。

vlan可以简单的理解为对每一个正常的[以太网包](http://en.wikipedia.org/wiki/Ethernet_frame)
打上一个tag，用来区分不同的网络，这个tag可以是1-4096。
那么vlan具体如何工作呢？我们对照下图（openwrt的vlan配置）来解释：
{% img center /images/posts/building-a-gateway/openwrt-vlan.png %}

这里我配置了三个VLAN，分别是1、10、11。分别分析以下场景：

* 一个没有tag的包进入``Port 0``，交换机会给这个包打上``10``这个tag。
  然后会查找有哪些接口开启了vlan 11，发现有``Port 2``和``Port CPU``。
  也就是说，这个包只可能从这两个接口之一流出，不可能从其他Port流出。
  这时候，假设该包的目的地要从``Port 2``流出，那么流出时会打上``10``这个tag。
* 一个tag为``11``的包流入``Port 0``，交换机发现``Port 0``上并不接受vlan11
  的包，于是这个包被丢弃。
* 一个没有tag的包流入``Port 2``，交换机发现在这个接口上只有vlan1是不需要
  tag的，于是给这个包打上``1``这个tag。接下来查找哪些接口允许vlan1，然后
  发现``Port 3``和``Port CPU``都接受。如果这个包最终需要从``Port 3``出去的话，
  出去时会先将``1``这个tag去除然后再流出。

简单的说，在交换机里，所有的包都会被打上一个vlantag。
交换机可以配置每个口允许通过的vlan，对于任何一个包，只能从允许通过相同vlan的几个端口出去。
因此，实际上 **vlan技术将一个交换机划分成了多个相互独立的交换机** 。

在较“大”一些的交换机上，配置VLAN时还会见到这些类型：Trunk端口、Hybrid端口、Access端口。
摘录一段网上的解释：

>* Access类型的端口只能属于1个VLAN，一般用于连接计算机的端口；
>* Trunk类型的端口可以允许多个VLAN通过，可以接收和发送多个VLAN的报文，一般用于交换机之间连接的端口；
>* Hybrid类型的端口可以允许多个VLAN通过，可以接收和发送多个VLAN的报文，可以用于交换机之间连接，也可以用于连接用户的计算机。
>* Hybrid端口和Trunk端口在接收数据时，处理方法是一样的，唯一不同之处在于发送数据时：Hybrid端口可以允许多个VLAN的报文发送时不打tag，而Trunk端口只允许缺省VLAN的报文发送时不打tag。

根据我的实践经验，一般都不需要使用Access端口和Hybrid端口，**Trunk端口使用起来方便环保**，既方便交换机级联，也可以方便的连接电脑。

看一下一台H3C交换机的vlan配置(点击看原图)：
[{% img center /images/posts/building-a-gateway/h3c-vlan.png 400 400 %}](/images/posts/building-a-gateway/h3c-vlan.png)
这个配置中：

* 1-19口的PVID为10，换用openwrt中配置的方法，意思就是：vlan 10: untagged。
* 其他端口的配置都一样。
* 这里所有的端口都允许所有vlan通过（1-4096），但是除了PVID以外的报文，其他vlan的报文流出端口时都会被打上tag，
  没有经过配置的pc会直接丢弃这些包。
* 这个交换机下接的主要是服务器，为了方便服务器配置加入其他vlan，这里允许所有端口都可以通过所有vlan。
* 如果希望将一个pc接到这个交换机上，并且仅允许这个pc接入某一个特定的vlan（假设为vlan100），
  那么只需要将该端口配置成PVID=100，且仅允许通过vlan 100（这就是Access端口的效果了）。

### 在Debian上配置vlan

好吧，罗嗦了许多了。那么看看在网关上如何配置使用vlan呢？
在Debian上可以很方便的通过``interfaces``文件配置vlan。首先安装``vlan``这个包：

    :::sh
    sudo apt-get install vlan

interfaces文件如下：

    :::text
    auto eth0
    iface eth0 inet static
        address 192.168.10.1
        netmask 255.255.255.0

    auto vlan0010
    iface vlan0010 inet static
        vlan-raw-devices eth0
        address 192.168.20.1
        netmask 255.255.255.0

    auto vlan0011
    iface vlan0011 inet static
        vlan-raw-devices eth0
        address 192.168.21.1
        netmask 255.255.255.0

    ...

这里，类似交换机，如果有一个没有vlan tag的包流入eth0，那么这个包就由eth0这个interface处理，
如果带有vlan tag ``10``，则由vlan0010这个interface处理，vlan tag ``11``亦然。是不是很简单呢？

这时候如果将一台pc接到openwrt的``Port 0``（LAN 4口）上，并且配置上一个``192.168.20.0/24``之后，
就可以ping通``192.168.20.1``了。

配置方式并不仅是上面一种，更多的配置方式见
[Debain Wiki](https://wiki.debian.org/NetworkConfiguration#Howto_use_vlan_.28dot1q.2C_802.1q.2C_trunk.29_.28Etch.2C_Lenny.29)
这里仅列出我比较喜欢的方式。

### vlan使用场景

那么为什么要配置vlan呢？这里介绍两个我正在使用场景。

#### 公司网关，通过vlan隔离部门以及上联出口

公司里有一个通过静态IP接入的ISP上联，以及若干部门组成的局域网。``interfaces``文件大致如下：

    :::text
    # 我们并不直接使用eth0，也就是进出网关设备的所有包都必须有vlan tag
    auto eth0
    iface eth0 inet manual

    auto vlan0002
    iface vlan0002 inet static
        address a.b.c.d
        netmask 255.255.255.224
        gateway a.b.c.e

    auto vlan0010
    iface vlan0010 inet static
        address 10.0.10.1
        netmask 255.255.255.0

    auto vlan0011
    iface vlan0011 inet static
        address 10.0.11.1
        netmask 255.255.255.0

    ...

在这个配置的命名规则上我耍了一些“技巧”，以方便后续配置防火墙规则。

* 使用vlan000*作为上联出口（可以预期即使接入多家ISP，也不会超过8个）。
  在后续的文章中会看到，在iptables中可以使用``vlan000+``来匹配左右的上联端口。
* 使用10以上的vlan给局域网使用，配置的内网网段的第三段使用vlan数字，这样可以方便的从ip看出vlan。

这时候，网关是并不工作的，要使得网关工作，只需要再运行两步配置即可：

    :::sh
    sudo sysctl -w net.ipv4.ip_forward=1
    sudo iptables -t nat -A POSTROUTING -o vlan0002 -j SNAT --to-source a.b.c.d

这里，第一行的作用是开启ip转发，执行完这一步后，所有内网网段的机器都可以互相ping通了。
第二步是设置SNAT，这一步进行完成后，内网机器即可访问互联网了。
当然，这样简单的配置的网关是很危险的，后续的文章中会介绍更安全的防火墙配置。

#### 家里的网关，通过vlan分别拨多路pppoe

根据前面的介绍，我家里有联通和电信通两路接入，全都是pppoe。pppoe，顾名思义，
其数据是走的以太网，因此也可以打vlan tag。我们可以通过vlan来隔离两个pppoe的数据。

首先创建两个vlan，``interfaces``文件如下：

    :::text
    # 给内网使用，没有必要配置vlan了
    auto eth0
    iface eth0 inet static
        address 192.168.10.1
        netmask 255.255.255.0

    auto vlan0010
    iface vlan0010 inet manual
        vlan-raw-devices eth0

    auto vlan0011
    iface vlan0011 inet manual
        vlan-raw-devices eth0

这里配置了vlan0010和vlan0011，分别用于两路pppoe拨号。根据前面的openwrt的配置截图，
以及[预告篇]({filename}2014-05-28-building-a-gateway.md)中dir825的
[照片](/images/posts/building-a-gateway/dir825.jpg)
可以看出的接线方式。

然后安装``pppoe``

    :::sh
    sudo apt-get install pppoe

然后在``interfaces``文件中增加配置：

    :::text
    auto kdt-dsl-provider
    iface kdt-dsl-provider inet ppp
        pre-up /bin/ip link set vlan0011 up
        provider kdt-dsl-provider

    auto unicom-dsl-provider
    iface unicom-dsl-provider inet ppp
        pre-up /bin/ip link set vlan0010 up
        provider unicom-dsl-provider

这里定义了两个ppp的provider，debian在配置网络时，会调用``pon $provider``来启动拨号。
两个``pre-up``语句仅仅是为了保证在开始拨号前所使用的interface状态是``up``的。

根据[Debain Wiki](https://wiki.debian.org/PPPoE)可以知道接下来要配置
``/etc/ppp/peers/{kdt,unicom}-dsl-provider``和``/etc/ppp/pap-secrets``文件。

我的``kdt-dsl-provider``如下：

    :::text
    noipdefault
    hide-password
    noauth
    persist
    plugin rp-pppoe.so vlan0011
    user "1300XXXXX"
    ifname pppoe-kdt

密码配置在``pap-secrets``中，在``pap-secrets``末尾加上一行：

    :::text
    "1300XXXXX" * "password"

这样，通过``pon kdt-dsl-provider``即可开始拨号，在``/var/log/syslog``中可以看到拨号过程，
如果拨号顺利的话，系统里会生成一个新的interface ``pppoe-kdt``。联通的配置同上。
如果拨号发现问题，可以根据``syslog``中的错误提示调整配置，``/etc/ppp/peers/dsl-provider``
中有比较详细的参数说明，可以作为参考。

这里，对于两个pppoe拨号，我都手动指定了``ifname``，如果不指定，那么生成的interface名字
会是``ppp0``和``ppp1``，哪个是哪个由拨号成功的顺序决定，这不利于配置防火墙规则。
后面讲隧道的配置也一样，如果不指定，生成的隧道名字会是``tun0``、``tun1``...，
我比较喜欢以``$proto-$name``来命名接口，接口名字包含足够的信息，方便维护。

### 总结

vlan的常见作用可以简述为两个：

  * 将一个交换机当多个交换机使用
  * 节省网卡的数量，使用一个网卡接入多个网络

普通的交换机并不支持vlan，支持vlan的交换机一般会比较贵，或者比较笨重。
在某宝上搜索“vlan 交换机”或者“楼道交换机”，会找到许多支持vlan的交换机，
最便宜的大概300左右吧，但体积比较大，长相比较丑。
我这里使用了一个openwrt的路由器来当vlan交换机使，价格便宜
（dir825还是挺贵的，但如果仅做vlan交换机使，便宜一点的交换机刷上openwrt应该也可以，
购买前还是参考一下openwrt的文档，确认相应的型号是否有programmable switch），
外观小巧漂亮还不占地。

在一般家里使用并不需要vlan，但如果不想使用openwrt或者其他小路由器，
而是想用通用pc来做网关的话，vlan还是挺有用的。（只有一个上联pppoe时，也并不需要vlan交换机，
比如将pc、网关、上联都接到同一个普通交换机上，网关同样可以拨号，
正常转发数据包，只是这样做会有潜在的隐患。）
