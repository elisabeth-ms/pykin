class Tree:
    """
    Tree
    """
    def __init__(self):
        self.vertices = []
        self.edges = []

    def add_vertex(self, q_joints):
        self.vertices.append(q_joints)

    def add_edge(self, q_joints_idx):
        self.edges.append(q_joints_idx)