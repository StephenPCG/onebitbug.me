Title: Use nginx as an HTTP Gateway
GitTime: off
Slug: nginx-as-a-gateway
Date: 2013-10-26 14:46

### 需求分析

Nginx是一款非常轻量级的HTTP Server，常用于Load Balance和App Router。

{% img /images/posts/2013-10-26/nginx-lb-router.png %}

在国内这样奇葩的网络环境下，一些较大的网站部署时，Nginx和App服务器往往不在一个机房。
通常App服务器部署在带宽成本较高的BGP机房，而网站前端放在价格较便宜的单线机房，
CDN也是这样的一种情形。因此结构如下：

{% img /images/posts/2013-10-26/nginx-cache-lb-router.png %}

这里，Nginx与Cache在同一个机房，而与App在不同的机房（可能跨地区、跨ISP）。
Cache服务器可以是squid、varnish或者其他产品，通常Cache服务器的逻辑比较简单，专注于Cache逻辑。
Cache服务器节省了大量跨机房的带宽资源（当然也顺带可以当App Cache使）。
(带宽)Cache服务器也正是这种结构存在的意义。

然而，常常会有一些请求需要按照区域、Session等变量来区分。
例如某个网页，对不同地区的人显示不同的内容，一些Cache服务器支持较复杂的逻辑，
可以对Session内容进行简单的分析，以决定如何分析，但是当逻辑更复杂时，就不能、
也不合适由Cache服务器来做这个事情。

