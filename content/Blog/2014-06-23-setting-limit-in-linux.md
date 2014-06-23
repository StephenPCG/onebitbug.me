Title: 配置 limit 参数
Slug: setting-limit-in-linux
Tag: ulimit, linux, upstart, sysvinit

曾经被配置ulimit这个问题困扰过很久，后来终于搞清楚了，写一篇文章记录一下。

做过访问量比较大的web服务的人可能都修改过``max open files``，
在Linux中一个TCP socket就是一个文件，所以当并发请求大于1024时
（Debian/Ubuntu等默认的``max open files``是1024），
服务软件（如nginx）就会开始抱怨``Too many open files ...``。

修改``max open files``最直接的方法是直接执行：

    :::sh
    ulimit -n 655350

但是很快就会发现，新开一个SSH连接到服务器上，执行``ulimit -n``看到的还是``1024``。
``ulimit``的修改仅对当前shell有效。
这是因为，``rlimit (resource limit)``是一个进程的属性，所以不出意外的，
修改``rlimit``的命令``ulimit``是shell的内建命令
（使用bash的话可以通过``man bash-builtins``获得帮助）。
同样不出意外的，可以通过``/proc/[pid]/limits``来查看各进程当前的limit配置情况。

``rlimit``属性在``fork()``时会被继承，在``exec()``时会保留，说人话就是，
子进程会继承父进程的``rlimit``属性。

通过简单的搜索，或者在``/etc/``下走一遭，就会发现``/etc/security/limits.conf``
和``/etc/security/limits.d/``。很happy的发现，修改之后重新启动应用程序发现生效了！
直到有一天发现，使用[salt](http://www.saltstack.com/)启动的程序``max open files``
仍然是1024。
经过检查发现，``salt-minion``进程的``nofile``确实是1024，所以毫不奇怪的，
其启动的子进程也都是``1024``。

经过一番搜索，以及通过``man pam_limits``的帮助，``/etc/security/limits.{conf,d/}``
仅在某些特定的情况下被应用，例如``sshd``、``login``、``cron``、``su``等，
所以通过ssh登陆系统后获得的shell应用了``limits.conf``的配置，
然后再手动启动的程序也都继承了该配置，
而通过upstart、sysvinit等启动的服务没有应用该配置。

找到了原因，就很容易找到解决方案。

对于``upstart``，可以在配置文件（如``/etc/init/${service}.conf``）中添加相应的配置
[帮助链接](http://upstart.ubuntu.com/wiki/Stanzas#limit)：

    :::sh
    limit $resource $softlimit $hardlimit

对于``sysvinit``，由于启动脚本（``/etc/init.d/${service}``）就是普通的shell脚本，
所以直接在开头加上``ulimit``命令即可，更新当前sh进程的配置，子进程自然继承。

对于``systemd``，参考``man systemd.exec``，在配置文件中增加``Limit${Resource}=xx``即可。

如果发现有其他进程的limits配置不对，那么首先查看一下这个进程是如何被启动的，向上追述。
通常，通过任何手段登陆进系统之后手动启动的进程，都会应用``pam_limits.so``
（至少Debian/Ubuntu默认配置如此），
如果没有被应用，那么检查``/etc/pam.d/``中的配置。
对于非手动启动的进程，那么通常会使用某种``init system``
（最常见的是upstart、sysvinit、systemd）启动，参考相应工具的文档即可。
