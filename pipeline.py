from log import quit_with_error

try:
    import path
except ImportError:
    quit_with_error("Pesto requiered path.py to be installed, "
                    "checkout requirement.txt.")
try:
    import networkx
except ImportError:
    quit_with_error("Pesto requiered path.py to be installed, "
                    "checkout requirement.txt.")


# class PipelineError(Exception):
#     def __init__(self, value):
#         self.value = value

#     def __str__(self):
#         return repr(self.value)

from node import Root

class Pipeline():
    _root = Root()
    _graph = networkx.DiGraph()
    _nodes = None

    def __init__(self, yaml_documents):
        # init with root
        self._nodes = {self._root.name: self._root}
        self._graph.add_node(self._root.name)
        # build graph
        self._build_nodes_from_documents(yaml_documents, self._root)
        self._build_edges()
        if not networkx.is_directed_acyclic_graph(self._graph):
            quit_with_error("Cycle detected in pipeline")
        # refine graph
        self._transitive_reduction()

    def _build_nodes_from_documents(self, documents, previous_node):
        from node import Node
        from yaml_io import YamlIO
        from evaluator import Evaluator
        from data_model import DataModel
        evltr = Evaluator()
        for doc in documents:
            if('__FILE__' in doc):
                filename = path.Path(evltr.evaluate(doc['__FILE__']))
                if(not filename.isabs()):
                    filename = DataModel.document_path / filename
                d = YamlIO.load_all_yaml(filename)
                previous_node = self._build_nodes_from_documents(d, 
                                                                 previous_node)
            else:
                node = Node(doc, previous_node)
                previous_node = node
                self._graph.add_node(node.name)
                self._nodes[node.name] = node
        return previous_node

    def _build_edges(self):
        for node in self._nodes:
            for parent in self._nodes[node].parents:
                self._graph.add_edge(parent, node)

    def _transitive_reduction(self):
        reducted_graph = networkx.DiGraph()
        reducted_graph.add_nodes_from(self._graph.nodes())

        #  get longest path between root and all nodes of the pipeline:
        for node in self._graph.nodes():
            if node == self._root.name:
                continue
            paths = self._find_longest_paths(self._root.name, node)
            # add edges corresponding to those paths to the reducted graph
            for p in paths:
                    end = len(p) - 1
                    for n1, n2 in zip(p[:end], p[1:]):
                        reducted_graph.add_edge(n1, n2)

        self._graph = reducted_graph

    # TODO: clean this up
    def _find_longest_paths(self, src, dest, visited=None, longest_paths=None):
        if visited is None:
            visited = []
        if longest_paths is None:
            longest_paths = [[]]
        # if not src in current_path:
        current_path = visited.copy()
        current_path.append(src)
        # are we at destination ? if yes compare and return
        if src == dest:
            is_longest = False
            for p in longest_paths:
                if len(p) <= len(current_path):
                    is_longest = True
                    longest_paths.append(current_path)
                    if len(p) < len(current_path):
                        longest_paths.remove(p)
                if is_longest:
                    return longest_paths

        # else continue to walk
        else:
            for src, child in self._graph.edges(src):
                longest_paths = self._find_longest_paths(child,
                                                         dest,
                                                         visited=current_path,
                                                         longest_paths=longest_paths)
        return longest_paths

    def walk(self, node=None):
        for n in networkx.dfs_preorder_nodes(self._graph, node):
            yield self._nodes[n]

    @property
    def root(self):
        return self._root


class PipelineExecutor():
    def print_progression(self):
        print("pouette")

    def execute_node(self, node):
        print("pouette execute")


from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from evaluator import Evaluator


class ThreadedPipelineExecutor(PipelineExecutor):
    _pipeline = None
    _max_workers = 0
    _futures = None

    def __init__(self, pipeline, max_workers):
        self._max_workers = max_workers
        self._pipeline = pipeline
        self._futures = dict()

    def print_execution(self):
        for node in self._pipeline.walk():
            if node == self._pipeline.root:
                print("This is root.")
                continue
            print("Executing: ", node.name)
            for scope_value in node.scope.values:
                evaluator = Evaluator(scope_value)
                cmd_str = evaluator.evaluate(" ".join(node.cmd))
                print(cmd_str)


    # def execute():
    #     for node in Pipeline.walk(Pipeline.root):
    #         max_workers = self._max_workers * node.max_workers
    #         with concurrent.future.ThreadPoolExecutor(max_workers) as ex:
    #             for scope_value in node.scope.values:                    
    #             self._futures[scope_value] = ex.submit()
