# Dockerized Stash

A Stash docker image with a focus on enabling user configuration and automation.

## Pre-requisites/assumptions:

* Requires a computer(real or virtual) running ubuntu
* Must have docker installed 
* Must have a configuration file called config.yml with all needed values. Or you can modify the included sample file to fit your particular installation. Please see the configuration section for details on how to setup your config file.

* If you are behind a proxy you must have your settings properly configured so that docker can retrieve the official stash image (if you want to build the image from the Dockerfile)
* Must have a database, be it in a docker container or a physical or virtual machine, properly configured with a user and a database for stash

## Usage:

* Create a text file called plugins.txt which contains a list of plugins to install in the following format: <plugin name>:<plugin version>
* Move the following files to your configuration directory:
   * config.yml
   * the rsa public keys of the stash users you wish to create
   * plugins.txt(optional)
* Run the following command:
``` 
sudo docker run -it -p <host http port>:7990 -p <host ssh port>:7999 \
-v <path to your configuration directory in the host>:/var/stash/config \
-v <path to the stash home in the host>:/var/atlassian/application-data/stash \
--link <name of database container>:<name of database container> \
verigreen/stash
```

* Wait a few seconds (about a minute or two should be more than enough)  for tomcat to initialize

* Point your browser to localhost:5000 (or whatever port you defined as the stash http port)
* If everything went well you should have a working stash container with your predefined users, projects and repositories already created and all your plugins and hooks installed.
* Enjoy!

## Configuration
The configuration contains the following fields:
* ### Stash administrator
   * admin_user: the username 
   * admin_password: the admin password
   * admin_name: the display name
   * admin_email: 

* ### Stash settings
   * system_name: The displayed name of this stash server. This is the same server name that appears in the login page.
    
* ### Database parameters
  If the database type is specified then you need to specify the other database parameters. Otherwise the internal database is used.

   * db_type: type of database(currently only postgresql and oracle are supported)
   * db_user: name of the database user for stash
   * db_password: password of the stash database user
   * db_host: hostname or container name or ip address where the database can be found
   * db_port: database port 
   * db_name: name of the database(or oracle schema) that stash will use

* ### Stash cloning parameters
   * license: license number from Atlassian, this is necessary if you want your stash server to be automatically setup. If you dont specify this, you 
   will have to manually setup the server the first time you log in.
   * server_id: the id of your server. This is required if you want server to be automatically setup
* ### Proxy
   Proxy settings are optional. If you provide either the http or https proxy, and dont provide the no_proxy parameter then it will default to localhost and 127.0.0.1. If you provide only http or https but not both, the missing one will take the same value as the one you provided.

   * http_proxy: Address of the http proxy
   * https_proxy: Address of the https proxy
   * no_proxy: Addresses for which no proxy should be used

* ### Stash regular users(for pushing code)
  This is the configuration for creating users, projects and repositories in a hierarchical way.
   * users: an array of users
      * - username: 
      *   password:
      *   name: The display name of the user
      *   email:
      *   RSA_key: the name of the rsa public key file for this user
      *   projects: an array of projects for which this user is the administrator
         * - key: the stash project key, which is a 3-character string.
         *   name: name of the project
         *   desc: description of the project
         * repositories: an array of repositories belonging to this project
            * - name: the name of the repository. this is the only repository characteristic needed in the configuration file