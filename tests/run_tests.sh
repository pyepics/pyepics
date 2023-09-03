cd Setup
export EPICS_CA_ADDR_LIST=localhost
export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_MAX_ARRAY_BYTES=20100300
sh ./start_ioc.sh
sleep 2
python simulator.py &
sleep 2
cd ..
sh run_coverage.sh
