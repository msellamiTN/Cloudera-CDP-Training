#!/bin/bash

#Tester localement vos codes avant de les soumettes a mapreduce

echo "abdata labs labs mapper mapper reducer" | ./mapper.py | sort -k1,1 | ./reducer.py
#sumbit a job using hadoop streaming
echo "Submtting the first job with default configuration"

hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar \
-D mapreduce.job.name="wordcount" \
-file  mapper.py    -mapper  mapper.py \
-file  reducer.py   -reducer  reducer.py \
-input /user/cloudera/abdata/wordcount/mapreduce.txt \
-output /user/cloudera/abdata/wordcount/output0 
  
#Options de streaming:Configure the number of reducers and mapper

#sumbit a job with 3 mapper and 2 reducer
echo "Submtting the job with 3 mapper and 2 reducer" 

hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar \
-D mapreduce.job.maps=3 \
-D mapreduce.job.reduces=2 \
-file  mapper.py    -mapper  mapper.py \
-file  reducer.py   -reducer  reducer.py \
-input /user/cloudera/abdata/wordcount/mapreduce.txt \
-output /user/cloudera/abdata/wordcount/output_3m_2r \


#sumbit a job with 0 reducers
echo "Submtting the job with default number of  mapper and 0 reducer"  
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar \
-D mapreduce.job.reduces=0 \
-file  mapper.py    -mapper  mapper.py \
-file  reducer.py   -reducer  reducer.py \
-input /user/cloudera/abdata/wordcount/mapreduce.txt \
-output /user/cloudera/abdata/wordcount/output_r0 \


#sumbit a job with 2 reducers
echo "Submtting the job with default number of  mapper and 1 reducer"
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar \
-D mapreduce.job.reduces=2 \
-file  mapper.py    -mapper  mapper.py \
-file  reducer.py   -reducer  reducer.py \
-input /user/cloudera/abdata/wordcount/mapreduce.txt \
-output /user/cloudera/abdata/wordcount/output_r2




cat 03-22-2020.csv | ./covid_mapper.py | sort -k1,1 | ./covid_reducer.py


hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar \
-D mapreduce.job.name="Covid-19" \
-file covid_mapper.py    -mapper covid_mapper.py \
-file covid_reducer.py   -reducer covid_reducer.py \
-input /user/cloudera/covid/format2/   \
-output /user/cloudera/covid/format2_output


## running the second version with full informations 
cat 03-22-2020.csv | ./covid_full_mapper.py | sort -k1,1 | ./covid_full_reducer.py

#
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar \
-D mapreduce.job.name="Covid-19" \
-file covid_full_mapper.py    -mapper covid_full_mapper.py \
-file covid_full_reducer.py   -reducer covid_full_reducer.py \
-input /user/cloudera/covid/format2/   \
-output /user/cloudera/covid/Full_output

# with hadoop and combiner
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar \
-D mapreduce.job.name="Covid-19" \
-file covid_full_mapper.py    -mapper covid_full_mapper.py \
-file covid_full_reducer.py   -reducer covid_full_reducer.py \
-file covid_full_reducer.py   -combiner covid_full_reducer.py \
-input /user/cloudera/covid/format2/   \
-output /user/cloudera/covid/Full_output



#with yarn and combiner
yarn jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar \
-D mapreduce.job.name="Covid-19" \
-file covid_full_mapper.py    -mapper covid_full_mapper.py \
-file covid_full_reducer.py   -reducer covid_full_reducer.py \
-file covid_full_reducer.py   -combiner covid_full_reducer.py \
-input /user/cloudera/covid/format2/   \
-output /user/cloudera/covid/Full_output23

#with yarn and compression
yarn jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar \
"-Dmapreduce.compress.map.output=true" \
"-Dmapreduce.map.output.compression.codec=org.apache.hadoop.io.compress.GzipCodec" \
"-Dmapreduce.output.compress=true" \
"-Dmapreduce.output.compression.codec=org.apache.hadoop.io.compress.GzipCodec" \
-file covid_full_mapper.py    -mapper covid_full_mapper.py \
-file covid_full_reducer.py   -reducer covid_full_reducer.py \
-file covid_full_reducer.py   -combiner covid_full_reducer.py \
-input /user/cloudera/covid/format2/   \
-output /user/cloudera/covid/Full_output23
