Title: 搭建网关系列 —— iptables篇
Tags: gateway, debian, iptables

做网关，iptables是必备的工具，也是一枚神器。
简单的说，iptables的功能就是对所有流过网关的包进行修改，并决定是放行还是丢弃。
当然，网关最重要的功能一个是防火墙，另外一个是路由。
iptables本身无法决定路由，但是它可以影响每一个包的路由。

### iptables基本概念

iptables的概念说复杂也复杂，说简单其实也很简单。
要解释清楚每一条规则是怎么运作的很麻烦，需要有许多背景知识，不过大多数规则都能从字面看懂含义。
这篇文章里可能有些地方只会点一下，有些地方会稍微讲的深入一些，我能力有限，也无法把握好这个度。

首先说一下看教程时能够看到的几个名词：table, chain, target, rule。

通常来说，我们看到的iptables脚本（其实是bash脚本）里的每一条iptables命令都会创建一条规则（rule），
每条规则会包含三个元素：table、chain和target。

其中table通常用来从大方向上区分这条规则是干什么的，
比如filter表主要是决策符合条件的包是被丢弃或放行或进一步处理，
nat表主要用来做对ip包头的源、目标地址进行修改，
mangle表主要用来对数据包的内容进行修改。
但这样分表的主要原因是因为不同的工作需要用到不同的内核模块，这应该是实现所需。
就通常使用而言，我们不需要深入的去理解、区分每一个表究竟能干什么，死记硬背（记不清时查man page）其实挺好的。

链（chain）是用来组织规则的辅助工具。系统自定义了一些链，主要是用来区分这些规则执行的时机，
但由于在链中的规则是顺序执行的，有时我们需要类似``if ... then ... else ...``的规则逻辑，可以通过创建链来实现。

目标（target）可以是用户定义的链、iptables扩展所定义的模块或者三个特殊的值``ACCEPT``、``DROP``、``RETURN``。
``ACCEPT``表示这个包将被接受，不再检查当前所在的内建链的剩余规则以及默认规则。
``DROP``表示这个包将被直接丢弃，后续规则也就没有必要被检查了。
``RETURN``表示不再检查当前所在的链的剩余规则，而返回上一层链的规则继续检查。
如果当前链是内建链的话，则由这条链的默认规则决定命运。

以上信息都可以通过 ``man iptables`` 获取到。

如果没有看懂这段内容也没有关系，等看过的规则、脚本比较多时，自然会理解这些内容。

### 一个简单的网关/防火墙配置

首先给出一个非常简单的网关配置脚本。然后我们再在其上面进行加工，增加功能。

    :::sh
    #!/bin/bash

    iptables -F
    iptables -X
    iptables -t nat -F
    iptables -t nat -X

    iptables -P INPUT DROP
    iptables -P OUTPUT ACCEPT
    iptables -P FORWARD DROP

    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

    # allow connections from lan
    iptables -A INPUT -i $IFACE_LAN -j ACCEPT
    # allow lan-to-anywhere forward
    iptables -A FORWARD -i $IFACE_LAN -j ACCEPT

    iptables -t nat -A POSTROUTING -o $IFACE_WAN -j MASQUERADE

这段代码只比[上一篇]({filename}2014-05-28-building-a-gateway-vlan.md)中的例子多了几行，
但对于网关来说会安全许多。我们简单分析一下这段代码。

前四行表示清空filter表和nat表中的所有规则，并删除所有用户自定义的链。
一般iptables的脚本都会在开头加上这几行，这样脚本就可以反复执行。
但是注意不要直接手动运行这几行，可能会导致断网，
一般写在脚本里可以一气呵成一下子运行，不会产生严重后果。

接下来三行配置了filter表内置链的默认策略。
``INPUT``表示对网关本身的访问，这里也就是默认不允许任何任何人访问网关本身。
``OUTPUT``表示网关访问其他机器，这里表示默认允许网关访问所有其他地址。
``FORWARD``是重点，所有由网关转发的包，默认全部丢弃，也就是默认不做转发。

