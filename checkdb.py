import pg
import sys
import yaml
import os
try:
   import cx_Oracle
   oracle_module = True
except ImportError:
   oracle_module = False  
   
postgres_driver = "org.postgresql.Driver"
oracle_driver   = "oracle.jdbc.driver.OracleDriver"

try:
   config_file = os.environ['STASH_CONFIG_PATH'] + "/config.yml"
   with open(config_file,'r') as configuration_file:      
      config = yaml.load(configuration_file) 
      if config is None:
         exit(-1)
      config['host'] = os.environ['STASH_HOST']
      config['stash_port'] = os.environ['STASH_PORT']
      config['stash_git_port'] = os.environ['STASH_GIT_PORT']
      config['stash_home'] = os.environ['STASH_HOME']
except Exception as e:
# If the config file cannot be imported as a dictionary, bail!
   print e
   sys.exit(-1)

# Check mandatory fields
wanted_keys = ['admin_user','admin_password','admin_name','admin_email',
               'system_name','host',
               'http_port','ssh_port','plugins_dir',
               'server_id','license']
if 'db_type' in config:
   wanted_keys.extend(['db_user','db_password','db_container','db_port','db_name'])
   if 'oracle' == config['db_type']:
      wanted_keys.append('SID')
#must add collector_address for verigreen hook version
missing_keys = []

for key in wanted_keys:
   if not key in config or  not str(config[key]).strip():
      missing_keys.append(key)

if missing_keys:
   print "[ERROR]: The following variables were not set in the configuration file:\a"
   for key in missing_keys:
      print key
   print "Please correct the configuration file and try again."
   sys.exit(-1)
else:
   print "The configuration file contains all needed variables"

# Print all the optional keys that were set but didnt have a value

# Create the properties file

with open(config['stash_home']+"/shared/stash-config.properties",'w') as f:
   f.write("setup.displayName="+str(config['system_name'])+"\n")
   f.write("setup.baseUrl=localhost:"+str(config['http_port'])+"\n")
   f.write("setup.license="+str(config['license'])+"\n")
   f.write("setup.server.id="+str(config['server_id'])+"\n")
   f.write("setup.sysadmin.username="+str(config['admin_user'])+"\n")
   f.write("setup.sysadmin.password="+str(config['admin_password'])+"\n")
   f.write("setup.sysadmin.displayName="+str(config['admin_name'])+"\n")
   f.write("setup.sysadmin.emailAddress="+str(config['admin_email'])+"\n")
   if 'db_type' in config and 'db_container' in config \
      and 'db_port' in config and 'db_name' in config:

      if not config['db_type'] in ("postgresql","oracle"):
         print "[ERROR]: Unsupported database " + config['db_type']
         sys.exit(-2)   

      if "oracle" == config['db_type']:
         f.write("jdbc.driver="+oracle_driver+"\n")

      if "postgresql" == config['db_type']:
         f.write("jdbc.driver="+postgres_driver+"\n")

      if "postgresql" == config['db_type']:
         f.write("jdbc.url=jdbc:postgresql://"+str(config['db_container']) \
                 +":"+str(config['db_port'])+"/"+str(config['db_name'])+"\n")
      if "oracle" == config['db_type']:
         line = "jdbc.url=jdbc:oracle:thin:@"+str(config['db_container']) \
                 +":"+str(config['db_port'])+":"+str(config['SID'])+"\n"
         f.write(line)

      f.write("jdbc.user="+str(config['db_user'])+"\n")
      f.write("jdbc.password="+str(config['db_password'])+"\n")
   f.close()

if not('db_type' in config):
   print "[INFO]: No database specified, using internal database."
   sys.exit(0)


try:

   if config['db_type']  == "postgresql":
      print "connecting to postgres"
      db = pg.DB('postgres',config['db_container'],config['db_port'],None,None,
              config['db_user'],config['db_password'])

   if config['db_type'] == "oracle" and oracle_module:
      # Oracle is different from other database management systems
      # if the user can connect it means(or can be relatively safely assumed) that the
      # database(oracle schema) exists


      dsn = cx_Oracle.makedsn(config['db_container'],config['db_port'],config['SID'])
      connection = cx_Oracle.connect(config['db_user'],config['db_password'],dsn)   

except Exception as e:
   print "[ERROR]: Unable to connect to the database. Please check your credentials."
   print e
   sys.exit(-1)

if 'postgresql' == config['db_type']:
   databases = db.get_databases()      

   if config['db_name'] in databases:
      print "[OK]: Database found"
      sys.exit(0)

   else:
      try: 
         query = 'create database ' + config['db_name']
         db.query(query)
         print "[OK]: Database successfully created"

         sys.exit(0)      
      except Exception as e:
         print e
         sys.exit(-1)
