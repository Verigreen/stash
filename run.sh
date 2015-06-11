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

hook_exe=`grep -m 1 "^hook_exe:" $yaml_file|awk '{print $2}'`
http_proxy=`grep -m 1 "^http_proxy:" $yaml_file|awk '{print $2}'`
https_proxy=`grep -m 1 "^https_proxy:" $yaml_file|awk '{print $2}'`
no_proxy=`grep -m 1 "^no_proxy:" $yaml_file|awk '{print $2}'`

# Start sendmail
#not for now, might add it again in the future
#/usr/sbin/service sendmail start

# Set proxy settings
if [[ -n $http_proxy || -n $https_proxy ]]; then
    if [[ -n $http_proxy ]]; then
       export http_proxy=$http_proxy
       export HTTP_PROXY=$http_proxy
    else
       export http_proxy=$https_proxy
       export HTTP_PROXY=$https_proxy
    fi
    if [[ -n $https_proxy ]]; then
       export https_proxy=$https_proxy
       export HTTPS_PROXY=$https_proxy      
    else   
       export https_proxy=$http_proxy
       export HTTPS_PROXY=$http_proxy      
    fi

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

if [[ -n $hook_exe ]]; then
   cp $config_path_in_container/$hook_exe $hooks_dir
   chmod u+x $hooks_dir/*
fi

# Make sure the database exists, if configured to use an external database
python checkdb.py
result=$?

if [[ $result -eq 0 ]];then
   # Start stash
   python stash_setup.py & >python.log
   eval "$1/bin/start-stash.sh -fg"
else
   echo "[ERROR]: Unable to access/create database"
fi
