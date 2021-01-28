
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

# Bulk load a graph 

Download LiveJournal to `../data`. Preprocess it using 

```
./preprocess.py -i ../data/soc-LiveJournal1.txt.gz -o livejournal
```

You will get two files 

```
livejournal.nodes.csv.gz
livejournal.edges.csv.gz
```

They can be used with <https://github.com/redisgraph/redisgraph-bulk-loader> in order to 
load the graph into Redis. Make sure you decompress them first. To load them you can: 

```
pip install redisgraph-bulk-loader
redisgraph-bulk-loader LIVEJOURNAL -n livejournal.nodes.csv -r livejournal.edges.csv
```

# Redis Graph examples 

<https://github.com/RedisGraph/RedisGraph/tree/master/demo/social>

