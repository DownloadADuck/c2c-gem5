
#include <iostream>
#include <memory>

#include "mem/ruby/fwd_interface/Interface_Entry.hh"
#include "mem/ruby/system/RubySystem.hh"

namespace gem5
{

namespace ruby
{

/** \brief Print the state of this object */
void
Interface_Entry::print(std::ostream& out) const
{
    out << "[Interface_Entry: ";
    out << "InterfaceState = " << m_InterfaceState << " ";
    out << "Sharers = " << m_Sharers << " ";
    out << "Owner = " << m_Owner << " ";
    out << "]";
}
} // namespace ruby
} // namespace gem5