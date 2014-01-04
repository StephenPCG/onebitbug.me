Title: The New Blog Comes
Date: 2011-02-01
Category: Life
Tags: debian, nginx, pmon, sqlite, wordpress
Slug: the-new-blog-comes
Author: Stephen Zhang
guid: http://onebitbug.me/?p=13

It’s been a long time I haven’t written any blog since Live Space moved to WordPress.
Meanwhile, all subdomains of wordpress is blocked in China, which makes me more lazy writing blogs.
I was considering buying my own domain name and host space.
As I was busy with the final exam of the term, it had been put off and off.
Finally I get some breath, and bought this domain on GoDaddy with $29/2yrs.
As for the host space, I used my own Fuloong box, and put it in the school library’s server room.

This blog is hosted by wordpress, with nginx and sqlite3.
Personally I prefer such database which needs nearlly zero-configuration and highly portable.
After all, it’s just a personal blog with very poor traffic, MySQL is more than too powerful for this.
For the good of sqlite, when I have to move my blog,
I just need to backup my nginx/php-fastcgi configuration and the entire wp folder.

The hosting operating system is GNU/Debian testing.
As there was no system on the box at first, I was thinking how to install system for it.
I installed system on a loongson box before through network, boot via a USB disk, but I wanna try some way new.
So I took off the harddisk and plugged it onto my own machine, mounted it, and tried debootstrap.
However there was one point that I forgot, at the second stage of debootstrap,
it will chroot in to the target env to proceed on, however, the target env requires MIPS env,
so my poor x86 host can offer nothing… The only thing I can do is give up.

Of course, I can use qemu to install system within my x86 host:

    qemu-mipsel -hda /dev/sdb

but I didn’t try it. I followed an [old article][1].
Since I already had access to the target harddisk, I didn’t need a flash disk,
just copy the bootstrap program into the disk and boot them.

I skimmed [loongson repo on anheng.com][2], and found a useful tool: `pmon-loongson-config`,
after installing the latest kernel, just fire `update-pmon` to update pmon’s `boot.cfg` automatically.
But don’t forget to modify `/etc/fstab` and `boot.cfg`,
change all `hda*` to `sda*`, since in the latest kernel, linux no longer use `hd*` to present harddisk.

I met another problem while using USTC Debian Repo:

    gzip: stdin: invalid compressed data—crc error

At first I thought errors occurred while the repo sync from the upstream,
then I changed to use the upstream mirror, the errors still persist.
After tried dozens of mirrors, I found only the [official repo][3] works.
I don’t know if there were anything wrong with distributing mirrors from the official repo,
or there were anything wrong with my own machine.

So that’s all for this post.
I just wanna replace the default Hello World post of wordpress, so I can test plugins and typesetting. 


[1]: http://blackaureole.wordpress.com/2009/05/08/%E9%BE%99%E8%8A%AF%E7%9B%92%E5%AD%90%E7%AC%94%E8%AE%B0%E6%9C%AC%E5%AE%89%E8%A3%85%E7%B3%BB%E7%BB%9F%E6%96%B9%E6%B3%95%E6%B1%87%E6%80%BB/
[2]: http://www.anheng.com.cn/loongson2f/
[3]: http://ftp.debian.org
