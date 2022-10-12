import hdfs
client = hdfs.InsecureClient("http://quickstart.cloudera:50070",user="cloudera")

# Affichage des données à la racine
# l'appel à "list()" renvoie une liste de noms de fichiers et de
# répertoires
print(client.list("/user/cloudera/"))

# Lecture d'un fichier complet
with client.read("mapreduce2.txt") as reader:
    for line in reader:
        print(line)












