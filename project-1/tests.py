import unittest
import warnings
import os
import datetime
import subprocess

from github import Github

from repository import Repository
from metrics import BusFactorMetric, CorrectnessMetric, RampUpMetric, ResponsivenessMetric, LicenseMetric
from score import Ranking 
from main import create_list_of_repositories, find_rankings, print_results, clear_log_file

def test_clear_log_file(repo):
    # We test to see if the function "clear_log_file()" actually clears the log file. This is necessary
    # to ensure that all logs are from the most recent run.

    log_file = os.environ['LOG_FILE']
    with open(log_file, "w") as file:
        for i in range(0, 10):
            if i % 2:
                file.write("This is line #" + str(i) + ".\n")
            else:
                file.write("\n")

    clear_log_file()

    with open(log_file, "r") as file:
        lines = file.readlines()
        if len(lines) != 0:
            print("The log file should have 1 empty line, but it had " + str(len(lines)) + ".")
            return False

    return True

def test_npm_repository_name(token):
    url    = 'https://www.npmjs.com/package/express'
    github = Github(token)
    repo   = Repository(url, github)

    expected_name = 'express'
    if repo.name != expected_name:
        print(f"The npm package with url '{url}' should have a github repository name of {expected_name}, but the fetched name is ${repo.name}.")
        return False

    return True

def test_repository_name(repo):
    test_name = "test"
    if repo.name == test_name:
        return True
        
    print("The fetched repository name, " + repo.name + ", does not match the expected name, " + test_name + ".")
    return False

def test_num_stars(repo):
    expected_num_stars = 1
    if repo.num_stars == expected_num_stars:
        return True

    print("The fetched number of stars, " + str(repo.num_stars) + ", does not match the expected number of stars, " + str(expected_num_stars) + ".")
    return False

def test_commits(repo):
    if len(repo.commits) != 7:
        print("There should be a total of 4 commits, but " + str(len(repo.commits)) + " were found.")
        return False

    for commit in repo.commits:
        if commit.author != 'MDQ6VXNlcjU2NTE1Mjgz':
            print("The author of commit " + commit.sha + " should be 'MDQ6VXNlcjU2NTE1Mjgz', but it was " + commit.author + ".")
            return False

    return True

def test_num_pull_requests(repo):
    expected_num_pull_requests = 0
    if repo.num_pull_requests == expected_num_pull_requests:
        return True

    print("The fetched number of pull requests, " + str(repo.num_pull_requests) + ", does not match the expected number of pull requests, " + str(expected_num_pull_requests) + ".")
    return False

def test_num_forks(repo):
    expected_num_forks = 0
    if repo.num_forks == expected_num_forks:
        return True

    print("The fetched number of forks, " + str(repo.num_forks) + ", does not match the expected number of forks, " + str(expected_num_forks) + ".")
    return False

def test_open_issues(repo):
    expected_num_open_issues = 3
    if len(repo.open_issues) == expected_num_open_issues:
        return True

    print("The fetched number of open issues, " + str(len(repo.open_issues)) + ", does not match the expected number of open issues, " + str(expected_num_open_issues) + ".")
    return False

def test_read_me(repo):
    expected_readme = "This is line #1.\n\nThis is line #3.\n"
    if repo.read_me == expected_readme:
        return True

    print("The fetched README text, " + repo.read_me + ", does not match the expected README text, " + expected_readme + ".")
    return False

def test_num_dependencies(repo):
    expected_num_dependencies = 0

    if repo.num_dependencies == expected_num_dependencies:
        return True

    print("The fetched number of dependencies, " + str(repo.num_dependencies) + ", does not match the expected number of dependencies, " + str(expected_num_dependencies) + ".")
    return False

def test_license_name(repo):
    expected_license_name = None
    if repo.license_name != expected_license_name:
        print("The fetched license name, " + str(repo.license_name) + ", does not match the expected license name, " + expected_license_name + ".")
        return False

    return True

def test_ramp_up_metric(repo):
    # The ramp up metric measures the length of a repository's read me. The test
    # repository should have a readme that has 4 lines of code. 

    ramp_up_metric = RampUpMetric("ramp up metric", .1)
    sub_score      = ramp_up_metric.calculate_score(repo)

    expected_sub_score = 4
    
    if sub_score != expected_sub_score:
        print(f"The expected 'ramp up' subscore should be {expected_sub_score}, but it was {sub_score}. This score is calculated by the number of lines in the repository's README.")
        return False

    return True

