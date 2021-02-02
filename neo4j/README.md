# Download Neo4j Server for Ubuntu
Run the following commands from a bash shell to donwnload the Neo4j Server and the related plugins.
```
# Donwload neo4j server community edition.
wget -O neo4j-community-4.1.6-unix.tar.gz https://neo4j.com/artifact.php?name=neo4j-community-4.1.6-unix.tar.gz
tar -xf neo4j-community-4.1.6-unix.tar.gz
cd neo4j-community-4.1.6/plugins/
# Download Graph Data Science Library plugin
wget https://s3-eu-west-1.amazonaws.com/com.neo4j.graphalgorithms.dist/graph-data-science/neo4j-graph-data-science-1.4.1-standalone.zip
unzip neo4j-graph-data-science-1.4.1-standalone.zip
rm neo4j-graph-data-science-1.4.1-standalone.zip
```

Then, modify the neo4j config file by executing the following commands:
```
cd neo4j-community-4.1.6
`vim conf/neo4j.conf`
```

Add the following line `dbms.security.procedures.unrestricted=gds.*`

Uncomment the following lines and set the heap size to something big (let's say something greater than 8GB)

```
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=512m
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

They can be used with <https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin> in order to load the graph into Neo4j. To load them you should:
```
cd neo4j-community-4.1.6
cd bin
./neo4j-admin import --nodes=Member=fullpath/Member.csv --relationships=Friend=fullpath/Friend.csv
```

After loading execute the following commands:
```
cd neo4j-community-4.1.6
cd bin
./neo4j console
```
From a different terminal execute the following commands:
```
cd neo4j-community-4.1.6
cd bin
./cypher-shell
```
While being into the cypher-shell create an index by using the following query:
`CREATE INDEX FOR(n:Member) ON(n.name);`

# Perform link prediction 

Run script `predict.py`

```
pip install neo4j
./predict.py
```

# Remove database data

If you want to remove the data from the database execute the following commands:

```
 cd neo4j-community-4.1.6/data
 rm -rf databases/neo4j/*
 rm -rf transactions/neo4j/*
```
