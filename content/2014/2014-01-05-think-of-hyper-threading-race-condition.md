Title: 超线程竞争问题引发的思考
Slug: think-of-hyper-threading-race-condition
Date: 2014-01-05 22:20
Category: Linux

### 问题起因

Varnish有一个bug（或者说feature也许更合适一些），有一个项资源`sess_mem`，对应一个计数器`n_sess`，
有人要用就`+1`，用完就`-1`，另外有一个函数会根据这个数字来决定是否要预分配更多的空间。
这里，为了避免太多的性能损耗，所以对`n_sess`的操作并没有加锁。在多线程（本文中`多线程`均指软件概念上的线程，
超线程指CPU的超线程技术）的环境下对同一个变量进行不加锁的读写肯定是有问题的，但是，因为在一段时间内`+`和`-`
的数量相当，因此一个线程中`+`和`-`操作被其他线程吞没的概率也相当，所以最终`n_sess`距离精确值的偏差（后面称漂移）
应该在一个比较小的范围内（即误差应该比较小），varnish认可这个误差，通过其他方式来定期的校准一下（例如定期
的数一下实际被使用的`sess_mem`有多少个）这个值。

然而，问题来了，有人发现，在启用了超线程(Hyper-Threading)的机器上，varnish经常会出现疯狂的分配`sess_mem`的情况，
直到`n_sess`达到一个预定的最大值（默认为100000），并且可以很容易的复现这个现象。
于是有人做了实验来验证了这个问题。见这个[ticket](https://www.varnish-cache.org/trac/ticket/897)。

这个问题在两年前被fix了，不过很可惜，我们2012年（好吧，习惯说去年，结果发现这个时候说去年歧义太大）
开始使用varnish时，debian stable中的varnish版本还没有修复这个问题，
且这个问题在压力比较小时不容易出现，所以一直没有发现。到2012年底发现varnish经常雪崩，但并没有找到原因。
今天无意中发现varnishstat输出中的`n_sess`特别高，于是搜索到了这个ticket。

### 实验

耳闻为虚，眼见为实，上面的ticket中只给了结论，因此我也亲自写代码实现了一下。代码如下：

```
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

volatile long counter = 0;

struct thread_arg{
    int cpu;
    long count;
};

void* iter(void* arg) {
    int cpu = ((struct thread_arg*)arg) -> cpu;
    long i = ((struct thread_arg*)arg) -> count;

    cpu_set_t cpuset;
    pthread_t thread = pthread_self();

    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);
    if (pthread_setaffinity_np(thread, sizeof(cpu_set_t), &cpuset) != 0)
        printf("pthread_getaffinity_np() failed.");

    for (; i>0; --i) {
        ++counter;
        --counter;
    }
}

int main(int argc, char** argv) {
    pthread_t thread1, thread2;
    struct thread_arg arg1, arg2;
    long count = 1000000000L;
    clock_t start, end;

    arg1.count = count;
    arg1.cpu = 0;
    arg2.count = count;

    int cpu = 0;

    for (cpu=0; cpu<8; cpu++) {
        counter = 0;
        arg2.cpu = cpu;

        start = clock();
        pthread_create(&thread1, NULL, iter, (void*)&arg1);
        pthread_create(&thread2, NULL, iter, (void*)&arg2);
        pthread_join(thread1, NULL);
        pthread_join(thread2, NULL);
        end = clock();

        printf("cpu0 vs cpu%d (%ld iterations in %.2f s)... counter drift = %ld\n",
                arg2.cpu, count, (end-start)*1.0/CLOCKS_PER_SEC, counter);
    }

    return 0;
}
```

编译运行：
```
$ gcc -l pthread httest.c

$ ./a.out
cpu0 vs cpu0 (1000000000 iterations in 6.78 s)... counter drift = 5
cpu0 vs cpu1 (1000000000 iterations in 15.72 s)... counter drift = 6539
cpu0 vs cpu2 (1000000000 iterations in 15.96 s)... counter drift = 6652
cpu0 vs cpu3 (1000000000 iterations in 16.02 s)... counter drift = 5260
cpu0 vs cpu4 (1000000000 iterations in 11.53 s)... counter drift = 10421225
cpu0 vs cpu5 (1000000000 iterations in 15.82 s)... counter drift = 6517
cpu0 vs cpu6 (1000000000 iterations in 16.12 s)... counter drift = 8464
cpu0 vs cpu7 (1000000000 iterations in 16.16 s)... counter drift = 6012

$ grep 'core id' /proc/cpuinfo
core id     : 0
core id     : 1
core id     : 2
core id     : 3
core id     : 0
core id     : 1
core id     : 2
core id     : 3
```

通过`top`查看cpu使用情况，如果两个都在cpu0上跑，发现只有cpu0被占满，其他核都是空载，
当选中两个不一样的核时，这两个核都会跑到100%，说明set affinity有效。

上面的结果中，除了重现了ticket中所述的漂移量的问题，还有两个有趣的现象：

* 当两个线程分别在不同的核上跑，速度最慢，在同一个核上跑最快，在一个核的不同超线程跑速度居中。
* <del>反复运行上述代码，counter drift总是正，交换`++`和`--`语句的顺序，counter drift总是负的。</del>
  反复运行，大多数情况下counter drift是正数，极少数情况下`cpu0 vs cpu0`的counter drift会出现负数，
  `cpu0 vs cpu*`总是正数。

### 分析原因

下面尝试分析产生这种现象的原因，以下内容并没有得到实验证实，仅仅是个人的猜想，欢迎大家讨论、指正。

* 在不同的core pair上运行时间不同，首先猜想是因为CPU一级缓存的原因。
  每个物理核独享一、二级缓存，共享三级缓存。
  当两个线程在同一个核上运行时，所有读、写`counter`变量的操作都命中cache，因此基本没有访存时间开销。
  当两个线程在不同物理核上运行时，一、二级缓存总是会失效，而要访问三级缓存，导致时间变长。
* 在相同物理核的不同超线程上运行的时间，比在同一个核上要短，猜测可能有两种原因：
    - 每个超线程独享一级缓存，两个超线程共享二级缓存。但我没有找到有关资料，
      在wiki上找到的关于我这个CPU（i7 3770）写一、二级cache都是per core的，
      但没有说明这里的core是physical core还是logical core。
    - 超线程本身的原因所致，超线程本身的意义在于，同时发射的两条指令使用不同的运算单元
      （如一个用ALU，一个用FPU），如果两条指令都是用相同的运算单元，则无法同时发射(issue)，
      这个实验中，显然两个线程的指令都会在使用相同的运算单元，因此不能同时发射，
      如果是这样，那么用两个线程完成这么多计算，应该跟用一个线程完成这么多计算所耗的时间相同，
      而不会更慢。因此我觉得缓存因素可能性更大一些。
* 我们先贴一下对counter自增、自减操作的汇编代码，再尝试继续分析：

```
.L4:
        jmp     .L5
.L6:
        movq    counter(%rip), %rax
        addq    $1, %rax
        movq    %rax, counter(%rip)
        movq    counter(%rip), %rax
        subq    $1, %rax
        movq    %rax, counter(%rip)
        subq    $1, -8(%rbp)
.L5:
        cmpq    $0, -8(%rbp)
        jg      .L6
        leave
```

* 如果两个线程在同一个核、同一个超线程上运行，对于每个线程，都会运行很长一段时间（for循环许多次）才被切换出去，
  整个for循环可能只被打断了很少的次数，每次context switch，最多带来±1的误差（也可能没有误差）。
    - 不妨更细致的分析一下，由上述汇编可以看到，循环体内共九条指令（抱歉偷懒不画图了，就用文字描述了）：
        - `1:内存读` - `2:寄存器加` - `3:内存写` - `4:内存读` - `5:寄存器减` -
          `6:内存写` - `7:寄存器减(i--)` - `8:比较` - `9:跳转`
    - 简化的循环流程为 `1:Mem->Reg` - `2:Reg-+/-` - `3:Reg-Mem`，运行奇数轮之后counter应该=1，偶数轮之后为0。
    - 如果thread1执行完某个`Mem->Reg`后被切出，thread2开始运行，假设正好运行了`读-op-写`完整的奇数轮之后被切出，
      此时继续执行thread1，此时Mem和Reg1产生1点误差。如果thread2的奇数轮中，加法多一次，则会导致Reg1比Mem少1，
      thread1计算并写回后回导致最终结果偏差-1；如果thread2的奇数轮中，减法多一次，则thread1计算写回后最终结果偏差1。
      由此分析，反复运行的话，这个漂移应该有正、有负，但实际情况是漂移总是正的。
    - 可以这样构造出一个漂移为-1的情形：
        - thread1运行到`4:内存读`，这时候内存为1，thread1的寄存器为1，此时线程切出
        - thread2运行若干遍，到`3:内存写`，这时候内存为2，thread2的寄存器为2，此时线程切出
        - thread1继续运行`5:寄存器减`，变为0，写回0，继续运行直到线程工作结束
        - thread2继续运行`4:内存读`，得到0，运行`5:寄存器减` `6:内存写`之后，寄存器、内存都变为-1，继续运行直到工作结束
        - 按照这个context switch的序列，最终结果是-1。
    - 漂移为负数的情况少时可以理解的，产生漂移的条件是thread1在1之后或者4之后被切出，thread2在3之后或6之后被切出，
      仅当有一次在3之后被切出时会产生奇数轮外，不会产生奇数轮的情况，在6之后被切出有4种可能（分别在6、7、8、9被切出），
      而在3之后被切出只有1种可能，因此两者的概率约1:4。
    - 当然这个分析并不完整，1:4应该是个错误的结论，但应该是一个差不多悬殊的比值。
* 如果两个线程在不同的物理核上运行，两者分别对自己的一级缓存操作，互不干涉。
  假设cpu在执行过程中从不检查是否一级缓存与三级缓存同步，尽在程序执行完成后检查一次，那么漂移应该为0。
  cpu每检查（并尝试同步）一次一级、三级缓存是否同步，最多造成1点误差。
  因此可以认为，如果drift == 6000，则至少发生了6000此缓存同步操作。
  分析方法同上，在两次缓存同步期间，thread1进行了奇数轮`读-op-写`，则会产生-1的偏差，否则产生1的偏差，
  这个偏差的比例通常，大约1:4。因此如果同步1w次，则偏差为`(1w*0.2*-1)+(1w*0.8*1) = 6000`。
  所以，从统计的角度看，这个drift几乎总是为正。 
* 为了验证上述结论，将for循环的count减小到1000次，反复运行，发现确实各种cpu pair都会产生负的drift。
* 两个线程在同一个物理核的不同hyperthread上运行时drift很大，如果延续上述的理解方法的话，是否可以理解为
  L1 cache与L2 cache的同步频率高于L2 cache与L3 cache的同步频率。
* 按照上述猜测，
    - L2与L3 cache同步的频率大概为 1w/16s = 625 Hz，
    - L1与L2 cache同步频率大概为：1kw*5/3 / 11.5s = 1449275 Hz
* 不知道哪里能查到CPU cache的同步频率数据，来验证一下上述猜测是否正确。

### 结论

这篇文章仅给出了一个现象。而结论嘛，上面分析了一大堆都只是自己的猜测，没有数据和实验的支持。
如果您有这方面的数据或知识，欢迎指点！
