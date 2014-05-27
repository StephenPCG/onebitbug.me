Title: ngx.location.capture与fastcgi的一个问题
GitTime: off
Slug: lua-ngx-location-capture-meets-fastcgi
Tags: nginx, lua, linux, debian, fastcgi
Date: 2013-10-10 22:18

标题起的不太好，但是一时也想不到简单的句子来概括这个问题。
解释问题之前，先描述一下我的需求吧。

### 原始需求

我用django开发了一个运维管理平台(后简称opsmgr)，希望把Nagios的管理集成进去，
用iframe内嵌。但是问题来了，nagios有自己的认证，opsmgr有自己的认证，
两套认证很麻烦，因此希望nagios能够借用opsmgr的认证，但是由于跨域，
且不方便修改nagios的代码，于是采用另外一种方法，在opsmgr的同域下，
配置nginx proxy_pass，而proxy_pass前，让nginx先向opsmgr询问授权，授权后再
proxy_pass，nagios那边对于来自opsmgr的proxy请求不再做验证。说的比较乱，
下面给个nginx的配置吧。

首先是两个url：

* http://opsmgr.example.com/api/auth/can-access-nagios 
  如果用户有权访问nagios，则此链接返回200，否则返回403
* http://opsmgr.example.com/nagios/*
  上述url被全部proxy_pass到nagios.example.com。

opsmgr的nginx配置如下（省略了部分无关代码）：

```
server {
    server_name opsmgr.example.com;

    location / {
        fastcgi_split_path_info ^()(.*)$;
        include fastcgi_params;
        fastcgi_pass unix:/path/to/django.sock;
    }

    location /nagios/ {
        access_by_lua '
            -- 仅对.cgi的请求验证权限，对静态文件不做验证，全数通行
            if string.find(ngx.var.uri, ".cgi") == nill then
                return true
            end
            local res = ngx.location.capture("/api/auth/can-access-nagios")
            if res.status == ngx.HTTP_OK then
                return true
            else
                ngx.exit(ngx.HTTP_FORBIDDEN)
            end
            ';
        proxy_set_header NagiosUser nagios-user;
        proxy_pass http://nagios.example.com;
    }
}
```

对上面的配置文件做一个简单的解释。当用户访问
http://opsmgr.example.com/nagios/cgi-bin/status.cgi
这个链接时，nginx首先调用[lua代码](http://wiki.nginx.org/HttpLuaModule)
来做权限验证。这里面，lua发起一个subrequest，访问授权url，授权url反馈
当前用户是否得到授权，如果没有授权，那么lua直接让nginx返回403，否则授权通过，
nginx正常去nagios.example.com回源。

### 问题

这个配置文件看上去没有什么问题，然而运行起来却发现很奇怪，访问
`/nagios/cgi-bin/status.cgi`时总是提示403。我首先单独访问授权url，确认该url工作正常。
于是在lua中增加了一句 `ngx.log(ngx.ERR, res.body)`，发现这个res输出的内容确实来自django，
并且为404。于是仔细查看django日志，发现`lua.location.capture`发起的请求，
django中看到的路径居然是`/nagios/cgi-bin/status.cgi`，
而不是`/api/auth/can-access-nagios`。这里显然是出问题了。

这时就傻了，以前也用过nginx的lua脚本，`ngx.location.capture`也用过，并没有发现过问题，
因此不应该是lua的bug，尝试换了好几个nginx/lua的版本，也都能稳定重现这个问题。
这时无意中发现，如果django不使用fastcgi启动，而是用最原始的runserver，然后让nginx
proxy_pass访问则没有任何问题。于是就把问题锁定到了`fastcgi_pass`上。

由于对fastcgi底层实现并不了解，也不值得花时间去细查、找文档。更何况fastcgi只是一个协议，
通过其传递的变量，不同的软件会有不同的处理方式。因此拿出了nc这个神器。`nc -l 1234`，
配置nginx `fastcgi_pass localhost:1234`。然后访问`/nagios/cgi-bin/status.cgi`，看nc这边
收到的数据，一堆乱七八糟的东西中看到了两个路径：

* `REQUEST_URI /nagios/cgi-bin/status.cgi`
* `DOCUMENT_URI /api/auth/can-access-nagios`

这时候再访问一个正常的url，比如`/some/django/url`，会发现`REQUEST_URI`和`DOCUMENT_URI`两个
变量的值相同。于是得出结论，django中是通过`REQUEST_URI`这个变量来确定当前访问的路径，
而不管`DOCUMENT_URI`这个变量的值。

问题找到了就好解决了。nginx配置中的`include fastcgi_param`，这里`fastcgi_param`是文件
`/etc/nginx/fastcgi_params`，因此查看这个文件，会发现：

```
fastcgi_param  REQUEST_URI        $request_uri;
fastcgi_param  DOCUMENT_URI       $document_uri;
```

这里，第三列小写的变量是nginx的变量，根据[文档](http://wiki.nginx.org/HttpCoreModule)，
[`$request_uri`](http://wiki.nginx.org/HttpCoreModule#.24request_uri)是一个“只读”变量，
它是用户请求的最原始的uri，而
[`$document_uri`](http://wiki.nginx.org/HttpCoreModule#.24document_uri)是会随着nginx内部
rewrite等操作而变化，显然在我这个情形下，lua发出的subrequest也只是发出了一个`document_uri`
为目标的请求。（对nginx-lua模块感兴趣的同学可以看看这个slides，有个感性的认识：
[http://agentzh.org/misc/slides/ngx-openresty-ecosystem/#42](http://agentzh.org/misc/slides/ngx-openresty-ecosystem/#42)）。

### 解决方法

通过上面的分析，解决问题的方法很简单：

```
include fastcgi_params;
fastcgi_param REQUEST_URI $document_uri; # 注意这个放在include后面，以覆盖fastcgi_params中的设置。
```

### 解决方法2

呵呵，这个解决方法可以认为不是针对这个问题的吧，但也算是解决了，那就是不用fastcgi，而改用uwsgi。
根据网上的一些评论，uwsgi是一个很高效的web gateway interface实现，从评测数据上比fastcgi好不少，
而且django将在1.9之后彻底放弃支持fastcgi。（目前的fastcgi通过flup，实际上也是最终调用了wsgi）。

经过实际测试，nginx中直接配置：

```
location / {
    include uwsgi_params;
    uwsgi_pass unix:/path/to/django.uwsgi.sock;
}
```

默认的配置就work的很好，不用折腾路径的问题，很好很happy，收场。
