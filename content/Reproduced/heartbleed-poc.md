Slug: heartbleed-poc
Date: 2014-04-09
Title: Heartbleed 实战：一个影响无数网站的缓冲区溢出漏洞
Category: Reproduced
Author: <a href=https://boj.blog.ustc.edu.cn>Bojie Li</a>
ReproducedSource: https://boj.blog.ustc.edu.cn/index.php/2014/04/heartbleed-poc/
GitTime: Off

昨天 OpenSSL 爆出了名为 Heartbleed 的重大安全漏洞（CVE-2014-0160），通过
TLS 的 heartbeat 扩展，可以读取运行 HTTPS 服务的服务器上长达 64 KB
的内存，获取内存中可能存在的敏感信息。由于这个漏洞已经存在两年，Debian
stable (wheezy) 和 Ubuntu 12.04 LTS、13.04、13.10
等流行的发行版都受影响，无数部署 TLS（HTTPS）的网站都暴露在此漏洞之下。

什么是 SSL heartbeat
--------------------

[![https](/images/reproduced/heartbleed-poc/https.png)](/images/reproduced/heartbleed-poc/https.png)

SSL 全名 Secure Socket Layer，是在 TCP
连接的基础上的安全层，提供了认证、加密等功能。只要你在上网的时候看到网址旁边有个小绿锁，或者网址是
https 开头的，或者网址栏是绿色背景的，就说明你在使用
SSL。涉及到金钱或敏感信息的网站，一般都会使用 SSL 安全连接。

SSL
连接建立的时候需要进行两个来回的握手，第一次握手协商所用的加密方式、获取服务器端的数字证书，第二次握手协商后续数据传输所使用的对称加密密钥（好比两个人协商一个公共密码）。如果服务器在大洋彼岸，这中间的延迟有几百毫秒。因此我们希望尽量重用已经建立的
SSL 连接。

问题是我们并不是在不停地点击网页，服务器怎么知道连接对面的人还 “活着”
呢？如果对面的人 “死掉”
了，服务器需要尽快释放资源，不然就会被僵尸连接占满。这就需要客户端隔一段时间就发一个
“心跳”，告诉服务器 “我还活着”。服务器也会返回一个心跳告诉客户端
“我还没把你忘掉”。这就是 SSL heartbeat 的由来。

SSL 安全连接层又分为两层：底层是记录层，这一层是不加密的，用 wireshark
就能抓出来；上层是握手信息、密钥信息、用户数据、心跳包等，加密后封装成一个个
“记录”。SSL 安全连接层之上，就是我们熟悉的 HTTP 等协议了。也就是说，SSL
安全连接层是透明地插在应用层（如 HTTP）和传输层（如 TCP）之间的。

[![IC197149](/images/reproduced/heartbleed-poc/IC197149.gif)](/images/reproduced/heartbleed-poc/IC197149.gif)

SSL heartbeat 跟上图中的 Handshake 等并列。一个 SSL heartbeat 由下述 4
个字段构成：

-   **心跳包类型**：1 字节，只有请求和响应两种可能。
-   **载荷长度**：2 字节，按 RFC 6520 规范，不能超过 2\^14 = 16384，不过
    OpenSSL 的实现只在发送请求的客户端检查了，服务器端没有检查。
-   **载荷**
    (payload)：载荷长度这么多字节，可以是任意字节。请求发送什么载荷，服务器就应该响应同样的载荷，就像是 “回显”。
-   **填充** (padding)：至少 16 字节，要把一个 SSL
    记录填满。请求和响应的填充字节都应该是随机的。

漏洞分析
--------

以下漏洞分析基于 OpenSSL-1.0.1e 源码。TLS 是 SSL
的一种传输方式，是比传统 SSL
更安全的，因此如果客户端和服务器都支持，会优先采用它。当服务器收到一个
TLS heartbeat 包时，就会调用 ssl/t1\_lib.c 中的 tls1\_process\_heartbeat
函数（如下图所示）。

