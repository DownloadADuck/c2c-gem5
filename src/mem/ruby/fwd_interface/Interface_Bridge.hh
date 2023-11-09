#ifndef __Interface_Bridge_HH__
#define __Interface_Bridge_HH__

#include "mem/port.hh"
#include "params/Interface_Bridge.hh"
#include "sim/sim_object.hh"

namespace gem5
{

class InterfaceBridge : public SimObject
{
    private:
        /**
         * Port on the chip0 side that receives requests.
         * Forwards them to chip1.
         * This object is fully blocking. Only a single request can be 
         * oustanding at a time.
         */
        class chip0SidePort : public ResponsePort
        {
            private:
                // The object that owns this object (Bridge)
                InterfaceBridge *owner;
                // If we tried to send a packet and it was blocked, store here
                PacketPtr blockedPacket;

            public:
                // Constructor
                chip0SidePort(const std::string& name, InterfaceBridge *owner):
                    ResponsePort(name, owner), owner(owner), blockedPacket(nullptr)
                { }

                /**
                 * Send a packet across this port.
                 * 
                 * @param packet to send.
                 */
                void sendPacket(PacketPtr pkt);

                /**
                 * Send a retry to the peer port only if needed. 
                 */
                void trySendRetry();
            
            protected:
                // Receive a packet from the chip0 request port
                Tick recvAtomic(PacketPtr pkt) override
                { panic("recvAtomic unimplemented"); }
        };

        /**
         * Port on the chip1 side that send requests
         */
        class chip1SidePort : public RequestPort
        {
            private:
                // The object that own this object (Bridge)
                InterfaceBridge *owner;

                // If we tried to send a packed and it was blockd, store here
                PacketPtr blockedPacket;

            public:
                // Constructor
                chip1SidePort(const std::string& name, InterfaceBridge *owner):
                    RequestPort(name, owner), owner(owner), blockedPacket(nullptr)
                { }

                void sendPacket(PacketPtr pkt);

            protected:
                ///**
                // * Receive a timing response from the response port.
                // */
                //bool recvTimingResp(PacketPtr pkt) override;
        };

        // Handle request from the chip0 side
        bool handleRequest(PacketPtr pkt);

        // Handle response from the memory side
        bool handleResponse(PacketPtr pkt);

        // Instantiation of the chip0-side ports
        chip0SidePort chip0Port;

        // Instantiation of the chip1-side ports
        chip1SidePort chip1Port;

        // True if currently blocked waiting for a response
        bool blocked;

    public:

        // Constructor
        InterfaceBridge(const InterfaceBridgeParams &params);

        /**
         * Get a port with a given name and index. This is used at
         * binding time and returns a reference to a protocol-agnostic
         * port.
         *
         * @param if_name Port name
         * @param idx Index in the case of a VectorPort
         *
         * @return A reference to the given port
         */
        Port &getPort(const std::string &if_name,
                      PortID idx=InvalidPortID) override;
};

} // namespace gem5

#endif // __Interface_Bridge_HH__