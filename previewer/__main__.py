import sys
import multiprocessing as mp
from previewer import IPythonProcess

# interactive previewer session for debugging
if __name__ == "__main__":
    exec_conn, exec_conn_c = mp.Pipe()
    ctrl_conn, ctrl_conn_c = mp.Pipe()
    ns_conn, ns_conn_c = mp.Pipe()
    sys.stdin.close()
    proc = IPythonProcess(exec_conn_c, ctrl_conn_c, ns_conn_c, interactive=True)
    proc.join()
