
#include <cassert>

#include "base/logging.hh"
#include "base/trace.hh"
#include "debug/ProtocolTrace.hh"
#include "debug/RubyGenerated.hh"
#include "mem/ruby/protocol/Interface_Controller.hh"
#include "mem/ruby/protocol/Interface_Event.hh"
#include "mem/ruby/protocol/Interface_State.hh"
#include "mem/ruby/protocol/Types.hh"
#include "mem/ruby/system/RubySystem.hh"

#define HASH_FUN(state, event)  ((int(state)*Interface_Event_NUM)+int(event))

#define GET_TRANSITION_COMMENT() (Interface_transitionComment.str())
#define CLEAR_TRANSITION_COMMENT() (Interface_transitionComment.str(""))

namespace gem5
{

namespace ruby
{

TransitionResult
Interface_Controller::doTransition(Interface_Event event,
                                  Addr addr)
{
    Interface_State state = getState(addr);
    Interface_State next_state = state;

    DPRINTF(RubyGenerated, "%s, Time: %lld, state: %s, event: %s, addr: %#x\n",
            *this, curCycle(), Interface_State_to_string(state),
            Interface_Event_to_string(event), addr);

    TransitionResult result =
    doTransitionWorker(event, state, next_state, addr);

    if (result == TransitionResult_Valid) {
        DPRINTF(RubyGenerated, "next_state: %s\n",
                Interface_State_to_string(next_state));
        countTransition(state, event);

        DPRINTFR(ProtocolTrace, "%15d %3s %10s%20s %6s>%-6s %#x %s\n",
                 curTick(), m_version, "Interface",
                 Interface_Event_to_string(event),
                 Interface_State_to_string(state),
                 Interface_State_to_string(next_state),
                 printAddress(addr), GET_TRANSITION_COMMENT());

        CLEAR_TRANSITION_COMMENT();
    setState(addr, next_state);
    setAccessPermission(addr, next_state);
    } else if (result == TransitionResult_ResourceStall) {
        DPRINTFR(ProtocolTrace, "%15s %3s %10s%20s %6s>%-6s %#x %s\n",
                 curTick(), m_version, "Interface",
                 Interface_Event_to_string(event),
                 Interface_State_to_string(state),
                 Interface_State_to_string(next_state),
                 printAddress(addr), "Resource Stall");
    } else if (result == TransitionResult_ProtocolStall) {
        DPRINTF(RubyGenerated, "stalling\n");
        DPRINTFR(ProtocolTrace, "%15s %3s %10s%20s %6s>%-6s %#x %s\n",
                 curTick(), m_version, "Interface",
                 Interface_Event_to_string(event),
                 Interface_State_to_string(state),
                 Interface_State_to_string(next_state),
                 printAddress(addr), "Protocol Stall");
    }

    return result;
}

TransitionResult
Interface_Controller::doTransitionWorker(Interface_Event event,
                                        Interface_State state,
                                        Interface_State& next_state,
                                        Addr addr)
{
    m_curTransitionEvent = event;
    m_curTransitionNextState = next_state;
    switch(HASH_FUN(state, event)) {
  case HASH_FUN(Interface_State_IDLE, Interface_Event_request):
    if (!(*m_reqOutPort_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
    fwdRequest(addr);
    return TransitionResult_Valid;

  case HASH_FUN(Interface_State_IDLE, Interface_Event_snoop):
    if (!(*m_snpOutPort_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
    fwdSnoop(addr);
    return TransitionResult_Valid;
  
  case HASH_FUN(Interface_State_IDLE, Interface_Event_response):
    if (!(*m_rspOutPort_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
    fwdResponse(addr);
    return TransitionResult_Valid;
  
  case HASH_FUN(Interface_State_IDLE, Interface_Event_data):
    if (!(*m_datOutPort_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
    fwdData(addr);
    return TransitionResult_Valid;
  
  case HASH_FUN(Interface_State_FWD, Interface_Event_fwd):
    fwdDone(addr);
    return TransitionResult_Valid;

      default:
        panic("Invalid transition\n"
              "%s time: %d addr: %#x event: %s state: %s\n",
              name(), curCycle(), addr, event, state);
    }

    return TransitionResult_Valid;
}

} // namespace ruby
} // namespace gem5
