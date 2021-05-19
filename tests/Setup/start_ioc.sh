$CONDA/bin/procServ -n pyepics_testioc \
		   --allow --noautorestart \
		   -P 9230 -L pyepics_testioc.log \
		   -e $CONDA/epics/bin/linux-x86_64/softIoc ./st.cmd
