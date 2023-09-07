#include <base/types.hh>
#include <unistd.h>

#include <cassert>
#include <sstream>
#include <string>
#include <typeinfo>

#include "mem/ruby/common/BoolVec.hh"

#include "base/compiler.hh"
#include "base/cprintf.hh"

#include "debug/RubyGenerated.hh"
#include "debug/RubySlicc.hh"
#include "mem/ruby/network/Network.hh"
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


int Interface_Controller::m_num_controllers = 0;
std::vector<statistics::Vector *>  Interface_Controller::eventVec;
std::vector<std::vector<statistics::Vector *> >  Interface_Controller::transVec;

// for adding information to the protocol debug trace
std::stringstream Interface_transitionComment;

#ifndef NDEBUG
#define APPEND_TRANSITION_COMMENT(str) (Interface_transitionComment << str)
#else
#define APPEND_TRANSITION_COMMENT(str) do {} while (0)
#endif

/** \brief constructor */
Interface_Controller::Interface_Controller(const Params &p)
    : AbstractController(p)
{
    m_machineID.type = MachineType_Interface;
    m_machineID.num = m_version;
    m_num_controllers++;
    p.ruby_system->registerAbstractController(this);

    m_in_ports = 2;
    m_interface_ptr = p.interface;
    m_toMemLatency = p.toMemLatency;
    m_reqOut_ptr = p.reqOut;
    m_snpOut_ptr = p.snpOut;
    m_rspOut_ptr = p.rspOut;
    m_datOut_ptr = p.datOut;
    m_reqIn_ptr = p.reqIn;
    m_snpIn_ptr = p.snpIn;
    m_rspIn_ptr = p.rspIn;
    m_datIn_ptr = p.datIn;

    for (int state = 0; state < Interface_State_NUM; state++) {
        for (int event = 0; event < Interface_Event_NUM; event++) {
            m_possible[state][event] = false;
            m_counters[state][event] = 0;
        }
    }
    for (int event = 0; event < Interface_Event_NUM; event++) {
        m_event_counters[event] = 0;
    }
}

void
Interface_Controller::initNetQueues()
{
    MachineType machine_type = string_to_MachineType("Interface");
    [[maybe_unused]] int base = MachineType_base_number(machine_type);

    assert(m_reqOut_ptr != NULL);
    m_net_ptr->setToNetQueue(m_version + base, m_reqOut_ptr->getOrdered(), 0,
                                     "request", m_reqOut_ptr);
    assert(m_snpOut_ptr != NULL);
    m_net_ptr->setToNetQueue(m_version + base, m_snpOut_ptr->getOrdered(), 1,
                                     "snoop", m_snpOut_ptr);
    assert(m_rspOut_ptr != NULL);
    m_net_ptr->setToNetQueue(m_version + base, m_rspOut_ptr->getOrdered(), 2,
                                     "response", m_rspOut_ptr);
    assert(m_datOut_ptr != NULL);
    m_net_ptr->setToNetQueue(m_version + base, m_datOut_ptr->getOrdered(), 3,
                                     "data", m_datOut_ptr);

    assert(m_reqIn_ptr != NULL);
    m_net_ptr->setFromNetQueue(m_version + base, m_reqIn_ptr->getOrdered(), 0,
                                     "request", m_reqIn_ptr);
    assert(m_snpIn_ptr != NULL);
    m_net_ptr->setFromNetQueue(m_version + base, m_snpIn_ptr->getOrdered(), 1,
                                     "snoop", m_snpIn_ptr);
    assert(m_rspIn_ptr != NULL);
    m_net_ptr->setFromNetQueue(m_version + base, m_rspIn_ptr->getOrdered(), 2,
                                     "response", m_rspIn_ptr);
    assert(m_datIn_ptr != NULL);
    m_net_ptr->setFromNetQueue(m_version + base, m_datIn_ptr->getOrdered(), 3,
                                     "data", m_datIn_ptr);
}

