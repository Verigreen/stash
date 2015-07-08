# Dockerized Stash

A Stash docker image with a focus on enabling user configuration and automation.

## Pre-requisites/assumptions:

* Requires a computer(real or virtual) running ubuntu
* Must have docker installed 
* Must have a configuration file called config.yml with all needed values. Or you can modify the included sample file to fit your particular installation. Please see the configuration section for details on how to setup your config file.

* If you are behind a proxy you must have your settings properly configured so that docker can retrieve the official stash image (if you want to build the image from the Dockerfile)

* Must have a database, be it in a docker container or a physical or virtual machine, properly configured with a user and a database for stash

## Usage:

* Move the following files to your configuration directory:
   * `config.yml`
   * the rsa public keys of the stash users you wish to create
   * the executable file for your pre-receive hook(optional)
     
   
* Run the following command:
```bash
sudo docker run -it -p <host http port>:7990 -p <host ssh port>:7999 \
-v /path/to/config/directory:/var/stash/config \
-v /path/to/stash/home:/var/atlassian/application-data/stash \
--link <name of database container>:<name of database container> \
verigreen/stash
```

* Wait a few seconds (about a minute or two should be more than enough)  for tomcat to initialize

* Point your browser to `localhost:5000` (or whatever port you defined as the stash http port)
* If everything went well you should have a working stash container with your predefined users, projects and repositories already created and all your plugins and hooks installed.
* Enjoy!

## Configuration
```yaml
# Stash administrator
admin: 
   username: 
   password:
   name: #display name of the admin
   email: 

# Stash regular users(for pushing code) this is an array of users and their information
users:
   - username: 
     password: 
     name: #display name of the user
     email: 
     ssh_key: #name of the RSA key file for this user

# Project and repository information
projects: # this is an array of projects
   - key: #project key
     name: #project display name
     desc: #short description of your project
     repositories: #this is an array of repositories for this project
        - name: #repository name
          permissions: #an array of permissions for this repository
             - username: #
               access: #access level, possible values: read, write, admin

#user_directories: #need to look this up


# Stash settings
system_name: #this is the name that appears in the login screen


# Database parameters
db_user: #username that you created for stash in the database
db_password: #password of the stash database user
db_type: #currently supported: oracle, postgresql
db_host: #container or host where the database resides
db_port: #database port, default oracle port is 1521, default postgresql port is 5432
db_name: #name of the database stash will be using

# Stash cloning parameters
license: #your stash licence goes here
server_id: #and your server id


# Proxy settings
# If either https or http is set, but not the other, the missing one will be set to the one that was provided. 
# If either http or https is provided and no_proxy is not provided, it will default to "127.0.0.1,localhost"
http_proxy: 
https_proxy:
no_proxy: 

# Plugins 
# These are the plugins to be installed, requires both the name and version
plugins:
   - name: "com.ngs.stash.externalhooks.external-hooks"
     version: 161
   - name: "com.risingoak.stash.plugins.stash-enforce-author-hook"
     version: 14

# External hook
hook_exe: #the program that will be executed as an external hook. this is optional.
hook_enable: # this controls if the hook is enabled: True or False

# Host-container interface parameters
http_port: #host port that will be used for http connections with the stash container
ssh_port: #host port that wil be used for ssh connections with the stash container
```
