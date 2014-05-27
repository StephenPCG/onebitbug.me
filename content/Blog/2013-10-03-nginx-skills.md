Title: 一些Nginx的使用技巧
GitTime: off
Slug: nginx-skills
Tags: nginx, linux, debian
Date: 2013-10-03 22:53

使用Nginx很久了，也在好几个不同的场景使用过，逐渐有了一些心得，这篇文章整理一下。

### 配置文件的组织

Debian的打包很贴心，使用了两个目录`sites-available/`和`sites-enabled/`，在`nginx.conf`
中有一句`include sites-enabled/*`。配置多个vhost时，一般每个vhost写一个配置文件，然后
放到`sites-available/`中。然后将需要启用的vhost的配置文件软链至`sites-enabled/`中即可。
对于个人网站来说，这种目录组合很合适也很方便，特别是经常需要临时停用某个vhost时，
仅需要添加、删除软链即可。

我在很长一段时间内一直按照这种方式使用。然而渐渐的碰到了一些问题：

* 添加新的站点很麻烦，需要添加一个配置文件，再做一个软链，需要两步。
* 有的时候多处要引用同一个公共配置文件时，这个文件放在上述目录中并不合适。
* 临时禁用一个vhost的需求，在大多数服务器上并不常见。
* 有时候一个/组vhost的配置文件会很复杂，需要多个文件，也不适合上述目录结构。

因此我开始逐渐转而使用`conf.d/`目录。对于有些配置复杂的项目，会在另外的地方（比如`/opt/`中）
创建配置文件，并将入口的配置文件软链到`conf.d/`中，这样可以很方便的解决上述问题。

### 反向代理的配置

