#!/bin/bash

# Download dataset in an empty directory

echo "Suppression success"
rm -rf COVID-19-master

hadoop fs -rm -rf /user/cloudera/covid/

hadoop fs -rm -rf /user/cloudera/covid/format1

hadoop fs -rm -rf /user/cloudera/covid/format2
echo "Suppression success"
wget https://codeload.github.com/CSSEGISandData/COVID-19/zip/master -O covid-19.zip

echo "Suppression success"

unzip covid-19.zip

cd COVID-19-master

echo "Suppression success"

# Remove commas between double quotes
sed -i ':a;s/^\(\([^"]*,\?\|"[^",]*",\?\)*"[^",]*\),/\1 /;ta' COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/*.csv

# Replace original file dates to match the dates included in the file names
for f in COVID-19-master/csse_covid_19_data/csse_covid_19_daily_reports/*.csv; do
    fdate=$(basename $f .csv | awk -F- {'print $3"-"$1"-"$2'})
    echo $fdate
    touch -d "$(date -d $fdate)" $f
done

# Copy the files to different directories depending on the date. They have different formats
mkdir format1
mkdir format2

find COVID-19-master/csse_covid_19_data/csse_covid_19_daily_reports/ -maxdepth 1 -not -newermt "2020-03-21" -exec basename \{} .po \; | grep csv | sort | xargs -I % mv COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/% format1/
find COVID-19-master/csse_covid_19_data/csse_covid_19_daily_reports/ -maxdepth 1 -newermt "2020-03-21" -exec basename \{} .po \; | grep csv | sort | xargs -I % mv COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/% format2/

# Prepare cloudera directories for PIG - Create and empty directories in the case there is data
mkdir -p /user/zarrouk/covid19
cd covid19
hadoop fs -get /user/cloudera/covid/format1
hadoop fs -get /user/cloudera/covid/format2
hadoop fs -mkdir -p /user/cloudera/covid/format1

hadoop fs -mkdir -p /user/cloudera/covid/format2

hadoop fs -put format1/* /user/cloudera/covid/format1
hadoop fs -put format2/* /user/cloudera/covid/format2



 