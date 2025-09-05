/*
 * Copyright (c) 2017,2019-2022 ARM Limited
 * All rights reserved.
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2011-2014 Mark D. Hill and David A. Wood
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "mem/ruby/slicc_interface/AbstractController.hh"

#include "debug/RubyQueue.hh"
#include "mem/ruby/network/Network.hh"
#include "mem/ruby/protocol/MemoryMsg.hh"
#include "mem/ruby/protocol/C2cMsg.hh"
#include "mem/ruby/system/RubySystem.hh"
#include "mem/ruby/system/Sequencer.hh"
#include "sim/system.hh"

namespace gem5
{

namespace ruby
{

AbstractController::AbstractController(const Params &p)
    : ClockedObject(p), Consumer(this), m_version(p.version),
      m_clusterID(p.cluster_id),
      m_id(p.system->getRequestorId(this)), m_is_blocking(false),
      m_number_of_TBEs(p.number_of_TBEs),
      m_transitions_per_cycle(p.transitions_per_cycle),
      m_buffer_size(p.buffer_size), m_recycle_latency(p.recycle_latency),
      m_mandatory_queue_latency(p.mandatory_queue_latency),
      m_waiting_mem_retry(false),
      memoryPort(csprintf("%s.memory", name()), this),
      c2cOutPort(csprintf("%s.C2cOut", name()), this),
      c2cInPort(csprintf("%s.C2cIn", name()), this),
      addrRanges(p.addr_ranges.begin(), p.addr_ranges.end()),
      stats(this)
{
    if (m_version == 0) {
        // Combine the statistics from all controllers
        // of this particular type.
        statistics::registerDumpCallback([this]() { collateStats(); });
    }
}

void
AbstractController::init()
{
    stats.delayHistogram.init(10);
    uint32_t size = Network::getNumberOfVirtualNetworks();
    for (uint32_t i = 0; i < size; i++) {
        stats.delayVCHistogram.push_back(new statistics::Histogram(this));
        stats.delayVCHistogram[i]->init(10);
    }

    if (getMemReqQueue()) {
        getMemReqQueue()->setConsumer(this);
    }
    if (getReqToC2cQueue()) {
        getReqToC2cQueue()->setConsumer(this);
    }
    if (getRespToC2cQueue()) {
        getRespToC2cQueue()->setConsumer(this);
    }

    // Initialize the addr->downstream machine mappings. Multiple machines
    // in downstream_destinations can have the same address range if they have
    // different types. If this is the case, mapAddressToDownstreamMachine
    // needs to specify the machine type
    downstreamDestinations.resize();
    for (auto abs_cntrl : params().downstream_destinations) {
        MachineID mid = abs_cntrl->getMachineID();
        const AddrRangeList &ranges = abs_cntrl->getAddrRanges();
        for (const auto &addr_range : ranges) {
            auto i = downstreamAddrMap.find(mid.getType());
            if ((i != downstreamAddrMap.end()) &&
                (i->second.intersects(addr_range) != i->second.end())) {
                fatal("%s: %s mapped to multiple machines of the same type\n",
                    name(), addr_range.to_string());
            }
            downstreamAddrMap[mid.getType()].insert(addr_range, mid);
        }
        downstreamDestinations.add(mid);
    }
    // Initialize the addr->upstream machine list.
    // We do not need to map address -> upstream machine,
    // so we don't examine the address ranges
    upstreamDestinations.resize();
    for (auto abs_cntrl : params().upstream_destinations) {
        upstreamDestinations.add(abs_cntrl->getMachineID());
    }

    // Initialize the chipID->C2CI map
    if (params().chipIDList.size() != 0) {
        for (int i = 0; i < params().chipIDList.size(); ++i) {
            MachineID mid(MachineType::MachineType_Interface, params().c2cHopList[i]);
            c2cHopMap[params().chipIDList[i]] = mid;
        }
    }

    // Initialize the MachineID->ChipID map
    if (params().cntrlList.size() % 3 != 0) {
        fatal("cntrlList size must be divisible by 3");
    }
    
    int numChips = params().cntrlList.size() / 3;

    int globalIdx = 0;

    for (int chipID = 0; chipID < numChips; ++chipID) {
        int l1Count = params().cntrlList[chipID * 3];
        int l2Count = params().cntrlList[chipID * 3 + 1];
        int hnfCount = params().cntrlList[chipID * 3 + 2];

        for (int i = 0; i < l1Count; ++i)
            machineToChipMap.emplace(MachineID
                (MachineType::MachineType_Cache, globalIdx++), chipID);
        for (int i = 0; i < l2Count; ++i)
            machineToChipMap.emplace(MachineID
                (MachineType::MachineType_Cache, globalIdx++), chipID);
        for (int i = 0; i < hnfCount; ++i)
            machineToChipMap.emplace(MachineID
                (MachineType::MachineType_Cache, globalIdx++), chipID);
    }
}

void
AbstractController::resetStats()
{
    stats.delayHistogram.reset();
    uint32_t size = Network::getNumberOfVirtualNetworks();
    for (uint32_t i = 0; i < size; i++) {
        stats.delayVCHistogram[i]->reset();
    }
}

void
AbstractController::regStats()
{
    ClockedObject::regStats();
}

void
AbstractController::profileMsgDelay(uint32_t virtualNetwork, Cycles delay)
{
    assert(virtualNetwork < stats.delayVCHistogram.size());
    stats.delayHistogram.sample(delay);
    stats.delayVCHistogram[virtualNetwork]->sample(delay);
}

void
AbstractController::stallBuffer(MessageBuffer* buf, Addr addr)
{
    if (m_waiting_buffers.count(addr) == 0) {
        MsgVecType* msgVec = new MsgVecType;
        msgVec->resize(m_in_ports, NULL);
        m_waiting_buffers[addr] = msgVec;
    }
    DPRINTF(RubyQueue, "stalling %s port %d addr %#x\n", buf, m_cur_in_port,
            addr);
    assert(m_in_ports > m_cur_in_port);
    (*(m_waiting_buffers[addr]))[m_cur_in_port] = buf;
}

void
AbstractController::wakeUpBuffer(MessageBuffer* buf, Addr addr)
{
    auto iter = m_waiting_buffers.find(addr);
    if (iter != m_waiting_buffers.end()) {
        bool has_other_msgs = false;
        MsgVecType* msgVec = iter->second;
        for (unsigned int port = 0; port < msgVec->size(); ++port) {
            if ((*msgVec)[port] == buf) {
                buf->reanalyzeMessages(addr, clockEdge());
                (*msgVec)[port] = NULL;
            } else if ((*msgVec)[port] != NULL) {
                has_other_msgs = true;
            }
        }
        if (!has_other_msgs) {
            delete msgVec;
            m_waiting_buffers.erase(iter);
        }
    }
}

void
AbstractController::wakeUpBuffers(Addr addr)
{
    if (m_waiting_buffers.count(addr) > 0) {
        //
        // Wake up all possible lower rank (i.e. lower priority) buffers that could
        // be waiting on this message.
        //
        for (int in_port_rank = m_cur_in_port - 1;
             in_port_rank >= 0;
             in_port_rank--) {
            if ((*(m_waiting_buffers[addr]))[in_port_rank] != NULL) {
                (*(m_waiting_buffers[addr]))[in_port_rank]->
                    reanalyzeMessages(addr, clockEdge());
            }
        }
        delete m_waiting_buffers[addr];
        m_waiting_buffers.erase(addr);
    }
}

void
AbstractController::wakeUpAllBuffers(Addr addr)
{
    if (m_waiting_buffers.count(addr) > 0) {
        //
        // Wake up all possible buffers that could be waiting on this message.
        //
        for (int in_port_rank = m_in_ports - 1;
             in_port_rank >= 0;
             in_port_rank--) {
            if ((*(m_waiting_buffers[addr]))[in_port_rank] != NULL) {
                (*(m_waiting_buffers[addr]))[in_port_rank]->
                    reanalyzeMessages(addr, clockEdge());
            }
        }
        delete m_waiting_buffers[addr];
        m_waiting_buffers.erase(addr);
    }
}

void
AbstractController::wakeUpAllBuffers()
{
    //
    // Wake up all possible buffers that could be waiting on any message.
    //

    std::vector<MsgVecType*> wokeUpMsgVecs;
    MsgBufType wokeUpMsgBufs;

    if (m_waiting_buffers.size() > 0) {
        for (WaitingBufType::iterator buf_iter = m_waiting_buffers.begin();
             buf_iter != m_waiting_buffers.end();
             ++buf_iter) {
             for (MsgVecType::iterator vec_iter = buf_iter->second->begin();
                  vec_iter != buf_iter->second->end();
                  ++vec_iter) {
                  //
                  // Make sure the MessageBuffer has not already be reanalyzed
                  //
                  if (*vec_iter != NULL &&
                      (wokeUpMsgBufs.count(*vec_iter) == 0)) {
                      (*vec_iter)->reanalyzeAllMessages(clockEdge());
                      wokeUpMsgBufs.insert(*vec_iter);
                  }
             }
             wokeUpMsgVecs.push_back(buf_iter->second);
        }

        for (std::vector<MsgVecType*>::iterator wb_iter = wokeUpMsgVecs.begin();
             wb_iter != wokeUpMsgVecs.end();
             ++wb_iter) {
             delete (*wb_iter);
        }

        m_waiting_buffers.clear();
    }
}

bool
AbstractController::serviceMemoryQueue()
{
    auto mem_queue = getMemReqQueue();
    assert(mem_queue);
    if (m_waiting_mem_retry || !mem_queue->isReady(clockEdge())) {
        return false;
    }

    const MemoryMsg *mem_msg = (const MemoryMsg*)mem_queue->peek();
    unsigned int req_size = RubySystem::getBlockSizeBytes();
    if (mem_msg->m_Len > 0) {
        req_size = mem_msg->m_Len;
    }

    RequestPtr req
        = std::make_shared<Request>(mem_msg->m_addr, req_size, 0, m_id);
    PacketPtr pkt;
    if (mem_msg->getType() == MemoryRequestType_MEMORY_WB) {
        pkt = Packet::createWrite(req);
        pkt->allocate();
        pkt->setData(mem_msg->m_DataBlk.getData(getOffset(mem_msg->m_addr),
            req_size));
    } else if (mem_msg->getType() == MemoryRequestType_MEMORY_READ) {
        pkt = Packet::createRead(req);
        uint8_t *newData = new uint8_t[req_size];
        pkt->dataDynamic(newData);
    } else {
        panic("Unknown memory request type (%s) for addr %p",
              MemoryRequestType_to_string(mem_msg->getType()),
              mem_msg->m_addr);
    }

    SenderState *s = new SenderState(mem_msg->m_Sender);
    pkt->pushSenderState(s);

    if (RubySystem::getWarmupEnabled()) {
        // Use functional rather than timing accesses during warmup
        mem_queue->dequeue(clockEdge());
        memoryPort.sendFunctional(pkt);
        // Since the queue was popped the controller may be able
        // to make more progress. Make sure it wakes up
        scheduleEvent(Cycles(1));
        recvTimingResp(pkt);
    } else if (memoryPort.sendTimingReq(pkt)) {
        mem_queue->dequeue(clockEdge());
        // Since the queue was popped the controller may be able
        // to make more progress. Make sure it wakes up
        scheduleEvent(Cycles(1));
    } else {
        scheduleEvent(Cycles(1));
        m_waiting_mem_retry = true;
        delete pkt;
        delete s;
    }

    return true;
}

// c2cOutPort serviceReqToC2cQueue
bool
AbstractController::serviceReqToC2cQueue()
{
    auto mem_queue = getReqToC2cQueue();
    assert(mem_queue);
    if (m_waiting_mem_retry || !mem_queue->isReady(clockEdge())) {
        return false;
    }

    const C2cMsg *mem_msg = (const C2cMsg*)mem_queue->peek();
    unsigned int req_size = RubySystem::getBlockSizeBytes();
    if (mem_msg->m_Len > 0) {
        req_size = mem_msg->m_Len;
    }

    RequestPtr req
        = std::make_shared<Request>(mem_msg->m_addr, req_size, 0, m_id);
    PacketPtr pkt;
    
    pkt = new Packet(req, MemCmd::c2c_packet);
    pkt->c2c_msg = mem_msg;

    SenderState *s = new SenderState(mem_msg->m_Sender);
    pkt->pushSenderState(s);

    if (RubySystem::getWarmupEnabled()) {
        panic("serviceReqToC2cQueue Warmup Enabled"); 
        // Use functional rather than timing accesses during warmup
        mem_queue->dequeue(clockEdge());
        memoryPort.sendFunctional(pkt);
        // Since the queue was popped the controller may be able
        // to make more progress. Make sure it wakes up
        scheduleEvent(Cycles(1));
        recvTimingResp(pkt);
    } else if (c2cOutPort.sendTimingReq(pkt)) {
        mem_queue->dequeue(clockEdge());
        // Since the queue was popped the controller may be able
        // to make more progress. Make sure it wakes up
        scheduleEvent(Cycles(1));
    } else {
        scheduleEvent(Cycles(1));
        m_waiting_mem_retry = true;
        delete pkt;
        delete s;
    }

    return true;
}

// c2cInPort serviceReqFromC2cQueue
bool
AbstractController::serviceRespToC2cQueue()
{
    auto resp_queue = getRespToC2cQueue();
    assert(resp_queue);

    if (m_waiting_mem_retry || !resp_queue->isReady(clockEdge())) {
        return false;
    }

    const C2cMsg *mem_msg = (const C2cMsg*)resp_queue->peek();
    unsigned int resp_size = RubySystem::getBlockSizeBytes();
    if (mem_msg->m_Len > 0) {
        resp_size = mem_msg->m_Len;
    }

    RequestPtr req
        = std::make_shared<Request>(mem_msg->m_addr, resp_size, 0, m_id);
    PacketPtr pkt;

    pkt = new Packet(req, MemCmd::c2c_packet);
    pkt->c2c_msg = mem_msg;

    SenderState *s = new SenderState(mem_msg->m_Sender);
    pkt->pushSenderState(s);

    if (RubySystem::getWarmupEnabled()) {
        panic("serviceResponseQueue getWarmupEnabled");
        // Use functional rather than timing accesses during warmup
        resp_queue->dequeue(clockEdge());
        // COMMENTED RECVFUNCTIONAL BECAUSE PROTECTED IN CONTEXT
        //memoryInPort.recvFunctional(pkt);
        // Since the queue was popped the controller may be able
        // to make more progress. Make sure it wakes up
        scheduleEvent(Cycles(1));

        // Not sure about this one 
        recvTimingResp(pkt);
    } else if (c2cInPort.sendTimingResp(pkt)) {
        resp_queue->dequeue(clockEdge());
        // Since the queue was popped the controller may be able
        // to make more progress. Make sure it wakes up
        scheduleEvent(Cycles(1));
    } else {
        panic("AbstractController sendTimingResp failed.");
        scheduleEvent(Cycles(1));
        m_waiting_mem_retry = true;
        delete pkt;
        delete s;
    }

    return true;
}

void
AbstractController::blockOnQueue(Addr addr, MessageBuffer* port)
{
    m_is_blocking = true;
    m_block_map[addr] = port;
}

bool
AbstractController::isBlocked(Addr addr) const
{
    return m_is_blocking && (m_block_map.find(addr) != m_block_map.end());
}

void
AbstractController::unblock(Addr addr)
{
    m_block_map.erase(addr);
    if (m_block_map.size() == 0) {
       m_is_blocking = false;
    }
}

bool
AbstractController::isBlocked(Addr addr)
{
    return (m_block_map.count(addr) > 0);
}

Port &
AbstractController::getPort(const std::string &if_name, PortID idx)
{
    if (if_name == "memory_out_port") {
        return memoryPort;
    } else if (if_name == "c2c_in_port") {
        return c2cInPort;
    } else if (if_name == "c2c_out_port") {
        return c2cOutPort;
    } else {
        fatal("Unknown port: %s", if_name);
    }
}

void
AbstractController::functionalMemoryRead(PacketPtr pkt)
{
    // read from mem. req. queue if write data is pending there
    MessageBuffer *req_queue = getMemReqQueue();
    if (!req_queue || !req_queue->functionalRead(pkt))
        memoryPort.sendFunctional(pkt);
}

int
AbstractController::functionalMemoryWrite(PacketPtr pkt)
{
    int num_functional_writes = 0;

    // Update memory itself.
    memoryPort.sendFunctional(pkt);
    return num_functional_writes + 1;
}

// memory_out_port classic recvTimingResp
void
AbstractController::recvTimingResp(PacketPtr pkt)
{
    assert(getMemRespQueue());
    assert(pkt->isResponse());

    std::shared_ptr<MemoryMsg> msg = std::make_shared<MemoryMsg>(clockEdge());
    (*msg).m_addr = pkt->getAddr();
    (*msg).m_Sender = m_machineID;

    SenderState *s = dynamic_cast<SenderState *>(pkt->senderState);
    (*msg).m_OriginalRequestorMachId = s->id;
    delete s;

    if (pkt->isRead()) {
        (*msg).m_Type = MemoryRequestType_MEMORY_READ;
        (*msg).m_MessageSize = MessageSizeType_Response_Data;

        // Copy data from the packet
        (*msg).m_DataBlk.setData(pkt->getPtr<uint8_t>(), 0,
                                 RubySystem::getBlockSizeBytes());
    } else if (pkt->isWrite()) {
        (*msg).m_Type = MemoryRequestType_MEMORY_WB;
        (*msg).m_MessageSize = MessageSizeType_Writeback_Control;
    } else {
        panic("Incorrect packet type received from memory controller!");
    }
    getMemRespQueue()->enqueue(msg, clockEdge(), cyclesToTicks(Cycles(1)));
    delete pkt;
}

// C2cOutPort c2cOutRecvTimingResp
void
AbstractController::c2cOutRecvTimingResp(PacketPtr pkt)
{
    assert(getRespFromC2cQueue());
    assert(pkt->isResponse());

    std::shared_ptr<C2cMsg> msg = std::make_shared<C2cMsg>(clockEdge());
    (*msg).m_addr = pkt->getAddr();
    (*msg).m_Sender = m_machineID;

    SenderState *s = dynamic_cast<SenderState *>(pkt->senderState);
    (*msg).m_OriginalRequestorMachId = s->id;
    delete s;

    if (pkt->isRead()) {
        (*msg).m_Type = (*(pkt->c2c_msg)).m_Type;
        (*msg).m_DataBlk = (*(pkt->c2c_msg)).m_DataBlk;
        (*msg).m_BitMask = (*(pkt->c2c_msg)).m_BitMask;
        (*msg).m_Responder = (*(pkt->c2c_msg)).m_Responder;

        (*msg).m_Stale = (*(pkt->c2c_msg)).m_Stale;
        (*msg).m_C2c_destination = (*(pkt->c2c_msg)).m_C2c_destination;
        (*msg).m_OriginalRequestor = (*(pkt->c2c_msg)).m_OriginalRequestor;
        (*msg).m_LocalRequestor = (*(pkt->c2c_msg)).m_LocalRequestor;
    } else {
        panic("Incorrect packet type received in the c2c_out_port!");
    }
    getRespFromC2cQueue()->enqueue(msg, clockEdge(), cyclesToTicks(Cycles(1)));
    delete pkt;
}

// C2cInPort recvTimingReq method
void
AbstractController::recvTimingReq(PacketPtr pkt)
{
    assert(getReqFromC2cQueue());
    assert(pkt->isRequest());

    std::shared_ptr<C2cMsg> msg = std::make_shared<C2cMsg>(clockEdge());
    (*msg).m_addr = pkt->getAddr();
    (*msg).m_Sender = m_machineID;

    SenderState *s = dynamic_cast<SenderState *>(pkt->senderState);
    (*msg).m_OriginalRequestorMachId = s->id;
    delete s;

    if (pkt->isRead()) {
        (*msg).m_Type = (*(pkt->c2c_msg)).m_Type;
        (*msg).m_C2c_sharers = (*(pkt->c2c_msg)).m_C2c_sharers;
        (*msg).m_RetToSrc = (*(pkt->c2c_msg)).m_RetToSrc;
        (*msg).m_OriginalRequestor = (*(pkt->c2c_msg)).m_OriginalRequestor;
        //(*msg).m_LocalRequestor = (*(pkt->c2c_msg)).m_LocalRequestor;
        (*msg).m_ReqAck = (*(pkt->c2c_msg)).m_ReqAck;
        (*msg).m_AllowRetry = (*(pkt->c2c_msg)).m_AllowRetry;
        (*msg).m_Priority = (*(pkt->c2c_msg)).m_Priority;
        (*msg).m_Responder = (*(pkt->c2c_msg)).m_Responder;
    } else {
        panic("Incorrect packet type received in the c2c_in_port!");
    }

    getReqFromC2cQueue()->enqueue(msg, clockEdge(), cyclesToTicks(Cycles(1)));
    delete pkt;
}

Tick
AbstractController::recvAtomic(PacketPtr pkt)
{
    return ticksToCycles(memoryPort.sendAtomic(pkt));
}

MachineID
AbstractController::mapAddressToMachine(Addr addr, MachineType mtype) const
{
    NodeID node = m_net_ptr->addressToNodeID(addr, mtype);
    MachineID mach = {mtype, node};
    return mach;
}

MachineID
AbstractController::mapAddressToDownstreamMachine(Addr addr, MachineType mtype)
const
{
    if (mtype == MachineType_NUM) {
        // map to the first match
        for (const auto &i : downstreamAddrMap) {
            const auto mapping = i.second.contains(addr);

            if (mapping != i.second.end())
                return mapping->second;
        }
    }
    else {
        const auto i = downstreamAddrMap.find(mtype);
        if (i != downstreamAddrMap.end()) {
            const auto mapping = i->second.contains(addr);
            if (mapping != i->second.end())
                return mapping->second;
        }
    }
    fatal("%s: couldn't find mapping for address %x mtype=%s\n",
        name(), addr, mtype);
}

MachineID
AbstractController::mapChipIDToC2CI(int ChipID)
const
{
    auto it = c2cHopMap.find(ChipID);
    assert(it != c2cHopMap.end());
    return it->second;
}

int 
AbstractController::mapMachineIDToChipID(MachineID mach)
const
{
    for (const auto& i : machineToChipMap) {
        if (i.first == mach) {
            return i.second;
        }
    }
    panic("MachineID not found in map");
}

// Used to check is inbound request is local or not
bool
AbstractController::hasDownstreamClient(Addr addr, MachineType mtype)
const
{
    if (mtype == MachineType_NUM) {
        // Check for any match
        for (const auto& i : downstreamAddrMap) {
            const auto mapping = i.second.contains(addr);
            if (mapping != i.second.end()) {
                return true;
            }
        }
    } else {
        const auto i = downstreamAddrMap.find(mtype);
        if (i != downstreamAddrMap.end()) {
            const auto mapping = i->second.contains(addr);
            if (mapping != i->second.end()) {
                return true;
            }
        }
    }
    return false;
}

// Classic memory port
bool
AbstractController::MemoryPort::recvTimingResp(PacketPtr pkt)
{
    controller->recvTimingResp(pkt);
    return true;
}

void
AbstractController::MemoryPort::recvReqRetry()
{
    controller->m_waiting_mem_retry = false;
    controller->serviceMemoryQueue();
}

AbstractController::MemoryPort::MemoryPort(const std::string &_name,
                                           AbstractController *_controller,
                                           PortID id)
    : RequestPort(_name, _controller, id), controller(_controller)
{
}

// c2c_out_port
bool
AbstractController::C2cOutPort::recvTimingResp(PacketPtr pkt)
{
    controller->c2cOutRecvTimingResp(pkt);
    return true;
}

void
AbstractController::C2cOutPort::recvReqRetry()
{
    controller->m_waiting_mem_retry = false;
    controller->serviceReqToC2cQueue();
}

AbstractController::C2cOutPort::C2cOutPort(const std::string &_name,
                                           AbstractController *_controller,
                                           PortID id)
    : RequestPort(_name, _controller, id), controller(_controller)
{
}

// c2c_in_port 

AddrRangeList
AbstractController::C2cInPort::getAddrRanges() const
{
    return controller->getAddrRanges();
}

void
AbstractController::C2cInPort::recvFunctional(PacketPtr pkt)
{
    // No implementation for Functionnal
}

bool
AbstractController::C2cInPort::recvTimingReq(PacketPtr pkt)
{
    // Pass it to the controller
    controller->recvTimingReq(pkt);
    return true;
}

AbstractController::C2cInPort::C2cInPort(const std::string &_name,
                                                AbstractController *_controller,
                                                PortID id)
    : ResponsePort(_name, _controller, id), controller(_controller)
{
}

void
AbstractController::C2cInPort::recvRespRetry()
{
    // Not implemented yet
}

AbstractController::
ControllerStats::ControllerStats(statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(fullyBusyCycles,
               "cycles for which number of transistions == max transitions"),
      ADD_STAT(delayHistogram, "delay_histogram")
{
    fullyBusyCycles
        .flags(statistics::nozero);
    delayHistogram
        .flags(statistics::nozero);
}

} // namespace ruby
} // namespace gem5