反向代理的配置方法很简单，用[HttpProxyModule](http://wiki.nginx.org/HttpProxyModule)可以
很方便的实现：

```
server {
    listen 80;
    server_name a.example.com;

    location / {
        proxy_pass http://a.internal.example.com;
    }
}
```

这里不细说HttpProxyModule的使用。我们介绍一下HttpMapModule这个模块的使用。
配置反向代理的机器，常常需要配置多个反向代理，这时候，如果对每个代理都配置一个上述的`server`
块显然会导致维护很麻烦。我们可以使用HttpMapModule这个模块来简化这项任务：

```
map $http_host $upstream_domain {
    default       default.internal.example.com;
    a.example.com a.internal.example.com;
    b.example.com b.internal.example.com;
    ...
}
server {
    listen 80 default_server;
    resolver 8.8.8.8;         # 指定一个合适的DNS服务器，最好在内网
    location / {
        proxy_pass http://$upstream_domain;
    }
}
```

在上述配置中，当需要增加一个新的代理站点时，仅需要在`map`块中添加一个新的映射关系即可。

如果`map`块很大的话，可以将内容提取出来，单独放到一个文件中，例如叫`reverse-proxy-map.conf`，
然后在`map`块中include这个文件即可，也方便了管理。

进一步，如果对某个backend需要特殊设置，只需要增加一个`server`定义即可：

```
server {
    listen 80;
    server_name c.example.com;
    ## vhost specific settings goes here
    location / {
        proxy_pass http://$upstream_domain;
        proxy_pass_header Authorization;
        proxy_set_header  X-Real-IP $remote_addr;
    }
}
```

注意前面一个配置中`listen 80 default_server`，这里`default_server`表示所有未被其他
`server`“抢”去的请求都会进入进入这里。因此如果对`c.example.com`需要特别设置，只需要为其
添加一个专门的`server`配置即可。

### HttpMapModule的更多用途

上述针对`$http_host`的`map`使用是最常见的用法之一，可能有不少读者在网上都见过。
HttpMapModule还有许多其他用途，这里举几例抛砖引玉。

##### 场景一

我有一个网站有多层结构，用户访问edge server，edge proxy_pass到的loadbalance server,
lb再proxy_pass到后端的content server。这里content server需要得到用户的IP，因此需要将
用户IP一层层传递到后端。假设我们使用HTTP Header `X-Real-IP`来传递。在edge上配置：

```
    location / {
        proxy_pass http://load_balance_server;
        proxy_set_header X-Real-IP $remote_addr;
    }
```

而在lb上再将这个header传递给后端：

```
    location / {
        proxy_pass http://content_server;
        proxy_pass_header X-Real-IP;
    }
```

这时候，假设有一部分客户端由于某些原因会直接到loadbalance请求的话，就不会有`X-Real-IP`这个头，
这时候该怎么办呢？在load balance上可以如是配置：

```
map $http_x_real_ip $x_real_ip {
    default $remote_addr;
    ~^.+$ $http_x_real_ip;    # 这里正则式 ~^.+$ 表示$http_x_real_ip这个变量非空，我不知道是否有更好的写法
}
server {
    location / {
        proxy_pass http://...;
        proxy_set_header X-Real-IP $x_real_ip;
    }
}
```

这样的配置，当下游给了`X-Real-IP`头时，就将这个头传递给后端，当下游没有给出这个头时，
就将下游的IP传递给后端。

这里，这份配置其实在edge和load balance上都可以用，两种服务器只需要维护同一份代码，相信
是很多系统管理员最喜欢的事情了。

##### 场景二

对于一些稍大些的网站，可能会有多个Application，假设我们有5个App，其访问url如下：

```
    app1:  http://www.example.com/
    app2:  http://www.example.com/app2/ && http://app2.example.com/app2/
    app3:  http://www.example.com/app3/
    app4:  http://app4.example.com/
    app5:  http://app5.example.com/
```

假设我们需要针对每个App设置并发请求数限制，那么该如何做呢？

```
map $http_host$uri $appname {
    default                       -;
    ~.+/app2/.*                app2;
    ~www.example.com/app3/.*   app3;
    ~www.example.com/.*        app1;
    ~app4.example.com/.*       app4;
    ~app5.example.com/.*       app4;
}
limit_req_zone $appname zone=request:10m rate=100r/s
server {
    ...
    limit_req zone=request burst=...
}
```

上述`$appname`还可以用于其他场合，例如写到日志中。

### 日志管理

在早期使用nginx时，我偏好将日志按域名(`server`)整理，即每个`server`的日志写到一个目录下，
如`/var/log/nginx/SERVER_NAME/access.log`。然而，后来在使用中发现了一些问题：

* 每次新建一个`server`时，都需要手动新建一个日志目录，批量部署时很蛋疼
* 有时希望查看按照App聚合的日志，如上述场景二的例子中app2的日志会分散到两个目录下
* 有时发现服务器的流量异常，需要查看是哪个`server`或者App导致的会很麻烦，需要挨个查看日志
* 有时可能需要有更多维度的统计信息，也很难实现

于是，我渐渐地更倾向于将所有`server`的日志都输出到同一个文件中。而在每一条日志中输出更多
的信息，稍后再来看具体的例子。

nginx默认的日志格式中，各个域按空格分隔，但也有一些域中本身含有空格，如`time_local`、
`$http_user_agent`等。这使得使用awk等脚本分析时变得比较困难。一般来说，nginx的日志里不会
出现非打印字符，因此我们可以使用非打印字符来分隔，如`^A`（通过ctrl-v ctrl-a来输入，在vim看
应该是一个字符，这里在网页上由于显示限制，只能打成2个字符了，读者您可别直接copy-paste哦）。

下面看一个具体的log_format例子：

```
log_format multidomain
    '$msec^A$remote_addr^A$x_real_ip^A$upstream_domain^A$app^A'
    '$server_protocol^A$request_method^A$scheme^A$http_host^A$request_uri^A'
    '$http_referer^A$http_user_agent^A$http_x_forwarded_for^A'
    '$status^A$gzip_ratio^A$body_bytes_sent^A$bytes_sent^A$request_time^A'
    '$proxy_host^A$proxy_port^A'
    '$tcpinfo_rtt^A$tcpinfo_rttvar^A$tcpinfo_snd_cwnd^A$tcpinfo_rcv_space';
```

上面的日志格式中有大量的信息，读者可以根据自己的需求“精简”。注意上面用到的一些
变量是前面的例子中通过`map`来设置的，如`x_real_ip`、`upstream_domain`、`app`等。

有些读者可能会好奇为什么时间不用`$time_local`，而用`$msec`，前者的可读性很好，
后者不具有可读性。原因可以参见我的前一篇文章
[strptime真慢……](|filename|2013-09-27-python-strptime-is-super-slow.md)。

这个日志，用awk分析的话，指定-F参数即可：`awk -F^A ...`。

过些日志我会将我正在使用的一个脚本整理一下放出来，用这个脚本可以方便的按照domain、
url、remote_addr等各种维度输出统计信息（如request/s、bandwidth、err/s等）。

well，这些都只是一些小技巧。要熟练应用，还是需要对nginx有一定的熟悉程度。
这里强烈推荐读者阅读一下（如果您还没有读过的话）：
[agentzh的Nginx教程](http://openresty.org/download/agentzh-nginx-tutorials-zhcn.html)。
（agentzh是nginx的二把手）。

### 最后了

突然想起来还有几个比较糙的“一行”命令，也算是比较实用的吧，不过由于现在日志格式变了，
而且我也有了专门的脚本来更直观的输出统计，这些对我也就没用了。

下面的命令仅对nginx默认的日志格式有效，形如：

```
54.215.120.49 - - [03/Oct/2013:21:20:32 +0800] "GET / HTTP/1.1" 200 7439 "http://onebitbug.me" "Feedspot http://www.feedspot.com"
```
这条命令可以显示实时的request/s：

```
tail -f access.log | awk '{print $4}' | uniq -c
```

这条命令每秒钟会输出一次，输出该秒内新增的日志行数，也就是request/s。

下面3条命令可以输出实时的带宽（单位分别为mb/s、kb/s、b/s）：

```

tail -f access.log | awk '{if(lastt==$4){size=size+$10}else{printf("%s %d Mbps\n", lastt, (size*8/1024.0/1024.0));lastt=$4;size=$10}}'
tail -f access.log | awk '{if(lastt==$4){size=size+$10}else{printf("%s %d Kbps\n", lastt, (size*8/1024.0));lastt=$4;size=$10}}'
tail -f access.log | awk '{if(lastt==$4){size=size+$10}else{printf("%s %d bps\n", lastt, (size*8));lastt=$4;size=$10}}'
```

不过注意，nginx默认的日志格式中，$10是body_bytes_sent，即http body的大小。302请求的body都是0，
此外请求的http header体积也是可观的，当request/s比较大时，body_bytes_sent的误差就会比较大。
我碰到过一次事故，某一台机器的带宽非常大，但是我用上面的命令对每个vhost的日志跑了一下，没有
发现哪个vhost的带宽特别大。后来发现是某个vhost下有上万r/s的302请求，
这些请求产生了上百兆bps的带宽。这也是我后来统一存储各vhost日志的直接导火索。
