
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
./preprocess.py -i ../data/soc-LiveJournal1.txt.gz
```

You will get two files 

```
Member.csv
Friend.csv
```

They can be used with <https://github.com/redisgraph/redisgraph-bulk-loader> in order to 
load the graph into Redis. Make sure you decompress them first. To load them you can: 

```
pip install redisgraph-bulk-loader
redisgraph-bulk-loader GRAPH -n Member.csv -r Friend.csv
```

After loading create an index by using the following query in `redis-cli`:

```
GRAPH.QUERY GRAPH "CREATE INDEX ON :Member(name)"
```

# Perform link prediction 

Run script `predict.py` using 

```
pip install redisgraph
./predict.py
```

# Redis Graph examples 

<https://github.com/RedisGraph/RedisGraph/tree/master/demo/social>