void
Interface_Controller::init()
{
    // initialize objects

    (*m_reqIn_ptr).setConsumer(this);
    (*m_snpIn_ptr).setConsumer(this);
    (*m_rspIn_ptr).setConsumer(this);
    (*m_datIn_ptr).setConsumer(this);

    possibleTransition(Interface_State_IDLE, Interface_Event_request);
    possibleTransition(Interface_State_IDLE, Interface_Event_snoop);
    possibleTransition(Interface_State_IDLE, Interface_Event_response);
    possibleTransition(Interface_State_IDLE, Interface_Event_data);
    possibleTransition(Interface_State_FWD, Interface_Event_fwd);
    AbstractController::init();
    resetStats();
}

Sequencer*
Interface_Controller::getCPUSequencer() const
{
    return NULL;
}

DMASequencer*
Interface_Controller::getDMASequencer() const
{
    return NULL;
}

GPUCoalescer*
Interface_Controller::getGPUCoalescer() const
{
    return NULL;
}

void
Interface_Controller::regStats()
{
    AbstractController::regStats();

    // For each type of controllers, one controller of that type is picked
    // to aggregate stats of all controllers of that type.
    if (m_version == 0) {

        Profiler *profiler = params().ruby_system->getProfiler();
        statistics::Group *profilerStatsPtr = &profiler->rubyProfilerStats;

        for (Interface_Event event = Interface_Event_FIRST;
             event < Interface_Event_NUM; ++event) {
            std::string stat_name =
                "Interface_Controller." + Interface_Event_to_string(event);
            statistics::Vector *t =
                new statistics::Vector(profilerStatsPtr, stat_name.c_str());
            t->init(m_num_controllers);
            t->flags(statistics::pdf | statistics::total |
                statistics::oneline | statistics::nozero);

            eventVec.push_back(t);
        }

        for (Interface_State state = Interface_State_FIRST;
             state < Interface_State_NUM; ++state) {

            transVec.push_back(std::vector<statistics::Vector *>());

            for (Interface_Event event = Interface_Event_FIRST;
                 event < Interface_Event_NUM; ++event) {
                std::string stat_name = "Interface_Controller." +
                    Interface_State_to_string(state) +
                    "." + Interface_Event_to_string(event);
                statistics::Vector *t = new statistics::Vector(
                    profilerStatsPtr, stat_name.c_str());
                t->init(m_num_controllers);
                t->flags(statistics::pdf | statistics::total |
                    statistics::oneline | statistics::nozero);
                transVec[state].push_back(t);
            }
        }
    }

    for (Interface_Event event = Interface_Event_FIRST;
                 event < Interface_Event_NUM; ++event) {
        std::string stat_name =
            "outTransLatHist." + Interface_Event_to_string(event);
        statistics::Histogram* t =
            new statistics::Histogram(&stats, stat_name.c_str());
        stats.outTransLatHist.push_back(t);
        t->init(5);
        t->flags(statistics::pdf | statistics::total |
                 statistics::oneline | statistics::nozero);

        statistics::Scalar* r = new statistics::Scalar(&stats,
                                             (stat_name + ".retries").c_str());
        stats.outTransLatHistRetries.push_back(r);
        r->flags(statistics::nozero);
    }

    for (Interface_Event event = Interface_Event_FIRST;
                 event < Interface_Event_NUM; ++event) {
        std::string stat_name = "inTransLatHist." +
                                Interface_Event_to_string(event);
        statistics::Scalar* r = new statistics::Scalar(&stats,
                                             (stat_name + ".total").c_str());
        stats.inTransLatTotal.push_back(r);
        r->flags(statistics::nozero);

        r = new statistics::Scalar(&stats,
                              (stat_name + ".retries").c_str());
        stats.inTransLatRetries.push_back(r);
        r->flags(statistics::nozero);

        stats.inTransLatHist.emplace_back();
        for (Interface_State initial_state = Interface_State_FIRST;
             initial_state < Interface_State_NUM; ++initial_state) {
            stats.inTransLatHist.back().emplace_back();
            for (Interface_State final_state = Interface_State_FIRST;
                 final_state < Interface_State_NUM; ++final_state) {
                std::string stat_name = "inTransLatHist." +
                    Interface_Event_to_string(event) + "." +
                    Interface_State_to_string(initial_state) + "." +
                    Interface_State_to_string(final_state);
                statistics::Histogram* t =
                    new statistics::Histogram(&stats, stat_name.c_str());
                stats.inTransLatHist.back().back().push_back(t);
                t->init(5);
                t->flags(statistics::pdf | statistics::total |
                         statistics::oneline | statistics::nozero);
            }
        }
    }
}

