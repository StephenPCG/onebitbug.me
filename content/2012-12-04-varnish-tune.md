Title: Varnish 调优
Slug: varnish-tune
Category: Varnish
Date: 2012-12-04

线上服务器使用Varnish已经有一个多月了，一直没有碰到问题，挺省心的，因此也没有比较深入的折腾Varnish。 上周由于业务变化，请求量一下子涨了很多，Varnish接二连三挂了，于是折腾了一下。

Thread Pool
------------

*问题现象*

Varnish响应很慢、甚至返回503，而backend是好的。

*复现方法*

经过检查发现，在此前某一时刻，一个backend响应很慢（回源时间很长），hold住了大量分配到这个backend的请求， 此后，对所有的请求（即使分配到其他健康的backend）都会变得很慢。

*问题分析*

每一个来自客户端请求在varnish中都是一个session，一个session会被分配到一个空闲的thread处理。
当没有空闲的thread时，varnish会创建新的thread来处理。
当全局的thread数量超过`thread_pool_max * thread_pools`时，
 varnish会将请求放入队列，当队列满时，varnish开始丢弃请求。
Varnish的默认配置，thread_pools为2，thread_pool_max为500，也即最多1000个thread。
当并发处理的请求量（注意不等价与并发请求量）大于1000时，varnish就过载了。

上述问题正是如此，有大量请求处于（响应较慢的backend）回源阶段，
占用了大量的thread，导致新进的请求无法处理。
对线上Varnish参数进行了调整，将thread_pool_max设置为5000，问题基本解决

*调优建议*

* `thread_pool_max` 根据Varnish Book所述，最高应该只有5000。
  我个人认为这个参数应该跟CPU的处理能力有关。
* `thread_pools` 根据Varnish Book所述，该参数最好设置为2（默认值），
  无需修改。
* `thread_pool_min` 网上有一些建议，如果服务器经常会有突发的高负载，
  可以将该值调高一些，以减少突发高负载时创建thread的延迟。

高内存占用
----------

*问题现象*

有一天发现varnishd占用的内存（top中的RES列）达到了15g，吃掉了所有的内存，导致系统负载变高。 而Varnish设置使用的Storage是malloc,1g。

*复现方法*

经过检查发现，由于客户端更新，上了了一个量很大的请求，每个客户端都待了一个随机参数，因此该请求无法命中， 而vcl中对所有的obj都设置了1h的beresp.grace时间。这导致所有的object都在cache中保存1h。 而每个object会额外占用1k左右的meta data，因此，10m数量个object会额外占用10g的内存。

*问题分析*

这个问题其实是因为最初写vcl时对grace的理解不准确所致。有两个grace值，req.grace和beresp.grace。

* `beresp.grace` 表示一个object即使已经过期了，仍然在缓存中存放一段时间。
* `req.grace` 表示，当一个请求命中了一个刚过期的object，由于回源需要一段时间，
  为了立刻返回，那么在过期后的`req.grace`时间内， 可以将过期的那个object返回给客户端，
  当然，这要求`beresp.grace >= req.grace`

根据我们实际的业务逻辑，这里beresp.grace无需设置为1h那么长。调整后的设置为：
```
sub vcl_fetch {
    # 仅当该请求可以缓存时，才设置beresp.grace，若该请求不能被缓存，则不设置beresp.grace
    if (beresp.ttl > 0s) {
        set beresp.grace = 1m;
    }
}

sub vcl_recv {
    # 若backend是健康的，则仅grace 5s，如果backend不健康，则grace 1m。
    # 这里，5s的目的是为了提高高并发时的吞吐率；
    # 1m的目的是，backend挂了之后，还能继续服务一段时间，期望backend挂的不要太久。。。
    if (req.backend.healthy) {
        set req.grace = 5s;
    } else {
        set req.grace = 1m;
    }
}
```

*调优建议*

观察varnishstat的输出，关注`n_object`这一项，实际内存占用率为这么多object本身的体积，
外加他们的1k的meta data。
如果这个值大到百万量级的话，内存占用就非常可观了，
这时候应该观察是什么样的请求导致了这么多object，
这样的请求要么是不该缓存（因此也无需grace）的，要么是需要normalize一下之后再缓存的。

Content-Length: chunked
------------------------

*问题现象*

由于我们有一个客户端（flash）比较二逼，不支持接收到Content-Length: chunked的数据。 而chunked一般是由gzip或者后端服务器产生，varnish如果回源时获取到的数据是chunked，那么返回给客户端的也一样。

*解决方法*

对于这样的请求，缓存两份（因此也回源两次），一份为不支持chunked的客户端（flash），一份为正常的客户端。

```
sub vcl_recv {
    if (req.http.User-Agent ~ "flash") {
        set req.http.X-Agent = "flash";
    }
}

sub vcl_hash {
    if (req.http.X-Agent) {
        hash_data(req.http.X-Agent);
    }
}

sub vcl_miss {
    if (req.http.X-Agent) {
        set bereq.http.Accept-Encoding = "identity";
    }
}

sub vcl_pass {
    if (req.http.X-Agent) {
        set bereq.http.Accept-Encoding = "identity";
    }
}
```

与Cookie有关的缓存
------------------

这个问题就不跟上面那样分析了。业务要求大致如此，对于一个domain下的请求，客户端总是会带Cookie， 而该domain下面有一些请求是需要缓存的。在之前的配置中，`vcl_recv`中设置了只要有Cookie就return(pass)， 因此如果某个url需要缓存，就需要手动对该url在`vcl_recv`中删除req.http.Cookie，并在vcl_fetch中删除beresp.http.Set-Cookie。 这样运维的工作与后端的开发工作就耦合了。期望的效果是，后端如果需要缓存某个url，则在该请求的返回头中带有Cache-Control头， 然后Varnish就自动根据该头来缓存相应的时间，而如果一个请求的返回中没有Cache-Control头，则默认不能缓存。

Varnish的默认设置中，是不会将req.http.Cookie添加到hash_data的，因此req.http.Cookie本身并不会影响缓存， 但是如果服务器返回的请求中含有Set-Cookie头，那么Varnish默认就不会缓存。

因此修改Varnish的配置如下：

```
sub vcl_fetch {
    # 如果反回头有Cache-Control，则删除Set-Cookie头
    if (beresp.http.Cache-Control && beresp.ttl > 0s) { 
        unset beresp.http.Set-Cookie;
    }
    # 如果反回头没有Cache-Control，则标记为hit_for_pass，强制后续请求回源
    if ((!beresp.http.Cache-Control && !beresp.http.Expires) ||
            beresp.http.Cache-Control ~ "(private|no-cache|no-store)") {
        set beresp.ttl = 120s;
        return (hit_for_pass);
    }
}
```
