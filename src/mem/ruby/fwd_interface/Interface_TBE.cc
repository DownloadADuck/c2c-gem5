#include <iostream>
#include <memory>

#include "mem/ruby/fwd_interface/Interface_TBE.hh"
#include "mem/ruby/system/RubySystem.hh"

namespace gem5
{

namespace ruby
{

/** \brief Print the state of this object */
void
Interface_TBE::print(std::ostream& out) const
{
    out << "[Interface_TBE: ";
    out << "storSlot = " << m_storSlot << " ";
    out << "addr = " << printAddress(m_addr) << " ";
    out << "accAddr = " << printAddress(m_accAddr) << " ";
    out << "accSize = " << m_accSize << " ";
    out << "state = " << m_state << " ";
    out << "dataBlk = " << m_dataBlk << " ";
    out << "dataBlkValid = " << m_dataBlkValid << " ";
    out << "rxtxBytes = " << m_rxtxBytes << " ";
    out << "requestor = " << m_requestor << " ";
    out << "destination = " << m_destination << " ";
    out << "useDataSepResp = " << m_useDataSepResp << " ";
    out << "]";
}
} // namespace ruby
} // namespace gem5