-   2490 行：p
    被初始化为指向数据区的指针，取出第一个字节（心跳包类型），放进
    hbtype 变量。
-   2491 行：把随后的两个字节（载荷长度）放进 payload 变量。n2s
    是个宏，会将 p 增加 2。注意，这里没有对载荷长度进行任何检查。
-   2492 行：后续的字节被认为是载荷和填充，赋值给 pl，稍后将被发送出去。

[![code1](/images/reproduced/heartbleed-poc/code1.png)](/images/reproduced/heartbleed-poc/code1.png)

注意，不要与 dtls1\_process\_heartbeat 这个 “孪生兄弟” 弄混，DTLS 是基于
UDP 的 TLS，我们网站一般都是用 TCP 传输，因此调用的是
tls1\_process\_heartbeat。

-   2499 行：如果这是一个心跳包请求……
-   2508 行：为即将发送的响应分配内存。
-   2509 行：使用 bp 作为即将发送的缓冲区指针。
-   2512 行：响应的第一个字节是心跳包类型。
-   2513 行：响应的第 2、3 字节是载荷长度。
-   2514
    行：把载荷从心跳包请求复制到响应缓冲区。缓冲区溢出就在这里：如果
    “载荷长度” 字段（payload
    变量）被发送端设置得很大，而实际的载荷长度比较短，就会把本来不属于载荷区域的内存复制到响应缓冲区。
-   2515\~2517 行：生成 16 个随机的填充字节并附加到载荷末尾。
-   然后，bp 指向的缓冲区就被装入 TLS 记录，发送给客户端了。

[![code2](/images/reproduced/heartbleed-poc/code21.png)](/images/reproduced/heartbleed-poc/code21.png)

不说有没有漏洞，相信有人已经闻到代码里的 “坏味道” 了。变量名 p、bp、pl
都是什么意思？也许能猜出来，但这种命名方式实在是不敢恭维。也许正是因为这些代码生涩难懂，才让
bug 有了藏身之地。

漏洞利用
--------

从前面的分析可以看出，这个漏洞利用方式简单，除 OpenSSL
版本外不需要额外条件，不需要考虑服务器上装的是何种 Web
服务器软件、有没有特殊路径的文件等。效果也非常明显：读出最多 64 KB
的服务器内存，且不会在服务器日志里留下痕迹。64 KB 是由于载荷长度的选项是
16 比特，最大是 65535，也就意味着最多泄露 (64KB – 1) 字节内存。

我写了一段 POC（Proof Of Concept）代码来验证。由于我比较懒，就不去研究
SSL 记录层格式和 SSL 握手那些麻烦事了，借用 OpenSSL 客户端库，把发送
heartbeat 请求的 payload 字段改大。如下图所示，修改 ssl/t1\_lib.c 的
2599 行，把 payload 换成不超过 65535 字节的数值。这样真正的载荷只有 18
字节，也就是返回的响应里只有前 18 字节是与发送的载荷一致，后面的接近 64
KB 全都是不该泄露的服务器内存。

[![code3](/images/reproduced/heartbleed-poc/code3.png)](/images/reproduced/heartbleed-poc/code3.png)

