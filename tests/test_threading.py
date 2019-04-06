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