接下来这两行比较特殊，表示放行所有已经建立的连接。
iptables处理时面对的单位是包（packet），而不是连接。
然而正常的通信都是双向的，例如从网关访问google.com，google.com响应的包对于网关来说就是INPUT，
按照前面的默认策略设置，这个包会被丢弃，于是网关出站的包虽然被放行了，但是入站的包都被丢了，实际上还是不能访问。
好在，常见的协议tcp是有状态的，udp虽然本身没有状态，但一般也可以根据四元组来判定连接状态，
而Linux的状态模块（``nf_conntrack``）也确实这么做了。
这里，当网关访问google.com时，发起了tcp SYN请求，状态系统标记了这是一个连接，
之后google.com返回的包（四元组相同）被标记为同一个连接，并且状态是RELATED或者ESTABLISHED，
这个包就会被放行。

可以这样理解，设置内置链的默认规则之后，实际上网关既无法联网，也不转发数据。
加上这两条规则之后，后续只需要关注任何连接的发起状态，只要某个请求的第一个包被后续的某条规则放行了，
那么整个这个连接都会被放行。

再接下来的两行：

    :::sh
    iptables -A INPUT -i $IFACE_LAN -j ACCEPT
    iptables -A FORWARD -i $IFACE_LAN -j ACCEPT

这里第一行允许内网的机器访问网关，这一条不是必须的，可以根据自己的实际需求配置。
接下来是放行所有从内网发起的转发请求，到这里位置，网关就可以正常转发包了。

最后一行我们上一篇中见过，只是换了一种方法。这一行的作用是NAT，准确的说是源地址转换（SNAT）。
与``-j SNAT --to-source $wan.ip``不同的是，``-j MASQUERADE``可以自动判断出口网卡的ip。
此外，当相应的wan口闪断时，``-j SNAT``所跟踪的连接会被保留，
而``-j MASQUERADE``会默认这个wan口不是静态ip，也就是每次断链恢复后ip会变，
每次断连后，连接状态都会被重置。因此推荐：

* 如果使用静态ip做上联（例如运营商提供的专线服务一般都是静态ip）推荐使用``-j SNAT``
* 如果是通过某种方式自动获取ip（如dhcp、pppoe等），推荐使用``-j MASQUERADE``
* 在使用静态IP时，如果断连并不常发生，并且不在乎闪断后所有连接被重置，那么也可以用``-j MASQUERADE``，以简化配置

至此，这样一段简单的脚本就实现了最基本的网关和防火墙，安全性也比较高。
接下来我们会介绍一些iptables的技巧，以及在实践中网关会遇到的一些问题的解决方法。

### 使用Zone来简化配置

``Zone``并不是iptables的概念，而是我从openwrt的iptables配置中“偷”来的概念。

在一个不太小的网络环境里，往往有多个内网和多个公网上联，还可能有多个vpn连接。
不同的网络在网关上反映出来的就是不同的interface。
而每一类的iface往往有相似或者相同的配置。例如我们要允许所有的内网网口访问网关本身，
按照前面的做法，假设vlan0010-vlan0025是16个不同的内网网段（iface），那么需要写16行的规则：

    :::sh
    iptables -A INPUT -i vlan0010 -j ACCEPT
    iptables -A INPUT -i vlan0011 -j ACCEPT
    ...
    iptables -A INPUT -i vlan0025 -j ACCEPT

如果会一些bash的技巧，可以简化成这样的语句：

    :::sh
    for i in seq 10 25; do
        iptables -A INPUT -i vlan00$i -j ACCEPT
    done

iptables提供了一种伪glob的方式，也可以这样写:

    :::sh
    iptables -A INPUT -i vlan001+ -j ACCEPT
    iptables -A INPUT -i vlan002+ -j ACCEPT

这两条命令会对vlan0010-vlan0029这20个vlan iface都生效，因此这种用法具有局限性。

如果只是上面这一条语句可能问题重复多行无所谓，但是如果有个规则需要对所有内网网卡配置，
那么就很麻烦了，有时候也容易遗漏配置。在openwrt中则使用了非常巧妙地方法，``Zone``。

