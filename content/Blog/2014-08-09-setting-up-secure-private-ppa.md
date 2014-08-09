Title: Setting Up a Secure Private PPA
Slug: setting-up-secure-private-ppa
Tag: debian, ppa, https, linux

For those companies and organizations who use Debian or Ubuntu for their servers,
a PPA (personal package archive) is a good friend of the Ops team.

We often need to make small modifications to some softwares and recompile them to
fit our own requirements. ``.deb`` files are easy to reuse among a lot of servers,
and proper ``{pre,post}{inst,rm}`` scripts also makes deployment easier.
With a bunch of ``.deb`` files, we need a center store to organize and
distribute them. A PPA is a good choice for this purpose.

A PPA is usually exported via HTTP, however, apt's http method does not support
any kind of authentication.
Also, since HTTP's traffic is in plain, anyone sit on a network device in between
your PPA and your server can easily capture the traffic and get access to the PPA.
Thus common authentication methods based on HTTP do not provide more security.

Let's have a look at what methods are supported by apt:

```
$ apt-file search /usr/lib/apt/methods/
apt: /usr/lib/apt/methods/bzip2
apt: /usr/lib/apt/methods/cdrom
apt: /usr/lib/apt/methods/copy
apt: /usr/lib/apt/methods/file
apt: /usr/lib/apt/methods/ftp
apt: /usr/lib/apt/methods/gpgv
apt: /usr/lib/apt/methods/gzip
apt: /usr/lib/apt/methods/http
apt: /usr/lib/apt/methods/lzma
apt: /usr/lib/apt/methods/mirror
apt: /usr/lib/apt/methods/rred
apt: /usr/lib/apt/methods/rsh
apt: /usr/lib/apt/methods/ssh
apt: /usr/lib/apt/methods/xz
apt-transport-https: /usr/lib/apt/methods/https
apt-transport-spacewalk: /usr/lib/apt/methods/spacewalk
apt-transport-tor: /usr/lib/apt/methods/tor
apt-transport-tor: /usr/lib/apt/methods/tor+http
apt-transport-tor: /usr/lib/apt/methods/tor+https
```

Wow! a long list!

From the names, we can easily find out two method with encryption and possibly authentication,
``ssh`` and ``https`` (ssh and rsh are the same binary).

For someone, the ssh method seems to be the most secure one. However, it has several Cons:

* It's complicated to setup, we have to distribute an ssh secret key to all servers' root account.
  With the help of a central configuration management tool like puppet, salt etc., it's not a problem.
* From the source code, we can see that ssh method logins the repository server and execute ``sh``,
  redirect its stdio and then use it for communications. It also needs tools like ``find``, ``dd``.
  For some teams with strong security policy, allow an ssh account to execute ``sh`` for just repository
  access it not accessible (my company is one of them). If however a server is cracked in, the cracker
  can then login the repository server and may get more sensitive data.

So we choose the https method. To use it, we will have ``apt-transport-https`` installed first.

The https method supports client side ssl authentication. Here is a brief introduction to how https
client side ssl authentication works, for those who don't already know.

* Create a CA cert, used to sign the clients' ssl certs.
* Config the https server to trust all certs signed by the CA (treat them as authenticated).
* Usually the server support a crl (cert revoke list) to revoke some specific client certs.

I will take nginx to setup the https server for example. Setup https as usual:

```
server {
    listen 443;
    server_name ppa.company.com;

    ssl on;
    ssl_certificate /path/to/ssl/cert;
    ssl_certificate_key /path/to/ssl/key;
    # other ssl options, like preferred ciphers, protocols, etc.
}
```

and then add two more directives:
```
server {
    ...
    ssl_verify_client on;
    ssl_client_certificate /path/to/ca.crt;
    ...
}
```

The first one enables client side ssl authentication, and the second one points to the ca cert
used to sign the clients' ssl certs.

That should be enough for the server side configuretion.

In the client side, firstly we should generate a key/cert pair, and sign the cert with the CA.
Create a apt conf file and put in ``/etc/apt/apt.conf.d/00ssl-client-auth``, with content:

```
Acquire::https::SslCert /path/to/apt-client.crt;
Acquire::https::Sslkey /path/to/apt-client.key;
```

If you will have multiple https repositories added into system, and need different client certs,
you can change the directive to:

```
Acquire::https::ppa.company.com::SslCert /path/to/apt-client.crt;
Acquire::https::ppa.company.com::Sslkey /path/to/apt-client.key;
```

Well, everything is done in the client side too. Enjoy now!

It's a pitty that there is few documents provided by the debian team, and it's also hard to find
useful instructions use google search with key words like "setting up private debian repo".
I believe most of debian system admins don't know the apt's https method support client side ssl
authentication. I find it out by looking into the https method's source code.
If you search with keyword "Acquire::https::SslCert", you can find some useful links however.
