#!/bin/bash
# This script sets up your stash server with all the plugins you have
# and also with the .properties file that you specify
# so that you can clone a stash server with minimal effort

# Set the required paths
config_path_in_container='/var/stash/config'
stash_home='/var/atlassian/application-data/stash'
config_file="$stash_home/shared/stash-config.properties"
yaml_file='/var/stash/config/config.yml'
hooks_dir="$stash_home/external-hooks"

if [[ ! -e "$yaml_file" ]]; then
    echo "ERROR: Configuration file $yaml_file not found, unable to start stash."
    exit -1
fi

# Read values from yaml file
http_port=`grep -m 1 "^http_port:" $yaml_file|awk '{print $2}'`
license=`grep -m 1 "^license:" $yaml_file|awk '{print $2}'`
server_id=`grep -m 1 "^server_id:" $yaml_file|awk '{print $2}'`
admin_user=`grep -m 1 "^admin_user:" $yaml_file|awk '{print $2}'`
admin_password=`grep -m 1 "^admin_password:" $yaml_file|awk '{print $2}'`
admin_name=`grep -m 1 "^admin_name:" $yaml_file|awk -F ": " '{print $2}'`
admin_email=`grep -m 1 "^admin_email:" $yaml_file|awk '{print $2}'`

system_name=`grep -m 1 "^system_name:" $yaml_file|awk '{print $2}'`

db_driver=`grep -m 1 "^db_driver:" $yaml_file|awk '{print $2}'`
db_type=`grep -m 1 "^db_type:" $yaml_file|awk '{print $2}'`
db_container=`grep -m 1 "^db_container:" $yaml_file|awk '{print $2}'`
db_port=`grep -m 1 "^db_port:" $yaml_file|awk '{print $2}'`
db_name=`grep -m 1 "^db_name:" $yaml_file|awk '{print $2}'`
db_user=`grep -m 1 "^db_user:" $yaml_file|awk '{print $2}'`
db_password=`grep -m 1 "^db_password:" $yaml_file|awk '{print $2}'`
hook_exe=`grep -m 1 "^hook_exe:" $yaml_file|awk '{print $2}'`
proxy_url=`grep -m 1 "^proxy:" $yaml_file|awk '{print $2}'`
no_proxy=`grep -m 1 "^no_proxy:" $yaml_file|awk '{print $2}'`

# Start sendmail
#not for now, might add it again in the future
#/usr/sbin/service sendmail start

# Set proxy settings
if [[ -n $proxy_url ]]; then
    export http_proxy=$proxy_url
    export https_proxy=$proxy_url
    export HTTP_PROXY=$proxy_url
    export HTTPS_PROXY=$proxy_url

    if [[ -n $no_proxy ]]; then
       export no_proxy="$no_proxy"    
       export NO_PROXY="$no_proxy" 
    else   
       export no_proxy="127.0.0.1, localhost"    
       export NO_PROXY="127.0.0.1, localhost"         
    fi   
fi

# Create directory structure
REF=/var/atlassian/application-data/stash/shared/plugins/installed-plugins
mkdir -p $REF
mkdir -p $hooks_dir

URL="https://marketplace.atlassian.com/download/plugins"
while read spec; do
    plugin=(${spec//:/ }); 
    [[ ${plugin[0]} =~ ^# ]] && continue
    [[ ${plugin[0]} =~ ^\s*$ ]] && continue
    curl -L $URL/${plugin[0]}/version/${plugin[1]} -o $REF/${plugin[0]}.jar;
done  < $config_path_in_container/plugins.txt

# Create .properties file

echo "setup.displayName=$system_name" >> $config_file
echo "setup.baseUrl=localhost:$http_port" >> $config_file
echo "setup.license=$license">> $config_file
echo "setup.server.id=$server_id" >> $config_file
echo "setup.sysadmin.username=$admin_user" >> $config_file
echo "setup.sysadmin.password=$admin_password" >> $config_file
echo "setup.sysadmin.displayName=$admin_name" >> $config_file
echo "setup.sysadmin.emailAddress=$admin_email" >>$config_file
echo "jdbc.driver=$db_driver" >> $config_file
echo "jdbc.url=jdbc:$db_type://$db_container:$db_port/$db_name" >>$config_file
echo "jdbc.user=$db_user" >> $config_file
echo "jdbc.password=$db_password" >> $config_file

if [[ -n $hook_exe ]]; then
   cp $config_path_in_container/$hook_exe $hooks_dir
   chmod u+x $hooks_dir/*  
fi

# Make sure the database exists
python checkdb.py
result=$?

if [[ $result -eq 0 ]];then
   # Start stash
   python stash_setup.py & >python.log
   eval "$1/bin/start-stash.sh -fg"
else
   echo "[ERROR]: Unable to access/create database" 
fi    