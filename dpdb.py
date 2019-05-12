import logging
import sys
import subprocess

from dpdb.db import DB, DEBUG_SQL, setup_debug_sql
from dpdb.db import BlockingThreadedConnectionPool
from dpdb.reader import TdReader
from dpdb.writer import StreamWriter
from dpdb.treedecomp import TreeDecomp
from dpdb.sat import Sat
from dpdb.sharpsat import SharpSat

logger = logging.getLogger(__name__)

def read_cfg(cfg_file):
    import json

    with open(cfg_file) as c:
        cfg = json.load(c)
    return cfg

def solve_problem(problem_type, cfg, fname):
    pool = BlockingThreadedConnectionPool(1,cfg["db"]["max_connections"],**cfg["db"]["dsn"])
    problem = problem_type(fname, pool)
    # Run htd
    p = subprocess.Popen([cfg["htd"]["path"], *cfg["htd"]["parameters"]], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    StreamWriter(p.stdin).write_gr(*problem.prepare_input(fname))
    p.stdin.close()
    p.wait()

    tdr = TdReader.from_stream(p.stdout)
    td = TreeDecomp(tdr.num_bags, tdr.tree_width, tdr.num_orig_vertices, tdr.root, tdr.bags, tdr.adjecency_list)
    logger.debug("#bags: {0} tree_width: {1} #vertices: {2} edges: {3}".format(td.num_bags, td.tree_width, td.num_orig_vertices, td.edges))
    problem.set_td(td)
    problem.setup()
    problem.solve()

if __name__ == "__main__":
    # TODO: parse args

    setup_debug_sql()
    logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s', level=logging.INFO)

    cfg = read_cfg("config.json")
    solve_problem(SharpSat, cfg, sys.argv[1])
