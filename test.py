import sympy
from graph_fault_analysis.graph_analysis import GraphAnalyser

#the data in this example are taken from example 5.22, "Diagnosis and Fault Tolerant Control"
h,h_dot,qi,qo,u,y = sympy.symbols('h,h_dot,qi,qo,u,y')
c1,c2,c3,c4,c5,c6 = sympy.symbols('c1,c2,c3,c4,c5,c6')

unknown_vars = [h,h_dot,qi,qo]
known_vars = [u,y]
constraints = dict({c1: [h_dot,qi,qo], c2: [qi,u], c3: [h,qo], c4: [h,y], c5: [u,y], c6: [h,h_dot]})

graph_analyser = GraphAnalyser(unknown_vars, known_vars, constraints)
ranking, matching = graph_analyser.find_matching()