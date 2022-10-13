import pandas as pd
import os, uuid
from datetime import date
from datetime import datetime
import numpy as np
from hdfs import Config
from hdfs.ext.dataframe import read_dataframe, write_dataframe
import pandas as pd
import hdfs
import logging
logging.info('# Connexion HDFS')
client = hdfs.InsecureClient("http://quickstart.cloudera:50070",user="cloudera")

# Affichage des données à la racine
# l'appel à "makedirs(hdfs_path, permission=None)()" qui cree un repertoire sous hdfs
# répertoires

today = date.today()
# dd/mm/YY
date_Ingestion = today.strftime("%Y-%m-%d")
print("date_Ingestion =", date_Ingestion)
logging.info('# Creation Dossier  HDFS')
#client.makedirs("/user/cloudera/covid-19/"+date_Ingestion)
logging.info('# Collect des fichiers COVID-19')
#1- specifier les urls necessaires au données COVID-19
url_confirmed = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
url_deaths= 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
url_recovred='https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
#2- Définir Dataframe pour charger chaque fichier
data_confirmed = pd.read_csv(url_confirmed, sep=",",  quotechar='"', encoding="utf-8")
data_deaths = pd.read_csv(url_deaths, sep=",",  quotechar='"', encoding="utf-8")
data_recovred= pd.read_csv(url_recovred, sep=",",  quotechar='"', encoding="utf-8")
logging.info('# Transformation de données')
#3-Transformation de données
##1- Pivotez les détails de chaque pays
##recuperer les colonnes decrivant les pays et les colonnes contenant les dates 
data_columns=data_confirmed.columns
country_columns=data_columns[:4]
date_columns=data_columns[4:]
country_columns
##Sur le dfDataFrame, nous allons appeler la melt()méthode et définir les arguments suivants:

###### id_vars à ['Province/State', 'Country/Region', 'Lat', 'Long'] puisque chaque ligne de df est identifiée par les information sur le pays
###### var_nameà 'date'depuis cette nouvelle colonne a besoin d' un nom
###### value_name à 'confirmed'depuis cette nouvelle colonne a besoin d' un nom

data_confirmed_unpivoted = data_confirmed.melt(id_vars=country_columns, var_name='date', value_name='confirmed')
data_deaths_unpivoted = data_deaths.melt(id_vars=country_columns, var_name='date', value_name='deaths')
data_recovred_unpivoted = data_recovred.melt(id_vars=country_columns, var_name='date', value_name='recovred')
#
data_confirmed_unpivoted.head()
#4 - Fusion des données des trois fichiers
# Fusion des données des tois fichiers
new_covid_data = data_confirmed_unpivoted.merge(data_recovred_unpivoted, left_on=['Province/State','Country/Region', 'Lat', 'Long', 'date'], right_on = ['Province/State','Country/Region', 'Lat', 'Long','date'], how='left')
# Fusion des données des trois fichiers
full_covid_data = new_covid_data.merge(data_deaths_unpivoted, left_on=['Province/State','Country/Region', 'Lat', 'Long', 'date'], right_on = ['Province/State','Country/Region', 'Lat', 'Long','date'], how='left')
#5 - Nettoyage de données
#On supprime les valeurs nulles (nan) dans notre jeux de données
full_covid_data.rename(columns={'Province/State':'Province'}, inplace=True)
full_covid_data.rename(columns={'Country/Region':'Country'}, inplace=True)
#Remplacer les valeurs 'Null (nan)' dans province avec counrty 
logging.info('Remplacer les valeurs  Null (nan)  dans province avec counrty ')
full_covid_data['Province'] = np.where(pd.isnull(full_covid_data['Province']), full_covid_data['Country'],full_covid_data['Province'] )
# Enregsiter le dataframe sous hdfs
logging.info('# Write dataframe to HDFS using CSV serialization.')
try:
    #write_dataframe(client, '/user/cloudera/covid-19/'+date_Ingestion+'/full_covid_data.avro', full_covid_data, overwrite=True)
    with client.write('/user/cloudera/covid-19/'+date_Ingestion+'/full_covid_data.csv', encoding='utf-8') as writer:
        full_covid_data.to_csv(writer)
except hdfs.util.HdfsError as e:
 
    logging.error('Probleme ecriture hdfs CSV'+str(e))
 