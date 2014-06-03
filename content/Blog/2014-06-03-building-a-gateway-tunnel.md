Title: 搭建网关系列 —— 隧道篇
Tags: gateway, debian, tunnel

在中国特色的网络里，使用vpn/openvpn连接国外的服务器十分不稳定，
无奈之下一些人会使用obfsproxy等作为openvpn的底层传输工具，
目前obfs3还算是比较稳定的，我在公司使用了一段时间并没有发现问题。
不过在家里搭建网关时发现，无论是openvpn还是obfsproxy都是很消耗CPU的，
这也是在有了一个dir825之后又买了一个minipc做网关的主要原因。

我们今天将介绍几种常见的ip隧道，包括``ipip``、``gre``、``sit``
（因为我正在用这三个），根据实践发现目前使用``gre``隧道与国外服务器连接很稳定，
没有发现被干扰的迹象。

大多数隧道都需要两端都有公网IP，这里提到的三种也不例外。
所以如果isp没有提供公网IP的话基本就没戏了，
如果使用pppoe，但能获得公网IP也是可以使用隧道的。

### 命令初识

使用``iproute2``套件创建隧道的命令都是一样的，只有很少的参数不同，所以学习成本很低。

我们首先贴一段真实的命令来看。以下命令在隧道的一端执行，
另一端执行的命令几乎完全相同，仅仅需要涉及到的IP交换一下。

    :::sh
    ip tunnel add tun0 mode ipip remote 1.2.3.4 ttl 255
    ip addr add 192.168.0.1/32 dev tun0
    ip link set tun0 up
    ip route add 192.168.0.2/32 dev tun0 scope link src 192.168.0.1

创建gre隧道时，只需要将``mode ipip``改成``mode gre``即可，
创建``sit``隧道时一样，不过``sit``隧道中使用ipv6通信，
所以后面设置ip和路由时也需要相应的修改。

#### 基本概念

