# flightgraph.org

This repository contains the source code for flightgraph.org. It is writen in 
Python and uses the Django web framework.

## Server configuration

flightgraph.org is hosted by Amazon Web Services in an EC2 instance running 
Ubuntu Server. The server configuration is described below.

/etc/nginx/sites-available/flightgraph

```nginx
server {
    listen 8000;
    server_name 0.0.0.0;

    location /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
            root /home/ubuntu/myproject;
    }

    location / {
            include proxy_params;
            proxy_pass http://unix:/home/ubuntu/myproject/myproject.sock;
    }
}
```

```shell
sudo ln -s /etc/nginx/sites-available/flightgraph /etc/nginx/sites-enabled
```

## Database configuration


