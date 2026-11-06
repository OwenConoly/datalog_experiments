from .chain import dataset as chain
from .dense import dataset as dense
from .geometric import dataset as geometric
from .oldenburg import dataset as oldenburg
from .shortcuts import dataset as shortcuts
from .triangle_relations import dataset as triangle_relations

DATASETS = {"chain": chain, "dense": dense, "geometric": geometric, "oldenburg": oldenburg, "shortcuts": shortcuts,
            "triangle_relations": triangle_relations}
