
# Base line tutorial
I started with this tutorial

[Getting Apache up and running with Flask](https://terokarvinen.com/2016/deploy-flask-python3-on-apache2-ubuntu/)


# Packages Used in this Example

```bash
$ pip3 install flask
$ pip3 install flask_restful
$ pip3 install webargs
```

# Apache site-available config file.

Replaces `moi.conf` in the tutorial.

**Command for opening editor**
```bash
sudoedit /etc/apache2/sites-available/notehubEndpointApp.conf
```

**notehubEndpointApp.conf contents**
```
## /etc/apache2/sites-available/notehubEndpointApp.conf
<VirtualHost *>
 ServerName my.server.address.com
 WSGIDaemonProcess notehubEndpointApp user=vagrant group=vagrant threads=5
 WSGIScriptAlias / /home/vagrant/apache2/notehubEndpointApp.wsgi
<Directory /home/vagrant/apache2/>
 WSGIProcessGroup notehubEndpointApp
 WSGIApplicationGroup %{GLOBAL}
 WSGIScriptReloading On
 Require all granted
</Directory>
</VirtualHost>
```

### Setting Default Site and Disabling Others
It's not clear to me this is exactly what you want to do, but it's a good starting point for testing

```bash
$ sudo a2dissite 000-default.conf
$ sudo a2ensite notehubEndpointApp.conf
$ sudo service apache2 restart
```

# WSGI-Script already exists.
You shouldn't have to do the tutorial section titled
"Your Own moi.wsgi Script" as that is already written in the "apache2" folder


