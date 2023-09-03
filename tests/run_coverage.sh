coverage erase
pytest test_camonitor_func.py
pytest test_ca_subscribe.py
pytest test_ca_clearcache.py
pytest test_cathread.py
pytest test_ca_typeconversion.py
pytest test_ca_unittests.py
pytest test_multiprocessing.py
pytest test_aodevice.py
pytest test_pv_callback.py
pytest test_pv_initcallbacks.py
pytest test_pvsubarray.py
pytest test_pv_typeconversion.py
pytest test_pv_unittests.py
pytest test_threading.py
coverage combine
coverage report -m --omit "wxlib*,ogl*,motor*,mca*,ad*,struck*,transform*,scan*,scal*,xspress*"
coverage html --omit "wxlib*,ogl*,motor*,mca*,ad*,struck*,transform*,scan*,scal*,xspress*"
