Title: 使用Nginx的Lua模块实现简单的权限验证系统
GitTime: off
Slug: nginx-lua-simpleauth-module
Tags: nginx, lua, linux
Date: 2014-01-04 22:22

Nginx本身是一个很单纯的http服务器，其附加功能少的可怜，也正因为单纯，nginx才能如此高效。

我们常常会有一些简单的权限验证的需求，例如一个纯静态文件的wiki站点，需要对不同的人进行简单的权限控制。

Nginx本身可以实现，使用[http_auth_basic_module](http://wiki.nginx.org/HttpAuthBasicModule)模块可以进行最基本的权限验证。
但缺点是，修改密码必须登录服务器进行修改，十分不方便，而且当团队人多时，基本上不具有管理账号的功能。
稍大一些的团队会使用LDAP来做集中的账号管理中心。

使用[auth_ldap](https://github.com/kvspb/nginx-auth-ldap)模块可以实现基于ldap的authn，但基本没有authz的能力。

## 什么是authn/authz？

常见的权限系统一般有两个任务，Authentication(常简称authn)和Authorization(常简称authz)。
authn的过程是验证一个用户是否是该系统内的合法用户，例如验证你是否拥有A网站的账号。
authz的过程是验证该用户是否有权限访问某项功能，例如你可能拥有账号，但你只能访问A网站的部分内容。

authn和authz有时会一起实现，有时也会分开实现。这两者都可能很简单也可能很复杂，看具体需求。

我们前面提到了使用LDAP做账号验证，通常是使用LDAP做authn。当然LDAP也支持简单的authz的功能，
可并不是任何时候都那么方便。

我在使用auth_ldap模块时碰到了有这些问题：

* 对每一个请求，都要该模块进行authn，当然该模块具有一定的缓存能力，但是当各种服务较多时，也会对ldap服务器带来较大的负担。
* 我需要稍微复杂一些authz，但也不需要过于复杂，支持基于uid list/group的验证即可，但创建组要足够方便，也支持嵌套组。

在网上搜了一圈，没有找到称心的解决方案，所以就自己写了一个。放在[Github](https://github.com/StephenPCG/nginx-lua-simpleauth-module)上了。
该项目目前有两个小模块，分别是simpleauthn_cookie和simpleauthz。

## simpleauthn_cookie.lua

这个模块本身并没有authn的功能，因为它不提供持久化存储账号信息的功能。它仅仅是对其他authn提供一个缓存的方案。

网站登录常见的做法：

* 用户发送自己的账号、密码
* 网站验证该账号、密码，如果验证成功，那么常见有两种做法：
    - 在服务器生成一个session_id，以此作为key，账号信息作为value，存放在memcache、redis之类的数据库中，将session_id种到客户端的Cookie中（HTTP响应中带Set-Cookie头即可）。客户端后续访问时带着这个session_id的Cookie，服务器通过查表知道这个session_id对应的账号。
    - 将用户的一些信息以及一些私钥生成一个hash，例如hash = md5(uid+secret)，然后将uid、hash种到客户端cookie中。客户端后续访问时，服务器端验证用户提供的hash和uid是否满足 hash == md5(uid+secret)，如果验证通过，则该用户是uid。

这种基于Cookie的验证缓存方案，可以大大减轻后端（如存放账号密码信息的数据库）的压力。simpleauthn_cookie.lua 就是这样一个模块。

使用这个模块，首先需要配置一个另外的server或location，用于真正的authn后端，其他路径的访问都用simpleauthn即可。例如：

    :::nginx
    init_by_lua 'simpleauthn = require "simpleauthn_cookie"
                 simpleauthn.set_secret_key("your-secret")
                 simpleauthn.set_max_age(3600) 
                 simpleauthn.set_auth_url_fmt('https://auth.example.com/?%s')
                ';
    server {
        server_name auth.example.com;
        ssl on;
        ssl configurations...
        location / {
            auth_ldap "Please login with LDAP account";
            other_auth_ldap_configurations ...;
            # 这里使用auth_ldap模块做authn，验证成功后，种一个cookie。并跳转回登录前的页面。
            content_by_lua 'simpleauthn.set_cookie(ngx.var.remote_user, ".example.com")';
        }
    }
    server {
        server_name app.example.com;
        location / {
            # 验证只需要一句话就可以了。如果发现没有登陆，会跳转到登陆页面进行登陆。
            access_by_lua 'simpleauthn.access()';
        }
    }

## simpleauthz.lua

这个模块提供了最基本的基于uid list/group的authz功能：

* 可以定义若干 group，每个 group 里包含一些 uid，支持嵌套。
* 可以定义一些规则，每个规则中，可以指定一个账号列表（specified by uid/group list），对这个列表进行allow或者deny的判定。

用法示例：

    :::nginx
    lua_package_path '/path/to/module/?.lua;;';
    init_by_lua '-- init authz
                 simpleauthz = require "simpleauthz"
                 simpleauthz.create_group("group1", "alice", "bob", ...)
                 simpleauthz.create_group("group2", "tom", "jerry", "@group1", ...)

                 simpleauthz.create_rule("RULE1", "allow", {"@group1", "Obama"}, {})
                 simpleauthz.create_rule("RULE2", "allow", {"@group2", "alice"}, {"jerry"})
                 simpleauthz.create_rule("RULE3", "deny", {"@group1"}, {})

                 -- init authn
                 simpleauthn = require "simpleauthn_cookie"
                 simpleauthn.set_secret_key("your-secret")
                 simpleauthn.set_max_age(3600)
                 simpleauthn.set_auth_url_fmt("https://auth.example.com/?%s")
                ';

    server {
        server_name apps.example.com;

        location /app1/ {
            # 这里并没有用到authn，仅仅将url中的uid参数当做用户的id。
            # 这里仅作演示，真实的服务器上是不会有人这么傻的。
            # RULE1: 允许alice、bob和Obama访问/app1/。
            access_by_lua 'simpleauthz.access("RULE1", ngx.var.arg_uid)';
        }

        location /app2/ {
            # 这条规则，通过authn.get_uid()来获取当前登陆的用户，如果用户没有登陆，
            # 则直接返回403，当然，这样的用户体验也是很不好的。
            # RULE2：允许tom, alice访问，但不允许jerry访问。
            access_by_lua 'simpleauthz.access("RULE2", simpleauthn.get_uid())';
        }

        location /app3/ {
            # 这个用法，需要注意第二和第三个参数。第二个参数是一个函数，第三个参数是一个值。
            # 首先调用函数来获取当前登陆的用户，如果没有登陆则跳转到登陆页面。若已登陆，则进行authz操作。
            # RULE3：不允许bob和alice访问，但允许所有其他人访问。
            access_by_lua 'simpleauthz.access_with_authn("RULE3", simpleauthn.get_uid, simpleauthn.get_auth_url())';
        }

        # 有两条预定义的规则
        #  ALLOW_ALL： 允许所有已登录的用户
        #  DENY_ALL：禁止所有已登陆的用户（未登陆用户也无法访问）
        location /app4/ { access_by_lua 'simpleauthz.access("ALLOW_ALL", ngx.var.arg_uid)'; }
        location /app5/ { access_by_lua 'simpleauthz.access("DENY_ALL", ngx.var.arg_uid)'; }

        location /app6/ {
            # 这个模块也可以跟nginx的Access模块一起使用，例如下面这个例子中，
            # 如果客户端在192.168.0.0/24这个子网中，则即使没有登陆或者authz失败了，同样可以访问。
            satisfy any;
            allow 192.168.0.0/24;
            deny all;
            access_by_lua 'simpleauthn.access()';
        }
    }

## TODO

* 实现一个纯lua的ldap authn。由于nginx官方release tarball中并不带auth_ldap模块，因此用户需要自己编译。
  如果有一个纯基于lua的ldap authn模块，那么就不需要编译了。
