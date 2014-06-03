Title: 搭建网关系列 —— 路由篇
Tags: gateway, debian, route

### 策略路由简介

使用过vpn的同学可能手动配置过一些路由设置，不过大多数时候可能做的都是目的路由，
也就是基于目的地址的选路。目的路由大概的样子如下：

    :::sh
    ip route add 8.8.8.8 via XX dev $vpn
    ip route add $blocked-network via XX dev $vpn
    ip route replace 0/0 via dev $pppoe
    ...

但是在为一个稍有规模的网络配置路由时，目的路由有时候会力不从心。例如这些需求：

* 小明想要所有的流量全都走 isp1 出去
* 小红想要所有的流量全部走 isp2 出去
* 小华想要所有443的流量全部走 isp1，其他流量走 isp2
* ……

这样的需求，单纯使用目的路由肯定就不够了，对于相同的目的，不同的人希望走不同的路由，
甚至不同的协议走不同的路由。
为了解决这个问题，Linux将传统的基于目的的路由表（destination based routing table），
改造成了路由策略数据库（routing policy database， RPDB），这种方式，
将根据一些规则（rules）来选择路由。

那么下面简单的介绍一些策略路由的使用。
这里我们使用iproute工具，在Debian中包名为``iproute2``，
所有功能都通过``/bin/ip``一个命令作为接口。

在Linux-2.x中，可以创建2^31个目的路由表，每个表使用数字标识，
也可以使用``/etc/iproute2/rt_tables``中指定的名字来代替数字使用。
Debian默认给三个表指定了名字，分别是``local``、``default``、``main``，
其中``local``和``default``都是内核维护的，一般我们都不需要手动去改，
``main``表一般由网络协议栈的工具来维护（例如pppoe拨号后自动修改默认路由，
debian networking配置网络后添加默认路由等），也可以手动加入条目。
在本文最开头的示例代码中没有指定对哪个table操作，默认对``main``进行操作。
如果要指定table的话，命令中加上``table $id``。

在Linux中，可以创建若干策略规则（ip rule），每条规则一般会有这几个元素：
优先级、选择规则（SELECTOR）和动作（ACTION）。
SELECTOR用来匹配我们希望的包，ACTION一般是（但不限于）查找某一个路由表。
举例说Linux默认的ip rule如下：

    :::sh
    $ ip rule
    0:  from all lookup local
    32766:  from all lookup main
    32767:  from all lookup default

这里，第一列是优先级，数字越小优先级越高。
所有的包首先检查第一条规则，SELECTOR是``from all``，显然所有的包都会被匹配到，
于是执行动作``lookup local``，``local``表中一般都是本地广播相关的表，大多数包都找不到路由项，
于是开始检查第二条规则，SELECTOR仍然是``from all``，于是查看``main``表，
在``main``表中一般能找到匹配的路由项，于是执行该路由，不再继续检查后续的策略规则。

我们不妨简单看一下最前面提出的三个需求：

* 小明想要所有的流量全都走 isp1 出去
* 小红想要所有的流量全部走 isp2 出去
* 小华想要所有443的流量全部走 isp1，其他流量走 isp2

可以首先创建两个路由表：

    :::sh
    # 要使用一个路由表，首先清空表项，以免有以前添进去的表项
    ip route flush table 100
    # 这个表只需要一个表项，就是默认路由，default也可以写成0/0
    ip route add default via $isp1-gw dev $isp1-iface table 100
    ip route flush table 101
    ip route add default via $isp2-gw dev $isp2-iface table 101

然后为小明和小红添加策略规则：

    :::sh
    ip rule add from $小明ip lookup 100
    ip rule add from $小红ip lookup 101

但是小华怎么办呢？我们通过``man ip rule``看``SELECTOR``，
发现是无法通过端口来匹配规则的，这时候需要借助iptables的帮忙，
我们后面再看。

### ISP路由

在有多个ISP接入时，或者使用vpn时，常常需要建立ISP路由，例如我们有两个出口，
一个是电信，一个是国外的vpn，我们常常需要这样的路由（这个需求大家都懂的）：

* 到中国的IP走电信出去
* 到其他IP走vpn

一般有两种做法，第一种做法是，为两个出口分别创建一个表，然后通过策略路由来控制，

    :::sh
    ip route flush table 100
    ip route add 0/0 dev $telecom table 100
    ip route flush table 101
    ip route add 0/0 dev $vpn table 101
    for network in `cat chnroute.txt`; do
        ip rule add from all to $network lookup 100
    done
    ip rule add from all lookup 101

这种做法有许多缺点，例如规则表的查找速度比路由表慢，不便于创建多个不同规则的表等。
此外也不容易与最复杂的规则配合使用。

第二种方法是创建一个表，让所有的包都走这个表：

    :::sh
    ip route flush table 100
    for network in `cat chnroute.txt`; do
        ip route add $network dev $vpn table 100
    done
    ip rule add from all lookup 100

