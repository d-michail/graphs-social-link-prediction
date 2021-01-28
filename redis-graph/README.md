
# Install redis on Ubuntu

```
sudo apt update
sudo apt install redis-server
```

# Install redis graph

```
apt-get install build-essential cmake m4 automake peg libtool autoconf
git clone --recurse-submodules -j8 https://github.com/RedisGraph/RedisGraph.git
make
```

The binary will be at `src/redisgraph.so`.

# Start redis-server 

Use 

```
redis-server --loadmodule redisgraph.so
```

# Bulk loading a graph 

See <https://github.com/redisgraph/redisgraph-bulk-loader>

# Redis Graph examples 

<https://github.com/RedisGraph/RedisGraph/tree/master/demo/social>

