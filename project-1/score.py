import re
from log import log

class Node:
    # Used to contain ranking information for a repository. Also has a left and right child
    # for use in a binary tree.
    
    def __init__(self, repository, score):
        self.repository = repository
        self.score      = score
        self.left  = None
        self.right = None

class Ranking:
    # When a ranking object is created, a list of repositories and a list of metrics is passed
    # to it's constructor. The purpose of this class is to calculate the sub scores and total
    # score for each repository, and returns an list of these repositories ordered by their
    # total score (in descending order). Uses a binary tree to store the rankings.

    def __init__(self, metrics):
        self.metrics = metrics
        self.tree    = None

    def get_rankings(self, repositories):
        for repository in repositories:
            score = self.__determine_score(repository)
            node  = Node(repository, score)
            self.__insert_into_tree(self.tree, node)

            log.log_overall_score_calculations(repository, self.metrics, score)
            log.log_overall_score(repository, score)

        return self.__get_ordered_list(self.tree)

    def __determine_score(self, repository):
        score = 0
        for i, sub_score in enumerate(repository.scores):
            score += sub_score * self.metrics[i].weight
        
        return score

    def __insert_into_tree(self, tree, node):
        if self.tree is None:
            self.tree = node
            return

        if node.score < tree.score:
            if tree.right is None:
                tree.right = node
            else:
                self.__insert_into_tree(tree.right, node)
        else:
            if tree.left is None:
                tree.left = node
            else:
                self.__insert_into_tree(tree.left, node)

    def __get_ordered_list(self, tree):
        if tree is None:
            return

        ordered_list = []

        left_list = self.__get_ordered_list(tree.left)
        if left_list is not None:
            ordered_list += left_list

        ordered_list.append(tree)

        right_list = self.__get_ordered_list(tree.right)
        if right_list is not None:
            ordered_list += right_list

        return ordered_list