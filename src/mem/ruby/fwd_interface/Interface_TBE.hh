#ifndef __Interface_TBE_HH__
#define __IntInterface_TBE_HH__

#include <iostream>

#include "mem/ruby/slicc_interface/RubySlicc_Util.hh"

#include "mem/ruby/fwd_interface/Interface_State.hh"
#include "mem/ruby/protocol/DataBlock.hh"
#include "mem/ruby/protocol/WriteMask.hh"
#include "mem/ruby/protocol/MachineID.hh"
#include "mem/ruby/protocol/MachineID.hh"
namespace gem5
{

namespace ruby
{

class Interface_TBE
{
  public:
    Interface_TBE
()
		{
        m_storSlot = 0;
         // default value of int
        // m_addr has no default
        // m_accAddr has no default
        m_accSize = 0;
         // default value of int
        m_state = Interface_State_IDLE;
         // default value of Interface_State
        // m_dataBlk has no default
        // m_dataBlkValid has no default
        m_rxtxBytes = 0;
         // default value of int
        // m_requestor has no default
        // m_destination has no default
        m_useDataSepResp = false;
         // default value of bool
    }
    Interface_TBE(const Interface_TBE&) = default;
    Interface_TBE
    &operator=(const Interface_TBE&) = default;
    Interface_TBE(const int& local_storSlot, const Addr& local_addr, const Addr& local_accAddr, const int& local_accSize, const Interface_State& local_state, const DataBlock& local_dataBlk, const WriteMask& local_dataBlkValid, const int& local_rxtxBytes, const MachineID& local_requestor, const MachineID& local_destination, const bool& local_useDataSepResp)
    {
        m_storSlot = local_storSlot;
        m_addr = local_addr;
        m_accAddr = local_accAddr;
        m_accSize = local_accSize;
        m_state = local_state;
        m_dataBlk = local_dataBlk;
        m_dataBlkValid = local_dataBlkValid;
        m_rxtxBytes = local_rxtxBytes;
        m_requestor = local_requestor;
        m_destination = local_destination;
        m_useDataSepResp = local_useDataSepResp;
    }
    Interface_TBE*
    clone() const
    {
         return new Interface_TBE(*this);
    }
    // Const accessors methods for each field
    /** \brief Const accessor method for storSlot field.
     *  \return storSlot field
     */
    const int&
    getstorSlot() const
    {
        return m_storSlot;
    }
    /** \brief Const accessor method for addr field.
     *  \return addr field
     */
    const Addr&
    getaddr() const
    {
        return m_addr;
    }
    /** \brief Const accessor method for accAddr field.
     *  \return accAddr field
     */
    const Addr&
    getaccAddr() const
    {
        return m_accAddr;
    }
    /** \brief Const accessor method for accSize field.
     *  \return accSize field
     */
    const int&
    getaccSize() const
    {
        return m_accSize;
    }
    /** \brief Const accessor method for state field.
     *  \return state field
     */
    const Interface_State&
    getstate() const
    {
        return m_state;
    }
    /** \brief Const accessor method for dataBlk field.
     *  \return dataBlk field
     */
    const DataBlock&
    getdataBlk() const
    {
        return m_dataBlk;
    }
    /** \brief Const accessor method for dataBlkValid field.
     *  \return dataBlkValid field
     */
    const WriteMask&
    getdataBlkValid() const
    {
        return m_dataBlkValid;
    }
    /** \brief Const accessor method for rxtxBytes field.
     *  \return rxtxBytes field
     */
    const int&
    getrxtxBytes() const
    {
        return m_rxtxBytes;
    }
    /** \brief Const accessor method for requestor field.
     *  \return requestor field
     */
    const MachineID&
    getrequestor() const
    {
        return m_requestor;
    }
    /** \brief Const accessor method for destination field.
     *  \return destination field
     */
    const MachineID&
    getdestination() const
    {
        return m_destination;
    }
    /** \brief Const accessor method for useDataSepResp field.
     *  \return useDataSepResp field
     */
    const bool&
    getuseDataSepResp() const
    {
        return m_useDataSepResp;
    }
    // Non const Accessors methods for each field
    /** \brief Non-const accessor method for storSlot field.
     *  \return storSlot field
     */
    int&
    getstorSlot()
    {
        return m_storSlot;
    }
    /** \brief Non-const accessor method for addr field.
     *  \return addr field
     */
    Addr&
    getaddr()
    {
        return m_addr;
    }
    /** \brief Non-const accessor method for accAddr field.
     *  \return accAddr field
     */
    Addr&
    getaccAddr()
    {
        return m_accAddr;
    }
    /** \brief Non-const accessor method for accSize field.
     *  \return accSize field
     */
    int&
    getaccSize()
    {
        return m_accSize;
    }
    /** \brief Non-const accessor method for state field.
     *  \return state field
     */
    Interface_State&
    getstate()
    {
        return m_state;
    }
    /** \brief Non-const accessor method for dataBlk field.
     *  \return dataBlk field
     */
    DataBlock&
    getdataBlk()
    {
        return m_dataBlk;
    }
    /** \brief Non-const accessor method for dataBlkValid field.
     *  \return dataBlkValid field
     */
    WriteMask&
    getdataBlkValid()
    {
        return m_dataBlkValid;
    }
    /** \brief Non-const accessor method for rxtxBytes field.
     *  \return rxtxBytes field
     */
    int&
    getrxtxBytes()
    {
        return m_rxtxBytes;
    }
    /** \brief Non-const accessor method for requestor field.
     *  \return requestor field
     */
    MachineID&
    getrequestor()
    {
        return m_requestor;
    }
    /** \brief Non-const accessor method for destination field.
     *  \return destination field
     */
    MachineID&
    getdestination()
    {
        return m_destination;
    }
    /** \brief Non-const accessor method for useDataSepResp field.
     *  \return useDataSepResp field
     */
    bool&
    getuseDataSepResp()
    {
        return m_useDataSepResp;
    }
    // Mutator methods for each field
    /** \brief Mutator method for storSlot field */
    void
    setstorSlot(const int& local_storSlot)
    {
        m_storSlot = local_storSlot;
    }
    /** \brief Mutator method for addr field */
    void
    setaddr(const Addr& local_addr)
    {
        m_addr = local_addr;
    }
    /** \brief Mutator method for accAddr field */
    void
    setaccAddr(const Addr& local_accAddr)
    {
        m_accAddr = local_accAddr;
    }
    /** \brief Mutator method for accSize field */
    void
    setaccSize(const int& local_accSize)
    {
        m_accSize = local_accSize;
    }
    /** \brief Mutator method for state field */
    void
    setstate(const Interface_State& local_state)
    {
        m_state = local_state;
    }
    /** \brief Mutator method for dataBlk field */
    void
    setdataBlk(const DataBlock& local_dataBlk)
    {
        m_dataBlk = local_dataBlk;
    }
    /** \brief Mutator method for dataBlkValid field */
    void
    setdataBlkValid(const WriteMask& local_dataBlkValid)
    {
        m_dataBlkValid = local_dataBlkValid;
    }
    /** \brief Mutator method for rxtxBytes field */
    void
    setrxtxBytes(const int& local_rxtxBytes)
    {
        m_rxtxBytes = local_rxtxBytes;
    }
    /** \brief Mutator method for requestor field */
    void
    setrequestor(const MachineID& local_requestor)
    {
        m_requestor = local_requestor;
    }
    /** \brief Mutator method for destination field */
    void
    setdestination(const MachineID& local_destination)
    {
        m_destination = local_destination;
    }
    /** \brief Mutator method for useDataSepResp field */
    void
    setuseDataSepResp(const bool& local_useDataSepResp)
    {
        m_useDataSepResp = local_useDataSepResp;
    }
    void print(std::ostream& out) const;
  //private:
    /** Slot in the storage tracker occupied by this entry */
    int m_storSlot;
    /** Line address for this TBE */
    Addr m_addr;
    /** Original access address. Set only for Write*Ptl */
    Addr m_accAddr;
    /** Access size. Set only for Write*Ptl */
    int m_accSize;
    /** Current line state */
    Interface_State m_state;
    /** Transaction data */
    DataBlock m_dataBlk;
    /** valid bytes in dataBlk */
    WriteMask m_dataBlkValid;
    /** Bytes sent or received */
    int m_rxtxBytes;
    /** Requestor that originated this request */
    MachineID m_requestor;
    /** Where we are sending data */
    MachineID m_destination;
    /** Replies with DataSepResp instead of CompData */
    bool m_useDataSepResp;
};
inline ::std::ostream&
operator<<(::std::ostream& out, const Interface_TBE& obj)
{
    obj.print(out);
    out << ::std::flush;
    return out;
}

} // namespace ruby
} // namespace gem5

#endif // __Interface_TBE_HH__
