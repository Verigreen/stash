# Author: Giovanni Matos
# Copyright: 2015 Hewlett Packard

# This program sets up Stash git server from a YAML configuration file

import json
import sys
import re
import time
import os

import requests
import yaml


# The following class handles REST requests(and thus the name)
class StashSetup:
    def __init__(self, config):
        self.config = config

        self.http_host = self.config['host'] + ':' + self.config['stash_port']
        self.ssh_host = self.config['host'] + ':' + self.config['stash_git_port']
        self.admin_auth = requests.auth.HTTPBasicAuth(self.config['admin']['username'],
                                                      self.config['admin']['password'])

        self.headers = {'content-type': 'application/json'}
        self.host_api = 'http://' + self.http_host + '/rest/api/1.0/'

    def set_ssh_key(self, key_file, user_auth):
        req = 'http://' + self.http_host + '/rest/ssh/1.0/keys'
        if not os.path.isfile('/var/stash/config/' + key_file):
            print "[INFO]: SSH key file " + str(key_file) + " does not exist"
            return

        with open('/var/stash/config/' + key_file, "r") as myfile:
            data = myfile.read().replace('\n', '')
        body = {'text': data}
        try:
            r = requests.post(
                req,
                data=json.dumps(body),
                auth=user_auth,
                headers=self.headers
            )

            if r.status_code == 201:
                print "RSA key successfully copied to the server"
            else:
                print "ERROR: Return code %d" % r.status_code
                print "ERROR: Unable to transfer RSA key: %s" % str(r.text)

        except Exception as e:
            print "Error transfering rsa key: " + e

    def create_project(self, project):
        command = 'projects'
        req = self.host_api + command
        proj = {
            'key': project['key'],
            'name': project['name'],
            'description': project['desc']
        }
        try:
            r = requests.post(
                req,
                data=json.dumps(proj),
                headers=self.headers,
                auth=self.admin_auth)

            if r.status_code == 201:
                print "Project " + str(project['name']) + " successfully created"
                # Create related repositories
                for repository in project['repositories']:
                    self.create_repo(repository, project['key'])
            else:
                print "ERROR: Return code %d" % r.status_code
                print "ERROR: Unable to create project: %s" % str(r.text)

        except Exception as e:
            print "Error creating project: " + e

    def create_repo(self, repository, project_key):
        command = 'projects/' + project_key + '/repos'
        req = self.host_api + command
        repo = {
            'name': repository['name'],
            'scmld': 'git',
            'forkable': True
        }
        try:
            r = requests.post(
                req,
                data=json.dumps(repo),
                headers=self.headers,
                auth=self.admin_auth)
            if r.status_code == 201:
                print "Repository " + str(repository['name']) + " successfully created"

                if 'hook_id' in config and 'hook_exe' in config:
                    # block for now, maybe move it to repository configuration?
                    self.hook_setup(repository, project_key)

                # set permissions:
                for permission in repository['permissions']:

                    if "read" == permission['access']:
                        access = "REPO_READ"
                    if "write" == permission['access']:
                        access = "REPO_WRITE"
                    if "admin" == permission['access']:
                        access = "REPO_ADMIN"

                    command = 'projects/' + project_key + '/repos/' + repository['name'] + \
                              '/permissions/users?name=' + permission['username'] + "&permission=" + access

                    req = self.host_api + command

                    try:
                        r = requests.put(
                            req,
                            headers=self.headers,
                            auth=self.admin_auth)
                        if r.status_code == 204:
                            print "Successfully set permissions for " + permission['username'] \
                                  + " to repository " + repository['name']
                        else:
                            print "Unable to set permissions: " \
                                  + str(r.text)
                    except Exception as e:
                        print "Error setting permissions: " + e

            else:
                print "ERROR: Return code %d" % r.status_code
                print "ERROR: Unable to create repository: %s" % str(r.text)
        except Exception as e:
            print "Error creating repository: " + e


    def create_user(self, user):
        # First create the user then set them as project creator
        # command = 'admin/users'
        # For some reason stash doesnt like this request using json.
        # Using a direct link instead
        command = 'admin/users?name=' + user['username'] \
                  + '&password=' + user['password'] \
                  + '&displayName=' + user['name'] \
                  + '&emailAddress=' + user['email']

        req = self.host_api + command
        # user = {
        # 'name':user['username'],
        #         'password':user['password'],
        #        'displayName':user['name'],
        #       'emailAddress':user['email'],
        # }
        try:
            r = requests.post(
                req,
                #data = json.dumps(user),
                headers=self.headers,
                auth=self.admin_auth)

            if r.status_code == 204:
                # Set the user as project creator
                #command = 'admin/permissions/users'
                # For some reason stash doesnt like this request using json.
                # Using a direct link instead
                command = 'admin/permissions/users?name=' + user['username'] \
                          + '&permission=PROJECT_CREATE'
                req = self.host_api + command
                perm = {
                    'name': user['username'],
                    'permission': 'PROJECT_CREATE'
                }
                try:
                    r = requests.put(
                        req,
                        #       data = json.dumps(user),
                        headers=self.headers,
                        auth=self.admin_auth
                    )
                except Exception as e:
                    print "Error setting user as project creator:" + e

                if r.status_code == 204:
                    print "User created and permissions set"
                else:
                    print "Unable to set user permissions: " \
                          + str(r.text)
            else:
                print "Unable to create user: " \
                      + str(r.text)

            user_auth = requests.auth.HTTPBasicAuth(user['username'], user['password'])

            # Set ssh key
            if 'ssh_key' in user:
                self.set_ssh_key(user['ssh_key'], user_auth)
        except Exception as e:
            print "Error creating user:" + e


    def hook_setup(self, repository, project_key):
        command = 'projects/' + project_key + '/repos/' \
                  + repository['name'] + '/settings/hooks/' \
                  + self.config['hook_id'] + '/settings'

        req = self.host_api + command

        params = {
            "exe": self.config['hook_exe'],
            "safe_path": "true",  # always use safe path
            "params": ""
        }
        try:
            r = requests.put(req, data=json.dumps(params), headers=self.headers, auth=self.admin_auth)
            if r.status_code == 200:
                print "Pre-receive hook successfull configured"
                if self.config['hook_enable']:
                    command = 'projects/' + project_key + '/repos/' \
                              + repository['name'] + '/settings/hooks/' \
                              + self.config['hook_id'] + '/enabled'
                    req = self.host_api + command
                    params = {
                        "enabled": "true",
                        "configured": "true",
                        "exe": self.config['hook_exe'],
                        "safe_path": "true",  # always use safe path
                        "params": ""
                    }

                    try:
                        r = requests.put(req, data=json.dumps(params), headers=self.headers, auth=self.admin_auth)
                        if r.status_code == 200:
                            print "Pre-receive hook successfully enabled"
                        else:
                            print "Unable to enable pre-receive hook: " \
                                  + str(r.text)
                    except Exception as e:
                        print "Error enabling pre-receive hook:" + str(e)
            else:
                print "Unable to configure pre-receive hook: " \
                      + str(r.text)

        except Exception as e:
            print "Error configuring pre-receive hook:" + str(e)  # Read config


