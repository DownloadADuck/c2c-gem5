
#include <sys/types.h>
#include <unistd.h>

#include <cassert>
#include <typeinfo>

#include "base/logging.hh"

#include "debug/RubyGenerated.hh"
#include "debug/RubySlicc.hh"
#include "mem/ruby/fwd_interface/Interface_Controller.hh"
#include "mem/ruby/fwd_interface/Interface_Event.hh"
#include "mem/ruby/fwd_interface/Interface_State.hh"

#include "mem/ruby/protocol/Types.hh"
#include "mem/ruby/system/RubySystem.hh"

#include "mem/ruby/slicc_interface/RubySlicc_includes.hh"

namespace gem5
{
namespace ruby
{

void
Interface_Controller::wakeup()
{
    if (getMemReqQueue() && getMemReqQueue()->isReady(clockEdge()))
    {
        serviceMemoryQueue();
    }

    int counter = 0;
    while (true)
    {
        unsigned char rejected[2];
        memset(rejected, 0, sizeof(unsigned char) * 2);
        // Some cases will put us into an infinite loop without this limit
        assert(counter <= m_transitions_per_cycle);
        if (counter == m_transitions_per_cycle)
        {
            // Count how often we are fully utilized
            stats.fullyBusyCycles++;

            // Wakeup in another cycle and try again
            scheduleEvent(Cycles(1));
            break;
        }
        // Interface reqIn port
        m_cur_in_port = 4;
        try
        {
            if ((((*m_reqIn_ptr)).isReady((clockEdge()))))
            {
                {
                    // Declare message
                    [[maybe_unused]] const CHIRequestMsg *in_msg_ptr;
                    in_msg_ptr = dynamic_cast<const CHIRequestMsg *>(((*m_reqIn_ptr)).peek());
                    if (in_msg_ptr == NULL)
                    {
                        // If the cast fails, this is the wrong inport (wrong message type).
                        // Throw an exception, and the caller will decide to either try a
                        // different inport or punt.
                        throw RejectException();
                    }
                    {

                        TransitionResult result = doTransition(Interface_Event_requestToBridge, ((*in_msg_ptr)).m_addr);

                        if (result == TransitionResult_Valid)
                        {
                            counter++;
                            continue; // Check the first port again
                        }
                        else if (result == TransitionResult_ResourceStall)
                        {

                            scheduleEvent(Cycles(1));
                        }
                        else if (result == TransitionResult_ProtocolStall)
                        {

                            scheduleEvent(Cycles(1));
                        }
                    };
                }
            }
        }
        catch (const RejectException &e)
        {
            rejected[0]++;
        }

        // Interface snpIn port 
        m_cur_in_port = 3;
        try
        {
            if ((((*m_snpIn_ptr)).isReady((clockEdge()))))
            {
                {
                    // Declare message
                    [[maybe_unused]] const CHIRequestMsg *in_msg_ptr;
                    in_msg_ptr = dynamic_cast<const CHIRequestMsg *>(((*m_snpIn_ptr)).peek());
                    if (in_msg_ptr == NULL)
                    {
                        // If the cast fails, this is the wrong inport (wrong message type).
                        // Throw an exception, and the caller will decide to either try a
                        // different inport or punt.
                        throw RejectException();
                    }
                    {

                        TransitionResult result = doTransition(Interface_Event_snoopToBridge, ((*in_msg_ptr)).m_addr);

                        if (result == TransitionResult_Valid)
                        {
                            counter++;
                            continue; // Check the first port again
                        }
                        else if (result == TransitionResult_ResourceStall)
                        {

                            scheduleEvent(Cycles(1));
                        }
                        else if (result == TransitionResult_ProtocolStall)
                        {

                            scheduleEvent(Cycles(1));
                        }
                    };
                }
            }
        }
        catch (const RejectException &e)
        {
            rejected[0]++;
        }

        // Interface rspIn port 
        m_cur_in_port = 2;
        try
        {
            if ((((*m_rspIn_ptr)).isReady((clockEdge()))))
            {
                {
                    // Declare message
                    [[maybe_unused]] const CHIResponseMsg *in_msg_ptr;
                    in_msg_ptr = dynamic_cast<const CHIResponseMsg *>(((*m_rspIn_ptr)).peek());
                    if (in_msg_ptr == NULL)
                    {
                        // If the cast fails, this is the wrong inport (wrong message type).
                        // Throw an exception, and the caller will decide to either try a
                        // different inport or punt.
                        throw RejectException();
                    }
                    {

                        TransitionResult result = doTransition(Interface_Event_responseToBridge, ((*in_msg_ptr)).m_addr);

                        if (result == TransitionResult_Valid)
                        {
                            counter++;
                            continue; // Check the first port again
                        }
                        else if (result == TransitionResult_ResourceStall)
                        {

                            scheduleEvent(Cycles(1));
                        }
                        else if (result == TransitionResult_ProtocolStall)
                        {

                            scheduleEvent(Cycles(1));
                        }
                    };
                }
            }
        }
        catch (const RejectException &e)
        {
            rejected[0]++;
        }

        // Interface datIn port 
        m_cur_in_port = 1;
        try
        {
            if ((((*m_datIn_ptr)).isReady((clockEdge()))))
            {
                {
                    // Declare message
                    [[maybe_unused]] const CHIDataMsg *in_msg_ptr;
                    in_msg_ptr = dynamic_cast<const CHIDataMsg *>(((*m_datIn_ptr)).peek());
                    if (in_msg_ptr == NULL)
                    {
                        // If the cast fails, this is the wrong inport (wrong message type).
                        // Throw an exception, and the caller will decide to either try a
                        // different inport or punt.
                        throw RejectException();
                    }
                    {

                        TransitionResult result = doTransition(Interface_Event_dataToBridge, ((*in_msg_ptr)).m_addr);

                        if (result == TransitionResult_Valid)
                        {
                            counter++;
                            continue; // Check the first port again
                        }
                        else if (result == TransitionResult_ResourceStall)
                        {

                            scheduleEvent(Cycles(1));
                        }
                        else if (result == TransitionResult_ProtocolStall)
                        {

                            scheduleEvent(Cycles(1));
                        }
                    };
                }
            }
        }
        catch (const RejectException &e)
        {
            rejected[0]++;
        }

        // BRIDGE side port wakeups
        // Interface fromBridge
        m_cur_in_port = 0;
        try
        {
            if ((((*m_datIn_ptr)).isReady((clockEdge()))))
            {
                {
                    // Declare message
                    [[maybe_unused]] const MemoryMsg *in_msg_ptr;
                    in_msg_ptr = dynamic_cast<const MemoryMsg *>(((*m_fromBridge_ptr)).peek());
                    if (in_msg_ptr == NULL)
                    {
                        // If the cast fails, this is the wrong inport (wrong message type).
                        // Throw an exception, and the caller will decide to either try a
                        // different inport or punt.
                        throw RejectException();
                    }
                    {
                        if((*in_msg_ptr).m_Type == MemoryRequestType_MEMORY_READ) {
                            // MemoryRequestType_MEMORY_READ -> Request
                            {
                                TransitionResult result = doTransition(Interface_Event_requestToNetwork, ((*in_msg_ptr)).m_addr);

                                if (result == TransitionResult_Valid)
                                {
                                    counter++;
                                    continue; // Check the first port again
                                }
                                else if (result == TransitionResult_ResourceStall)
                                {

                                    scheduleEvent(Cycles(1));
                                }
                                else if (result == TransitionResult_ProtocolStall)
                                {

                                    scheduleEvent(Cycles(1));
                                }
                            };
                        } else if ((*in_msg_ptr).m_Type == MemoryRequestType_MEMORY_WB) {
                            // MemoryRequestType_MEMORY_WB -> Response
                            {
                                TransitionResult result = doTransition(Interface_Event_responseToNetwork, ((*in_msg_ptr)).m_addr);

                                if (result == TransitionResult_Valid)
                                {
                                    counter++;
                                    continue; // Check the first port again
                                }
                                else if (result == TransitionResult_ResourceStall)
                                {

                                    scheduleEvent(Cycles(1));
                                }
                                else if (result == TransitionResult_ProtocolStall)
                                {

                                    scheduleEvent(Cycles(1));
                                }
                            };
                        } else if ((*in_msg_ptr).m_Type == MemoryRequestType_MEMORY_DATA) {
                            // MemoryRequestType_MEMORY_DATA -> Data
                            {
                                TransitionResult result = doTransition(Interface_Event_dataToNetwork, ((*in_msg_ptr)).m_addr);

                                if (result == TransitionResult_Valid)
                                {
                                    counter++;
                                    continue; // Check the first port again
                                }
                                else if (result == TransitionResult_ResourceStall)
                                {

                                    scheduleEvent(Cycles(1));
                                }
                                else if (result == TransitionResult_ProtocolStall)
                                {

                                    scheduleEvent(Cycles(1));
                                }
                            };
                        } else {
                            // MemoryRequestType_MEMORY_ACK -> Snoop
                            {
                                TransitionResult result = doTransition(Interface_Event_snoopToNetwork, ((*in_msg_ptr)).m_addr);

                                if (result == TransitionResult_Valid)
                                {
                                    counter++;
                                    continue; // Check the first port again
                                }
                                else if (result == TransitionResult_ResourceStall)
                                {

                                    scheduleEvent(Cycles(1));
                                }
                                else if (result == TransitionResult_ProtocolStall)
                                {

                                    scheduleEvent(Cycles(1));
                                }
                            };
                        }
                    };
                }
            }
        }
        catch (const RejectException &e)
        {
            rejected[0]++;
        }


        // If we got this far, we have nothing left todo or something went
        // wrong
        break;
    }
}

} // namespace ruby
} // namespace gem5