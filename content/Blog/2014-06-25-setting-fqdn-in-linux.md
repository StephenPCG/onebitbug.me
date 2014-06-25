Title: Linux下配置FQDN
Slug: settings-fqdn-in-linux
Tag: hostname, fqdn, debian, linux

近来可能博客有一些多，闲在家里，把过去两年里碰到的一些问题都总结一下，
写点文章，刷一下存在感。

主机名是我进入云成后碰到的第一个比较棘手的问题，所谓棘手，
是指折腾了很久没搞明白是怎么回事。
“主机名”，往细节里说主要有两种，一种是hostname，一种是fqdn。
一般来说hostname是短名字，不含``.``。
通常hostname在某个特定的范围内应该是唯一的，以免产生冲突，
这个特定的范围通常用域（dnsdomain）表示。
而fqdn（full qulified domain name）则应该在一个更大的范围内（比如全球）唯一，
通常fqdn是${hostname}.${dnsdomain}。
下面讨论时会尽量避免使用“主机名”，而使用``hostname``、``fqdn``和``dnsdomain``。

不过在不同的发行版里，设置hostname和fqdn的方法并不完全相同，甚至十分混乱。
比如在ArchLinux中，``/etc/hostname`` 中直接填写fqdn，而其他大多数发行版里，
``/etc/hostname``中写的都是hostname。
通常Linux发行版中并不存在一个配置文件或者配置选项可以直接设置fqdn。
在``man hostname``中的``FQDN``一节给出了解释：

    :::text
    Technically: The FQDN is the name getaddrinfo(3) returns for  the  host
    name returned by gethostname(2).  The DNS domain name is the part after
    the first dot.

    Therefore it depends on the configuration of the resolver  (usually  in
    /etc/host.conf) how you can change it. Usually the hosts file is parsed
    before DNS or NIS,  so  it  is  most  common  to  change  the  FQDN  in
    /etc/hosts.

也就是说，``dnsdomainname``通常不由本地配置，而应该由DNS服务来指定。
不过由于几乎所有的发行版都默认配置为，解析域名时优先查找``/etc/hosts``，
然后再去外部DNS服务器查询，所以通常我们可以在``/etc/hosts``中通过某种方式
配置``dnsdomain``，而不管外部DNS服务器如何设置。

## 如何设置hostname和fqdn

首先是hostname。hostname是一个内核里的属性，通过``gethostname()``、
``sethostname()``这两个system call来读取和设置。
``hostname``这个命令行工具是对这个功能的封装。
我们可以随时通过``hostname``这个命令行工具获取和设置hostname。
在系统开机时，通常有一个系统服务来读取``/etc/hostname``文件，
并将内容设置为hostname。在Debian中这个服务是``/etc/init.d/hostname.sh``。

所以，通常提到修改hostname时，都需要做两件事：

    :::sh
    # hostname foo
    # echo foo > /etc/hostname

第一步是修改当前系统里的hostname，第二步是使得重启后自动使用这个hostname。

然后是fqdn。在Debian的``man hostname``中有建议：

    :::text
    The  recommended  method of setting the FQDN is to make the hostname be
    an alias for the fully qualified name using /etc/hosts,  DNS,  or  NIS.
    For  example,  if  the  hostname was "ursula", one might have a line in
    /etc/hosts which reads

        127.0.1.1    ursula.example.com ursula

然而，在实践中，这样一条解释不够完整，我们下一段会分析几个常见的问题。

## 试玩/etc/hosts

在安装完Debian后，默认的配置如下：

    :::sh
    $ cat /etc/hostname
    foo

    $ cat /etc/hosts
    127.0.0.1 localhost
    127.0.1.1 foo.example.com foo
    <ipv6 related lines stripeed>

    $ hostname && hostname --fqdn
    foo
    foo.example.com

一切都符合预期。细心的朋友会注意到，``hosts``文件中第二行的ip是127.0.*1*.1，
而不是127.0.0.1，这是为何呢？

我们不妨将其改为127.0.0.1看看：

    :::sh
    $ cat /etc/hosts
    127.0.0.1 localhost
    127.0.0.1 foo.example.com foo

    $ hostname && hostname -f
    foo
    foo.example.com

看上去完全没有问题啊。可是这时候，我们看从python中用``socket.getfqdn()``会
读出什么来：

    :::sh
    $ python -c 'import socket; print socket.getfqdn()'
    localhost

