from .chain import dataset as chain
from .dense import dataset as dense
from .geometric import dataset as geometric
from .oldenburg import dataset as oldenburg
from .roadnet_ca import dataset as roadnet_ca
from .shortcuts import dataset as shortcuts
from .triangle_relations import dataset as triangle_relations

DATASETS = {"chain": chain, "dense": dense, "geometric": geometric, "oldenburg": oldenburg, "roadnet_ca": roadnet_ca,
            "shortcuts": shortcuts, "triangle_relations": triangle_relations}
