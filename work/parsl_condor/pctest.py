import parsl
from parsl.providers import CondorProvider
from parsl.config import Config
from parsl.executors import HighThroughputExecutor

from parsl.configs.local_threads import config

SCHED_OPTS = """
kill_sig        = SIGINT
+Experiment     = "astro"
GetEnv          = True
Notification    = Never
Image_Size       =  1000000
"""

WORKER_INIT = """
export OMP_NUM_THREADS=1

if [[ -n $_CONDOR_SCRATCH_DIR ]]; then
    # the condor system creates a scratch directory for us,
    # and cleans up afterward
    tmpdir=$_CONDOR_SCRATCH_DIR
    export TMPDIR=$tmpdir
else
    # otherwise use the TMPDIR
    tmpdir='.'
    mkdir -p $tmpdir
fi

source activate bnl

echo `which python`
"""

WALLTIME = "48:00:00"

condor_config = Config(
    executors=[
        HighThroughputExecutor(
            worker_debug=True,
            provider=CondorProvider(
                cores_per_slot=1,
                mem_per_slot=2,
                nodes_per_block=1,
                init_blocks=10,
                max_blocks=10,
                scheduler_options=SCHED_OPTS,
                worker_init=WORKER_INIT,
                walltime=WALLTIME
            )
        )
    ],
)

parsl.load(condor_config)


@parsl.python_app
def app_double(x):
    return x*2


@parsl.python_app
def app_sum(inputs=[]):
    return sum(inputs)


items = range(0, 30)

mapped_results = []
for i in items:
    x = app_double(i)
    mapped_results.append(x)

total = app_sum(inputs=mapped_results)

print(total.result())