这样的方法，可以预定义多个不同的路由表。例如中科大的网络通，有电信、联通、移动等多个出口，
给同学提供了多个上网出口以供选择，如：

* 教育网出口，所有流量从教育网出去
* 电信出口，到联通走联通出口，到教育网走教育网出口，其他流量走电信
* 联通出口，到电信走电信出口，到教育网走教育网出口，其他流量走联通
* ……

实现方法很简单，分别创建三个路由表，然后用户可以添加一条匹配自己IP的策略路由：

    :::sh
    # 为了简洁省略flush以及for语句
    ip route add default dev $cernet table 100

    ip route add $unicom dev $unicom table 101
    ip route add $cernet dev $cernet table 101
    ip route add default dev $telecom table 101

    ip route add $telecom dev $telecom table 102
    ip route add $cernet dev $cernet table 102
    ip route add default dev $unicom table 102

    # 每个用户可以通过一个web接口来添加自己的策略路由规则：
    ip rule add from $individual-ip lookup $desired-table-id

（实际上中科大网络通似乎仍在使用Linux2.4内核，大致实现原理如上，
但jameszhang当时做了许多优化工作。）

### 我的网关的配置

这里说一下我的网关的的实际策略配置（公司和家里的配置类似）。

    :::sh
    $ ip rule
    0:      from all lookup local
    80:     from all to 192.168.10.0/24 lookup main
    80:     from all to 192.168.200.0/24 lookup main
    80:     from all to 192.168.201.0/24 lookup main
    85:     from $pppoe-lt-addr lookup 300
    85:     from $pppoe-kdt-addr lookup 301
    85:     from 192.168.200.1 lookup 302
    85:     from 192.168.200.2 lookup 303
    85:     from 192.168.200.3 lookup 304
    ...
    90:     from all fwmark 0x1 lookup 300
    90:     from all fwmark 0x2 lookup 301
    90:     from all fwmark 0x3 lookup 302
    90:     from all fwmark 0x4 lookup 303
    90:     from all fwmark 0x5 lookup 304
    ...
    99:     from all lookup 99
    100:    from all lookup 100
    199:    from 192.168.10.99 lookup 304
    500:    from all lookup 500
    32766:  from all lookup main
    32767:  from all lookup default


下面详细解释一下这个规则。

首先是三条优先级为``80``的规则，这里``192.168.10.0/24``、
``192.168.200.0/24``、``192.168.201.0/24``是我的三个内网网段，
到这三行的路由在main表中都有，如：

    :::sh
    $ ip route show table main
    ...
    192.168.10.0/24 dev br-lan  proto kernel  scope link  src 192.168.10.1
    ...

如果没有这三行，那么有时候可能会导致问题。比如``192.168.10.99``要访问``192.168.200.2``，
假设在优先级为``199``的规则之前没有一条规则能匹配且指定的路由表能路由这个包的，
那么就有``199``这条规则进行路由，这里的``304``表里面只有一条默认路由规则，使用某个isp出口，
这事就会发现``192.168.10.99``无法访问``192.168.200.2``。
所以这里的三行主要是保护内网用的，对所有网关直接接入的网段，都使用系统自动维护的``main``表。

接下来若干条优先级为``85``的规则，这里面from的ip都是网关自己的（``192.168.200.xx``
其实都是我的tunnel的peer ip），这几条规则主要是对网关自己上网产生效果的。
例如在网关上某程序访问外网时，bind到某个特定的interface，也就是指定了通信这一端的ip，
那么就要从相应的interface出去，后面的``30x``的路由表，全都只有一条默认路由，从相应的出口出去。

在接下来优先级为``90``的规则，这些规则很有意思。还记得
[上一篇文章]({filename}2014-06-01-building-a-gateway-iptables.md)
中路由设置导致端口映射配置失效的例子么？

我们这里再举个例子，我们简化一下场景，我有若干个出口（包括pppoe和多个tunnel），
分别创建了``30x``若干个只有默认路由的路由表，从相应的出口出去。
这里``192.168.10.99``选择所有的包都从``$isp5``这个出口出去（``lookup 304``）。
并且，这个ip做了一个端口映射：``portmap $isp1 $isp1-ip 8080 192.168.10.99 80``，
此时公网有一台主机，ip为``1.2.3.4``，访问``$isp1-ip``的8080端口，
然后``192.168.10.99``的响应包，根据当前的路由，会从``$isp5``出去，而我们期望的是``$isp1``。
那怎么办呢？这个场景下我们希望能够根据tcp连接来进行路由，即这个连接第一个包是从哪个出口走的，
后续的包都需要从这个出口走。这时候就需要借助iptables了。

