# flightgraph.org

This repository contains the source code for flightgraph.org. It is writen in 
Python and uses the Django web framework.

## Server configuration

flightgraph.org is hosted by Amazon Web Services in an EC2 instance running 
Ubuntu Server. The server configuration is described below.

Server information in `/etc/nginx/sites-available/flightgraph`:

```nginx
server {
    listen 8000;
    server_name 54.91.110.22;

    location /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
            root /home/ubuntu/flightgraph;
    }

    location / {
            include proxy_params;
            proxy_pass http://unix:/home/ubuntu/flightgraph/flightgraph.sock;
    }
}
```

Use the following shell commands to enable the configuration and restart the server, resepectively:

```shell
sudo ln -s /etc/nginx/sites-available/flightgraph /etc/nginx/sites-enabled
```

```shell
gunicorn --daemon --workers 3 --bind unix:/home/ubuntu/flightgraph/flightgraph.sock flightgraph.wsgi
sudo service nginx restart
```

## Database configuration

```shell
sudo apt-get install mysql-server
sudo apt-get install python-dev libmysqlclient-dev
sudo apt-get install python3-mysqldb
mysql -p -u root
CREATE DATABASE flightgraph;
```


