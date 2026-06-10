set pagination off
set confirm off
set print pretty on
set print object on
set print elements 0
set breakpoint pending on

set logging file gdb_outtrans_callstack.txt
set logging overwrite on
set logging enabled on

handle SIGABRT stop print nopass
handle SIGSEGV stop print nopass

break gem5::ruby::AbstractController::outgoingTransactionEnd

commands
  silent
  printf "\n\n========== BREAK outgoingTransactionEnd ==========\n"
  printf "addr = 0x%lx\n", addr
  printf "retried = %d\n", retried
  printf "isAddressed = %d\n", isAddressed
  printf "curTick = %lu\n", gem5::curTick()
  printf "controller this = %p\n", this
  printf "controller name = %s\n", this->name().c_str()
  printf "m_outTransAddressed.size = %lu\n", this->m_outTransAddressed.size()
  printf "m_outTransUnaddressed.size = %lu\n", this->m_outTransUnaddressed.size()
  bt 20
  continue
end

run configs/example/gem5_library/multichip_c2c/C2C/noncaching-c2c.py --benchmark blackscholes --size test

printf "\n\n========== PROGRAM STOPPED ==========\n"
bt full
info locals
info args

set logging enabled off
quit