def test_correctness_metric(repo):
    # The correctness metric uses the semgrep libary to look for errors, anti-patterns,
    # and security vulnerabilities in the repository. The metric uses a list of semgrep 
    # tests found in the 'semgrep.txt' file. This metric should find 3 issues with the
    # test repository. A repository should have as little issues as possible, so it's score
    # is the negative of the number of issues found. 

    correctness_metric = CorrectnessMetric("correctness metric", .2)
    sub_score          = correctness_metric.calculate_score(repo)

    expected_sub_score = -3

    if sub_score != expected_sub_score:
        print(f"The correctness metric should have found {expected_sub_score} issues in the test repository, but it found {sub_score}.")
        return False

    return True    

def test_bus_factor_metric(repo):
    # A repository's "bus factor" measures how dependent a repository is on specific contributers.
    # The more contributers there are, the higher the bus factor. 

    bus_factor = BusFactorMetric("bus factor", .5)
    sub_score  = bus_factor.calculate_score(repo)

    expected_sub_score = 1

    if sub_score != expected_sub_score:
        print(f"The bus factor should have a score of {expected_sub_score}, but it was {sub_score}.")
        return False

    return True

def test_responsiveness_factor_metric(repo):
    # The "responsiveness" factor measured how quickly a repository's contributers respond to/fix and
    # issue. To measure this, we go through all of a repository's open issues and find the average time
    # that these issues have been open. We add this to the number of dependencies that a repositry has.
    # The test repository has no dependencies, so we'll igore that factor for now. Once again, a repository
    # should have a response time that's as fast as possible, so the score is the negative of the average
    # time that an issue is open. 

    responsiveness_factor = ResponsivenessMetric("responsiveness factor", .5)
    sub_score             = responsiveness_factor.calculate_score(repo)

    start_dates = [
        datetime.datetime(2021, 10, 3, 18, 57, 0),
        datetime.datetime(2021, 9, 29, 16, 3, 5),
        datetime.datetime(2021, 9, 29, 16, 2, 47),
    ]

    avg_time_issue_is_open = 0
    for start_date in start_dates:
        avg_time_issue_is_open += (datetime.datetime.now() - start_date).days

    expected_sub_score = -avg_time_issue_is_open / len(start_dates)

    if expected_sub_score != sub_score:
        print(f"The responsiveness factor should have a score of {expected_sub_score}, but it was {sub_score}.")
        return False

    return True

def test_license_metric(repo):
    # The "license" metric checks to see if the repository has a licence that is compaatable with the requirements.
    # The test repository does not have a license, so a score of 0 should be returned. 

    license_metric = LicenseMetric("license metric", .2)
    sub_score      = license_metric.calculate_score(repo)

    expected_sub_score = 0

    if sub_score != expected_sub_score:
        print(f"The license metric should have a score of {expected_sub_score}, but it was {sub_score}.")
        return False

    return True

def test_score_calculation(repo):
    # When calculating the subscores for each repository, the scores are normalized so that the max score for
    # each metric is 1. A repository's total score is the weighted sum of these subscores. If there is only one
    # repository being analyzed, then all of it's subscores will be 1, and the total score will be the sum of the
    # weights. Here we test that fact.

    metrics = [
        RampUpMetric("ramp up metric", .1),
        CorrectnessMetric("correctness metric", .2),
        BusFactorMetric("bus factor", .5),
        ResponsivenessMetric("responsiveness factor", .5),
        LicenseMetric("license metric", .1),
    ]
    repositories = [repo]
    rankings     = find_rankings(metrics, repositories)

    expected_total_score = sum([metric.weight for metric in metrics])
    repository_score     = rankings[0].score

    for repository in repositories:
        repository.scores = []

    if repository_score != expected_total_score:
        print(f"The total score should be {expected_total_score}, but it was {repository_score}.")
        return False

    return True
    
