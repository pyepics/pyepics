#!/usr/bin/env python

from EpicsCA import PV, PVcache, connect_all, disconnect_all
import time

def test_connection(pvs):
    "test connection time for a list of pv names"
    import time
    t0 = time.time()
    
    x = []
    # first, create PV without connecting
    for pvname in pvs:
        x.append(PV(pvname,connect=False))
    
    t1 = time.time()
    # now connect all unconnected PVs
    for m in PVcache.values():
        m.connect() # if not m.connected: m.connect()#         m.connect() 
    
    # connect_all()

    t2 = time.time()

    dt1 = t1-t0
    dt2 = t2-t1
    print "Create time for %i PVs = %.3f sec" % (len(x), dt1)
    
    print "Connect time for %i PVs = %.3f sec  (%.3f msec / PV)" % (len(x), dt2, 1000.*dt2/len(x) )

    # test for unconnected PVs
    nx = 0
    for i in x:
        if not i.connected: nx = nx + 1
    if nx > 0:
        print "%i of %i PVs did not connect" % (nx, len(x))
    else:
        print "All PVs connected."
    return

xpvlist = ['13IDC:m2.VAL', '13IDC:m1.VAL', '13IDC:m3.VAL', '13IDC:m4.VAL']

pvlist  = ['13BMA:BMC_BS_status.DESC', '13BMA:BMC_BS_status.VAL',
'13BMA:BMD_BS_status.DESC', '13BMA:BMD_BS_status.VAL',
'13BMA:cc1.VAL', '13BMA:cc2.VAL', '13BMA:cc3.VAL', '13BMA:cc4.VAL',
'13BMA:cc7.VAL', '13BMA:cc8.VAL', '13BMA:cc9.VAL',
'13BMA:DMM1Ch2_calc.VAL', '13BMA:DMM1Ch3_calc.VAL',
'13BMA:E:Energy.VAL', '13BMA:eps_bo1.VAL', '13BMA:eps_bo2.VAL',
'13BMA:ip10_Current.VAL', '13BMA:ip10_Pressure.VAL',
'13BMA:ip10_Volts.VAL', '13BMA:ip1_Current.VAL',
'13BMA:ip1_Pressure.VAL', '13BMA:ip1_Volts.VAL',
'13BMA:ip2_Current.VAL', '13BMA:ip2_Pressure.VAL',
'13BMA:ip2_Volts.VAL', '13BMA:ip7_Current.VAL',
'13BMA:ip7_Pressure.VAL', '13BMA:ip7_Volts.VAL', '13BMA:ip8:CUR.VAL',
'13BMA:ip8:PRES.VAL', '13BMA:ip8:VOLT.VAL', '13BMA:ip9:CUR.VAL',
'13BMA:ip9:PRES.VAL', '13BMA:ip9:VOLT.VAL', '13BMA:pr10.VAL',
'13BMA:pr1.VAL', '13BMA:pr2.VAL', '13BMA:pr3.VAL', '13BMA:pr4.VAL',
'13BMA:pr7.VAL', '13BMA:pr8.VAL', '13BMA:pr9.VAL',
'13BMA:V1_status.VAL', '13BMA:V2_status.VAL', '13BMA:V3_status.VAL',
'13BMA:V4C_status.VAL', '13BMA:V4D_status.VAL',
'13BMD:A1offset_num.VAL', '13BMD:A1offset_unit.VAL',
'13BMD:A1sens_num.VAL', '13BMD:A1sens_unit.VAL',
'13BMD:A2offset_num.VAL', '13BMD:A2offset_unit.VAL',
'13BMD:A2sens_num.VAL', '13BMD:A2sens_unit.VAL',
'13BMD:A3offset_num.VAL', '13BMD:A3offset_unit.VAL',
'13BMD:A3sens_num.VAL', '13BMD:A3sens_unit.VAL',
'13BMD:DMM1Ch10_calc.VAL', '13BMD:DMM1Ch19_calc.VAL',
'13BMD:DMM1Ch1_calc.VAL', '13BMD:DMM1Ch2_calc.VAL',
'13BMD:DMM1Ch3_calc.VAL', '13BMD:DMM1Ch4_calc.VAL',
'13BMD:DMM1Ch5_calc.VAL', '13BMD:DMM1Ch6_calc.VAL',
'13BMD:DMM1Ch7_calc.VAL', '13BMD:DMM1Ch8_calc.VAL',
'13BMD:DMM1Ch9_calc.VAL', '13BMD:DMM2Ch10_calc.VAL',
'13BMD:DMM2Ch1_calc.VAL', '13BMD:DMM2Ch2_calc.VAL',
'13BMD:DMM2Ch3_calc.VAL', '13BMD:DMM2Ch4_calc.VAL',
'13BMD:DMM2Ch5_calc.VAL', '13BMD:DMM2Ch6_calc.VAL',
'13BMD:DMM2Ch7_calc.VAL', '13BMD:DMM2Ch8_calc.VAL',
'13BMD:DMM2Ch9_calc.VAL', '13BMD:Verdi1:AvrCurrent.VAL',
'13BMD:Verdi1:BaseTemp.VAL', '13BMD:Verdi1:Diode1Current.VAL',
'13BMD:Verdi1:Diode1Heatsink.VAL', '13BMD:Verdi1:Diode1Power.VAL',
'13BMD:Verdi1:Diode1Temp.VAL', '13BMD:Verdi1:Etalon.VAL',
'13BMD:Verdi1:LBOt.VAL', '13BMD:Verdi1:Vanadate.VAL',
'13IDA:BS_status.VAL', '13IDA:cc1.VAL', '13IDA:cc2.VAL',
'13IDA:cc3.VAL', '13IDA:cc5.VAL', '13IDA:cc6.VAL', '13IDA:cc7.VAL',
'13IDA:DAC1_3.VAL', '13IDA:DMM1Ch2_calc.VAL',
'13IDA:DMM1Ch3_calc.VAL', '13IDA:DMM2Ch9_raw.VAL',
'13IDA:E:Energy.VAL', '13IDA:ILM200_calc1.VAL',
'13IDA:ILM200_calc2.VAL', '13IDA:ip1_Current.VAL',
'13IDA:ip1_Pressure.VAL', '13IDA:ip1_Volts.VAL', '13IDA:ip2:CUR.VAL',
'13IDA:ip2:PRES.VAL', '13IDA:ip2:VOLT.VAL', '13IDA:ip3_Current.VAL',
'13IDA:ip3_Pressure.VAL', '13IDA:ip3_Volts.VAL',
'13IDA:ip5_Current.VAL', '13IDA:ip5_Pressure.VAL',
'13IDA:ip5_Volts.VAL', '13IDA:ip6:CUR.VAL', '13IDA:ip6:PRES.VAL',
'13IDA:ip6:VOLT.VAL', '13IDA:ip7:CUR.VAL', '13IDA:ip7:PRES.VAL',
'13IDA:ip7:VOLT.VAL', '13IDA:mono_pid1_incalc.E',
'13IDA:mono_pid1_incalc.O', '13IDA:mono_pid1_incalc.P',
'13IDA:mono_pid1Locked.VAL', '13IDA:mono_pid1.VAL', '13IDA:pr1.VAL',
'13IDA:pr2.VAL', '13IDA:pr3.VAL', '13IDA:pr5.VAL', '13IDA:pr6.VAL',
'13IDA:pr7.VAL', '13IDA:V1_status.VAL', '13IDA:V2_status.VAL',
'13IDA:V3_status.VAL', '13IDA:V4_status.VAL', '13IDA:V5_status.VAL',
'13IDA:V6_status.VAL', '13IDC:A1offset_num.VAL',
'13IDC:A1offset_unit.VAL', '13IDC:A1sens_num.VAL',
'13IDC:A1sens_unit.VAL', '13IDC:A2offset_num.VAL',
'13IDC:A2offset_unit.VAL', '13IDC:A2sens_num.VAL',
'13IDC:A2sens_unit.VAL', '13IDC:IP330_10.VAL', '13IDC:IP330_11.VAL',
'13IDC:IP330_12.VAL', '13IDC:IP330_9.VAL', '13IDD:DMM1Ch1_calc.VAL',
'13IDD:DMM1Ch2_calc.VAL', '13IDD:DMM3Ch6_calc.VAL',
'13IDD:DMM3Ch6_raw.VAL', '13IDD:DMM3Dmm_raw.VAL', '13IDD:IP330_1.VAL',
'13IDD:IP330_2.VAL', '13IDD:IP330_3.VAL', '13IDD:IP330_4.VAL',
'13IDD:IP330_5.VAL', '13IDD:IP330_6.VAL', '13IDD:IP330_7.VAL',
'13IDD:IP330_8.VAL', '13IDD:IP330_9.VAL', '13IDD:pico:A1:pM0_dir.VAL',
'13IDD:pico:A1:pM0_pos.VAL', '13IDD:pico:A1:pM1_dir.VAL',
'13IDD:pico:A1:pM1_pos.VAL', '13IDD:pico:A1:pM2_dir.VAL',
'13IDD:pico:A1:pM2_pos.VAL', '13IDD:scaler1.S1', '13IDD:scaler1.S2',
'13IDD:scaler1.S3', '13IDD:scaler1.S4', '13IDD:scaler1.S5',
'13IDD:scaler1.S6', '13IDD:scaler1.S7', '13IDD:scaler1.S8',
'13IDD:us_las_temp.VAL', '13IDD:ds_las_temp.VAL',
'ACIS:ShutterPermit.VAL', 'BL13:ActualMode.VAL',
'BL13:BeamPresent.VAL', 'BL13:GblFeedback.VAL',
'BL13:OrbitCorrection.VAL', 'BL13:SRBM:VAngle.VAL',
'BL13:SRBM:VPosition.VAL', 'BL13:srCurrent.VAL',
'BL13:SRID:HAngle.VAL', 'BL13:SRID:HPosition.VAL',
'BL13:SRID:VAngle.VAL', 'BL13:SRID:VPosition.VAL',
'BL13:srLifetime.VAL', 'BL13:TopUpStatus.VAL', 'FE:13:ID:IP7.CRNT',
'FE:13:ID:IP7.VAL', 'FE:13:ID:IP7.VOLT', 'G:AHU:FP5085Ai.VAL',
'G:AHU:FP5087Ai.VAL', 'G:AHU:FP5088Ai.VAL', 'G:AHU:FP5095Ai.VAL',
'G:AHU:FP5097Ai.VAL', 'G:AHU:FP5098Ai.VAL', 'ID13ds:Energy.VAL',
'ID13ds:Gap.VAL', 'ID13ds:HarmonicValue.VAL', 'ID13ds:TaperGap.VAL',
'ID13ds:TotalPower.VAL', 'PA:13BM:Q01:00.VAL', 'PA:13BM:Q01:01.VAL',
'PA:13BM:Q01:02.VAL', 'PA:13BM:Q01:03.VAL', 'PA:13ID:Q01:00.VAL',
'PA:13ID:Q01:01.VAL', 'PA:13ID:Q01:02.VAL', 'PA:13ID:Q01:03.VAL',
'S:FillNumber.VAL', 'SRFB:GBL:HLoopStatusBI.VAL',
'SRFB:GBL:LoopStatusBI.VAL', 'SRFB:GBL:VLoopStatusBI.VAL',
'S:SRcurrentAI.VAL'   ]

test_connection(pvlist)
disconnect_all()
