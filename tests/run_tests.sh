cd Setup
export EPICS_CA_ADDR_LIST=localhost
export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_MAX_ARRAY_BYTES=20100300
sh ./start_ioc.sh
sleep 1
python simulator.py &

cd ..
coverage erase
coverage run --source=epics -a  --timid  test_camonitor_func.py
coverage run --source=epics -a  --timid  test_ca_subscribe.py
coverage run --source=epics -a  --timid  test_ca_clearcache.py
coverage run --source=epics -a  --timid  test_cathread.py
coverage run --source=epics -a  --timid  test_ca_typeconversion.py
coverage run --source=epics -a  --timid  test_ca_unittests.py
coverage run --source=epics -a  --timid  test_multiprocessing.py
coverage run --source=epics -a  --timid  test_aodevice.py
coverage run --source=epics -a  --timid  test_pv_callback.py
coverage run --source=epics -a  --timid  test_pv_initcallbacks.py
coverage run --source=epics -a  --timid  test_pvsubarray.py
coverage run --source=epics -a  --timid  test_pv_typeconversion.py
coverage run --source=epics -a  --timid  test_pv_unittests.py
coverage run --source=epics -a  --timid  test_threading.py
coverage combine
coverage report -m
coverage html
