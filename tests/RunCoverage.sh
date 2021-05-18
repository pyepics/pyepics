coverage erase

coverage run --source=epics -a -p --timid  test_camonitor_func.py
coverage run --source=epics -a -p --timid  test_ca_subscribe.py
coverage run --source=epics -a -p --timid  test_cathread.py
coverage run --source=epics -a -p --timid  test_ca_typeconversion.py
coverage run --source=epics -a -p --timid  test_ca_unittests.py
coverage run --source=epics -a -p --timid  test_multiprocessing.py
coverage run --source=epics -a -p --timid  test_aodevice.py
coverage run --source=epics -a -p --timid  test_pv_callback.py
coverage run --source=epics -a -p --timid  test_pv_initcallbacks.py
coverage run --source=epics -a -p --timid  test_pvsubarray.py
coverage run --source=epics -a -p --timid  test_pv_typeconversion.py
coverage run --source=epics -a -p --timid  test_pv_unittests.py
coverage run --source=epics -a -p --timid  test_threading.py

coverage combine
coverage report -m
