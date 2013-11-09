Title: cygwin编译GUI应用
Slug: cygwin-compile-non-console-program
Date: 2012-11-02
Author: Stephen Zhang
Category: Other

```
gcc -oQQExternal.exe -mwindows -xc - <<< "int main(){sleep(0x2b);}"
```

据说QQExternal.exe是为了提升QQ稳定性的，一些容易出问题的组件会放在这个进程运行。 
杀掉这个进程也没有关系。而在我的机器上，碰到过好几次QQExternal.exe占满一个核的CPU，
有时候甚至会占用上G的内存，显然，这个组件相当的不稳定。

没有精力去折腾精简QQ，就用个最裸的方法，自己写个程序替换掉原来的QQExternal.exe。

参数解释：
```
-mwindows [将程序链接为GUI应用][1]
-xc       由于从stdin输入，因此gcc无法判断输入的源码的语言
```

好吧，标题似乎有点太大了。。。
