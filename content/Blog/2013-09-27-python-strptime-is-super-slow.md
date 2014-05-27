Title: strptime 真慢……
GitTime: off
Slug: python-strptime-is-super-slow
Date: 2013-09-27 14:47

写了一个脚本用来分析nginx日志，结果发现慢的难以忍受，每秒仅能处理4M左右的日志数据。
根据以前写python的经验，不应该慢到这种程度，因此用[pycallgraph][1]跑了一下，结果如
下图（由于图片太大，可以下载到本地查看）：

{% img /images/posts/2013-09-27/pycallgraph-1.png %}

从图中可以看到，75%以上的时间都消耗在了`strptime()`这个函数上了。被调用的这行代码如下：

```python
from datetime import datetime
while a-big-loop:
    tstr = '26/Sep/2013:15:48:46 +0800'
    t = datetime.strptime(tstr, '%d/%b/%Y:%H:%M:%S +0800')
```

由于我并不需要每行日志的具体时间，只需要一个秒级的递增的数（这个脚本每读取出5秒的日志
就输出一次该5秒内的统计信息）。所以最后的解决方法是修改nginx配置，使其输出日志时直接
输出unix timestamp（`$msec`，样例：`1380263457.387`），这样python中直接float(tstr)即可。

再次运行pycallgraph的结果如下图（两图的日志样本不相同，上图日志1382695行，本图1823525行）：

{% img /images/posts/2013-09-27/pycallgraph-2.png %}

不过既然发现了这个问题，不妨做一些实验，看看如何能够提高处理这种格式时间戳的效率，
这毕竟是一个很常见的需求。我们来做一些测试。

由于月份转化的特殊性，我们先假定时间格式为：`2006/01/02:15:04:05`，首先看一下
`strptime()`的速度：

```
>>> timeit.timeit('datetime.strptime("2006/01/02:15:04:05", "%Y/%m/%d:%H:%M:%S")',
...                   'from datetime import datetime', number=5000000)
83.93022108078003
```

这里字段规整，可以用`split()`来做：

```
>>> import re
>>> def with_regex(tstr):
...     return datetime.datetime(*map(int, p.split(tstr)))
... 
>>> timeit.timeit('with_regex("2006/01/02:15:04:05")',
...                   'from __main__ import with_regex', number=5000000)
16.251402854919434
```

这里，时间的各字段宽度确定，因此可以用slice来做：

```
>>> import timeit
>>> def with_indexing(tstr):
...     return datetime.datetime(*map(int, [tstr[:4], tstr[5:7], tstr[8:10],
...                                         tstr[11:13], tstr[14:16], tstr[17:]]))
...
>>> timeit.timeit('with_indexing("2006/01/02:15:04:05")',
...                   'from __main__ import with_indexing', number=5000000)
12.590821981430054
```

这个方法，速度快了6倍多。然而这个方法具有很强的局限性。上述slice的方法书写极易出错，
且不易维护。而split和slice两种方法都要求所有字段都是数字，否则书写会变得更加麻烦。
但是在特定情况下，这不失为一个好的选择。

再看最初的需求，时间的格式为：`26/Sep/2013:15:48:46 +0800`，我们尽力来提高一下性能。

仍然先看一下直接`strptime`的速度：

```
>>> timeit.timeit('datetime.strptime("26/Sep/2013:15:48:46", "%d/%b/%Y:%H:%M:%S")',
...                   'from datetime import datetime', number=1000000)
16.97735905647278
```

用正则式分隔的速度：

```
>>> months = ['-', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
>>> p = re.compile('(\d{2})/(\w{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2})')
>>> def with_regex(tstr):
...     result = p.search(tstr).groups()
...     day, year, hour, minute, second = map(int, [result[0], result[2], result[3], result[4], result[5]])
...     month = months.index(result[1])
...     return datetime(year, month, day, hour, minute, second)
...
>>> timeit.timeit('with_regex("26/Sep/2013:15:48:46")', 'from __main__ import with_regex', number=1000000)
3.47182512283
```

从第一张pycallgraph可以看出，`strptime`慢主要慢在跟locale有关的处理上，然而，
在处理日志等日常操作中，这往往是不重要的。然而[fmt][2]中有大量的转义符都与locale相关，如：

```
%b      Month as locale’s abbreviated name.
%B      Month as a zero-padded decimal number.
```

以中文环境启动python，`LC_ALL=zh_CN.utf8 LANG=zh_CN bpython`，打印可见：

```
>>> from datetime import datetime
>>> print datetime.now().strftime('%b %B')
9月 九月
```

从这里也可知，前面的方法`datetime.strptime('26/Sep/2013:15:48:46', '%d/%b/%Y:%H:%M:%S')`
并不是一个可靠地方法，在不同的locale下面就会出错，无法识别该时间串。实际验证也确实如此：

```
>>> datetime.strptime('26/Sep/2013:15:48:46', '%d/%b/%Y:%H:%M:%S')
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File "/usr/lib/python2.7/_strptime.py", line 325, in _strptime
    (data_string, format))
ValueError: time data '26/Sep/2013:15:48:46' does not match format '%d/%b/%Y:%H:%M:%S'
```

根据以上的各种乱七八糟的尝试可以得出结论：

* 如果一个脚本运行的locale可能会变，或者说无法预知、控制脚本将来的运行环境，
  那么应该避免使用`strptime()`。
* 如果这个脚本对性能要求很高，且对时间处理函数调用频率很高，那么应该避免使用`strptime()`，
  而是通过slice或者正则式来自行分析，效率会提高许多。

[1]: https://github.com/gak/pycallgraph/
[2]: http://docs.python.org/2.7/library/datetime#strftime-and-strptime-behavior
