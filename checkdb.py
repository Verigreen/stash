import pg
import sys

try:
   config_file = os.environ['STASH_CONFIG_PATH'] + "/config.yml"
   with open(config_file,'r') as configuration_file:      
      config = yaml.load(configuration_file) 
      if config is None:
         exit(-1)
      config['host'] = os.environ['STASH_HOST']
      config['stash_port'] = os.environ['STASH_PORT']
      config['stash_git_port'] = os.environ['STASH_GIT_PORT']
except Exception as e:
# If the config file cannot be imported as a dictionary, bail!
   print e
   sys.exit(-1)

try:
db = pg.db('postgres',config['db_container'],config['db_port'],None,None,
           config['db_user'],config['db_password'])
except Exception as e:
   print e
   sys.exit(-1)

#if the stash database exists, then everything is ok, leave with status 0
databases = db.get_databases()

if config['db_name'] in databases:
   print "[OK]: Database found"
   sys.exit(0)

else:
   try: 
      query = 'create database ' + config['db_name']
      db.query(query)
      print "[OK]: Database successfully created"
   except Exception as e:
      print e
      sys.exit(-1)