这里，我们将网卡按照规则分类，每一类称为一个Zone。我们为每一个zone创建一个链，
然后在系统链的开头处让所有的包都按类别进入不同的Zone中，这样后续的规则就可以只写一条了。
例如：

    :::sh
    # 创建一个Zone表示内网，取名为Lan，创建一个chain用于接受INPUT
    iptables -N ZoneLanInput
    iptables -A INPUT -i vlan001+ -j ZoneLanInput
    iptables -A INPUT -i vlan002+ -j ZoneLanInput

    # 允许内网访问网关
    iptables -A ZoneLanInput -j ACCEPT

当然，由于系统的链很多，所以我们其实要创建多个链，于是可以写两个helper函数：

    :::sh
    # 为每一个Zone创建多个chain，这里由于我后续的规则只用到
    # filter-INPUT, filter-FORWARD, nat-POSTROUTING 这三个链，
    # 所以也仅创建三个链来承接
    create_zone() {
        local zonename=$1
        iptables -N Zone${zonename}Input
        iptables -N Zone${zonename}Forward
        iptables -t nat -N Zone${zonename}Postrouting
    }

    add_to_zone() {
        local zonename=$1; shift
        local iface=
        for iface in $@; do
            iptables -A INPUT -i $iface -j Zone${zonename}Input
            iptables -A FORWARD -i $iface -j Zone${zonename}Forward
            iptables -t nat -A POSTROUTING -o $iface -j Zone${zonename}Postrouting
        done
    }

这样脚本就可以这样写了：

    :::sh
    create_zone Wan
    add_to_zone Wan pppoe-lt pppoe-kdt vlan0002 tun+
    create_zone Lan
    add_to_zone Lan vlan001+ vlan0020 vlan0021 vlan0022 vlan0023 vlan0024 vlan0025

    # 允许内网访问网关
    iptables -A ZoneLanInput -j ACCEPT
    # 允许lan-to-anywhere的转发
    iptables -A ZoneLanForward -j ACCEPT

    # 对所有公网网卡全都做``-j MASQUERADE``
    iptables -t nat -Z ZoneWanPostrouting -j MASQUERADE

在以后，如果添加了新的iface，则只需要将这个iface加入到相应的zone当中即可。

### NAT配置
NAT分为SNAT和DNAT，由于公网地址短缺，内网的机器要上网都要经过SNAT，而通常说的端口映射一般仅需要DNAT。
这里我不打算赘述SNAT和DNAT的作用，只要知道通信的四元组，基本都能把问题想清楚。
这里主要介绍我配置NAT的一些脚本。

首先，配置SNAT的命令前面都已经见过了：

    :::sh
    # 这里的$lanaddr/$wanaddr可以是单纯的ip地址，也可以是ip:port
    iptables -t nat -A POSTROUTING -o $waniface -s $lanaddr -j SNAT --to-source $wanaddr

配置DNAT的命令十分相似，不过DNAT是在PREROUTING阶段做的：

    :::sh
    iptables -t nat -A PREROUTING -d $wanaddr -j DNAT --to-destination $lanaddr
    # 由于我们之前配置默认不允许从外部对内部主动发起访问，所以需要添加规则
    iptables -A FORWARD -s $wanaddr -d $lanaddr -j ACCEPT

当我们添加/修改了一个NAT规则之后，并不是很愿意重新执行整个iptables脚本。
我们许多时候总是喜欢让（部分）脚本是可重复执行的，自定义chain是我们的好朋友。

    :::sh
    setup_nat_chains() {
        while read table builtin_chain user_chain; do
            if iptables -t $table -n --list "$user_chain" >/dev/null 2>&1; then
                iptables -t $table -F $user_chain
                iptables -t $table -D $builtin_chain -j $user_chain >/dev/null 2>&1 || :
                iptables -t $table -X $user_chain
            fi
            iptables -t $table -N $user_chain
            iptables -t $table -A $builtin_chain -j $user_chain
        done <<EOF
    filter FORWARD     PortmapFilterForward
    nat    PREROUTING  PortmapNatPrerouting
    nat    POSTROUTING PortmapNatPostrouting
    EOF
    }

