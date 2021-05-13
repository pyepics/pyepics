import ctypes
import epics.dbr as dbr


def _build_args(dbr_type, c_data):
    args = dbr.event_handler_args()
    args.type = dbr_type
    args.count = len(c_data)
    args.raw_dbr = ctypes.cast(c_data, ctypes.c_void_p)
    args.status = dbr.ECA_NORMAL
    return args


def test_cast_args():
    # cast_args casts a single native_type to [None, pointer to the native type]
    args = _build_args(dbr.DOUBLE, (ctypes.c_double * 1)(3.1415))
    assert dbr.cast_args(args)[0] is None
    assert 1 == len(dbr.cast_args(args)[1])
    assert 3.1415 == dbr.cast_args(args)[1][0]

    # cast_args casts an array of native_type to [None, pointer to the native type]
    args = _build_args(dbr.DOUBLE, (ctypes.c_double * 4)(1, 2, 3, 5))
    assert dbr.cast_args(args)[0] is None
    assert 4 == len(dbr.cast_args(args)[1])
    assert [1, 2, 3, 5] == [v for v in dbr.cast_args(args)[1]]

    # cast_args casts unknown type to [None, None]
    args = _build_args(123456789, (ctypes.c_char * 1)(123))
    assert dbr.cast_args(args)[0] is None
    assert dbr.cast_args(args)[1] is None
