import os
import subprocess
import json

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from log import log

class Metric(ABC):
    # Base class for all metric classes. The method calculate_scores() calculates the normalized
    # scores for each metric. The abstract class calculate_score() forces all derived metric 
    # classes to provide functionality on how a metric score is calculated.

    def __init__(self, name, weight):
        self.name   = name
        self.weight = weight

    def calculate_scores(self, repositories):
        # Calculates the metric score for each repository. Returns a normalized list of these
        # scores. 

        scores = []
        for repo in repositories:
            scores.append(self.calculate_score(repo))

        log.log_metric_subscores_calculated(self, scores, repositories)

        if len(scores) == 0:
            return scores
        if len(scores) == 1:
            return [1.0]

        maxScore, minScore = max(scores), min(scores)
        if maxScore == minScore:
            maxScore, minScore = 1, 0
        for i, score in enumerate(scores):
            scores[i] = (score - minScore) / (maxScore - minScore)

        log.log_norm_metric_subscores_calculated(self, scores, repositories)
        return scores

    @abstractmethod
    def calculate_score(self, repo):
        pass

class RampUpMetric(Metric):
    # "Ramp Up" measures how long it takes for developers to start using a package. We look at the
    # length of the README file to determine how much documentation is available to developers.

    def calculate_score(self, repo):
        read_me_size = len(repo.read_me.split("\n"))

        log.log_subscore_calculated(repo, read_me_size, self)
        return read_me_size

class CorrectnessMetric(Metric):
    # "Correctness" measures how the repository's standard of correctness. Here we perform static 
    # analysis of the repository with semgrep. Runs a series of tests (found in a "semgrep.txt"
    # file) and keeps track of the number of issues that appear. As we want a repository to have
    # the minimal number of issues, we return a negated issue count. 

    directory = "repositories"

    def calculate_score(self, repo):
        path = self.__download_repository_to_local(repo)

        num_issues = 0 
        with open("project-1/semgrep.txt", "r") as filePtr:
            for line in filePtr.readlines():
                if line.endswith("\n"):
                    line = line[:-1]
                num_issues += self.__run_test(line, path)

        score = -num_issues
        log.log_subscore_calculated(repo, score, self)
        return score

    def __download_repository_to_local(self, repo):
        path          = self.directory + "/" + repo.name
        clone_command = "git clone " + repo.url + " " + path

        if not os.path.exists(path):
            os.system(clone_command)

        return path

    def __run_test(self, test_name, repository_path):
        output = subprocess.Popen(["semgrep", "--config", test_name, "--json", '-q', repository_path], shell=False, stdout=subprocess.PIPE)
        output.wait()

        line   = output.stdout.readline()
        object = json.loads(line)

        num_issues = len(object['results'])
        log.log_semgrep_test_results(repository_path.split("/")[1], test_name, num_issues)
        return num_issues

class BusFactorMetric(Metric):
    # "Bus factor" measures how many developers are contributing to a package. We look at how many
    # unique developers made a contribution (commit) to the source code within the past year. 

    def calculate_score(self, repo):
        contributors = {}
        for commit in repo.commits:
            if commit.author not in contributors:
                contributors[commit.author] = 1
            else:
                contributors[commit.author] += 1

        score = len(contributors.keys())

        log.log_subscore_calculated(repo, score, self)
        return score
 
class ResponsivenessMetric(Metric):
    # "Responsiveness" measures how quickly developers respond to an issue with the repository. We
    # use the average time that currently opened issues have been open for and the number of dependencies
    # that the repository has. The average time is measured in days. 

    def calculate_score(self, repo):
        ave_time_issue_is_open = self.__get_ave_time_issue_is_open(repo)
        num_dependencies       = self.__get_num_dependencies(repo)
        score = -(ave_time_issue_is_open + (num_dependencies))
        
        log.log_subscore_calculated(repo, score, self)
        return score

    def __get_ave_time_issue_is_open(self, repo):
        avg_time_issue_is_open = 0
        for issue in repo.open_issues:
            avg_time_issue_is_open += (datetime.now() - issue.created_at).days

        score = (avg_time_issue_is_open / len(repo.open_issues))
        return score

    def __get_num_dependencies(self, repo):
        return repo.num_dependencies

class LicenseMetric(Metric):
    # We test to see if a repository is compatable with the 'lgpl-2.1'.

    def calculate_score(self, repo):
        score = 1 if repo.license_name in ['MIT', 'lgpl-2.1'] else 0
        
        log.log_subscore_calculated(repo, score, self)
        return score

    
class DependencyMetric(Metric):
    def calculate_score(self, repo):
        num_dependencies       = self.__get_num_dependencies(repo)
        if num_dependencies == 0:
            score = 1.0
        else: 
            score = 1.0 / (num_dependencies)

        log.log_subscore_calculated(repo, score, self)
        return score

    def __get_num_dependencies(self, repo):
        return repo.num_dependencies
