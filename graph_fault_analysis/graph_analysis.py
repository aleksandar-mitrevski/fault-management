import networkx as nx
import matplotlib.pyplot as plt
import sympy

class GraphAnalyser(object):
    '''Defines a library for creating and analysing graphs that represent system constraints and variables.
    The class is based on M. Blanke, M. Kinnaert, J. Lunze and M. Staroswiecki, Diagnosis and Fault Tolerant Control. Germany: Springer-Verlag Berlin Heidelberg, 2006.

    Author -- Aleksandar Mitrevski

    '''
    def __init__(self, unknown_vars, known_vars, constraints):
        '''
        Keyword arguments:
        unknown_vars -- A list of unknown system variables.
        known_vars -- A list of known system variables.
        constraints -- A dictionary where the keys represent constraints and the values represent list of variables associated with the appropriate constraints.
        
        '''
        self.__unknown_vars = list(unknown_vars)
        self.__known_vars = list(known_vars)
        self.__constraints = dict(constraints)

        #dictionary used for better visualisation of the graph
        self.__node_positions = dict()

        self.__graph = self.__create_graph(unknown_vars, known_vars, constraints)

    def __create_graph(self, unknown_vars, known_vars, constraints):
        '''Creates a bipartite graph connecting system variables and constraints.

        Keyword arguments:
        unknown_vars -- A list of unknown system variables.
        known_vars -- A list of known system variables.
        constraints -- A dictionary where the keys represent constraints and the values represent list of variables associated with the appropriate constraints.

        Returns:
        graph -- A 'networkx.Graph' object.

        '''
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

    def draw_graph(self, edge_colours=None):
        '''Draws 'self.__graph'. The nodes are coloured as in http://stackoverflow.com/questions/13517614/draw-different-color-for-nodes-in-networkx-based-on-their-node-value?rq=1

        Keyword arguments:
        edge_colours -- If it is equal to None, the variable is ignored; if not, it is expected to be a list of colours, such that the i-th element corresponds to the i-th edge in 'self.__graph.edges()'.

        '''
        node_colours = list()
        for node in self.__graph.nodes():
            if node in self.__unknown_vars:
                node_colours.append('r')
            elif node in self.__known_vars:
                node_colours.append('g')
            else:
                node_colours.append('b')

        if edge_colours != None:
            nx.draw(self.__graph, pos=self.__node_positions, node_color=node_colours, edge_colour=edge_colours)
        else:
            nx.draw(self.__graph, pos=self.__node_positions, node_color=node_colours)

    def draw_matched_graph(self, matching):
        '''Draws 'self.__graph' using a previously found matching.

        Keyword arguments:
        matching -- A dictionary where the keys represent constraints and the values represent variables matched with the constraints.

        '''
        matching_edges = self.get_matching_edges(matching)

        edge_colours = list()
        for _,edge in enumerate(self.__graph.edges()):
            if edge in matching_edges or edge[::-1] in matching_edges:
                edge_colours.append('r')
            else:
                edge_colours.append('k')

        self.draw_graph(edge_colours)

    def draw_directed_graph(self, matching):
        '''Uses a matching for finding a directed version of 'self.__graph'; draws the directed graph after constructing it.

        Keyword arguments:
        matching -- A dictionary where the keys represent constraints and the values represent variables matched with the constraints.

        '''

        directed_graph = self.__create_matching_graph(matching)
        zero_var = sympy.Symbol('zero')

        node_colours = list()
        for node in directed_graph.nodes():
            if node in self.__unknown_vars:
                node_colours.append('r')
            elif node in self.__known_vars or node == zero_var:
                node_colours.append('g')
            else:
                node_colours.append('b')

        node_positions = dict(self.__node_positions)
        node_positions[zero_var] = ((len(self.__unknown_vars) + len(self.__known_vars))*10., 20.)
        nx.draw(directed_graph, pos=node_positions, node_color=node_colours)

    def get_nodes(self):
        return self.__graph.nodes()

    def get_edges(self):
        return self.__graph.edges()

    def get_matching_edges(self, matching):
        '''Converts the input dictionary into a list of tuples and returns the list.

        Keyword arguments:
        matching -- A dictionary where the keys represent constraints and the values represent variables matched with the constraints.

        Returns:
        matching_edges -- A list of tuples; each tuple represents an edge that belongs to a matching.

        '''
        matching_edges = list()
        for key,value in matching.iteritems():
            matching_edges.append((key,value))
        return matching_edges

    def get_adjacency_matrix(self):
        '''Finds a reduced version of the adjacency matrix representing 'self.__graph',
        such that the rows represent constraints and the columns represent variables.

        Returns:
        reduced_matrix -- The reduced adjacency matrix.
        ordered_constraints -- A list of constraints represented by the graph, such that the i-th constraint represents the i-th row of 'reduced_matrix'.
        ordered_variables -- A list of variables represented by the graph, such that the i-th variables represents the i-th column of 'reduced_matrix'.

        '''
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
        '''Finds a matching in 'self.__graph'.
        The matching algorithm uses the ranking algorithm described in Blanke et al., p. 142.

        Returns:
        matching -- A dictionary where the keys represent constraints and the values represent variables matched with the constraints.

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

        return matching

    def __create_matching_graph(self, matching):
        '''Finds a directed version of 'self.__graph' using the input matching; the conversion of the graph is based on Blanke et al., p. 125.

        Returns:
        graph -- A 'network.DiGraph' object representing the graph's directed version.

        '''
        graph = nx.DiGraph()
        matching_edges = self.get_matching_edges(matching)

        for _,edge in enumerate(self.__graph.edges()):
            if edge in matching_edges:
                graph.add_edge(edge[0], edge[1])
            elif edge[::-1] in matching_edges:
                graph.add_edge(edge[1], edge[0])
            else:
                if edge[0] in self.__constraints:
                    graph.add_edge(edge[1], edge[0])
                else:
                    graph.add_edge(edge[0], edge[1])

        zero_var = sympy.Symbol('zero')
        for _,edge in enumerate(matching_edges):
            if zero_var == edge[1]:
                graph.add_edge(edge[0], edge[1])

        return graph