所谓ip隧道，就是将普通的ip包封装到另外一个ip包里面，其实各种vpn也是都是隧道，
不同类型的隧道，主要区别是封装的内容、格式不同，在
[网络虚拟化技术大观](https://boj.blog.ustc.edu.cn/index.php/2014/02/network-virtualization-techniques/)
这篇文章中有很详细的介绍。
简单的说，通常一个隧道有三层，Encap层、Shim层、Payload层。
Encap层也可以理解为传输层，也就是传输层使用什么，ipip隧道一般使用ip，
openvpn使用tcp或udp。Shim层可以理解为metadata，一般可以控制是否加密，是否有序列号等。
Payload就是内容，ipip和gre隧道放的是ip包，openvpn的tap模式放的是mac包（所以也支持arp等功能）。

ipip和gre隧道，其Encap层使用的是IP包，所以就需要有通信双方的ip，又叫endpoint，
在配置时，本地的公网IP叫local endpoint，可以省略，其功能主要是bind到某个具体的iface上。
远程的公网IP叫remote endpoint。
其Payload也是IP包，所以这个tunnel担当了路由中的一跳，为了配置路由，这两端都需要配置ip，
这一对IP称为virtual ip，下面简写为``vip``，
相应的，在配置时就分别称为remote vip和local vip。
vip可以是任何ip，两端不需要在相同的网段，一般配置的都是一个``/32``的单独ip。
通常使用保留ip作为vip，不会使用一个可在公网使用的ip作为vip。

#### 命令解释

我们再贴一下前面创建隧道的命令：

    :::sh
    ip tunnel add tun0 mode ipip remote 1.2.3.4 ttl 255
    ip addr add 192.168.0.1/32 dev tun0
    ip link set tun0 up
    ip route add 192.168.0.2/32 dev tun0 scope link src 192.168.0.1

这里，remote endpoint的ip为1.2.3.4，local vip为192.168.0.1/32，
remote vip为192.168.0.2/32。

第一行的作用是创建一个隧道，创建时没有指定local endpoint，如果需要的话
加上参数``local a.b.c.d``即可。
这一行执行完后，系统里就会多出一个名为``tun0``的interface。
这里名字可以是任意的，不一定要是``tun0``，比如我网关上的一个隧道的名字是
``gre-sg-lt``，表示这事一个gre隧道，对端在新加坡，本端使用联通出口，
当隧道比较多时，这样命名比用``tun0``更易于管理。
在隧道两端，interface的名字不必相同，可以随意，比如我在服务器端相应隧道的名字是
``gre-homelt``，表示隧道对端是我家里的联通。

第二行是为新建的这个interface配置vip，这里添加了一个/32的ip。

第三行是up这个interface，也可以用``ifconfig``来做：``ifconfig tun0 up``。

第四行是增加一条路由，使得remote vip从这个隧道走。隧道两边都执行这组命令后
（注意交换两端的endpoint和vip），就可以互相ping同对端的vip了。

接下来，如果要使用这个隧道，可以正常添加路由规则了，例如：

    :::sh
    ip route add 8.8.8.8 dev tun0

一个小Tip：使用这类隧道的路由命令可以不写``via $remotevip``，
因为这种隧道不支持arp，这个interface在逻辑上只与一个节点相连，所以``via``就是多余的。
如果是接到一个tap上面（如openvpn的tap模式），其实就是接到一个交换机上，
必须要指定下一跳的ip。

注意，这里仅仅是创建了一个tunnel，tunnel两端可以互相通信，
但如果要访问两端以外的地方，例如当vpn用，那么对端就是一个网关，需要进行必要的配置，
如：

    :::sh
    sysctl -w net.ipv4.ip_forward=1
    iptables -t nat -A POSTROUTING -s $remotevip/32 -j MASQUERADE

#### 没有固定公网IP时使用隧道

在家里使用pppoe，每次获得的公网ip都不相同，如果每次断连之后都要到服务器手动创建隧道的话
不免有些麻烦，所以我们就写一个脚本放在服务器上，每次公网ip发生变化之后，就"ping"一下服务器，
告诉这个脚本最新的ip，重新创建隧道。

这里如何"ping"呢，方法有许多许多，可以写个daemon程序，监听一个端口，也可以写个cgi程序，
通过http调用。我这里使用ssh，方便又安全，只需要写一个创建tunnel的脚本，
脚本里不需要关心任何其他事情，而ssh本身自带了很好的加密，因此也不用担心安全的问题。

这个脚本需要以root权限执行，所以我们也不用麻烦配置sudo了，直接ssh root@xxx来运行最方便。
既然是脚本肯定不能使用密码交互，我们使用rsa-key来验证身份。
ssh的authorized_keys可以限制某个key登陆后只能执行特定的命令，
只需要在``/root/.ssh/authorized_keys``中相应key的开头增加以下内容：

    :::
    no-port-forwarding,no-X11-forwarding,no-agent-forwarding,command="/root/create-tunnel.sh"

    # 完整的样例：
    no-port-forwarding,no-X11-forwarding,no-agent-forwarding,command="/root/create-tunnel.sh" ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCrk5wDGXELhOIYhqAwJxTv94vkOS9TuLKMCz5iXLmwsEh4SujDkfxeAiOMBYAmh728+gHwPRTCAdPKUCrK3lEf4XYdbYd52nUwdehygxI++SXcde91jyXkMqLdT7NFC1IXSESK6Z6eSV03TqTn7gYp9YjDvkbEA7JjTjlXTOdxHscSEa4gLdbWY7lmFs3vo0TvAjuGeWhP2yO4y8PZ5dBfXuOjwcKI3BEn199U6tsDBKlJGYYq0XdU4aaXqSO9yCQXc6M1KmAPM6q4Qu0ovghT0/WVSM9Ag6VcojZgOwRRhquLRZHJ/oVcVyvaj2wJDAF9yrLuuzaVjeYLpOV/Y8bF user@example.com


使用这个key登陆后，不允许任何端口转发，且仅能执行``/root/create-tunnel.sh``这个命令，
所以安全性可以进一步得以保证。

然后是``create-tunnel.sh``这个脚本。

    :::sh
    #!/bin/bash

    set -e

    # this script should only be run on server side
    # this script is supposed to be invoked by ssh-key allowed command
    # save this script as /root/create-tunnel.sh
    # usage: ./create-tunnel.sh mode name remote-endpoint remote-vip local-vip

    init_chain() {
        local table=$1
        local upstream_chain=$2
        local chain=$3

        if iptables -t $table -n --list $chain > /dev/null 2>&1; then
            iptables -t $table -F $chain
            iptables -t $table -D $upstream_chain -j $chain >/dev/null 2>&1 || :
            iptables -t $table -X $chain
        fi
        iptables -t $table -N $chain
        iptables -t $table -A $upstream_chain -j $chain
    }

    create_tunnel() {
        local mode=$1
        local name=$mode-$2
        local remote=$3
        local remotevip=$4
        local localvip=$5

        [[ -z "$mode" || -z "$name" || -z "$remote" || -z "$remotevip" || -z "$localvip" ]] && return

        # 如果tunnel已经存在，则删除之
        ip tunnel del $name 2>/dev/null || :
        # 创建tunnel
        ip tunnel add $name mode $mode remote $remote ttl 255
        ip addr add $localvip/$CIDR dev $name
        ip link set $name up
        ip route replace $remotevip/$CIDR dev $name scope link src $localvip

        # 直接向"-t nat -A POSTROUTING"中添加规则并不好，难以维护，
        # 将来也难以删除旧的规则，所以用上老伎俩，创建一个单独的chain来做这个事。
        # 如果不需要NAT的话，这个配置也就不需要了
        init_chain nat POSTROUTING $name
        iptables -t nat -A $name -s $remotevip/$CIDR -j MASQUERADE

        echo "[$(hostname -f)] created $mode tunnel: $name"
    }

    if [ -z "$SSH_CONNECTION" ]; then
        create_tunnel $@
    else
        create_tunnel $SSH_ORIGINAL_COMMAND
    fi

这样只用执行以下命令即可完成远端的配置：

    :::sh
    ssh -i /path/to/private/key root@remote $mode $name $local-endpoint $localvip $remotevip

需要注意的是，这个命令参数里的``$local-xx``和``$remote-xx``，在对端执行时语义的对调。
这里的``$mode``可以是``ipip``或者``gre``，命令都完全一样，只不过里面封装的内容不一样。

### sit隧道

``gre``隧道是可以封装ipv6数据包的，所以其实我并不需要``sit``隧道。
不过由于我在校园网的一台服务器由于某种原因不支持``gre``隧道，所以我改而使用``sit``隧道。

``sit``隧道的使用方法与上述没有任何区别，仅仅是``$local-vip``和``$remote-vip``只能使用
IPv6地址（在``gre``隧道上，可以分别有v4和v6的``$local-vip``/``$remote-vip``）。

这里再啰嗦一下创建sit隧道的命令：

    :::sh
    ip tunnel add sit-xxx mode sit remote 1.2.3.4 ttl 255
    ip addr add 2001:abcd::1/128 dev sit-xxx
    ip link set sit-xxx up
    ip route add 2001:abcd::2/128 dev sit-xxx scope link src 2001:abcd::1

在使用ipv6时，我们并不愿意使用NAT，不过不使用NAT的话，需要在ipv6提供方配置路由，
例如找校园网管理员分配一个/64的网段，路由到我的服务器上，然后我再路由回我家里的网络。
有了/64的网段，才可以使用radvd来自动配置ipv6。
可是这操作起来有一些麻烦，校园网管理员也未必会满足我的请求，于是我使用了NAT（好吊丝，都ipv6了还NAT……），
配置方法跟ipv4没有任何区别：

    :::sh
    ip6tables -t nat -A POSTROUTING -o sit-xxx -j MASQUERADE

在内网的网卡上增加了一个ip： ``fc00::1/64``，然后配置radvd，使得内网使用这个网段自动配置：

    :::sh
    interface $lan-iface
    {
        AdvSendAdvert on;
        prefix fc00::/64
        {
            AdvRouterAddr on;
        };
    };

### 小结

隧道创建好之后，其实就可以简单的理解为在网关上多了一个网卡（interface），
因此如何使用tunnel就不需要多说了，前面的iptables篇和路由篇涵盖了大多数所需的知识了。

至此，我的搭建网关系列的文章也就完结了，可以说基本覆盖了我在搭建过程中使用到的所有工具。
这个网关可以用在家庭小型网络，也可以用在几百人甚至上千人的中型网络，
上万人的网络也未尝不可，只是由于带宽更大，ISP接入的方式更多，所以需要更好的硬件
（可能使用硬件路由器）以及会碰到更多的路由协议、通信协议。这里就不讨论了。
