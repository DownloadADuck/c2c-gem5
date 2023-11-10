#include "mem/ruby/fwd_interface/Interface_Bridge.hh"

#include "base/trace.hh"
#include "debug/InterfaceBridge.hh"

namespace gem5
{

InterfaceBridge::InterfaceBridge(const InterfaceBridgeParams &params) :
    SimObject(params),
    chip0Port(params.name + ".chip0_port", this),
    chip1Port(params.name + ".chip1_port", this),
    blocked(false)
{
}

Port &
InterfaceBridge::getPort(const std::string &if_name, PortID idx)
{
    panic_if(idx != InvalidPortID, "This object doesn't support vector ports");

    // Name from the Python SimObject declaration (Interface_Bridge.py)
    if (if_name == "chip0_port") {
        return chip0Port;
    } else if (if_name == "chip1_port") {
        return chip1Port;
    } else {
        // Pass it along to our super class
        return SimObject::getPort(if_name, idx);
    }
}

// CHIP0 SIDE
void
InterfaceBridge::chip0SidePort::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked");

    // If we can't send the packet across the port, store it for later
    if(!sendTimingResp(pkt)) {
        blockedPacket = pkt;
    }
}

AddrRangeList
InterfaceBridge::chip0SidePort::getAddrRanges() const
{
    return owner->getAddrRanges();
}

void
InterfaceBridge::chip0SidePort::trySendRetry()
{
    if (needRetry && blockedPacket == nullptr) {
        // Only send a retry if the port is now free
        needRetry = false;
        DPRINTF(InterfaceBridge, "Sending retry req for %d\n", id);
        sendRetryReq();
    }
}

// CHIP1 SIDE
void
InterfaceBridge::chip1SidePort::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked");

    // If we can't send the packet across the port, store it for later
    if (!sendTimingReq(pkt)) {
        blockedPacket = pkt;
    }
}

// BRIDGE FUNCTIONS
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
    chip0Port.sendPacket(pkt);

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
    chip0Port.sendPacket(pkt);

    // For the chip0, it there is a retry, it is done now since this Bridge
    // object may be unblocked now
    chip0Port.trySendRetry();

    return true;
}

} // namespace gem5