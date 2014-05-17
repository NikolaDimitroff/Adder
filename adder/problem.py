# Depends on: graphs.py

class InvalidArgumentError(Exception):
    pass

class _Node:
    def __init__(self, state, parent, action, path_cost):
        self.__state = state
        self.__parent = parent
        self.__action = action
        self.__path_cost = path_cost
        
    def __eq__(self, other):
        return self.state == other.state
        
    def __ne__(self, other):
        return not self == other
        
    def __hash__(self):
        return hash(self.state)
        
    def __str__(self):
        parent_name = self.parent.state if self.parent else "None"
        return self.state
        return "(State: {0}, Parent: {1}, Action: {2})".format(self.state, parent_name, self.action)
        
    def __repr__(self):
        return str(self)
        
    @property
    def state(self): return self.__state
    @property
    def parent(self): return self.__parent
    @property
    def action(self): return self.__action
    @property
    def path_cost(self): return self.__path_cost

FAILURE = "FAILURE"
SOLUTION_UNKNOWN = "SOLUTION_UNKNOWN"

class _Problem:    
    def child_node(self, node, action):
        parent = node
        state = self.result(node.state, action)
        action = action
        path_cost = node.path_cost + self.step_cost(node.state, action)
        
        child = _Node(state, parent, action, path_cost)
        return child
        
    def actions_iter(self, state):
        raise NotImplementedError("_Problem is abc")
        
    def step_cost(state, action):
        raise NotImplementedError("_Problem is abc")
        
    def result(self, state, action):
        raise NotImplementedError("_Problem is abc")
        
    def goal_test(self, state):
        raise NotImplementedError("_Problem is abc")
        
    def construct_solution(self, end_node):
        path = []
        while end_node != self.initial:
            parent = end_node.parent
            if parent.state in [node for node, action in path]:
                return FAILURE
                
            path.append((end_node.state, end_node.action))           
            end_node = parent
        path.append((self.initial.state, None))
        path.reverse()
        return path
        
        
    def solution_cost(self, solution):
        if solution is FAILURE or solution is SOLUTION_UNKNOWN:
            return 0
            
        cost = 0
        previous_state = None
        for state, action in solution:
            cost += self.step_cost(previous_state, action) if previous_state else 0
            previous_state = state
        return cost
        

class _GraphProblem(_Problem):
    def __init__(self, graph, root, goal):
        if root not in graph.get_nodes():
            raise InvalidArgumentError("root must be be a node in the graph")
        if goal not in graph.get_nodes():
            raise InvalidArgumentError("goal must be be a node in the graph")
            
        self.graph = graph
        self.initial = _Node(root, None, None, 0)
        self.goal = goal
        
    def actions_iter(self, state):
        return self.graph.children_iter(state)
        
    def step_cost(self, state, action):
        return self.graph.edge_cost(state, action)
        
    def result(self, state, action):
        return action if action in self.graph.children_iter(state) else None                      
        
    def goal_test(self, state):
        return state == self.goal


class _NPuzzleProblem(_Problem):
    def __init__(self, initial, goal):
        self.board_size = (initial.count(" ") + 1) ** 0.5
        if not self.board_size.is_integer():
            raise InvalidArgumentError("The size of the board must be a exact square!")

        self.board_size = int(self.board_size)
        self.initial = _Node(initial, None, None, 0)
        self.goal = goal
        
    def _swap_letters(self, text, first, second):
        text_array = text.split()

        first_letter = text_array[first]
        text_array[first] = text_array[second]
        text_array[second] = first_letter

        return " ".join(text_array) 

    def coords_of(self, state, number):
        number = str(number)
        index = -1
        for num_index, num in enumerate(state.split()):
            if num == number:
                index = num_index
                break
                 
        # index = i * 3 + j
        j = index % self.board_size
        i = (index - j) / self.board_size
        return (i, int(j))
    
    def actions_iter(self, state):
        i, j = self.coords_of(state, 0)

        index = int(i * self.board_size + j)
        neighbours = []
        if i < self.board_size - 1:
            neighbours.append(self._swap_letters(state, index, index + self.board_size))
        if i > 0:
            neighbours.append(self._swap_letters(state, index, index - self.board_size))
        if j < self.board_size - 1:
            neighbours.append(self._swap_letters(state, index, index + 1))
        if j > 0:
            neighbours.append(self._swap_letters(state, index, index - 1))

        return iter(neighbours)
            
        
    def step_cost(self, state, action):
        return 1
        
    def result(self, state, action):
        return action
        
    def goal_test(self, state):
        return state == self.goal


        
class ProblemFactory:
    def from_graph(self, graph, root, goal):
        return _GraphProblem(graph, root, goal)        

    def from_functions(self, initial_state, actions, step_cost, result, goal_test):
        problem = _Problem()
        problem.initial = _Node(initial, None, None, 0)
        problem.actions_iter = actions
        problem.step_cost = step_cost
        problem.result = result
        problem.goal_test = goal_test

        return problem

    def from_npuzzle(self, initial, goal):
        return _NPuzzleProblem(initial, goal)
