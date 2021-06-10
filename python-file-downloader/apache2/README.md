
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
sudoedit /etc/apache2/sites-available/fileServerApp.conf
```

**fileServerApp.conf contents**
```
## /etc/apache2/sites-available/fileServerApp.conf
<VirtualHost *>
 ServerName my.fileserver.address.com
 WSGIDaemonProcess fileServerApp user=vagrant group=vagrant threads=5
 WSGIScriptAlias / /home/vagrant/apache2/fileServerApp.wsgi
<Directory /home/vagrant/apache2/>
 WSGIProcessGroup fileServerApp
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
$ sudo a2ensite fileServerApp.conf
$ sudo service apache2 restart
```

# WSGI-Script already exists.
You shouldn't have to do the tutorial section titled
"Your Own moi.wsgi Script" as that is already written in the "apache2" folder

# Assets Folder
The `assets` folder is where file server looks for files to serve.

In `fileServerApp.py` there is a line that currently defines this folder relative to the folder containing `fileServerApp.py`  which looks like this:
```python
assetPath = os.path.join(rootPath, '../assets')
```
That is

```
  some_root_dir
   |
   |
   -apache2
   |   |
   |   -fileServerApp.py
   |   - ...
   |
   -assets
       |
       - firmware_image_1.bin
       - firmware_image_2.bin
       _...
```

You can change the location of this assets folder by changing the value of `assetPath` in `fileServerApp.py`




