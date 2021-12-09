import os
import datetime

from dotenv import load_dotenv

class Log():
    load_dotenv()
    log_file  = os.getenv('LOG_FILE')
    log_level = int(os.getenv('LOG_LEVEL')) if os.getenv('LOG_LEVEL') else 0 
    warning   = "[WARNING] "
    debug     = "[DEBUG  ] "
    trace     = "[TRACE  ] "
    error     = "[ERROR  ] "

    def log_url_file_read(self, file_name):
        log = self.debug + file_name + " is open."
        self.__write_log_to_file(log)

    def log_url_file_closed(self, file_name):
        log = self.debug + file_name + " is closed."
        self.__write_log_to_file(log)

    def log_repository_created(self, repo):
        log = self.trace + "'" + repo.name + "'" + " repository is downloaded"
        self.__write_log_to_file(log)
        
    def log_repo_list_created(self, repoList):
        log = self.trace + "Repository list is created, contains repositories: ["
        for repo in repoList:
            log += "'" + repo.name + "', "
        log += "]"
        self.__write_log_to_file(log)

    def log_metrics_created(self, metrics):
        log = self.trace + "Metrics are created, contains metrics: ["
        for metric in metrics:
            log += "'" + metric.name + "', "
        log += "]"
        self.__write_log_to_file(log)

    def log_no_dependencies(self, repo):
        log = self.warning + "No dependencies found for repository '" + repo.name + "'"
        self.__write_log_to_file(log)

    def log_no_license(self, repo):
        log = self.warning + "No license found for repository '" + repo.name + "'"
        self.__write_log_to_file(log)

    def log_url_type(self, url, repo_type):
        log = self.debug + url + " is of type: " + repo_type
        self.__write_log_to_file(log)

    def log_subscore_calculated(self, repo, score, metric):
        log = self.debug + "Repository '" + repo.name + "' has '" + metric.name + "' score of " + str(score)
        self.__write_log_to_file(log)

    def log_metric_subscores_calculated(self, metric, scores, repositories):
        log = self.debug + "Scores for metric '" + metric.name + "' are: ["
        for i, score in enumerate(scores):
            log += "'" + repositories[i].name + "': " + str(score) + ", "
        log += "]"
        self.__write_log_to_file(log)

    def log_norm_metric_subscores_calculated(self, metric, scores, repositories):
        log = self.trace + "Normalized scores for metric '" + metric.name + "' are: ["
        for i, score in enumerate(scores):
            log += "'" + repositories[i].name + "': " + str(score) + ", "
        log += "]"
        self.__write_log_to_file(log)

    def log_overall_score_calculations(self, repository, metrics, score):
        log = self.debug +  "Repository '" + repository.name + "' has subscores: " + str(repository.scores) + " and the metric weights are ["
        for metric in metrics:
            log += metric.name + ": " + str(metric.weight) + ", "
        log += "]"
        self.__write_log_to_file(log)

    def log_overall_score(self, repository, score):
        log = self.trace + "Repository '" + repository.name + "' has overall score of " + str(score)
        self.__write_log_to_file(log)

    def log_final_rankings(self, rankings):
        log = self.trace + "final scores: ["
        for ranking in rankings:
            log += str(ranking) + ", "
        log += "]"
        
        self.__write_log_to_file(log)

    def log_semgrep_test_results(self, repo_name, test_name, num_issues):
        log = self.debug + "semgrep test " + test_name + " found " + str(num_issues) + " issues with repository '" + repo_name + "'"
        self.__write_log_to_file(log)

    def __write_log_to_file(self, log):
        if self.log_level > 0 and (self.log_level == 2 or self.debug not in log):
            log = str(datetime.datetime.now()) + ": " + log + "\n"
            with open(self.log_file, 'a') as file:
                file.write(log)

log = Log()
