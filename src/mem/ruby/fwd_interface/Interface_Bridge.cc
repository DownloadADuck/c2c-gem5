#include "mem/ruby/fwd_interface/Interface_Bridge.hh"

#include "base/trace.hh"
#include "debug/InterfaceBridge.hh"

namespace gem5
{

InterfaceBridge::InterfaceBridge(const InterfaceBridgeParams &params) :
    SimObject(params),
    chip0RequestPort(params.name + ".chip0Request", this),
    chip0ResponsePort(params.name + ".chip0Response", this),
//    chip1RequestPort(params.name + ".chip1Request", this),
//    chip1ResponsePort(params.name + ".chip1Response", this),
    blocked(false)
{
}

Port &
InterfaceBridge::getPort(const std::string &if_name, PortID idx)
{
    panic_if(idx != InvalidPortID, "This object doesn't support vector ports");

    // Name from the Python SimObject declaration (Interface_Bridge.py)
    if (if_name == "chip0Request") {
        return chip0RequestPort;
    } else if (if_name == "chip0Response") {
        return chip0ResponsePort;
//    } else if (if_name == "chip1Request") {
//        return chip1RequestPort;
//    } else if (if_name == "chip1Response") {
//        return chip1ResponsePort;
    } else {
        // Pass it along to our super class
        return SimObject::getPort(if_name, idx);
    }
}

// CHIP0 SIDE /////////////////////////////////////////////////////////////////
// REQUEST //
void
InterfaceBridge::chip0Request::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked");

    // If we can't send the packet across the port, store it for later
    if (!sendTimingReq(pkt)) {
        blockedPacket = pkt;
    }
}

bool
InterfaceBridge::chip0Request::recvTimingResp(PacketPtr pkt)
{
    // Just forward to the memobj
    return owner->handleResponse(pkt);
}

void
InterfaceBridge::chip0Request::recvReqRetry()
{
    // If this is called, we have a blocked packet
    assert(blockedPacket != nullptr);

    // Grab the blocked packet
    PacketPtr pkt = blockedPacket;
    blockedPacket = nullptr;

    // Try to resend it
    sendPacket(pkt);
}

void
InterfaceBridge::chip0Request::recvRangeChange()
{
    owner->sendRangeChange();
}

// RESPONSE //
void
InterfaceBridge::chip0Response::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked");

    // If we can't send the packet across the port, store it for later
    if(!sendTimingResp(pkt)) {
        blockedPacket = pkt;
    }
}

AddrRangeList
InterfaceBridge::chip0Response::getAddrRanges() const
{
    return owner->getAddrRanges();
}

void
InterfaceBridge::chip0Response::trySendRetry()
{
    if (needRetry && blockedPacket == nullptr) {
        // Only send a retry if the port is now free
        needRetry = false;
        DPRINTF(InterfaceBridge, "Sending retry req for %d\n", id);
        sendRetryReq();
    }
}

void
InterfaceBridge::chip0Response::recvFunctional(PacketPtr pkt)
{
    // Just forward to the memobj
    return owner->handleFunctional(pkt);
}

bool
InterfaceBridge::chip0Response::recvTimingReq(PacketPtr pkt)
{
    // Just forward to the memobj
    if (!owner->handleRequest(pkt)) {
        needRetry = true;
        return false;
    } else {
        return true;
    }
}

void
InterfaceBridge::chip0Response::recvRespRetry()
{
    // If this is called, we have a blocked packet
    assert(blockedPacket != nullptr);

    // Grab the blocked packet
    PacketPtr pkt = blockedPacket;
    blockedPacket = nullptr;

    // Try to resend it
    sendPacket(pkt);
}

///////////////////////////////////////////////////////////////////////////////

// CHIP1 SIDE /////////////////////////////////////////////////////////////////
// REQUEST //
void
InterfaceBridge::chip1Request::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked");

    // If we can't send the packet across the port, store it for later
    if (!sendTimingReq(pkt)) {
        blockedPacket = pkt;
    }
}

bool
InterfaceBridge::chip1Request::recvTimingResp(PacketPtr pkt)
{
    // Just forward to the memobj
    return owner->handleResponse(pkt);
}

void
InterfaceBridge::chip1Request::recvReqRetry()
{
    // If this is called, we have a blocked packet
    assert(blockedPacket != nullptr);

    // Grab the blocked packet
    PacketPtr pkt = blockedPacket;
    blockedPacket = nullptr;

    // Try to resend it
    sendPacket(pkt);
}

void
InterfaceBridge::chip1Request::recvRangeChange()
{
    owner->sendRangeChange();
}

// RESPONSE //
void
InterfaceBridge::chip1Response::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked");

    // If we can't send the packet across the port, store it for later
    if(!sendTimingResp(pkt)) {
        blockedPacket = pkt;
    }
}

AddrRangeList
InterfaceBridge::chip1Response::getAddrRanges() const
{
    return owner->getAddrRanges();
}

void
InterfaceBridge::chip1Response::trySendRetry()
{
    if (needRetry && blockedPacket == nullptr) {
        // Only send a retry if the port is now free
        needRetry = false;
        DPRINTF(InterfaceBridge, "Sending retry req for %d\n", id);
        sendRetryReq();
    }
}

void
InterfaceBridge::chip1Response::recvFunctional(PacketPtr pkt)
{
    // Just forward to the memobj
    return owner->handleFunctional(pkt);
}

bool
InterfaceBridge::chip1Response::recvTimingReq(PacketPtr pkt)
{
    // Just forward to the memobj
    if (!owner->handleRequest(pkt)) {
        needRetry = true;
        return false;
    } else {
        return true;
    }
}

void
InterfaceBridge::chip1Response::recvRespRetry()
{
    // If this is called, we have a blocked packet
    assert(blockedPacket != nullptr);

    // Grab the blocked packet
    PacketPtr pkt = blockedPacket;
    blockedPacket = nullptr;

    // Try to resend it
    sendPacket(pkt);
}

///////////////////////////////////////////////////////////////////////////////

// BRIDGE FUNCTIONS ///////////////////////////////////////////////////////////
bool
InterfaceBridge::handleRequest(PacketPtr pkt)
{
    if (blocked) {
        // There is currently an outstanding request. Stall.
        return false;
    }

    DPRINTF(InterfaceBridge, "Request for addr %#x\n", pkt->getAddr());

    // This object is now blocked waiting for the response to this packet.
    blocked = true;

    // Simply forward to the chip1 port
    chip0ResponsePort.sendPacket(pkt);

    return true;
}

bool
InterfaceBridge::handleResponse(PacketPtr pkt)
{
    assert(blocked);
    DPRINTF(InterfaceBridge, "Response for addr %#x\n", pkt->getAddr());

    // The packet is done.
    // Put it in the port, no need for this object to stall more
    // We need to freee the resource before sending the packet
    blocked = false;

    // Forward to the port
    chip0RequestPort.sendPacket(pkt);

    // For the chip0, it there is a retry, it is done now since this Bridge
    // object may be unblocked now
    chip0ResponsePort.trySendRetry();

    return true;
}

void
InterfaceBridge::handleFunctional(PacketPtr pkt)
{
    // Just pass this to the chip1 side to handle for now
//    chip1RequestPort.sendFunctional(pkt);
}

AddrRangeList
InterfaceBridge::getAddrRanges() const
{
    DPRINTF(InterfaceBridge, "Sending new ranges\n");
    // Just use the same ranges as whatever is on the memory side
//    return chip1RequestPort.getAddrRanges();
}

void
InterfaceBridge::sendRangeChange()
{
    chip0ResponsePort.sendRangeChange();
}

} // namespace gem5