void
Interface_Controller::collateStats()
{
    for (Interface_Event event = Interface_Event_FIRST;
         event < Interface_Event_NUM; ++event) {
        for (unsigned int i = 0; i < m_num_controllers; ++i) {
            RubySystem *rs = params().ruby_system;
            std::map<uint32_t, AbstractController *>::iterator it =
                     rs->m_abstract_controls[MachineType_Interface].find(i);
            assert(it != rs->m_abstract_controls[MachineType_Interface].end());
            (*eventVec[event])[i] =
                ((Interface_Controller *)(*it).second)->getEventCount(event);
        }
    }

    for (Interface_State state = Interface_State_FIRST;
         state < Interface_State_NUM; ++state) {

        for (Interface_Event event = Interface_Event_FIRST;
             event < Interface_Event_NUM; ++event) {

            for (unsigned int i = 0; i < m_num_controllers; ++i) {
                RubySystem *rs = params().ruby_system;
                std::map<uint32_t, AbstractController *>::iterator it =
                         rs->m_abstract_controls[MachineType_Interface].find(i);
                assert(it != rs->m_abstract_controls[MachineType_Interface].end());
                (*transVec[state][event])[i] =
                    ((Interface_Controller *)(*it).second)->getTransitionCount(state, event);
            }
        }
    }
}

void
Interface_Controller::countTransition(Interface_State state, Interface_Event event)
{
    assert(m_possible[state][event]);
    m_counters[state][event]++;
    m_event_counters[event]++;
}
void
Interface_Controller::possibleTransition(Interface_State state,
                             Interface_Event event)
{
    m_possible[state][event] = true;
}

uint64_t
Interface_Controller::getEventCount(Interface_Event event)
{
    return m_event_counters[event];
}

bool
Interface_Controller::isPossible(Interface_State state, Interface_Event event)
{
    return m_possible[state][event];
}

uint64_t
Interface_Controller::getTransitionCount(Interface_State state,
                             Interface_Event event)
{
    return m_counters[state][event];
}

int
Interface_Controller::getNumControllers()
{
    return m_num_controllers;
}

MessageBuffer*
Interface_Controller::getMandatoryQueue() const
{
    return NULL;
}

MessageBuffer*
Interface_Controller::getMemReqQueue() const
{
    return NULL;
}

MessageBuffer*
Interface_Controller::getMemRespQueue() const
{
    return NULL;
}

void
Interface_Controller::print(std::ostream& out) const
{
    out << "[Interface_Controller " << m_version << "]";
}

void Interface_Controller::resetStats()
{
    for (int state = 0; state < Interface_State_NUM; state++) {
        for (int event = 0; event < Interface_Event_NUM; event++) {
            m_counters[state][event] = 0;
        }
    }

    for (int event = 0; event < Interface_Event_NUM; event++) {
        m_event_counters[event] = 0;
    }

    AbstractController::resetStats();
}

void
Interface_Controller::recordCacheTrace(int cntrl, CacheRecorder* tr)
{
}

// Actions
/** \brief Forwards the request message */
void
Interface_Controller::fwdRequest(Addr addr)
{
    DPRINTF(RubyGenerated, "executing fwdRequest\n");
    {
    // Declare message
    [[maybe_unused]] const CHIRequestMsg* in_msg_ptr;
    in_msg_ptr = dynamic_cast<const CHIRequestMsg *>(((*m_reqIn_ptr)).peek());
    if (in_msg_ptr == NULL) {
        // If the cast fails, this is the wrong inport (wrong message type).
        // Throw an exception, and the caller will decide to either try a
        // different inport or punt.
        throw RejectException();
    }
{
    std::shared_ptr<CHIRequestMsg> out_msg = std::make_shared<CHIRequestMsg>(clockEdge());
    (*out_msg).m_addr = addr;
    //(*out_msg).m_Sender = m_machineID;
    (*out_msg).m_requestor = ((*in_msg_ptr)).m_requestor;
    //(*out_msg).m_DataBlk = ((*in_msg_ptr)).m_DataBlk;
    ((*m_reqOut_ptr)).enqueue(out_msg, clockEdge(), cyclesToTicks(Cycles((1))));
}
}
}

