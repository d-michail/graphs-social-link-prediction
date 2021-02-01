# Download Neo4j Desktop for Ubuntu
Go to the [Neo4j website](https://neo4j.com/download/) and download the Neo4j Desktop executable file

# Start Neo4j Desktop
Example (your executable file may have a different name depending on the current version of Neo4j):
`./neo4j-desktop-1.4.1-x86_64.AppImage`

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
* Create a new database using the Neo4j Desktop application. To do so:
    * Select 'Add'
    * Select '**Local DBMS**' (Do not start the database yet!)
* Select the 'Terminal' option of the database (check the database's options button (...))
* When the terminal is open run the commands below
```
cd bin
./neo4j-admin import --nodes=Member=fullpath/Member.csv --relationships=Friend=fullpath/Friend.csv
```

After loading, from the Neo4j Desktop user interface:
* Start the database
* Select 'Open' (Open with Neo4j Browser)
* create an index by using the following query: `CREATE INDEX FOR(n:Member) ON(n.name)`

# Perform link prediction 

Run script `predict.py` using 

```
pip install TODO
./predict.py
```
