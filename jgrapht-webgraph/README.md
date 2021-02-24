
# Preprocess 

```
./preprocess.py -i ../data/twitter_combined.txt.gz -r true -o data.txt
```

# Run with JGraphT sparse


```
java -cp target/linksocial-0.0.1-SNAPSHOT.jar org.hua.linksocial.LoadAndPredictSparseGraphApp -renumberFile renumber.txt -mindegree 250 data.txt
```