def test_ranking(repo):
    # Now that we tested all the subsystems and modules, all we have to do is to make sure that
    # the repositories are ranked in the correct order. We'll test this by creating a list of metrics
    # and a list of repositories, and passing them into the function "find_rankings()". We'll test to
    # see if the results from this function are in the correct order. 

    token  = os.environ["GITHUB_TOKEN"]
    github = Github(token)
    metrics      = [
        RampUpMetric        ("RAMP_UP_SCORE"              , .1),
        CorrectnessMetric   ("CORRECTNESS_SCORE"          , .2),
        BusFactorMetric     ("BUS_FACTOR_SCORE"           , .5),
        ResponsivenessMetric("RESPONSIVE_MAINTAINER_SCORE", .3),
        LicenseMetric       ("LICENSE_SCORE"              , .9)
    ]
    repos  = [
        Repository('https://github.com/cloudinary/cloudinary_npm', github),
        Repository('https://www.npmjs.com/package/browserify',     github)   
    ]

    rankings = find_rankings(metrics, repos)

    for i in range(1, len(rankings)):
        if rankings[i].score > rankings[i - 1].score:
            print(f"""
                The repositories should be in descending order (based on total score). However, the repository 
                '{rankings[i].repository.name}' nas a score of {rankings[i].score} and the previous repository 
                '{rankings[i - 1].repository.name}' has a score of {rankings[i - 1].score}. Therefore, the 
                repositories are not in descending order.
            """)
            return False 

    return True

def test_output(repo):
    metrics      = [
        RampUpMetric        ("RAMP_UP_SCORE"              , .1),
        CorrectnessMetric   ("CORRECTNESS_SCORE"          , .2),
        BusFactorMetric     ("BUS_FACTOR_SCORE"           , .5),
        ResponsivenessMetric("RESPONSIVE_MAINTAINER_SCORE", .3),
        LicenseMetric       ("LICENSE_SCORE"              , .9)
    ]
    repositories = [repo]
    rankings     = find_rankings(metrics, repositories)
    output       = print_results(metrics, rankings)

    expected_header = "URL RAMP_UP_SCORE CORRECTNESS_SCORE BUS_FACTOR_SCORE RESPONSIVE_MAINTAINER_SCORE LICENSE_SCORE"
    expected_scores = "https://github.com/ECE-461-Group-G/test 2.0 1.0 1.0 1.0 1.0 1.0"
    header = output.split("\n")[0]
    scores = output.split("\n")[1]

    for repository in repositories:
        repository.scores = []

    if expected_header != header:
        print(f"The header should be '{expected_header}', but it was '{header}'.")
        return False

    if expected_scores != scores:
        print(f"The scores should be '{expected_scores}', but it was '{scores}'.")
        return False

    return True

def test_metric_when_empty(repo):
    metric = RampUpMetric("ramp up metric", .1)
    scores = metric.calculate_scores([])

    if scores != []:
        print(f"The metric should have returned an empty list, but it returned {scores}.")
        return False

    return True

def test():
    # Here we run our tests. Most tests are a function that accept a 'repo' argument. These test functions are
    # stored in a list and iterated through. Other tests accept unique arguments, so they are run individually.
    # Each test function tests for a specific functionality in a specific part of the code. Each function returns
    # True if the test passes, and False if it fails. The number of tests passed and the total number of tests run
    # are displayed at the end. 

    token  = os.environ['GITHUB_TOKEN'] 
    url    = 'https://github.com/ECE-461-Group-G/test'   
    github = Github(token)
    repo   = Repository(url, github)
    
    num_passes = 0
    num_tests  = 0

    if test_npm_repository_name(token):
        num_passes += 1
    num_tests += 1

    repo_tests = [
        test_license_name,
        test_ranking,
        test_repository_name,
        test_num_stars,
        test_commits,
        test_num_pull_requests,
        test_num_forks,
        test_open_issues,
        test_read_me,
        test_num_dependencies,
        test_ramp_up_metric,
        test_correctness_metric,
        test_bus_factor_metric,
        test_license_metric,
        test_responsiveness_factor_metric,
        test_score_calculation,
        test_output,
        test_metric_when_empty,
        test_clear_log_file
    ]
    for test in repo_tests:
        if test(repo):
            num_passes += 1
        num_tests += 1

    print(str(num_passes) + "/" + str(num_tests))

if __name__ == "__main__":
    test()

    
    