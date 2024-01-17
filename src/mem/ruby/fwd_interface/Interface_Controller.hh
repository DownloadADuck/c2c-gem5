#ifndef __Interface_Controller_HH__
#define __Interface_Controller_HH__

#include <iostream>
#include <sstream>
#include <string>

#include "mem/ruby/common/Consumer.hh"
#include "mem/ruby/protocol/TransitionResult.hh"
#include "mem/ruby/protocol/Types.hh"
#include "mem/ruby/slicc_interface/AbstractController.hh"
#include "params/Interface_Controller.hh"
#include "mem/ruby/fwd_interface/Interface_State.hh"
#include "mem/ruby/fwd_interface/Interface_Event.hh"
#include "mem/ruby/fwd_interface/Interface_Entry.hh"

namespace gem5
{

namespace ruby
{

extern std::stringstream Interface_transitionComment;

class Interface_Controller : public AbstractController
{
  public:
    typedef Interface_ControllerParams Params;
    Interface_Controller(const Params &p);
    static int getNumControllers();
    void init();

    MessageBuffer *getMandatoryQueue() const;
    MessageBuffer *getMemReqQueue() const;
    MessageBuffer *getMemRespQueue() const;
    void initNetQueues();

    void print(std::ostream& out) const;
    void wakeup();
    void resetStats();
    void regStats();
    void collateStats();

    void recordCacheTrace(int cntrl, CacheRecorder* tr);
    Sequencer* getCPUSequencer() const;
    DMASequencer* getDMASequencer() const;
    GPUCoalescer* getGPUCoalescer() const;

    bool functionalReadBuffers(PacketPtr&);
    bool functionalReadBuffers(PacketPtr&, WriteMask&);
    int functionalWriteBuffers(PacketPtr&);

    void countTransition(Interface_State state, Interface_Event event);
    void possibleTransition(Interface_State state, Interface_Event event);
    uint64_t getEventCount(Interface_Event event);
    bool isPossible(Interface_State state, Interface_Event event);
    uint64_t getTransitionCount(Interface_State state, Interface_Event event);

private:
    DirectoryMemory* m_interface_ptr;
    Cycles m_toMemLatency;
    Cycles m_to_bridge_latency;
    MessageBuffer* m_reqOut_ptr;
    MessageBuffer* m_snpOut_ptr;
    MessageBuffer* m_rspOut_ptr;
    MessageBuffer* m_datOut_ptr;
    MessageBuffer* m_reqIn_ptr;
    MessageBuffer* m_snpIn_ptr;
    MessageBuffer* m_rspIn_ptr;
    MessageBuffer* m_datIn_ptr;

    MessageBuffer* m_toBridge_ptr;
    MessageBuffer* m_fromBridge_ptr;

    int m_data_channel_size;

    TransitionResult doTransition(Interface_Event event,
                                  Addr addr);

    TransitionResult doTransitionWorker(Interface_Event event,
                                        Interface_State state,
                                        Interface_State& next_state,
                                        Addr addr);

    Interface_Event m_curTransitionEvent;
    Interface_State m_curTransitionNextState;

    Interface_Event curTransitionEvent() { return m_curTransitionEvent; }
    Interface_State curTransitionNextState() { return m_curTransitionNextState; }

    int m_counters[Interface_State_NUM][Interface_Event_NUM];
    int m_event_counters[Interface_Event_NUM];
    bool m_possible[Interface_State_NUM][Interface_Event_NUM];

    static std::vector<statistics::Vector *> eventVec;
    static std::vector<std::vector<statistics::Vector *> > transVec;
    static int m_num_controllers;

    // Internal functions
    Interface_Entry* getInterfaceEntry(const Addr& param_addr);
    Interface_State getState(const Addr& param_addr);
    void setState(const Addr& param_addr, const Interface_State& param_state);
    AccessPermission getAccessPermission(const Addr& param_addr);
    void setAccessPermission(const Addr& param_addr, const Interface_State& param_state);
    void functionalRead(const Addr& param_addr, Packet* param_pkt);
    int functionalWrite(const Addr& param_addr, Packet* param_pkt);

    // Actions
    // Sending to the Bridge
    /** \brief Send request to Bridge */
    void sendReqToBridge(Addr addr);
    /** \brief Send snoop to Bridge */
    void sendSnpToBridge(Addr addr);
    /** \brief Send response to Bridge */
    void sendRspToBridge(Addr addr);
    /** \brief Send data to Bridge */
    void sendDatToBridge(Addr addr);

    // Sending to the Network
    /** \brief Send request to Network */
    void sendReqToNetwork(Addr addr);
    /** \brief Send snoop to Network */
    void sendSnpToNetwork(Addr addr);
    /** \brief Send response to Network */
    void sendRspToNetwork(Addr addr);
    /** \brief Send data to Network */
    void sendDatToNetwork(Addr addr);

    // Objects
};

} // namespace ruby
} // namespace gem5

#endif // __Interface_Controller_HH__