import requests
import os
import re
from datetime import datetime, timedelta

from urllib.parse import urlparse
from github import Github

from log import log

class Issue():
    def __init__(self, title, created_at, closed_at):
        self.title      = title
        self.created_at = created_at
        self.closed_at  = closed_at

class Commit():
    def __init__(self, author):
        self.author = author

class Repository():
    # A class that, when initialzed, fetches all needed data from the github repository.
    # Accepts a url and a github object. The github object is used to interact with the
    # github REST API. The url could either be a github url or an npm url. If it is an 
    # npm url, it is converted into a github url. Also contains a list of sub-scores that
    # have been calculated for this repository. 

    def __init__(self, url, github):
        self.github = github
        print("URL: " + url)
        self.__set_github_repo(url)

        self.num_stars         = self.__fetch_num_stars()
        self.num_pull_requests = self.__fetch_num_pull_requests()
        self.num_forks         = self.__fetch_num_forks()
        self.open_issues       = self.__fetch_open_issues()
        self.commits           = self.__get_commits()
        self.read_me           = self.__get_read_me_file()
        self.num_dependencies  = self.__get_num_dependencies()
        self.license_name      = self.__get_license()

        self.scores = []

        log.log_repository_created(self)

    def __set_github_repo(self, url):
        url_components = urlparse(url)
        repo_url       = ""
        # print(url)
        if 'github' in url_components[1]:           
            log.log_url_type(url, "github")
            repo_url = url
        else:
            log.log_url_type(url, "npm")
            
            package_name = urlparse(url)[2].split('/package/')[1]
            url          = "https://registry.npmjs.org/{}".format(package_name)
            response     = requests.get(url).json()
            repo_url     = response['repository']['url'].strip('git+')[:-1]

        url_components = urlparse(repo_url)
        self.repo      = self.github.get_repo(url_components[2][1:])
        self.name      = self.repo.name
        self.url       = repo_url

    def __fetch_num_stars(self):
        return self.repo.stargazers_count

    def __fetch_num_pull_requests(self):
        pull_requests = self.repo.get_pulls()   
        return len(list(pull_requests))
        
    def __fetch_num_forks(self):
        return self.repo.forks_count

    def __fetch_open_issues(self):
        open_issues = []
        for issue in self.repo.get_issues(state='open'):
            open_issues.append(Issue(issue.title, issue.created_at, None))

        return open_issues

    def __get_commits(self):
        commits   = []
        dateStart = datetime.now() - timedelta(days=365)

        for commit in self.repo.get_commits(since=dateStart):
            if commit.author is not None:
                commits.append(Commit(commit.author.node_id))

        return commits

    def __get_read_me_file(self):
        return str(self.repo.get_readme().decoded_content.decode())

    def __get_num_dependencies(self):
        package_json   = self.repo.get_contents("package.json")
        text           = str(package_json.decoded_content)
        results        = re.search('"dependencies": {[^}]*', text)

        if results == None:
            log.log_no_dependencies(self)
            return 0

        return len(results.group(0).split('"dependencies": {')[1].split(','))

    def __get_license(self):
        try:
            return self.repo.get_license().license.spdx_id
        except:
            log.log_no_license(self)
            return None
    
        

