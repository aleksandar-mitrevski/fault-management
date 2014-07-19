import networkx as nx
import matplotlib.pyplot as plt
import sympy

class GraphAnalyser(object):
    def __init__(self, unknown_vars, known_vars, constraints):
        self.__unknown_vars = list(unknown_vars)
        self.__known_vars = list(known_vars)
        self.__constraints = dict(constraints)
        self.__node_positions = dict()

        self.__graph = self.__create_graph(unknown_vars, known_vars, constraints)

    def __create_graph(self, unknown_vars, known_vars, constraints):
        graph = nx.Graph()
        for i in xrange(len(unknown_vars)):
            graph.add_node(unknown_vars[i])
            self.__node_positions[unknown_vars[i]] = (len(self.__node_positions.keys())*10., 20.)

        for i in xrange(len(known_vars)):
            graph.add_node(known_vars[i])
            self.__node_positions[known_vars[i]] = (len(self.__node_positions.keys())*10., 20.)

        #counter used for visualisation purposes
        constraint_counter = 0
        for constraint, variables in constraints.iteritems():
            graph.add_node(constraint)
            self.__node_positions[constraint] = (constraint_counter*10., 0.)
            constraint_counter = constraint_counter + 1
            for j in xrange(len(variables)):
                graph.add_edge(constraint, variables[j])

        return graph

    def draw_graph(self):
        '''Coloring as done in http://stackoverflow.com/questions/13517614/draw-different-color-for-nodes-in-networkx-based-on-their-node-value?rq=1
        '''
        node_colors = list()
        for node in self.__graph.nodes():
            if node in self.__unknown_vars:
                node_colors.append('r')
            elif node in self.__known_vars:
                node_colors.append('g')
            else:
                node_colors.append('b')

        nx.draw(self.__graph, pos=self.__node_positions, node_color=node_colors)
        plt.show()

    def get_nodes(self):
        return self.__graph.nodes()

    def get_adjacency_matrix(self):
        matrix = nx.adjacency_matrix(self.__graph).tolist()
        nodes = self.__graph.nodes()

        ordered_constraints = []
        ordered_variables = []

        for i,node in enumerate(nodes):
            if node in self.__constraints:
                ordered_constraints.append(node)
            else:
                ordered_variables.append(node)

        reduced_matrix = []

        for i,node in enumerate(nodes):
            if node in self.__constraints:
                adjacency_row = list(matrix[i])
                j = len(nodes)-1
                while j >= 0:
                    if nodes[j] in self.__constraints:
                        del adjacency_row[j]
                    j = j - 1
                reduced_matrix.append(adjacency_row)

        return reduced_matrix, ordered_constraints, ordered_variables

    def find_matching(self):
        '''Matching algorithm based on Blanke's ranking algorithm.
        '''

        rank = 0
        matching = dict()
        ranking = dict()
        zero_var = sympy.Symbol('zero')

        for _,variable in enumerate(self.__known_vars):
            ranking[variable] = rank

        adj_matrix, ordered_constraints, ordered_variables = self.get_adjacency_matrix()
        continue_ranking = True
        while continue_ranking:
            for i,constraint in enumerate(ordered_constraints):
                unmatched_vars_counter = 0
                unmatched_var = None
                for j,variable in enumerate(ordered_variables):
                    if adj_matrix[i][j] > 0. and variable not in ranking.keys():
                        unmatched_vars_counter = unmatched_vars_counter + 1
                        unmatched_var = variable

                if unmatched_vars_counter == 1:
                    ranking[unmatched_var] = rank
                    ranking[constraint] = rank
                    matching[constraint] = unmatched_var

            for i,constraint in enumerate(ordered_constraints):
                if constraint not in ranking.keys():
                    unmatched_vars_counter = 0
                    unmatched_var = None
                    for j,variable in enumerate(ordered_variables):
                        if adj_matrix[i][j] > 0. and variable not in ranking.keys():
                            unmatched_vars_counter = unmatched_vars_counter + 1
                            unmatched_var = variable

                    if unmatched_vars_counter == 0:
                        ranking[constraint] = rank
                        matching[constraint] = zero_var

            all_variables_ranked = True
            for _,variable in enumerate(ordered_variables):
                if variable not in ranking.keys():
                    all_variables_ranked = False
                    break

            all_constraints_ranked = True
            for _,constraints in enumerate(ordered_constraints):
                if constraints not in ranking.keys():
                    all_constraints_ranked = False
                    break

            if all_constraints_ranked or all_variables_ranked:
                continue_ranking = False
            else:
                rank = rank + 1

        return ranking, matching