使用以下的命令：

    :::sh
    iptables -t mangle -A PREROUTING -j CONNMARK --restore-mark
    iptables -t mangle -A PREROUTING -j CONNMARK -i $isp1 -j MARK --set-mark 0x1
    iptables -t mangle -A PREROUTING -j CONNMARK --save-mark

简单解释一下这三条命令：

* 第一行，首先看在这个``连接``是否有mark，如果有，将这个mark打到当前这个``ip包``上
* 第二行，无论当前的``ip包``是否有mark，如果它是从$isp1这个interface进来的，那么就打上``0x1``这个标记
* 第三行，将当前``ip包``上的标记保存到当前的``连接``上

要注意区分上面说的``连接``和``ip包``，无论是iptables还是ip rule，面对的都是一个单独的``ip包``，
而``连接``则是一系列有关联的``ip包``。
我们可以将连接的信息存到``连接``上，但要ip rule使用时，就需要将这些信息附加到当前的``ip包``上。

再看前面的场景，当``1.2.3.4``发起访问``$isp1-ip:8080``时，这是这个连接的第一个包，
``--restore-mark``相当于什么都没做，然后给这个包打上了``0x1``这个标记，并存到了连接里。
随后这个通信中的所有的包，无论哪个方向在``--restore-mark``时都会被打上``0x1``这个标记，
于是在策略路由时，就会匹配上这条规则：

    :::sh
    ...
    90:     from all fwmark 0x1 lookup 300
    ...

于是这个包就会正常的从$isp1出口出站。

fwmark这几句话其实也解决了许多潜在的问题，我们后续还会看到。

回到前面的话题，继续分析我当前的ip rules。
在一串``fwmark``的规则之后，有

    :::sh
    ...
    99:     from all lookup 99
    100:    from all lookup 100
    199:    from 192.168.10.99 lookup 304
    500:    from all lookup 500
    ...

这里首先看``500:    from all lookup 500``，这里的``table 500``表是一个isp智能路由表，
就是上一节中所说的，不同的isp网段走不同的出口，大多数内网的访问都会从这个表里出去。

``199:    from 192.168.10.99 lookup 304``这条规则是用户通过web界面创建的，
{% img center /images/posts/building-a-gateway/choose-isp.png %}
这条规则的优先级高于``500``，所以来自``192.168.10.99``发出的访问总是从$isp5出去。

那么``table 99``和``table 100``的作用是什么呢？其实没啥特别的，
就是一些不希望被isp路由影响的路由，例如指定访问vpn1服务时使用pppoe-lt出站等。
这里分两个表主要是为了方便脚本，其中``table 99``是手写，
而``table 100``是通过脚本在各vpn/tunnel的up/down脚本中维护的。

最后的两行是系统自动创建的，作为fallback使用，我们不用关心，一般如果前面的rule
能够覆盖所有的包的路由，那么这两行也就没什么用了。

### 流量均衡

当有多个isp时，常常会想到自动流量均衡。例如有两条电信线路接入，想按一定的比例在两个出口上分配流量。
这里，目的路由就可以实现。

我们前面看到的路由表项都是这样创建的：

    :::sh
    ip route add $some-network via $gateway dev $iface [table 100]

在前面的文章里曾经提过，所谓的gateway，其实只是nexthop，也就是下一跳送往哪里。
在这里，我们也可以使用nexthop来配置：

    :::sh
    ip route add $some-network nexthop via $gateway dev $iface weight 1

写成这样之后，我们就很容易扩展成多线路均衡的命令了：

    :::sh
    ip route add $some-network \
             nexthop via $gw1 dev $iface1 weight 1 \
             nexthop via $gw2 dev $iface2 weight 2 \
             ...

这里可以添加多个出口，每个出口一个nexthop，可以通过后面的weight来设置权重。

### 小结

策略路由其实很简单，本文中也只涉及了很少的一部分，其中``SELECTOR``只用了
``from XXX``、``to XXX``和``fwmark``这三种，实际上还可有``tos``、``iif``、``oif``等，
这些项目也可以混合使用。详细内容可以参考``man ip rule``。
其中我觉得``fwmark``是最灵活的，配合``iptables``或者其他工具，可以分析出流量，
并按照各种规则进行标记（例如本文中根据连接进行标记，也可以根据协议进行标记，
根据端口进行标记，甚至根据ip包的payload进行标记），这样我们就可以创造出非常灵活的路由配置。

当然，在更大的网络当中，策略路由是远远不够的，策略路由毕竟还是一个手动维护的路由，
在更大的网络中，需要一定程度的自动路由配置，包括最优路径选择、链路断连热备等，
会用到许多更“高级”的路由协议，例如BGP等。

本文中没有太多的给出实际的脚本，我计划在整个系列结束后分享出整套脚本，以供大家参考。

在下一篇中将介绍ip隧道的使用方法，作用嘛你懂的。
