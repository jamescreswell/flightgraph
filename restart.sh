gunicorn --daemon --workers 3 --bind unix:/home/ubuntu/flightgraph/flightgraph.sock flightgraph.wsgi
sudo service nginx restart