/** \brief Forwards the snoop message */
void
Interface_Controller::fwdSnoop(Addr addr)
{
    DPRINTF(RubyGenerated, "executing fwdRequest\n");
    {
    // Declare message
    [[maybe_unused]] const CHIRequestMsg* in_msg_ptr;
    in_msg_ptr = dynamic_cast<const CHIRequestMsg *>(((*m_snpIn_ptr)).peek());
    if (in_msg_ptr == NULL) {
        // If the cast fails, this is the wrong inport (wrong message type).
        // Throw an exception, and the caller will decide to either try a
        // different inport or punt.
        throw RejectException();
    }
{
    std::shared_ptr<CHIRequestMsg> out_msg = std::make_shared<CHIRequestMsg>(clockEdge());
    (*out_msg).m_addr = addr;
    //(*out_msg).m_Sender = m_machineID;
    (*out_msg).m_requestor = ((*in_msg_ptr)).m_requestor;
    //(*out_msg).m_DataBlk = ((*in_msg_ptr)).m_DataBlk;
    ((*m_snpOut_ptr)).enqueue(out_msg, clockEdge(), cyclesToTicks(Cycles((1))));
}
}
}

/** \brief Forwards the response message */
void
Interface_Controller::fwdResponse(Addr addr)
{
    DPRINTF(RubyGenerated, "executing fwdRequest\n");
    {
    // Declare message
    [[maybe_unused]] const CHIResponseMsg* in_msg_ptr;
    in_msg_ptr = dynamic_cast<const CHIResponseMsg *>(((*m_rspIn_ptr)).peek());
    if (in_msg_ptr == NULL) {
        // If the cast fails, this is the wrong inport (wrong message type).
        // Throw an exception, and the caller will decide to either try a
        // different inport or punt.
        throw RejectException();
    }
{
    std::shared_ptr<CHIResponseMsg> out_msg = std::make_shared<CHIResponseMsg>(clockEdge());
    (*out_msg).m_addr = addr;
    (*out_msg).m_responder = m_machineID;
    (*out_msg).m_Destination = ((*in_msg_ptr)).m_Destination;
    //(*out_msg).m_DataBlk = ((*in_msg_ptr)).m_DataBlk;
    ((*m_rspOut_ptr)).enqueue(out_msg, clockEdge(), cyclesToTicks(Cycles((1))));
}
}
}

/** \brief Forwards the request message */
void
Interface_Controller::fwdData(Addr addr)
{
    DPRINTF(RubyGenerated, "executing fwdRequest\n");
    {
    // Declare message
    [[maybe_unused]] const CHIDataMsg* in_msg_ptr;
    in_msg_ptr = dynamic_cast<const CHIDataMsg *>(((*m_datIn_ptr)).peek());
    if (in_msg_ptr == NULL) {
        // If the cast fails, this is the wrong inport (wrong message type).
        // Throw an exception, and the caller will decide to either try a
        // different inport or punt.
        throw RejectException();
    }
{
    std::shared_ptr<CHIDataMsg> out_msg = std::make_shared<CHIDataMsg>(clockEdge());
    (*out_msg).m_addr = addr;
    (*out_msg).m_responder = ((*in_msg_ptr)).m_responder;
    (*out_msg).m_Destination = (*(getInterfaceEntry(addr))).m_Owner;
    ((*m_datOut_ptr)).enqueue(out_msg, clockEdge(), cyclesToTicks(Cycles((1))));
}
}

}