通过查看python的源码
[Lib/socket.py:593](http://hg.python.org/cpython/file/default/Lib/socket.py#l593)
可以得知，python是这样获取fqdn的：

* 当没有设置``name``参数时（正是我们这里的情形），通过``gethostname()``来获得``hostname``，
  这里得到的是``foo``。
* 然后调用``gethostbyaddr(name)``函数，获得``hostname``, ``aliases``, ``ipaddrs``。
  根据``/etc/hosts``文件的规范，其格式为``IP_address canonical_hostname [aliases...]``，
  在python中，``gethostbyaddr()``首先找到``foo``的ip为``127.0.0.1``，然后找到``hosts``
  文件中第一个ip为``127.0.0.1``的行，即``127.0.0.1 localhost``，
  所以其返回值为：``('localhost', [], ['127.0.0.1'])``。
  然后再从hostname和aliases中选择一个含有``.``的名字返回，如果没有找到，则返回hostname。
  所以最终返回了``localhost``。

可以再做一个实验来验证这个结论，修改/etc/hosts文件的内容如下：

    :::sh
    $ cat /etc/hosts
    127.0.0.1 localhost
    1.2.3.4   bar.example.com
    1.2.3.4   foo.example.com foo

    $ hostname && hostname -f
    foo
    foo.example.com

    $ python -c 'import socket; print socket.getfqdn()'
    bar.example.com

Debian中的``hostname``命令的代码（抱歉没有找到可以在线浏览的链接）中，
是直接将``getaddrinfo(..., &res)``中的``res->ai_canonname``返回了，
我没有再跟进libc库中的``getaddrinfo()``的实现，
不过看上去它是直接在``/etc/hosts``中查找含有``foo``这个alias的行，并将该行的canonical name返回了。

这时候，我们可以理解为何Debian中默认不用``127.0.0.1``，而使用``127.0.1.1``了，
这是为了最大程度的兼容各种工具的的getfqdn()实现。

至此，得到一个结论，首先需要按照这个格式写上含有fqdn以及hostname的行：

    :::text
    $ip-address foo.example.com foo

然后要保证这个$ip-address在整个``/etc/hosts``中第一次出现。
通常来说，这个ip应该是一个可以使用的ip，即可以ping通，也可以用于连接，例如可以``ssh 127.0.1.1:22``。
对于Debian的安装程序来说，只有``127.x.x.x``是在安装过程时能够确定的可以使用的ip，
而习惯上大家都会将``127.0.0.1 localhost``放在第一行，所以Debian就选择了``127.0.1.1``来配置fqdn。

至此，Debian默认的设置似乎是完美的，不过我还是碰到了问题。

以前使用glassfish，发现glassfish启动会失败，报错信息大概是：

    :::text
    no free port, can not bind to ${port}

这里的``${port}``是在``domain.xml``中设置的监听端口，这时可以确认这个端口并没有被占用，
使用``nc -l ${port}``也可以正常监听。后来经过检查，发现java不知何原因，会从``hosts``
文件中查找``hostname``的行获取ip，并试图监听这个ip的相应端口。
``127.0.1.1``虽然可以用来连接，但却不能用来bind & listen。

所以，在配置fqdn这一行中，最好使用一个能够bind & listen的ip。
一般服务器都会有固定的ip（无论是private ip还是public ip），请使用这个ip。

## 总结

最后总结一下修改/配置fqdn的步骤。

首先修改hostname（如果有必要的话）：

    :::sh
    # hostname foo
    # echo foo > /etc/hostname

然后在``/etc/hosts``中增加一行：

    :::text
    ${one-of-assigned-ip} foo.example.com foo

并注意几点：

* 这一行中可以包含多个alias，hostname需要在alias列表中。
  如果没有特别需求，就只写hostname一个吧。
* 第二列是fqdn（用术语说叫canonical hostname），这是``hosts``文件的规范
* 在这一行前面的内容里不要使用这里用的ip，也就是说这一行应该尽可能靠前，
  如果没有洁癖、强迫症，那么放在第一行是最好的。
* 这里用到的ip应该是一个可以使用的（可以连接、可以bind&listen的）ip，
  但这不是硬性要求。
  如果这个ip不可连接，那么当发现``ping `hostname -f` ``不能ping通时会多么沮丧，
  不能bind&listen，在某些极诡异的情况下也许会出一些问题，并让自己摸不着头脑。
  ``127.0.1.1``其实是个不错的选择。