这个函数的作用，创建三个chain（分别是SNAT、DNAT的配置中涉及到的三个builtin chain。
这个函数被调用时，首先判断三个自定义的chain是否存在，如果存在则删除并重建，
如果不存在则直接新建。

然后是两个helper函数：

    :::sh
    dnat() {
        local waniface=$1
        local wanaddr=$2
        local lanaddr=$3
        [[ -z "$waniface" || -z "$wanaddr" || -z "$lanaddr" ]] && return
        iptables -A PortmapFilterForward -i "$waniface" -d $lanaddr -j ACCEPT
        iptables -t nat -A PortmapNatPrerouting -d $wanaddr -j DNAT --to-destination $lanaddr
    }

    snat() {
        local waniface=$1
        local lanaddr=$2
        local wanaddr=$3
        [[ -z "$waniface" || -z "$wanaddr" || -z "$lanaddr" ]] && return
        iptables -t nat -A PortmapNatPostrouting -o "$waniface" -s $lanaddr -j SNAT --to-source $wanaddr
    }

    o2onat() {
        # 1:1映射，我们在后面会讨论
        local waniface=$1
        local wanaddr=$2
        local lanaddr=$3
        dnat $waniface $wanaddr $lanaddr
        snat $waniface $lanaddr $wanaddr
    }

    portmap() {
        # 端口映射，其实就是dnat()，不过仅用于TCP/UDP协议，因为其他协议可能没有端口的概念
        local waniface=$1
        local wanaddr=$2
        local wanport=$3
        local lanaddr=$4
        local lanport=$5
        [[ -z "$waniface" || -z "$wanaddr" || -z "$wanport" || -z "$lanaddr" || -z "$lanport" ]] && return
        iptables -A PortmapFilterForward -i "$waniface" -d $lanaddr -p tcp --dport "$lanport" -j ACCEPT
        iptables -A PortmapFilterForward -i "$waniface" -d $lanaddr -p udp --dport "$lanport" -j ACCEPT
        iptables -t nat -A PortmapNatPrerouting -d $wanaddr -p tcp --dport $wanport -j DNAT --to $lanaddr:$lanport
        iptables -t nat -A PortmapNatPrerouting -d $wanaddr -p udp --dport $wanport -j DNAT --to $lanaddr:$lanport
    }

那么所有关于nat/端口映射的设置都可以抽象出一个脚本来``setup-nat.sh``：

    :::sh
    setup_nat_chains
    portmap vlan0002 1.2.3.4 1234 192.168.10.101 1234
    portmap vlan0002 1.2.3.4 8080 192.168.10.101 80
    ...

这个脚本可以单独重复运行。

#### 同网段内网无法访问DNAT端口

这个问题说起来有些拗口，为了方便描述，我们做如下约定：

* 有两个内网，分别为``192.168.1.0/24``, ``192.168.2.0/24``
* 有一个公网，网关拥有的IP为``1.2.3.4``
* 配置了一条端口映射，用上述脚本为：``portmap $waniface 1.2.3.4 8080 192.168.1.100 80``

在这个情形下，我们发现：

* 从外网访问 ``1.2.3.4:8080`` 可以访问到内网的 ``192.168.1.100:80``
* 从``192.168.2.0/24``网内的所有机器也都可以通过``1.2.3.4:8080``访问到``192.168.1.100:80``，这符合预期
* 但是从``192.168.1.0/24``中的任何机器都无法通过``1.2.3.4:8080``访问到预期的``192.168.1.100:80``

我们不妨用四元组``(srcip, srcport, dstip, dstport)``来做一个简单的分析。

