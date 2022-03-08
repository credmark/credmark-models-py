import os
import webbrowser
import dask.distributed as dask_dist

if __name__ == '__main__':
    # Below is similar to launching server with # dask-scheduler.exe --show --host localhost --port 8786
    THREADS_PER_WORKER = 1
    cluster = dask_dist.LocalCluster(
        threads_per_worker=THREADS_PER_WORKER, host=None, scheduler_port=8786, processes=True,)

    # We use fixed instead of adative: cluster.adapt(minimum=0, maximum_memory="100 GiB", interval='500ms')
    webbrowser.open(cluster.dashboard_link, new=2)

    print(f'Launched cluser with dashboard at {cluster.dashboard_link}')

    userInput = None
    while userInput != 'end':
        userInput = input(f'Running. Type "end" to end. Or kill the process {os.getpid()}\n')
