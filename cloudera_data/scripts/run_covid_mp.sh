 hadoop fs -get /user/cloudera/raw_data/covid_app/*.py .
 hadoop fs -get /user/cloudera/raw_data/covid/*.csv
cat covid/covid19_dataset_part_1.csv | ./covid_full_mapper.py | sort | ./covid_full_reducer.py  
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar -D mapreduce.job.name="Covid-19" -file covid_full_mapper.py    -mapper covid_full_mapper.py -file covid_full_reducer.py   -reducer covid_full_reducer.py -input /user/cloudera/raw_data/covid/   -output /user/cloudera/clean_data/covid/Full_outputFinal
yarn jar /usr/lib/hadoop-mapreduce/hadoop-streaming-*.jar  -D mapreduce.job.name="Covid-19" -file covid_full_mapper.py    -mapper covid_full_mapper.py -file covid_full_reducer.py   -reducer covid_full_reducer.py -input /user/cloudera/raw_data/covid/   -output /user/cloudera/clean_data/covid/Full_outputFinal2
