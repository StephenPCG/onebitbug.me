Title: 绕过运营商HTTP劫持
GitTime: off
Slug: escape-isp-http-hijacking
Tags: linux, firewall, iptables
Date: 2013-12-19 19:30

中国的网络是奇葩的，原因之一是有奇葩的屌丝运营商。

许多小运营商（二级运营商、三级运营商、N级运营商）为了节省成本，会使用缓存系统。
这个缓存系统可以认为是一种CDN，如果做得好的话，不仅会节省成本，也会提高用户体验，
例如许多小区里大家看优酷视频从来不会缓冲，下载速度都有3MB/s以上的速度。
然而，这些缓存系统并不是CDN，而是一种非常没有节操的黑盒子。

* 你不知道什么请求会被缓存，没法控制。
* 你不知道会被缓存多久。
* 这种缓存不遵守任何行业内的规则（例如不遵守Cache-Control头）。
* 发现缓存了错误的内容，你没有地方投诉。

许多用户和开发者都为此非常头疼。例如：

* 我去年入手iPad后，尝试在电脑上安装iTunes，从官网下载安装后，提示版本太旧，不支持新iPad，于是
  自动更新，更新非常快，但更新之后仍然提示版本太旧，仔细观察发现版本并没有变。后来发现是运营商
  缓存了一份老的，而苹果分发iTunes时是同名更新的。
* 许多网页游戏（主要是flash）的开发者都非常的头疼，flash资源的加载成功率能到90%以上就算非常不错了。
  为此我们也想了各种dirty的方法，例如将后缀都改成`.aspx?rnd-query-string`，以期望绕过运营商缓存。

其劫持的手段也是非常的无节操的，主要受益于郭嘉的某墙开发的成果。其劫持原理大致如下：

* 客户端C向服务器S发出一个HTTP请求；
* 运营商网关将该请求分光（复制）送到缓存服务器；
* 缓存服务器如果发现命中缓存，则伪装成S返回一个302响应，该响应通常比S的正确响应早到，因此C接受
  了该响应，而忽略了S的响应，从而跳转到缓存服务器取数据；

是的，这正是伟大的墙发送RST的方法。

我们看一个例子，正常的请求应该是这样的：

``` sh
$ curl -I http://mirrors.ustc.edu.cn/ubuntu/dists/lucid-updates/main/binary-amd64/Packages.bz2
HTTP/1.1 200 OK
Server: nginx/1.2.1
Date: Thu, 19 Dec 2013 09:54:42 GMT
Content-Type: text/plain
Content-Length: 724863
Last-Modified: Thu, 19 Dec 2013 09:02:00 GMT
Connection: keep-alive
Accept-Ranges: bytes
```

被劫持的请求是这样的：

```
$ curl -I http://mirrors.ustc.edu.cn/ubuntu/dists/lucid-updates/main/binary-amd64/Packages.bz2
HTTP/1.1 302 Found
Connection: close
Location: http://59.108.200.39/files/512100000196E4FC/us.archive.ubuntu.com/ubuntu/dists/lucid-updates/main/binary-amd64/Packages.bz2
```

通常缓存服务器的IP是有限的，因此我们可以这样绕过运营商的劫持，在网关（或自己机器上）添加一条iptables规则：

```
iptables -A FORWARD -p tcp --sport 80 -m string --string "Location: http://59.108.200.39" --algo bm -j DROP
```

该规则的意义是，如果某个HTTP响应包（这里并没有真正判断是否HTTP，仅分析来自80端口的包）中含有
`Location: http://59.108.200.39` 字样，就直接丢弃。这样后续S真实的响应包就能被客户端接收，从而保证正确的通信。

注意，如果是在自己的机器上，则将`FORWARD`替换成`INPUT`。

这里我们要感谢该运营商没有像某墙那样的没节操，某墙在向C发送RST的同时，也向S发送了RST，而该缓存服务器并没有
向S发送RST，彻底破坏tcp通信。
