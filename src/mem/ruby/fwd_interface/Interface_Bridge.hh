#ifndef __Interface_Bridge_HH__
#define __Interface_Bridge_HH__

#include "mem/port.hh"
#include "params/InterfaceBridge.hh"
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

                // True is the port needs to send a retry req.
                bool needRetry;

                // If we tried to send a packet and it was blocked, store here
                PacketPtr blockedPacket;

            public:
                // Constructor
                chip0SidePort(const std::string& name, InterfaceBridge *owner):
                    ResponsePort(name, owner), owner(owner), needRetry(false),
                    blockedPacket(nullptr)
                { }

                /**
                 * Send a packet across this port.
                 * 
                 * @param packet to send.
                 */
                void sendPacket(PacketPtr pkt);

                /**
                 * Get a list of the non-overlapping address ranges the owner 
                 * is responsible for. All response ports must override this 
                 * function and return a populated list with at least one item.
                 */
                AddrRangeList getAddrRanges() const override;

                /**
                 * Send a retry to the peer port only if needed. 
                 */
                void trySendRetry();
            
            protected:
                // Receive a packet from the chip0 request port
                Tick recvAtomic(PacketPtr pkt) override
                { panic("recvAtomic unimplemented"); }

                /**
                 * Receive a functional request packet from the request port.
                 * 
                 * @param packet the requestor sent.
                 */
                void recvFunctional(PacketPtr pkt) override;

                /**
                 * Receive a timing request from the request port.
                 */
                bool recvTimingReq(PacketPtr pkt) override;

                /**
                 * Called by the request port if sendTimingResp was called on
                 * this response port and was unsuccesfull.
                 */
                void recvRespRetry() override;
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
                /**
                 * Receive a timing response from the response port.
                 */
                bool recvTimingResp(PacketPtr pkt) override;

                /**
                 * Called by the response port if senTimingReq was called on
                 * this request port and was unsuccesful.
                 */
                void recvReqRetry() override;

                /**
                 * Called to receive an address range from the peer responder
                 * port. The default implementation ignores the change and does
                 * nothing. Override this function in a defived class if the 
                 * owner needs to be aware of the address ranges, e.g. in an
                 * interconnect component like a bus.
                 */
                void recvRangeChange() override;
        };

        // Handle request from the chip0 side
        bool handleRequest(PacketPtr pkt);

        // Handle response from the memory side
        bool handleResponse(PacketPtr pkt);

        // Handle a packet functionally
        void handleFunctional(PacketPtr pkt);

        // Return the address ranges this obj is responsible for
        AddrRangeList getAddrRanges() const;

        // Tell the cpu side to ask for our memory ranges
        void sendRangeChange();

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