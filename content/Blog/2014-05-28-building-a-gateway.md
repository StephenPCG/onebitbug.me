Title: 搭建网关系列 -- 预告篇
Tags: gateway, debian

最近离职了，回家休息一阵子。闲下来，花点时间总结一下这两年的工作。
也将其中一些有意思的东西整理出博客文章来。
这两天好好折腾了一下家里的网络，所以第一波打算写写关于搭建网关的事。

打算写一系列文章，介绍与搭建网关会用到的概念、工具和使用，初步计划包括以下内容：

* *VLAN篇* 将介绍VLAN的基本概念，在debian中如何使用。
* *iptables篇* 将介绍如何使用iptables配置防火墙、转发、NAT等功能。
* *路由篇* 将简单介绍iproute2套件，讲述简单的目的路由、策略路由，以及如何实现自定义（
  智能）路由。
* *隧道篇* 将介绍常用的隧道，如ipip、gre、sit，未解决某些国情造成的问题，隧道的效果比
  vpn要好很多。

END_SUMMARY

因为我是一个Debian guy，所以我使用Debian来搭建网关。
当然这系列文章里的大多数东西都适用于其他Linux发行版，也基本都能在openwrt上使用。

这里首先介绍一下这个网关具有的功能吧。

* 多ISP上联。
* 通过ipip/gre/sit等隧道技术连接到其他机房，访问国外网站、接入ipv6等。
* 内网每个设备可以独立选择自己的出口（或者路由策略），类似于科大网络通的效果。
* ipv6接入。
* 基本的防火墙功能，如端口映射等。

#### 家里接入的isp

* *宽带通*，号称50M，实测在鹏博士内网有50M的上、下行带宽，但访问公网只有4M的下
  行带宽。（两个测速图分别是通过鹏博士内网服务器和直接出网访问）。<br />
  {% img /images/posts/building-a-gateway/speedtest-kdt.png %}
  {% img /images/posts/building-a-gateway/speedtest-kdt-wan.png %}
* *联通*，20M adsl，实测下行可以达到接近40M，上行2M左右。
  {% img center /images/posts/building-a-gateway/speedtest-lt.png %}

#### 服务器资源：

* 一台鹏博士内网服务器（宽带通是鹏博士的子品牌），公网带宽大于50M
* 一台某VPS在新加坡的节点
* 一台位于科大网络中心的龙芯盒子，具有ipv6接入

#### 网关使用的设备:

* 一个D-Link dir825，刷了openwrt，原本直接用来做网关的，用过一段时间openvpn，
  发现性能不行，跑到2MB/s左右时CPU就满了，于是换用龙芯2f的笔记本做网关，结果
  发现性能并没有质的提升，只能跑到3MB/s。目前这个openwrt仅当vlan交换机使。wan
  口被桥接到lan口上，成为交换机上的一个普通接口。
  [{% img center /images/posts/building-a-gateway/dir825.jpg 400 %}](/images/posts/building-a-gateway/dir825.jpg)
* 一个无分扇小主机（赛扬双核1037U/8G内存/32G ssd+1T机械硬盘）做网关。
  由于使用这样的一个主机做网关有些太浪费，所以干脆把配置调高一些，上面做一个
  全家的平台、下载机，以及其他应用，如搭了一个gitlab管理代码。（自己拍摄的照片
  效果太差，就拿商家的宣传照片代替了。）
  [{% img center /images/posts/building-a-gateway/fanslesspc.jpg 400 %}](/images/posts/building-a-gateway/fanslesspc.jpg)

#### 最终上网出口选择

图中第二个方括号表示这个隧道是从哪个接口连出去的，实际的服务器资源比较多，
对一些不重要的服务器打了码。
{% img center /images/posts/building-a-gateway/choose-isp.png %}

最后show一下前两天下载东西时的带宽使用情况：
{% img center /images/posts/building-a-gateway/bandwidth.png %}