* 例如从``192.168.1.123:1234``发起请求，四元组为 ``(192.168.1.123, 1234, 1.2.3.4, 8080)``
* 网关机器收到该请求，进行了DNAT，四元组变为``(192.168.1.123, 1234, 192.168.1.100, 80)``
* 此时``192.168.1.100``收到了这个请求，四元组为``(192.168.1.123, 1234, 192.168.1.100, 80)``
* ``192.168.1.100``进行回复时，回复的包四元组为``(192.168.1.100, 80, 192.168.1.123, 1234)``
* 该回复包由于目的地与源在同一个网段，因此这个包不会交给网关，而是直接投递给了``192.168.1.123``
* ``192.168.1.123``此时正期待收到来自``1.2.3.4:8080``的回复，但收到了``192.168.1.100:80``的包，
  后者这个包对其来说是垃圾包，直接被丢弃，于是整个通信失败。

问题很清楚了，那么如何解决呢？很简单，对于这个问题，我们在做DNAT的同时也做一个SNAT，在``portmap()``
函数的末尾加上两行代码，下面是完整的代码：

    :::sh
    portmap() {
        local waniface=$1; local wanaddr=$2; local wanport=$3; local lanaddr=$4; local lanport=$5
        [[ -z "$waniface" || -z "$wanaddr" || -z "$wanport" || -z "$lanaddr" || -z "$lanport" ]] && return
        iptables -A PortmapFilterForward -i "$waniface" -d $lanaddr -p tcp --dport "$lanport" -j ACCEPT
        iptables -A PortmapFilterForward -i "$waniface" -d $lanaddr -p udp --dport "$lanport" -j ACCEPT
        iptables -t nat -A PortmapNatPrerouting -d $wanaddr -p tcp --dport $wanport -j DNAT --to $lanaddr:$lanport
        iptables -t nat -A PortmapNatPrerouting -d $wanaddr -p udp --dport $wanport -j DNAT --to $lanaddr:$lanport

        # 获取内网的网段，这里假设内网都是/24的网段，根据实际情况修改代码
        local lannet=$(echo $lanaddr | sed 's/\.[^.]\+$/.0/')/24
        # 如果一个端口映射访问来自同网段，则同时进行SNAT
        iptables -t nat -A PortmapNatPostrouting -s $lannet -d $lanaddr -j SNAT --to-source "$wanaddr"
    }

我们再利用四元组来讨论:

* 例如从``192.168.1.123:1234``发起请求，四元组为 ``(192.168.1.123, 1234, 1.2.3.4, 8080)``
* 网关机器收到该请求，进行了DNAT，四元组变为``(192.168.1.123, 1234, 192.168.1.100, 80)``
* 这个包在走出网关的前一刻，又进行了SNAT，四元组变为``(1.2.3.4, 1234, 192.168.1.100, 80)``
* ``192.168.1.100``收到这个请求，回复时四元组变为``(192.168.1.100, 80, 1.2.3.4, 1234)``
* 这个包被投递给了网关，网关自动进行了反向转换，这个四元组最终变为``(1.2.3.4, 8080, 192.168.1.123, 1234)``
* 这个包最后返回到``192.168.1.123``，并且四元组符合预期，通信成功。

同样，对于``dnat()``函数也需要进行相应的修改，这里不再列出代码。

#### 路由设置导致端口映射配置失效

在有多个ISP上联时，这是非常常见的问题。不仅端口映射的配置会失效，正常的访问也会出问题。
我们这里以端口映射作为例子。

场景设置：

* 内网机器A，IP为``192.168.1.100``，记为IPa
* 网关G接两个ISP上联，IP分别为IPg1和IPg2
* 公网有一台机器B，IP为IPb
* 网关上配置了端口映射``portmap $IFACE_G1 IPg1 8080 IPa 80``
* 网关上配置了策略路由，使得所有从IPa发出的对外请求的包都从GW2出去，我们下一篇再将具体的配置方法

在这个场景下，当B主动通过映射的端口向A发起请求，情景如下：

* B发出请求，四元组``(IPb, 1234, IPg1, 8080)``
* G收到数据包，进行DNAT，变成了``(IPb, 1234, IPa, 80)``
* A收到了这个数据包，发出回复包，``(IPa, 80, IPb, 1234)``
* 网关进行路由，选择从G2发送出去，然后反解DNAT，得到``(IPg1, 8080, IPb, 1234)``
* 由于网关从G2出去，但源地址确是IPg1，许多上联网关会拒绝这个数据包，于是通信失败