# Start of main procedure
try:
    config_file = os.environ['STASH_CONFIG_PATH'] + "/config.yml"
    with open(config_file, 'r') as configuration_file:
        config = yaml.load(configuration_file)
        if config is None:
            exit(-1)
        config['host'] = os.environ['STASH_HOST']
        config['stash_port'] = os.environ['STASH_PORT']
        config['stash_git_port'] = os.environ['STASH_GIT_PORT']
        config['hook_id'] = "com.ngs.stash.externalhooks.external-hooks%3Aexternal-pre-receive-hook"
except Exception as e:
    # If the config file cannot be imported as a dictionary, bail!
    print e
    sys.exit()

url = "http://" + config['host'] + ":" + config['stash_port']
# 10 minute timeout by default
limit = 600
if 'timeout' in config and type(config['timeout']) == int:
    limit = config['timeout']

total_time = 0
wait_time = 10
success = False
preg = re.compile('/projects\Z')

while total_time < limit:
    try:
        r = requests.get(url)
        if preg.search(r.url):
            success = True
            break
    except Exception:
        pass
    total_time += wait_time
    time.sleep(wait_time)


# Set up the ssh key, project and repository only if stash started properly.
if success:
    print "\n\n\nStash has started succesfully\n\n\n"
    # Not sure why the admin account has no admin powers until you click on "view my profile"
    # Applying browns law and sending a curl request for that page before setting everything up
    commander = StashSetup(config)
    cmd = "curl -u " + commander.config['admin']['username'] + ":" \
          + commander.config['admin']['password'] + " " + url + "/profile >/dev/null"
    os.system(cmd)
    for user in config['users']:
        commander.create_user(user)

    for project in config['projects']:
        commander.create_project(project)

    print "Setup complete"
else:
    print "[INFO]: Timeout expired, gave trying to setup stash."