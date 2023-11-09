#include "src/mem/ruby/fwd_interface/Bridge.hh"

#include "base/trace.hh"
#include "debug/Bridge.hh"

namespace gem5
{

Bridge::Bridge(const BridgeParams &params) :
    SimObject(params),
    chip0Port(params.name + ".chip0_port", this),
    chip1Port(params.name + ".chip1_port", this),
    blocked(false)
{
}

Port &
Bridge::getPort(const std::string &if_name, PortID idx)
{
    panic_if(idx != InvalidPortID, "This object doesn't support vector ports");

    // Name from the Python SimObject declaration (Bridge.py)
    if (if_name == "chip0_port") {
        return chip0Port;
    } else if (if_name == "chip1_port") {
        return chip1Port;
    } else {
        // Pass it along to our super class
        return SimObject::getPort(if_name, idx);
    }
}

void
Bridge::chip0SidePort::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked");

    // If we can't send the packet across the port, store it for later
    if(!sendTimingResp(pkt)) {
        blockedPacket = pkt;
    }
}

void
Bridge::chip1SidePort::sendPacket(PacketPtr pkt)
{
    panic_if(blockedPacket != nullptr, "Should never try to send if blocked");

    // If we can't send the packet across the port, store it for later
    if (!sendTimingReq(pkt)) {
        blockedPacket = pkt;
    }
}

bool
Bridge::handleRequest(PacketPtr pkt)
{
    if (blocked) {
        // There is currently an outstanding request. Stall.
        return false;
    }

    DPRINTF(Bridge, "Request for addr %#x\n", pkt->getAddr());

    // This object is now blocked waiting for the response to this packet.
    blocked = true;

    // Simply forward to the chip1 port
    chip0Port.sendPacket(pkt);

    return true;
}

bool
Bridge::handleResponse(PacketPtr pkt)
{
    assert(blocked);
    DPRINTF(Bridge, "Response for addr %#x\n", pkt->getAddr());

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