这个问题无法通过增加SNAT来解决。因为反解SNAT是在选择路由之前进行的，因此对路由没有任何影响。
这里仅可以通过给连接打标记配合策略路由来解决，这一篇中暂时不给解决方法，在下一篇中再给出。
等不及的小伙伴可以从这篇文章中找答案：
[端口映射的两个坑](https://boj.blog.ustc.edu.cn/index.php/2014/02/port-mapping-fallacies/#comment-539)。

### 修复mss

如果使用了一些隧道，比如vpn、gre等，有时候会发现访问不了许多网站。
具体现象是可以与网站建立连接，并发送请求，但收数据时卡着不动，
用curl的现象如下：

    :::sh
    curl -v http://baidu.com
    * Rebuilt URL to: http://baidu.com/
    * * Hostname was NOT found in DNS cache
    * *   Trying 220.181.111.86...
    * * Connected to baidu.com (220.181.111.86) port 80 (#0)
    * > GET / HTTP/1.1
    * > User-Agent: curl/7.37.0
    * > Host: baidu.com
    * > Accept: */*
    * >
    *
    # 卡在这里等待服务器返回，但是最终超时

这种现象一般是由于mtu设置的问题造成的。用下图解释（来自cisco.com）：
{% img center /images/posts/building-a-gateway/gre-mss.gif %}

网关配置的内网iface一般mtu为1500，因此客户端自动配置得到的也是1500，
同理服务器获取到的mtu一般也为1500（其实具体是多少不重要）。
然而在网关和服务器的网关中间有无数种可能，其中最小的mtu可能小于1500。
当内网客户端向服务器发出请求时，第一个SYN包中会告知服务器客户端这边的mss（一般为mtu-40）。
服务器会根据自己情况告知客户端这个值可以接受或者需要配置较小的mss。
在上图的情形中，客户端与服务器约定了使用1460作为mss。
客户端发起HTTP请求时，请求的大小一般小于1460字节，所以可以正常的发送，而服务器返回的内容超过了1460字节，
所以就发送了一个1460字节的包，并且打上了DF标记（don't fragment），途径中间某个接口时，发现无法传送，
就会丢弃这个包，并向这个包的发送方返回一个icmp包（type 3 code 4），告知该问题，发送方收到这个包之后，
会根据需要修改mss重新发送内容。然而，在有些时候，这类的icmp包会被中间设备丢弃，导致服务器收不到。
我这里解释的比较粗糙，详细的解释参见
[cisco网站](http://www.cisco.com/c/en/us/support/docs/ip/generic-routing-encapsulation-gre/13725-56.html)。

知道了问题，也就有解决方案。
其中一个是配置内网的客户端，使得所有客户端iface的mtu都设置成网关上所有iface中最小的mtu，例如设置成1400。
但是这个方案很不灵活，需要手动计算最小的mtu，当增加新的iface时，可能都需要调整。
另一种方案就是悄悄修改所有tcp的SYN包，将其中的MSS设置为一个合理的数值。
这种修改类似于NAT，不过NAT修改的是四元组，而这里需要修改包里的内容。所以这个操作需要在mangle表中进行。


    :::sh
    iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-mptu

### 1:1映射

在NAT一节我们主要讨论了DNAT/SNAT，还有端口映射，同时我们也给出了一个函数``o2onat()``，
也就是1:1映射，有些地方成为``DMZ``。从代码知道，其实1:1映射就是同时进行DNAT和SNAT
（其实在普通路由器上因为只有一个公网IP，所以DMZ其实只需单独配置一条DNAT规则即可）。
什么时候会有用呢？

企业申请ISP的专线时，一般会获得多个公网IP，例如我们获得了16个IP。那么这些公网IP如何使用呢？
一般有两种方案。（运营商可能会配置一对保留IP做互联IP，有的不提供互联IP，
有一些小差别，我们假设有互联IP的情况来讨论。）

假设某运营商提供了16个公网IP，分别为a.b.c.16-a.b.c.31，互联IP分别为192.168.1.1, 192.168.1.2。

方案一如下图：
{% img center /images/posts/building-a-gateway/topo1.jpg %}

在这种方案中，使用a.b.c.17作为内网大多数机器访问外网时的源IP，也就是给大家当SNAT的源地址使用。
而需要使用外网IP的机器则需要加入vlan3，并配置一个公网IP。这种方式很明显有这些缺点：

* 使用不灵活，需要使用公网IP的机器都需要加入特定的VLAN，如果不哪天不需要使用时还需要修改网络配置。
  当有内网机器要添加或者去除公网IP时，会改变这台机器在内网的拓扑。
* 有16个公网IP，但是却只能用14个，有两个IP（.16和.31，分别是全0和全1）无法使用。
  但是这里的全0和全1的IP仅对这个/28的网段有意义，在公网上，没有人会认为这是全0或者全1的ip，
  跟普通的ip没有区别，所以其实都可以使用。
* 能够接触到vlan3的所有主机，都可以使坏，私自配置公网IP，导致公网IP管理困难。

方案二则会灵活很多：
{% img center /images/posts/building-a-gateway/topo2.jpg %}

在这种方案中，并不直接将公网IP配置到具体某一台设备上，而是通过配置1:1映射来配置。
这样就带来了许多好处：

* 配置灵活，只需要配置一条1:1映射的规则，即可将某个公网IP配置到内网的某一设备上，回收IP进去取消这条规则。
* 所有公网IP（其实是所有运营商会路由过来的IP）都可以充分利用。
* 内部设备无法配置自己的公网IP，不会出现管理混乱的情况。

许多云主机厂商都如此设计网络，例如ec2。
除了上述好处外，还有许多其他好处，例如可以在网关上集中配置所有拥有公网IP机器的防火墙规则，
如果有安全需求也可以仅作DNAT而不做SNAT，同时这种拓扑在云集群应用中也更容易搭建虚拟网络。
所有的设备都可以在相同的内网中，无论该设备是否拥有公网IP，这就组成了一个子网。
对某些设备添加公网IP只是像贴标签一样简单，不会影响内网的网络拓扑。

在后续讲到路由时，我们还会发现第二种方案会更容易配置路由策略，可以有更灵活的应用。

因此，在实践中，如果没有特殊需求，比较推荐使用第二种方案。
在管理大型集群时，第二种方案优势会格外明显。
（试想有一个上千台主机的集群，但只有几十个公网IP时，如何管理使用公网IP。）

### 对付运营商劫持的问题

这个在以前的[一篇文章]({filename}2013-12-19-escape-isp-http-hijacking.md)中已经提到过了，
这里不再展开，仅列出链接。

### 小结

iptables有许多功能，这里只是用了冰山一角。
那么如何快速一窥iptables的能力呢？查看``iptables-extensions``的manpage：

    :::sh
    man iptables-extensions

iptables扩展主要有两部分，一部分是有许多``match extensions``，用来做匹配条件。
例如在对付运营商劫持的方法中使用了``-m string --string "Location: ..." --algo bm``，
这里使用了``string``这个``match extension``。
在本文中也大量使用了``-m state --state ...``，即``state``这个``match extension``。
另一部分是定义了许多``TARGET``，也就是如何处理这些包。
这些``TARGET``一般对应一些代码，用来修改包的内容。
例如``-j SNAT --to-source ip:addr``，即``SNAT``这个``TARGET``可以用来修改包的源地址。
再比如使用``-j TCPMSS --clamp-mss-to-mptu``来修改TCP SYN包中的mss option字段。

当看到一条iptables命令不知道其什么作用时，查阅``iptables``或者``iptables-extensions``
的manpage通常都可以得到答案。

在下一篇中我们将介绍路由。网关的重要职责就是路由，所以路由也是最精彩的部分，尽请期待:-)
