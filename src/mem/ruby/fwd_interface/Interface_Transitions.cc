
#include <cassert>

#include "base/logging.hh"
#include "base/trace.hh"
#include "debug/ProtocolTrace.hh"
#include "debug/RubyGenerated.hh"
#include "mem/ruby/fwd_interface/Interface_Controller.hh"
#include "mem/ruby/fwd_interface/Interface_Event.hh"
#include "mem/ruby/fwd_interface/Interface_State.hh"
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

    // To the BRIDGE
    case HASH_FUN(Interface_State_IDLE, Interface_Event_requestToBridge):
      if (!(*m_toBridge_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
      sendReqToBridge(addr);
      return TransitionResult_Valid;

    case HASH_FUN(Interface_State_IDLE, Interface_Event_snoopToBridge):
      if (!(*m_toBridge_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
      sendSnpToBridge(addr);
      return TransitionResult_Valid;

    case HASH_FUN(Interface_State_IDLE, Interface_Event_responseToBridge):
      if (!(*m_toBridge_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
      sendRspToBridge(addr);
      return TransitionResult_Valid;

    case HASH_FUN(Interface_State_IDLE, Interface_Event_dataToBridge):
      if (!(*m_toBridge_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
      sendDatToBridge(addr);
      return TransitionResult_Valid;

    // To the NETWORK
    case HASH_FUN(Interface_State_IDLE, Interface_Event_requestToNetwork):
      if (!(*m_reqOut_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
      sendReqToNetwork(addr);
      return TransitionResult_Valid;

    case HASH_FUN(Interface_State_IDLE, Interface_Event_snoopToNetwork):
      if (!(*m_snpOut_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
      sendSnpToNetwork(addr);
      return TransitionResult_Valid;

    case HASH_FUN(Interface_State_IDLE, Interface_Event_responseToNetwork):
      if (!(*m_rspOut_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
      sendRspToNetwork(addr);
      return TransitionResult_Valid;

    case HASH_FUN(Interface_State_IDLE, Interface_Event_dataToNetwork):
      if (!(*m_datOut_ptr).areNSlotsAvailable(1, clockEdge()))
        return TransitionResult_ResourceStall;
      sendDatToNetwork(addr);
      return TransitionResult_Valid;

    case HASH_FUN(Interface_State_FWD, Interface_Event_fwd):
    //fwd(addr);
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
