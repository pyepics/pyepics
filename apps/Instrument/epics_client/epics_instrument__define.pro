;
; Epics Instrument

function epics_instrument::move_to_position, position, instrument=instrument, wait=wait

;+
; NAME:               instrument::move_to_position
;
; PURPOSE:            move Instrument to named Position 
;
; CALLING SEQUENCE:   inst->move_to_position(position, /wait)

; INPUTS:             position - position name
;
; KEYWORD PARAMETERS: instrument  - name of instrument
;                     wait        - flag to wait for completion of move
;
; OUTPUTS:            returns -1 on error (position invalid, no instrument)
;                     returns 0 on success
;
; EXAMPLE:            inst = obj_new('epics_instrument', prefix='13XRM:Inst')
;                     print, inst->move_to_position, 'Spot1', 'Sample Stage', /wait
;
; MODIFICATION HISTORY:  2011-Apr-29  M Newville
;
;-
if (keyword_set(instrument) ne 0) then begin
    ret = self->set_instrument(instrument)
    if (ret ne 1) then return, -1
endif

ret = self->set_position(position)
if (ret ne 1) then return, -1

x = caput(self.prefix + 'Move', 1)
if (keyword_set(wait) ne 0) then begin
    moving = 1
    while (moving eq 1) do begin
        wait, 0.1
        x = caget(self.prefix + 'Move', moving)
    endwhile
endif
return, 0
end


function epics_instrument::set_position, position

self.position = position
x = caput(self.prefix + 'PosName', position)
wait, 0.5
x = caget(self.prefix + 'PosOK', pos_ok)
return, pos_ok
end


function epics_instrument::set_instrument, inst_name

self.instrument = inst_name
x = caput(self.prefix + 'InstName', inst_name)
wait, 0.5
x = caget(self.prefix + 'InstOK', inst_ok)
return, inst_ok
end

function epics_instrument::init, prefix=prefix
self.prefix = prefix
return, 1
end

pro epics_instrument__define
;+
; NAME:
;       EPICS_INSTRUMENT__DEFINE
;
; PURPOSE:
;       Defines an Epics Instrument object that interacts with Epics Record of PyInstrumet
;
;
; CALLING SEQUENCE:
;       einst = obj_new('epics_instrument', '13XRM:Inst:')
;
;
; INPUTS:
;       None.
;
; OPTIONAL INPUTS:
;       None.
;
; KEYWORD PARAMETERS:
;       None.
;
;
; OUTPUTS:
;       Return value will contain the object reference.
;
;
; OPTIONAL OUTPUTS:
;       None.
;
;
; COMMON BLOCKS:
;       None.
;
;
; SIDE EFFECTS:
;       EPICS_Instrument object is created.
;
;
; EXAMPLE:
;       einst = obj_new('epics_instrument', '13XRM:Inst')
;       einst->move_to_position, 'Spot1', 'Sample Stage', /wait
;
; MODIFICATION HISTORY:  2011-Apr-29  M Newville
;-

epics_instrument = {epics_instrument, prefix: '', instrument: '', position: ''}
end