剩下的部分就是用客户端库完成 SSL 握手、发送和接收 heartbeat
了。由于修改的 tls1\_heartbeat 函数是未导出的私有函数，需要直接链接上 .o
文件。（具体的编译命令参见 POC 代码开头的注释）。我把代码放到 gist
上了：[POC 代码](https://gist.github.com/bojieli/10164334)

这段 POC 代码可以发送正常的 HTTPS 请求来做测试，也可以在 SSL
握手完成后发送 heartbeat 请求并等待响应。如果服务器不支持 TLS heartbeat
扩展或者已经修补了这个漏洞，就不会收到任何响应，此时需要按 Ctrl+C
退出。如果服务器中招了，就会以类似 hexdump -C 的格式输出接近 64 KB
的服务器内存。

哪些信息会被泄露
----------------

首先拿 CSDN 热热身，SSL 证书赫然可见，下图是 X.509 Subject
部分，其中的那些 \\x 是 UTF-8
表示的中文字符，翻译过来就是那家公司的中文名字。当然，似乎这里面没有
private key，因此影响不是很大。

[![csdn](/images/reproduced/heartbleed-poc/csdn.png)](/images/reproduced/heartbleed-poc/csdn.png)

我们可爱的 12306 怎么样呢？看，这位哥正买 2014 年 4 月 8
日从呼和浩特（电报码 HHC）到熊岳城（电报码 XYT）的成人票呢！

[![12306-1](/images/reproduced/heartbleed-poc/12306-1.png)](/images/reproduced/heartbleed-poc/12306-1.png)

某公司内部网站，泄露了 nginx 配置。

[![corpweb](/images/reproduced/heartbleed-poc/corpweb.png)](/images/reproduced/heartbleed-poc/corpweb.png)

就连雅虎这么大的网站也未能幸免，用户发送的 HTTP 请求中的 Cookie
清晰可见，据此可以伪装成其他用户登录。

[![yahoo](/images/reproduced/heartbleed-poc/yahoo.png)](/images/reproduced/heartbleed-poc/yahoo.png)

某个人博客上刚发表的评论（垃圾评论，呵呵）。

[![Capture](/images/reproduced/heartbleed-poc/Capture.png)](/images/reproduced/heartbleed-poc/Capture.png)

更有趣的是，由于服务器内存的内容是在不停变动的，每次 SSL
heartbeat，泄露出来的 64 KB 内容都可能是不同的。

[USTC LUG 所有服务器对 OpenSSL
进行了紧急升级](https://servers.blog.ustc.edu.cn/index.php/2014/04/lug-openssl-upgrade/)
以应对这个漏洞。

结语
----

RFC 6520 中明确规定 heartbeat 包的长度不能超过
2\^14（16384），如果载荷过长，这个 heartbeat 请求应该被丢弃：

    The total length of a HeartbeatMessage MUST NOT exceed 2^14 or max_fragment_length when negotiated as defined in [RFC6066].

    If the payload_length of a received HeartbeatMessage is too large, the received HeartbeatMessage MUST be discarded silently.

但 OpenSSL 的实现者们似乎把 RFC
中关于最大载荷长度的限制当成了耳旁风（不然最多泄露 16 KB 而非 64 KB
内存），而且完全信任客户端发来的载荷长度。信任用户的输入在网络编程中是非常危险的，但就是这样拙劣的
bug，在数以百万计的服务器上藏身长达两年之久（这段代码是 2011
年底引入，2012 年 3 月随 OpenSSL 1.0.1 版本发布的）。

微软漏洞应急响应中心的人曾说，软件的安全问题要靠专业的人去排查和测试，只是眼球足够多，bug
并不一定就能被发现。OpenSSL
作为网络安全的底层支持，应该有足够多的眼球关注了，但仍然不止一次爆出安全漏洞，这是值得我们深思的。

值得称道的是此次漏洞的发现和处理过程：漏洞的发现者没有急于公之于众，而是通过
CVE 平台向大型互联网公司和主要 Linux 发行版的维护团队报告，让关系互联网
“生死存亡” 的大型网站先补上漏洞，Linux
发行版也准备好了补丁。在预定的时间，漏洞向全世界公开，一时间网络上关于此漏洞的报道铺天盖地，此时普通用户只要应用
Linux
发行版准备好的补丁，就能有效防御漏洞，这使得漏洞对整个互联网的危害降到最低。

参考文献
--------

1.  http://heartbleed.com/
2.  http://tools.ietf.org/html/rfc6520
3.  http://technet.microsoft.com/en-us/library/cc781476(v=ws.10).aspx

