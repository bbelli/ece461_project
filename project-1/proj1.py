import json
import sys
import os
from flask.json.tag import JSONTag

from github import Github

from repository import Repository
from metrics import LicenseMetric, RampUpMetric, CorrectnessMetric, BusFactorMetric, ResponsivenessMetric, DependencyMetric
from score import Ranking 
from log import log

def clear_log_file():
    log_file = os.environ['LOG_FILE']
    with open(log_file, "w") as file:
        file.write("")

def create_list_of_repositories(file_name, github):
    # Accepts the file name that contains a list of repository urls. Creates a list of Repository 
    # objects from these urls and returns this list. 

    repositories = []
    with open(file_name, "r") as file:
        log.log_url_file_read(file_name)
        for line in file.readlines():
            if line[-1] == "\n":
                line = line[:-1]
            print(line)

            repo = Repository(line, github)
            repositories.append(repo)

    log.log_url_file_closed(file_name)
    log.log_repo_list_created(repositories)

    return repositories

def print_results(metrics, rankings):
    # Prints out the metric names, repository urls, repository total scores, and repository sub 
    # scores. The repositories are printed in order of their total score. 
    output_string = ""

    header = "URL"
    for metric in metrics:
        header += " " + metric.name
    output_string += header + "\n"

    for ranking in rankings:
        repo_line = ranking.repository.url + " " + str(ranking.score)
        for score in ranking.repository.scores:
            repo_line += " " + str(score)
        output_string += repo_line + "\n"

    return output_string

def find_rankings(metrics, repositories):
    for metric in metrics:
        sub_scores = metric.calculate_scores(repositories)
        for i, sub_score in enumerate(sub_scores):
            repositories[i].scores.append(sub_score)

    rankingObject = Ranking(metrics)
    rankings      = rankingObject.get_rankings(repositories)

    log.log_final_rankings(rankings)
    return rankings

def ranking_dict(repo):

    rankings = {'ramp_up' : repo.repository.scores[0] * (0.2), 
                'correctness' : repo.repository.scores[1] * (0.2), 
                'bus_factor' : repo.repository.scores[2] * (0.3), 
                'responsiveness' : repo.repository.scores[3] * (0.1),
                'license' : repo.repository.scores[4] * (0.1),
                'dependency' : repo.repository.scores[5] * (0.2)
                }
    values = rankings.values()
    final_score = sum(values)
    
    rankings['score'] = final_score
    print(rankings)
    return rankings


    

def main(args):
    # Creates a github object used for interacting with GitHub. Creates a list of repositories
    # that will be analyzed, and a list of metrics that will be used to calculate the score. 
    # Iterates through each metric to calculate each sub score for each repository. Ranks the 
    # repositories based on the total score.
    clear_log_file()

    token  = os.environ["GITHUB_TOKEN"]
    github = Github(token)

    repositories = create_list_of_repositories(args[0], github)
    metrics      = [
        RampUpMetric        ("RAMP_UP_SCORE"              , .2),
        CorrectnessMetric   ("CORRECTNESS_SCORE"          , .2),
        BusFactorMetric     ("BUS_FACTOR_SCORE"           , .3),
        ResponsivenessMetric("RESPONSIVE_MAINTAINER_SCORE", .1),
        LicenseMetric       ("LICENSE_SCORE"              , .1), 
        DependencyMetric    ("DEPENDENCY_SCORE"           , .2)
    ]
    log.log_metrics_created(metrics)

    rankings      = find_rankings(metrics, repositories)
    
    with open('dict.txt','w') as dict_file:
        for repo_scores in rankings:
            scores_dict = ranking_dict(repo_scores)
            dict_file.write(json.dumps(scores_dict))
            dict_file.write("\n")
    
    # with open('dict.txt','w') as dict_file:
    #     dict_file.write(json.dumps(scores_dict))

    output_string = print_results(metrics, rankings)

    print(output_string)


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
    # main()
