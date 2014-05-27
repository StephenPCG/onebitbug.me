Author: Stephen Zhang
GitTime: off
Title: NIC Packet Broken Issue Solved
Tags: ethtool, loongson, rtl8169, rx offload
guid: http://onebitbug.me/?p=19
Slug: nic-packet-broken-issue-solved

In the [first post][1], I mentioned that errors occurred while using USTC Debian Repo to upgrade this server.
There were also problems when transfering data with scp and wget at a high speed (>5MB/s).

Thanks for [Shiwei Liu][2]'s help, the problem is solved now.
It is due to a bug in rtl8169 nic.
When the firmware version is below 25, we should turn off rx offload option.
RX offload is the checksum for received mac packets.
rtl8169 computes this checksum in hardware, to reduce CPU workload, when rx offload is on, the operating system will not compute it again.
But there is a bug in computing rx offload checksum with firmware version below 25, so we should turn it off with ethtool:

    ethtool -K eth0 rx off

After executing the above command, everything works fine!

[1]: {% post_url 2011-02-01-the-new-blog-comes %}
[2]: http://www.bjlx.org.cn/blog/1