Interface_Entry*
Interface_Controller::getInterfaceEntry(const Addr& param_addr)
{
Interface_Entry* interface_entry
 = static_cast<Interface_Entry *>((((*m_interface_ptr)).lookup(param_addr)))
;
    if ((interface_entry == NULL)) {
        interface_entry = static_cast<Interface_Entry *>((((*m_interface_ptr)).allocate(param_addr, new Interface_Entry)))
        ;
    }
    return interface_entry;

}
Interface_State
Interface_Controller::getState(const Addr& param_addr)
{
    if ((((*m_interface_ptr)).isPresent(param_addr))) {
        return (*(getInterfaceEntry(param_addr))).m_InterfaceState;
    } else {
        return Interface_State_IDLE;
    }

}
void
Interface_Controller::setState(const Addr& param_addr, const Interface_State& param_state)
{
(*(getInterfaceEntry(param_addr))).m_InterfaceState = param_state;

}
AccessPermission
Interface_Controller::getAccessPermission(const Addr& param_addr)
{
    if ((((*m_interface_ptr)).isPresent(param_addr))) {
        Interface_Entry* e
         = (getInterfaceEntry(param_addr));
        return (Interface_State_to_permission((*e).m_InterfaceState));
    } else {
        return AccessPermission_NotPresent;
    }

}
void
Interface_Controller::setAccessPermission(const Addr& param_addr, const Interface_State& param_state)
{
    if ((((*m_interface_ptr)).isPresent(param_addr))) {
        Interface_Entry* e
         = (getInterfaceEntry(param_addr));
        ((*(e)).changePermission((Interface_State_to_permission(param_state))));
    }

}
void
Interface_Controller::functionalRead(const Addr& param_addr, Packet* param_pkt)
{
(functionalMemoryRead(param_pkt));

}
int
Interface_Controller::functionalWrite(const Addr& param_addr, Packet* param_pkt)
{
    if ((functionalMemoryWrite(param_pkt))) {
        return (1);
    } else {
        return (0);
    }

}
int
Interface_Controller::functionalWriteBuffers(PacketPtr& pkt)
{
    int num_functional_writes = 0;
    num_functional_writes += m_reqIn_ptr->functionalWrite(pkt);
    num_functional_writes += m_snpIn_ptr->functionalWrite(pkt);
    num_functional_writes += m_rspIn_ptr->functionalWrite(pkt);
    num_functional_writes += m_datIn_ptr->functionalWrite(pkt);

    num_functional_writes += m_reqOut_ptr->functionalWrite(pkt);
    num_functional_writes += m_snpOut_ptr->functionalWrite(pkt);
    num_functional_writes += m_rspOut_ptr->functionalWrite(pkt);
    num_functional_writes += m_datOut_ptr->functionalWrite(pkt);
    return num_functional_writes;
}

bool
Interface_Controller::functionalReadBuffers(PacketPtr& pkt)
{
    if (m_reqIn_ptr->functionalRead(pkt)) return true;
    if (m_snpIn_ptr->functionalRead(pkt)) return true;
    if (m_rspIn_ptr->functionalRead(pkt)) return true;
    if (m_datIn_ptr->functionalRead(pkt)) return true;

    if (m_reqOut_ptr->functionalRead(pkt)) return true;
    if (m_snpOut_ptr->functionalRead(pkt)) return true;
    if (m_rspOut_ptr->functionalRead(pkt)) return true;
    if (m_datOut_ptr->functionalRead(pkt)) return true;
    return false;
}

bool
Interface_Controller::functionalReadBuffers(PacketPtr& pkt, WriteMask &mask)
{
    bool read = false;
    if (m_reqIn_ptr->functionalRead(pkt, mask)) read = true;
    if (m_snpIn_ptr->functionalRead(pkt, mask)) read = true;
    if (m_rspIn_ptr->functionalRead(pkt, mask)) read = true;
    if (m_datIn_ptr->functionalRead(pkt, mask)) read = true;

    if (m_reqOut_ptr->functionalRead(pkt, mask)) read = true;
    if (m_snpOut_ptr->functionalRead(pkt, mask)) read = true;
    if (m_rspOut_ptr->functionalRead(pkt, mask)) read = true;
    if (m_datOut_ptr->functionalRead(pkt, mask)) read = true;
    return read;
}

} // namespace ruby
} // namespace gem5
