############################################################
#                                                          #
# TCL program for testing tcl script                       #
#                                                          #
############################################################

# Display error and close procedure
proc DisplayErrorAndClose {socketID code APIName} {
    global tcl_argv
    if {$code != -2} {
        set code2 [catch "ErrorStringGet $socketID $code strError"]
        if {$code2 != 0} {
            puts "$APIName ERROR => $code - ErrorStringGet ERROR => $code2"
            set tcl_argv(0) "$APIName ERROR => $code - ErrorStringGet ERROR => $code2"
        } else {
            puts stdout "$APIName ERROR => $code : $strError"
            set tcl_argv(0) "$APIName ERROR => $code : $strError"
        }
    } else {
        puts stdout "$APIName ERROR => $code : TCP timeout"
        set tcl_argv(0) "$APIName ERROR => $code : TCP timeout"
    }
    set code2 [catch "TCP_CloseSocket $socketID"] 
    return
}

# Main process
# Get library version
set code [catch "GetLibraryVersion strVersion"]
if {$code != 0} {
    DisplayErrorAndClose $socketID $code "GetLibraryVersion"
    return
}
puts stdout "Library Version = $strVersion"

# Open socket
set TimeOut 60
set code [catch "OpenConnection $TimeOut socketID"]
if {$code == 0} {

      # Get firmware version
      set code [catch "FirmwareVersionGet $socketID strVersion"]
      if {$code != 0} {
          DisplayErrorAndClose $socketID $code "FirmwareVersionGet"
          return
      }
      puts stdout "Firmware Version = $strVersion"
      
      #### Close TCP socket
      set code [catch "TCP_CloseSocket $socketID"]

} else {

     puts stdout "OpenConnection Error => $code"
     
}