有时候，我们需要应用防火墙，防御一些简单的DoS、DDoS攻击。例如最简单的攻击，某人用ab
猛请求同一个URL，如果攻击者带宽足够大，那么可能会消耗大量的前端带宽，如果攻击者使用POST请求
（一般Cache服务器会配置永不缓存POST请求），那么回源带宽资源也会十分容易被耗尽。
在Nginx这一层，我们可以使用[LimitReqModule](http://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
来限制"$binary_remote_addr"或者"$binary_remote_addr$uri"的请求数量。
但是，这个模块很难实现更复杂一些的防御逻辑。
（有条件的公司，可能会使用硬件防火墙，不过那都是非常高帅富的公司了。）

在网络的术语中，网关（Gateway）的功能主要就是转发和防火墙，在这里，Nginx实际上就担任了HTTP网关的角色。

淘宝有一个开源项目[httpgate](http://code.taobao.org/p/httpgate/)，这个项目可以说从某种程度上重造了nginx的轮子，
而且该项目似乎没有形成社区，对于没有形成社区的项目，一般不推荐在生产环境使用（不能保证该项目有人长期维护，
碰到问题时也很难快速得到帮助）。

但是我们使用Nginx就可以很方便的实现前面提到的需求。

### 再提Nginx Lua模块

还记得前两篇文章(
[1](|filename|2013-10-10-use-nginx-lua-module-to-prevent-hotlinking.md),
[2](|filename|2013-10-10-lua-ngx-location-capture-meets-fastcgi.md)
)中提到的Nginx使用例子么？这两篇文章中，我们分别使用Lua模块实现了一个“序列号”验证逻辑和鉴权逻辑。

由此启发，在Nginx这一层，我们可以做许多事情。

{% img /images/posts/2013-10-26/nginx-modules.png %}

在这里，我们可以实现许多模块，每一个模块可以是一个lua脚本，也可以是HTTP服务，也可以其他Lua能访问到得东西。

#### 实例1：按Session显示不同的内容

我们先看一个最简单的例子，假设我们有某个页面需要按照不同的省份显示不同的内容。
这个需求实质上是要求Cache Server对不同省的用户分别缓存一份不同的内容。
我们可以使用[`set_by_lua`](http://wiki.nginx.org/HttpLuaModule#set_by_lua)来实现：

```
location = /some/page {
    set $cache_key '
        -- return 'BJ';
        return get_province_code(ngx.var.remote_addr);
    ';
    proxy_pass http://app1_cache_server;
    proxy_set_header CacheKey $cache_key;
}
```

这里我们略去`get_province_code()`的代码，因为这里通常是更复杂的需求，例如根据用户的session将用户分类等。
为了分离代码，使得nginx和模块能够单独维护，我们在这里也可以使用
[`set_by_lua_file`](http://wiki.nginx.org/HttpLuaModule#set_by_lua_file)。

如果有更复杂的需求，我们也可以使用一个外部的程序提供这个服务，这个程序提供一个http接口：
`http://localhost:1234/make_cache_key`，在Lua代码中访问这个接口。
不过注意，在`set_by_lua`中不能使用`ngx.location.capture`，因此这里也可以借用`access_by_lua`。

PS: 对于分省这个具体的需求来说，也可以用Nginx的
[`HttpGeoModule`](http://nginx.org/en/docs/http/ngx_http_geo_module.html)
来简单的实现：

```
geo $cache_key {
  default   default;
  iprange-bj     BJ;
  iprange-sh     SH;
  ...
}
location = /some/page {
    proxy_pass http://app1_cache_server;
    proxy_set_header CacheKey $cache_key;
}
```

#### 实例2：简单的准实时应用防火墙

防火墙不仅仅用来防止来自外部的主动攻击，对于一个快速开发的团队来说，也是防止灾难的重要工具。
一些网站常常会多个App同时开发，有些App在开发时可能由于疏忽，导致产生了大量的请求，消耗了太多的带宽和CPU资源，
导致其他App都受到牵连。因此我们需要一些策略来限制各App的资源使用（以及发出报警）。
如果只需要限制请求数，可以使用Nginx的
[`HttpLimitReqModule`](http://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
来实现：

```
map $request_uri $app {
    ptn_app1    app1;
    ptn_app2    app2;
    ...
}
limit_req_zone $app zone=apprps:1m rate=100r/s;
server {
    limit_req zone=apprps burst=150;
}
```

上述配置可以限制每个App最多只能有100 request/s。不过实际情况下的需求比这个会复杂许多，
单单限制request/s并不够，例如某App开发者不小心写了某个请求的返回body特别大，虽然请求很少，
但却会占用大量的带宽。而另一方面，也可能某App的开发者写了一个过于频繁的heartbeat请求，
总的带宽不大，但是请求数量过高，产生了不必要的资源消耗。因此我们不能单纯的限制请求数
或是带宽，需要共同限制。

在这里，我们可以写一个日志分析的程序，该程序实时的分析nginx日志，根据日志分析各App的
负载情况，决定是否可以继续接受新的请求。这个程序暴露一个http接口（或者将结果保存在
memcached等内存数据库中），在nginx中，在处理每个请求前使用`access_by_lua`确认是否应该服务该App。

```
location / {
    access_by_lua '
        local res = ngx.location.capture('/appquota/' .. app1)
        if res.status == ngx.HTTP_OK then
            return true
        else
            ngx.exit(ngx.HTTP_FORBIDDEN)
        end
    ';
    proxy_pass ...;
}
```

运行在外部的这个日志分析程序，可以有比较复杂的逻辑，除了上述的并发请求数、总带宽以外，
还可以检查回源带宽、回源请求数、POST请求数等其他逻辑。

#### 实例3：动态修改某些配置

我们公司在某段时期硬件资源不够充分，当用户量比较大时，硬件资源已经不够用了，这时候唯一
能做的就是在前端主动放弃一些请求。但是随机丢弃请求对用户体验不友好，最好是选择性丢弃一些不影响
核心功能的请求，因此我们需要有一个易于配置的接口。这里我们使用`lua_shared_dict`来存储
配置（也可以使用memcached或者其他外部存储方式）。

```
lua_shared_dict ban_urls 10m;
server {
    location /ban/ {
        content_by_lua '
            local ban_urls = ngx.shared.ban_urls
            ban_urls:set(ngx.var.arg_url, 1)
            ngx.say("banned")
            ';
    }
    location /unban/ {
        content_by_lua '
            local ban_urls = ngx.shared.ban_urls
            ban_urls:delete(ngx.var.arg_url)
            ngx.say("unbanned")
            ';
    }
    location / {
        access_by_lua '
            local ban_urls = ngx.shared.ban_urls
            local value, flags = ban_urls:get(ngx.var.uri)
            if value == nil then
                return true
            else
                ngx.exit(HTTP_FORBIDDEN)
            end
            ';
        proxy_pass ...;
    }
}
```

以上是一段最简化的代码，假设要禁止某个请求$url1，可以访问一下 `http://server/ban/?url=$url1`，
lua会将$url1存入共享字典ban_urls中，以后请求$url1时，nginx发现该url存在于ban_urls中，则拒绝该请求。
需要解禁该url时，访问一下 `http://server/unban/?url=$url1`即可。当然，上述例子还可以进一步完善，
例如支持按正则式ban，甚至支持对某个url按比例丢弃。还有，安全性方面也需要做一些加固。

### 总结

这篇文章算是总结了Nginx的一种用法，可以通过Lua模块，与内部(lua脚本)或者外部(如外部提供http的服务)程序交互，
给Nginx加上更强大的过滤功能，作为一个网关，Nginx是十分优秀的。

大量使用模块时，也要注意模块的容错性，要保证一个模块挂了，不能影响其他的请求，
最好写代码时也充分考虑模块挂掉的情况，设置好一个默认行为。性能方面，Nginx本身的调度性能是很好的，
但是自己实现的代码，性能还是要靠自己把关的。
