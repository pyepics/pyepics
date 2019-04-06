import pytest

import epics
import threading
import pvnames


def test_basic_thread():
    result = []
    def thread():
        epics.ca.use_initial_context()
        pv = epics.PV(pvnames.double_pv)
        result.append(pv.get())

    epics.ca.use_initial_context()
    t = threading.Thread(target=thread)
    t.start()
    t.join()

    assert len(result) and result[0] is not None


def test_basic_cathread():
    result = []
    def thread():
        pv = epics.PV(pvnames.double_pv)
        result.append(pv.get())

    epics.ca.use_initial_context()
    t = epics.ca.CAThread(target=thread)
    t.start()
    t.join()

    assert len(result) and result[0] is not None


def test_attach_context():
    result = []
    def thread():
        epics.ca.create_context()
        pv = epics.PV(pvnames.double_pv2)
        assert pv.wait_for_connection()
        result.append(pv.get())
        epics.ca.detach_context()

        epics.ca.attach_context(ctx)
        pv = epics.PV(pvnames.double_pv)
        assert pv.wait_for_connection()
        result.append(pv.get())

    epics.ca.use_initial_context()
    ctx = epics.ca.current_context()
    t = threading.Thread(target=thread)
    t.start()
    t.join()

    assert len(result) == 2 and result[0] is not None
    print(result)


def test_pv_from_main():
    result = []
    def thread():
        result.append(pv.get())

    epics.ca.use_initial_context()
    pv = epics.PV(pvnames.double_pv2)

    t = epics.ca.CAThread(target=thread)
    t.start()
    t.join()

    assert len(result) and result[0] is not None


@pytest.mark.parametrize('num_threads', [1, 200])
def test_pv_multithreaded_get(num_threads):
    def thread(thread_idx):
        result[thread_idx] = (pv.get(),
                              pv.get_with_metadata(form='ctrl')['value'],
                              pv.get_with_metadata(form='time')['value'],
                              )

    result = {}
    epics.ca.use_initial_context()
    pv = epics.PV(pvnames.double_pv2)

    threads = [epics.ca.CAThread(target=thread,
                                 args=(i, ))
               for i in range(num_threads)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(result) == num_threads
    print(result)
    values = set(result.values())
    assert len(values) == 1

    value, = values
    assert value is not None
