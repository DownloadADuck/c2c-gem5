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
        class chip0Request : public RequestPort
        {
            private:
                InterfaceBridge *owner;

                PacketPtr blockedPacket;

            public:
                chip0Request(const std::string& name, InterfaceBridge *owner):
                    RequestPort(name, owner), owner(owner), blockedPacket(nullptr)
                { }

                void sendPacket(PacketPtr pkt);

            protected:
                bool recvTimingResp(PacketPtr pkt) override;

                void recvReqRetry() override;

                void recvRangeChange() override;
        };

        class chip0Response : public ResponsePort
        {
            private:
                InterfaceBridge *owner;

                bool needRetry;
                PacketPtr blockedPacket;

            public:
                // Constructor
                chip0Response(const std::string& name, InterfaceBridge *owner):
                    ResponsePort(name, owner), owner(owner), needRetry(false),
                    blockedPacket(nullptr)
                { }

                void sendPacket(PacketPtr pkt);

                AddrRangeList getAddrRanges() const override;

                void trySendRetry();
            
            protected:
                // Receive a packet from the chip0 request port
                Tick recvAtomic(PacketPtr pkt) override
                { panic("recvAtomic unimplemented"); }

                void recvFunctional(PacketPtr pkt) override;

                bool recvTimingReq(PacketPtr pkt) override;

                void recvRespRetry() override;
        };


        /**
         * Port on the chip1 side that send requests
         */
        class chip1Request : public RequestPort
        {
            private:
                InterfaceBridge *owner;

                PacketPtr blockedPacket;

            public:
                chip1Request(const std::string& name, InterfaceBridge *owner):
                    RequestPort(name, owner), owner(owner), blockedPacket(nullptr)
                { }

                void sendPacket(PacketPtr pkt);

            protected:
                bool recvTimingResp(PacketPtr pkt) override;

                void recvReqRetry() override;

                void recvRangeChange() override;
        };

        class chip1Response : public ResponsePort
        {
            private:
                InterfaceBridge *owner;

                bool needRetry;
                PacketPtr blockedPacket;

            public:
                // Constructor
                chip1Response(const std::string& name, InterfaceBridge *owner):
                    ResponsePort(name, owner), owner(owner), needRetry(false),
                    blockedPacket(nullptr)
                { }

                void sendPacket(PacketPtr pkt);

                AddrRangeList getAddrRanges() const override;

                void trySendRetry();
            
            protected:
                // Receive a packet from the chip0 request port
                Tick recvAtomic(PacketPtr pkt) override
                { panic("recvAtomic unimplemented"); }

                void recvFunctional(PacketPtr pkt) override;

                bool recvTimingReq(PacketPtr pkt) override;

                void recvRespRetry() override;
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

        // Ports instantiation
        // chip0-side
        chip0Request chip0RequestPort;
        chip0Response chip0ResponsePort;
        // chip1-side
        //chip1Request chip1RequestPort;
        //chip1Response chip1ResponsePort;

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