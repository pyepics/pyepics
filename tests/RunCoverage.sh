coverage erase

coverage run --source=epics -a -p --timid  alarm.py
coverage run --source=epics -a -p --timid  ca_connection_callback.py
coverage run --source=epics -a -p --timid  ca_simpletest.py
coverage run --source=epics -a -p --timid  ca_subscribe.py
coverage run --source=epics -a -p --timid  ca_subscribe2.py
coverage run --source=epics -a -p --timid  ca_type_conversion.py
coverage run --source=epics -a -p --timid  ca_unittest1.py
coverage run --source=epics -a -p --timid  connect.py
coverage run --source=epics -a -p --timid  memleak.py
coverage run --source=epics -a -p --timid  no_monitor.py
coverage run --source=epics -a -p --timid  putwait.py
coverage run --source=epics -a -p --timid  pv_callback.py
coverage run --source=epics -a -p --timid  pv_connection_callback.py
coverage run --source=epics -a -p --timid  pv_multiple_callbacks.py
coverage run --source=epics -a -p --timid  pv_simpletest.py
coverage run --source=epics -a -p --timid  pv_type_conversion.py
coverage run --source=epics -a -p --timid  thread_test.py
coverage run --source=epics -a -p --timid  sg_test.py

coverage combine

coverage report -m
