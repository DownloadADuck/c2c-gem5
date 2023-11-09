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

}

void
Bridge::chip1SidePort::sendPacket(PacketPtr pkt)
{

}

bool
Bridge::handleRequest(PacketPtr pkt)
{

}

bool
Bridge::handleResponse(PacketPtr pkt)
{

}

} // namespace gem5