
# Install redis on Ubuntu

```
sudo apt update
sudo apt install redis-server
```

Open file `/etc/redis/redis.conf` and change the `supervised` directive to `systemd`. 
Then start using 

```
sudo systemctl restart redis.service
```

# Install redis graph

```
apt-get install build-essential cmake m4 automake peg libtool autoconf
git clone --recurse-submodules -j8 https://github.com/RedisGraph/RedisGraph.git
make
```

The binary will be at `src/redisgraph.so`. Load it by opening `/etc/redis/redis.conf` 
and adding a line like: 

```
loadmodule /path/to/module/src/redisgraph.so
```

# Redis Graph examples 

<https://github.com/RedisGraph/RedisGraph/tree/master/demo/social>

